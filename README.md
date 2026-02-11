# Atoms Jerry

基于 `Next.js + FastAPI + Postgres` 的多智能体工作流演示项目，支持：

- 普通账号密码登录/注册
- Google / GitHub OAuth 登录
- Runs 执行流式事件展示
- 代码产物查看、下载、导出

## 1. 技术栈

- Web: `Next.js` (`apps/web`)
- API: `FastAPI` (`apps/api`)
- DB: `Postgres`（Docker）
- Workspace: `pnpm` monorepo

## 2. 快速启动（Docker）

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 启动服务：

```bash
docker compose up -d --build
```

3. 打开页面：

- Web: `http://localhost:13000`
- API Docs: `http://localhost:18000/api/docs`

## 3. 环境变量说明

关键项（见 `.env.example`）：

- `TEST_MODE=false`
- `WEB_APP_URL=http://localhost:13000`
- `OAUTH_SESSION_SECRET=<长度足够的随机字符串>`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`

说明：

- `TEST_MODE=true` 时 OAuth 走测试分支，不会跳第三方授权。
- `TEST_MODE=false` 才会走真实 Google/GitHub OAuth。

## 4. OAuth 配置（本地）

### Google OAuth

Google Cloud OAuth 客户端中填写：

- Authorized JavaScript origins:
  - `http://localhost:13000`
- Authorized redirect URIs:
  - `http://localhost:13000/api/auth/oauth/google/callback`

### GitHub OAuth

GitHub OAuth App 中填写：

- Homepage URL:
  - `http://localhost:13000`
- Authorization callback URL:
  - `http://localhost:13000/api/auth/oauth/github/callback`

## 5. 常见问题排查

### 5.1 `{"detail":"Google OAuth not configured"}`

- 检查 `.env` 是否填写了 `GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET`
- 检查 `TEST_MODE=false`
- 执行 `docker compose up -d --build api web`

### 5.2 `{"detail":"OAuth token exchange failed for google"}`

常见原因：

- 重复使用旧 callback URL（授权码一次性）
- callback URL 和 Google 控制台不一致
- 浏览器里旧 cookie 导致 `state mismatch`

建议：

- 从 `/login` 重新点击 Google 登录，不要手动复用 callback URL
- 清除 `localhost:13000` 的站点 cookie 后重试

### 5.3 普通注册失败（422）

当前后端校验：

- `username` 必填
- `email` 必须合法
- `password` 最少 8 位

## 6. 开发与测试命令

```bash
pnpm -r lint
pnpm -r typecheck
pnpm -r test
pnpm --filter @atoms/web test:e2e
```

## 7. 目录结构

```text
apps/
  api/        # FastAPI backend
  web/        # Next.js frontend
packages/
  shared/     # shared schemas/types
docker-compose.yml
.env.example
```

## 8. 重启与日志

```bash
docker compose up -d --build api web
docker compose logs -f api
docker compose logs -f web
```

