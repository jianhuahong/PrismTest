# Prism

自建测试平台。当前是 M0：能一键起服务、注册登录、按项目隔离权限。接口执行从 M1 开始，入口已留在 `runner/core/executor.py`。

## 五分钟启动

在 `deploy` 目录：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

然后：

- 后端健康检查：<http://127.0.0.1:8001/health> 应返回 `{"status":"ok"}`
- 前端：<http://127.0.0.1:8080>
- MinIO 控制台：<http://127.0.0.1:9101>（账号见 `.env` 的 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`）。官方 `minio/minio` 镜像已下架，Compose 使用 Chainguard 构建的 MinIO。容器内控制台仍是 9001。
- 接口文档：<http://127.0.0.1:8001/docs>

本机若已有别的 MySQL / Redis / MinIO 占用 3306、6379、9001、8000，Compose 把宿主机端口错开为 3307、6380、9100/9101、8001。容器之间仍用 3306 和 6379。

第一个注册的用户是管理员，之后的用户是成员。

本地只起中间件、自己跑后端时：

```powershell
cd deploy
docker compose up -d mysql redis minio
cd ..\backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
$env:DATABASE_URL = "mysql+aiomysql://root:prism_root@127.0.0.1:3307/prism"
$env:REDIS_URL = "redis://127.0.0.1:6380/0"
$env:SECRET_KEY = "please-change-this-secret-key-at-least-32-bytes"
.\.venv\Scripts\alembic upgrade head
$env:PYTHONPATH = ".."
.\.venv\Scripts\uvicorn app.main:app --reload --port 8001
```

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

前端开发地址是 <http://127.0.0.1:5173>，`/api` 会代理到 `8001`。

## 目录

```
backend/     FastAPI。models / schemas / api / services
frontend/    Vue 3 + TypeScript + Vite
runner/      runner/core/executor.py 是执行入口
docs/        protocol.md
deploy/      docker-compose.yml 与 .env.example
```

## 检查

```powershell
cd backend
.\.venv\Scripts\ruff check app tests ../runner alembic
.\.venv\Scripts\pytest
cd ..\frontend
npm run lint
npm run build
```

测试使用 `prism_test` 库和 Redis 1 号库。请先起 MySQL 与 Redis。默认账号是 `root` / `prism_root`。

## Git

`main` 加 `feature/*`。提交说明用 Conventional Commits。

GitHub 仓库里把 `main` 设为保护分支，要求 CI 的 `backend` 和 `frontend` 两个检查通过后才能合入。仓库还没有远程地址时，这一步要在 GitHub 上手工打开。

## 范围

M0 不做 RabbitMQ、用例执行、Mock、UI 自动化。任务消息格式见 `docs/protocol.md`。
