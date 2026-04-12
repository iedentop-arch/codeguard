# Need Human Decision

> 本文件记录开发过程中需要人工决策的问题、建议和优化点。
> 规则：任何错误尝试解决2次后仍无法解决，记录到此文件等待决策。

---

## 问题记录格式

```markdown
### [日期] 问题标题
- **状态**: 待决策 / 已解决 / 已关闭
- **优先级**: P0(阻塞) / P1(重要) / P2(一般) / P3(建议)
- **影响范围**: 描述影响的功能或模块
- **问题描述**: 详细描述问题
- **尝试方案**: 已尝试的解决方案
- **建议方案**: 推荐的解决方案
- **决策结果**: (待填写)
```

---

## 问题列表

### [2026-04-10] npm install 在某些情况下不创建 node_modules/.bin 符号链接
- **状态**: 已解决
- **优先级**: P2
- **影响范围**: 前端原型开发
- **问题描述**: 运行 `npm install` 后 node_modules 存在但 .bin 目录不存在，导致无法使用 `npm run dev`
- **尝试方案**: 
  1. 删除 node_modules 重新安装 - 无效
  2. 使用 `node ./node_modules/vite/bin/vite.js` 直接运行 - 成功
- **解决方法**: 直接使用 node 执行 vite 二进制文件
- **根本原因**: 可能是 npm 缓存或权限问题，在重新完整安装后解决

---

### [2026-04-10] 规范库页面 Card 组件未导入
- **状态**: 已解决
- **优先级**: P1
- **影响范围**: 乙方开发的规范学习页面
- **问题描述**: SpecsPlaceholder 组件使用了 Card 组件但未导入，导致页面崩溃
- **尝试方案**: 在 App.tsx 顶部添加 Card 组件导入
- **解决方法**: 添加 `import { Card, CardContent } from '@/components/ui/card'`

---

## 待决策项

(暂无)

---

## 优化建议

### [2026-04-10] 角色切换需要重新登录
- **优先级**: P3
- **现状**: 点击"切换角色"按钮会登出用户，需要重新选择角色
- **建议**: 实现直接切换角色的功能，不需要重新登录
- **决策**: (待定)

### [2026-04-10] 考试计时器实现优化
- **优先级**: P3
- **现状**: 考试计时器使用 useState 实现，可能存在状态问题
- **建议**: 使用 useEffect + setInterval 实现更可靠的倒计时
- **决策**: (待定)

---

## 技术债务

(暂无)

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-04-11 | 完成数据库环境配置，记录配置过程 |
| 2026-04-10 | 初始化文件，记录前端原型问题 |

---

## 数据库环境配置记录

### [2026-04-11] MySQL + Redis Docker 容器部署完成

**配置方式**: Docker Compose 容器化部署

**服务状态**:
- MySQL 8.0 (codeguard-mysql): ✅ 运行中，端口 3306
- Redis 7 (codeguard-redis): ✅ 运行中，端口 6379

**数据库信息**:
- 数据库名: `codeguard`
- 用户: `root` / 密码: `password`
- 字符集: `utf8mb4` / 排序规则: `utf8mb4_unicode_ci`
- 表数量: 11 张表（包括 alembic_version）

**已创建的表**:
| 表名 | 说明 |
|------|------|
| vendors | 乙方公司信息 |
| vendor_members | 乙方成员信息 |
| spec_documents | 规范文档 |
| exam_questions | 考试题库 |
| pull_requests | PR记录 |
| quality_gates | 质量门禁检查结果 |
| monthly_scores | 月度SLA评分 |
| deliveries | 交付记录 |
| delivery_checklists | 交付检查清单 |
| users | 系统用户 |
| alembic_version | 迁移版本控制 |

**依赖安装**:
- Python 3.9.6 + venv
- FastAPI 0.128.8 + Uvicorn 0.39.0
- SQLAlchemy 2.0.49 + Alembic 1.16.5
- aiomysql 0.3.2 + pymysql 1.1.2
- email-validator 2.3.0 (新增依赖)

**问题修复**:
- 启动时缺少 `email-validator` 模块 → 已安装解决

**启动命令**:
```bash
# 启动 Docker 服务
cd /Users/eden-f/code-work/Qoder-w/vendor-code-mgmt
docker compose up -d

# 启动后端
cd backend && source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# API 文档访问
http://127.0.0.1:8000/api/docs
```