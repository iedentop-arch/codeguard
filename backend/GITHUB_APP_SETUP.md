# GitHub App 配置指南

## 前置条件检查

运行以下命令确认服务状态：
```bash
# 检查后端是否运行
lsof -i :8000

# 检查 ngrok 是否已配置
ngrok config check
```

---

## Step 1: 配置 ngrok

### 1.1 注册 ngrok 账号
访问 https://ngrok.com/signup 注册免费账号

### 1.2 获取 Authtoken
登录后访问 https://ngrok.com/dashboard/authtokens
点击 "New Authtoken" 创建并复制 token

### 1.3 配置 ngrok
```bash
ngrok config add-authtoken <你的token>
```

### 1.4 启动 ngrok 隧道
```bash
ngrok http 8000
```

记录输出的 Forwarding 地址，例如：
```
Forwarding  https://abc1-23-45-67.ngrok-free.app -> http://localhost:8000
```

---

## Step 2: 注册 GitHub App

### 2.1 创建 GitHub App
访问 https://github.com/settings/apps → "New GitHub App"

### 2.2 基本配置
| 字段 | 值 |
|------|-----|
| GitHub App name | CodeGuard-PR-Checker |
| Homepage URL | http://localhost:8000 |
| Webhook URL | https://<ngrok-id>.ngrok-free.app/api/v1/webhooks/github |
| Webhook Secret | codeguard-webhook-secret-2024 |

### 2.3 权限配置
Repository permissions:
- Contents: Read-only
- Pull requests: Read and write

Subscribe to events:
- Pull request
- Push

### 2.4 获取 App ID 和私钥
创建后：
1. 记录 **App ID**（页面顶部）
2. 点击 **Generate a private key**
3. 下载 .pem 文件，保存到 `backend/private-key.pem`

---

## Step 3: 更新配置文件

编辑 `backend/.env`：

```bash
# App ID (从 GitHub App 页面获取)
GITHUB_APP_ID=123456

# 私钥文件已保存为 private-key.pem，无需配置此项
# 或直接粘贴私钥内容：
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...

# Webhook Secret (与 GitHub App 设置一致)
GITHUB_WEBHOOK_SECRET=codeguard-webhook-secret-2024

# Installation ID (安装后获取，见 Step 4)
GITHUB_APP_INSTALLATION_ID=12345678
```

---

## Step 4: 安装 GitHub App

### 4.1 安装到仓库
访问 https://github.com/settings/apps/CodeGuard-PR-Tracker/installations
点击 "Install" 选择目标仓库

### 4.2 获取 Installation ID
安装后，访问：
```bash
# 或直接在 GitHub App 安装页面查看 URL
# https://github.com/settings/installations/<installation_id>
```

更新 .env 中的 GITHUB_APP_INSTALLATION_ID

---

## Step 5: 测试

### 5.1 创建测试 PR
在目标仓库创建一个 Pull Request

### 5.2 检查 webhook 接收
查看 ngrok 界面 (http://127.0.0.1:4040) 确认 webhook 请求

### 5.3 检查数据库
```bash
mysql -u root -p codeguard -e "SELECT * FROM pull_requests;"
```

---

## 快速配置命令

完成上述步骤后，可以一键更新配置：

```bash
cd vendor-code-mgmt/backend

# 方式1: 使用私钥文件
# 保存下载的 .pem 文件为 private-key.pem

# 方式2: 使用环境变量
export GITHUB_APP_ID="你的App ID"
export GITHUB_APP_INSTALLATION_ID="你的Installation ID"
export GITHUB_WEBHOOK_SECRET="codeguard-webhook-secret-2024"

# 重启后端
uvicorn app.main:app --reload
```