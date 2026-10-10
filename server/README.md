# TradingLog Server

TradingLog 的后端服务，基于 **FastAPI + uv** 构建。

---

## 一、目录命名

命名为 **`server/`**，与仓库根目录的前端源码 `src/` 平级：

```
TradingLog/
├─ src/            # 前端源码（Vue 3）
├─ public/         # 前端静态资源
├─ package.json    # 前端依赖
├─ vite.config.js  # 前端构建配置
└─ server/         # ← 后端模块（本目录）
```

选择理由：语义清晰、足够简短，且与前端惯用的 `client/`、`web/` 对称。备选方案是 `backend/`（更直白）或 `apps/api/`（为将来拆分多个后端服务预留层级）。如日后要改名，需要同步调整：`pyproject.toml` 的 `name`、CI 脚本中的路径、以及部署配置。

---

## 二、目录结构

```
server/
├─ .python-version          # uv 锁定的 Python 版本（3.13）
├─ .env.example             # 环境变量模板（.env 不入库）
├─ .gitignore
├─ pyproject.toml           # 项目元数据 + 依赖声明 + 工具配置（唯一配置入口）
├─ uv.lock                  # 依赖锁文件，保证可复现安装（需提交到版本库）
├─ README.md
├─ src/
│  └─ app/                  # 应用包，导入路径即 app.xxx
│     ├─ __init__.py        # 包元信息（__version__）
│     ├─ __main__.py        # 命令行入口：python -m app / uv run tradinglog-server
│     ├─ main.py            # 应用工厂 create_app() 与 ASGI 实例 app
│     ├─ core/
│     │  └─ config.py       # 基于 pydantic-settings 的配置中心
│     └─ api/
│        └─ v1/
│           ├─ router.py    # v1 路由汇总，新增模块在这里注册
│           └─ endpoints/
│              └─ health.py # 健康检查（唯一的示例接口）
└─ tests/
   ├─ conftest.py           # pytest 共享夹具（TestClient）
   └─ test_health.py        # 健康检查冒烟测试
```

**分层约定：**

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 入口 | `main.py` | 创建 FastAPI 实例、挂中间件、挂路由 |
| 配置 | `core/config.py` | 所有可配置项集中在此，避免散落的硬编码 |
| 路由 | `api/v1/router.py` | 汇总各业务模块的路由，统一挂到 `/api/v1` |
| 接口 | `api/v1/endpoints/*.py` | 单个业务模块的 HTTP 实现 |
| 测试 | `tests/` | 与 `src/` 平级，避免被打包进产物 |

> 采用 **src-layout**（源码在 `src/` 下），这是 uv 初始化应用项目时的默认布局。好处是 `import app` 一定来自已安装的包，不会因为恰好存在同名目录而误导入。

---

## 三、环境要求

- **uv** ≥ 0.12（本机已装：`0.12.17`）
- **Python** 3.13（由 uv 管理，无需手动安装；`.python-version` 已固定）
- 无需手动创建虚拟环境，`uv` 会按目录自动管理 `server/.venv`

---

## 四、初始化过程（已执行，供复现参考）

```bash
cd TradingLog

# 1) 初始化 uv 应用项目
#    --app          应用类型（非库）
#    --python 3.13  固定 Python 版本，写入 .python-version
#    --vcs none     不生成嵌套 git 仓库（整个仓库应统一在根目录管理）
uv init server --app --name tradinglog-server --python 3.13 --managed-python --vcs none

# 2) 添加运行时依赖
cd server
uv add fastapi "uvicorn[standard]" pydantic-settings

# 3) 添加开发依赖（写入 [dependency-groups].dev）
uv add --dev pytest httpx2 ruff

# 4) 安装/同步环境（拉取依赖并按 uv.lock 精确复现）
uv sync
```

`uv init --app` 默认按项目名推导包名（`tradinglog_server`）。本项目改用 `app` 作为包名，因此需要在 `pyproject.toml` 中显式声明：

```toml
[tool.uv.build-backend]
module-name = "app"
module-root = "src"
```

---

## 五、依赖管理方式

**核心原则：`pyproject.toml` 声明「需要什么」，`uv.lock` 锁定「实际装了什么」。**

