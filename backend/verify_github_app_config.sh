#!/bin/bash
# GitHub App 配置验证脚本
# 运行方式: ./verify_github_app_config.sh

# 不使用 set -e 以允许继续检查

echo "=========================================="
echo "  GitHub App 配置验证"
echo "=========================================="

cd "$(dirname "$0")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果
PASS=0
FAIL=0

check_pass() {
    echo "${GREEN}✓ $1${NC}"
    ((PASS++))
}

check_fail() {
    echo "${RED}✗ $1${NC}"
    echo "  → $2"
    ((FAIL++))
}

check_warn() {
    echo "${YELLOW}⚠ $1${NC}"
    echo "  → $2"
}

# 1. 检查后端是否运行
echo ""
echo "=== 1. 后端服务状态 ==="
if lsof -i :8000 >/dev/null 2>&1; then
    check_pass "后端服务运行中 (端口 8000)"
else
    check_fail "后端服务未运行" "运行: uvicorn app.main:app --reload"
fi

# 2. 检查数据库连接
echo ""
echo "=== 2. 数据库连接 ==="
if mysql -u root -ppassword -e "SELECT 1 FROM codeguard.vendors LIMIT 1" >/dev/null 2>&1; then
    check_pass "数据库连接正常"
else
    check_fail "数据库连接失败" "启动 Docker MySQL: docker-compose up -d"
fi

# 3. 检查 Redis 连接
echo ""
echo "=== 3. Redis 连接 ==="
if redis-cli ping >/dev/null 2>&1; then
    check_pass "Redis 连接正常"
else
    check_warn "Redis 连接失败" "启动 Docker Redis: docker-compose up -d"
fi

# 4. 检查 ngrok 配置
echo ""
echo "=== 4. ngrok 配置 ==="
if ngrok config check >/dev/null 2>&1; then
    check_pass "ngrok 已配置 authtoken"
    
    # 检查 ngrok 是否运行
    if curl -s http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
        NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'https://[^"]*ngrok-free.app' | head -1)
        check_pass "ngrok 隧道运行中: $NGROK_URL"
    else
        check_warn "ngrok 隧道未运行" "运行: ngrok http 8000"
    fi
else
    check_fail "ngrok 未配置" "配置: ngrok config add-authtoken <your-token>"
fi

# 5. 检查 .env 配置
echo ""
echo "=== 5. GitHub App 配置 ==="

# 检查配置文件
source venv/bin/activate
CONFIG_CHECK=$(python -c "
from app.core.config import settings, get_private_key
import json

result = {
    'app_id': settings.GITHUB_APP_ID,
    'webhook_secret': settings.GITHUB_WEBHOOK_SECRET,
    'installation_id': settings.GITHUB_APP_INSTALLATION_ID,
    'private_key': bool(get_private_key()),
}

print(json.dumps(result))
" 2>/dev/null || echo '{"error": true}')

if echo "$CONFIG_CHECK" | grep -q '"error"'; then
    check_fail "配置加载失败" "检查 .env 文件格式"
else
    APP_ID=$(echo "$CONFIG_CHECK" | python -c "import json,sys; print(json.load(sys.stdin)['app_id'])")
    WEBHOOK_SECRET=$(echo "$CONFIG_CHECK" | python -c "import json,sys; print(json.load(sys.stdin)['webhook_secret'])")
    INSTALLATION_ID=$(echo "$CONFIG_CHECK" | python -c "import json,sys; print(json.load(sys.stdin)['installation_id'])")
    HAS_PRIVATE_KEY=$(echo "$CONFIG_CHECK" | python -c "import json,sys; print(json.load(sys.stdin)['private_key'])")
    
    # App ID
    if [ "$APP_ID" != "" ] && [ "$APP_ID" != "placeholder_replace_with_actual_app_id" ]; then
        check_pass "GITHUB_APP_ID: $APP_ID"
    else
        check_fail "GITHUB_APP_ID 未配置" "在 .env 中填写 GitHub App ID"
    fi
    
    # Webhook Secret
    if [ "$WEBHOOK_SECRET" != "" ]; then
        check_pass "GITHUB_WEBHOOK_SECRET 已设置"
    else
        check_fail "GITHUB_WEBHOOK_SECRET 未配置" "在 .env 中填写 webhook secret"
    fi
    
    # Installation ID
    if [ "$INSTALLATION_ID" != "0" ]; then
        check_pass "GITHUB_APP_INSTALLATION_ID: $INSTALLATION_ID"
    else
        check_fail "GITHUB_APP_INSTALLATION_ID 未配置" "安装 App 后获取 ID"
    fi
    
    # Private Key
    if [ "$HAS_PRIVATE_KEY" = "True" ]; then
        check_pass "私钥已配置"
    else
        check_fail "私钥未配置" "保存私钥到 backend/private-key.pem 或填写 GITHUB_APP_PRIVATE_KEY"
    fi
fi

# 6. 检查 webhook 端点
echo ""
echo "=== 6. API 端点检查 ==="

# 健康检查端点
HEALTH=$(curl -s http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo '{"error": true}')
if echo "$HEALTH" | grep -q '"status"'; then
    check_pass "/health 端点正常"
else
    check_warn "/health 端点未响应" "检查后端是否正确启动"
fi

# Webhook 端点检查（仅检查路由是否注册）
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/webhooks/github >/dev/null 2>&1 || true

# 7. 检查前端
echo ""
echo "=== 7. 前端状态 ==="
if lsof -i :5173 >/dev/null 2>&1 || lsof -i :5174 >/dev/null 2>&1; then
    check_pass "前端运行中"
else
    check_warn "前端未运行" "运行: npm run dev"
fi

# 8. 总结
echo ""
echo "=========================================="
echo "  验证完成"
echo "=========================================="
echo "${GREEN}通过: $PASS${NC}"
echo "${RED}失败: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "${GREEN}🎉 所有检查通过！GitHub App 已正确配置${NC}"
    echo ""
    echo "下一步："
    echo "1. 在目标仓库创建 PR 测试 webhook"
    echo "2. 查看 ngrok 界面: http://127.0.0.1:4040"
    echo "3. 检查数据库 PR 记录"
    exit 0
else
    echo "${RED}请完成上述失败项的配置${NC}"
    echo ""
    echo "快速修复命令:"
    echo "  ngrok config add-authtoken <token>"
    echo "  ngrok http 8000"
    echo "  cp <downloaded.pem> backend/private-key.pem"
    echo "  编辑 backend/.env 填写 App ID 和 Installation ID"
    exit 1
fi