### 1. 依赖声明（`pyproject.toml`）

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.143.0",
    "pydantic-settings>=2.15.0",
    "uvicorn[standard]>=0.54.0",
]

# 开发期依赖单独分组，不进入生产环境
[dependency-groups]
dev = [
    "httpx2>=2.13.1",
    "pytest>=9.1.1",
    "ruff>=0.17.0",
]
```

- 运行时依赖写在 `[project].dependencies`；
- 开发依赖（测试、lint）写在 `[dependency-groups].dev`（PEP 735 标准分组），部署时可用 `--no-dev` 跳过；
- **不要手工编辑 `uv.lock`**，它由 uv 生成。

### 2. 日常操作

| 目的 | 命令 |
| --- | --- |
| 添加运行时依赖 | `uv add <包名>` |
| 添加开发依赖 | `uv add --dev <包名>` |
| 移除依赖 | `uv remove <包名>`（加 `--dev` 移除开发依赖） |
| 安装/同步环境 | `uv sync` |
| 升级全部依赖 | `uv lock --upgrade` |
| 按锁文件精确复现（CI/部署） | `uv sync --frozen --no-dev` |

`uv add` / `uv remove` 会自动改写 `pyproject.toml`、更新 `uv.lock` 并同步虚拟环境，**不需要**手动 `pip install`。

### 3. 与 pip 的差异

- 不写 `requirements.txt`，依赖的唯一事实来源是 `pyproject.toml` + `uv.lock`；
- 不需要手动 `activate` 虚拟环境，所有命令用 `uv run <cmd>` 前缀即可。

---

## 六、常用命令

```bash
cd server

# 启动开发服务器（读取 .env，RELOAD=true 时代码改动自动重载）
uv run uvicorn app.main:app --reload --port 8000
# 或使用配置好的命令行入口
uv run tradinglog-server
# 或
uv run python -m app

# 测试
uv run pytest              # 全量
uv run pytest -v           # 详细输出
uv run pytest tests/test_health.py::test_health

# 代码检查与格式化
uv run ruff check .        # 静态检查
uv run ruff check --fix .  # 自动修复
uv run ruff format .       # 格式化
```

启动后：

- 接口：http://127.0.0.1:8000/api/v1/health
- Swagger 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

---

## 七、配置方式

配置由 `src/app/core/config.py` 中的 `Settings` 统一管理（基于 `pydantic-settings`），读取优先级为：

**环境变量 > `.env` 文件 > 代码中的默认值**

```bash
cp .env.example .env   # 按需修改；.env 已在 .gitignore 中忽略
```

可配置项见 `.env.example`，包括 `APP_NAME`、`DEBUG`、`HOST`、`PORT`、`RELOAD`、`API_V1_PREFIX`、`CORS_ORIGINS`。

新增配置项时，在 `Settings` 中加一个带默认值的字段即可：

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./tradinglog.db"
```

随后即可通过环境变量 `DATABASE_URL` 或 `.env` 覆盖。

---

## 八、与前端联调

后端通过 `Settings.cors_origins` 中配置的来源处理跨域（默认已包含 `http://localhost:5173`）。

如果希望前端用相对路径 `/api` 请求、避免写死后端域名，可在前端根目录的 `vite.config.js` 中加一段代理：

```js
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
```

这样前端请求 `/api/v1/health` 会被转发到后端；生产环境再由 Nginx 等网关承担同样的转发职责。

---

## 九、新增一个接口的步骤

1. 在 `src/app/api/v1/endpoints/` 下新建模块，例如 `trades.py`：

   ```python
   from fastapi import APIRouter

   router = APIRouter(prefix="/trades", tags=["trades"])

   @router.get("")
   def list_trades() -> list[dict]:
       return []
   ```

2. 在 `src/app/api/v1/router.py` 中注册 `api_router.include_router(trades.router)`；
3. 在 `tests/` 下补对应测试。

如需请求体/响应体的数据校验，建议新增 `src/app/schemas/` 存放 Pydantic 模型；如需数据库，建议新增 `src/app/models/` 与 `src/app/crud/`，并在 `core/config.py` 中补 `database_url` 配置项。
