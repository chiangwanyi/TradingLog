# TradingLog Server

TradingLog 的后端服务，基于 **FastAPI + uv** 构建，为「交易截图相册」等模块提供 REST API。

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
├─ data/                    # 运行期数据（已 gitignore，用户数据不提交）
│  ├─ tradinglog.db         #   SQLite 库
│  └─ uploads/<album_id>/   #   截图原图与缩略图
├─ src/
│  └─ app/                  # 应用包，导入路径即 app.xxx
│     ├─ __init__.py        # 包元信息（__version__）
│     ├─ __main__.py        # 命令行入口：python -m app / uv run tradinglog-server
│     ├─ main.py            # 应用工厂 create_app()、lifespan、异常处理器
│     ├─ core/
│     │  ├─ config.py       # 基于 pydantic-settings 的配置中心
│     │  ├─ db.py           # SQLite 连接、建表、轻量列迁移
│     │  └─ errors.py       # 领域异常（NotFound / Validation）
│     ├─ schemas/           # Pydantic 请求 / 响应模型
│     │  ├─ album.py
│     │  ├─ image.py
│     │  ├─ annotation.py
│     │  └─ preference.py   # 批注调色板等 UI 偏好
│     ├─ services/          # 业务逻辑（不依赖 FastAPI，可单独测试）
│     │  ├─ albums.py       #   图集 CRUD
│     │  ├─ images.py       #   图片落盘、缩略图生成、元数据
│     │  ├─ annotations.py  #   批注 CRUD、颜色归一化与序号压实
│     │  ├─ preferences.py  #   键值偏好读写（最近使用的批注颜色）
│     │  └─ common.py       #   now_iso / truncate_to_minute 等
│     ├─ api/
│     │  └─ v1/
│     │     ├─ router.py    # v1 路由汇总，新增模块在这里注册
│     │     └─ endpoints/
│     │        ├─ health.py       # 健康检查
│     │        ├─ albums.py       # 图集接口 + 图片上传
│     │        ├─ images.py       # 原图 / 缩略图读取、图片删除
│     │        ├─ annotations.py  # 批注接口
│     │        └─ preferences.py  # UI 偏好接口
└─ tests/
   ├─ conftest.py           # pytest 共享夹具（隔离的临时数据目录）
   ├─ test_health.py        # 健康检查冒烟测试
   ├─ test_albums.py        # 相册全链路测试（含批注颜色）
   ├─ test_preferences.py   # 最近使用颜色的去重 / 截断
   └─ test_db_migration.py  # 给旧库补列的迁移测试
```

**分层约定：**

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 入口 | `main.py` | 创建 FastAPI 实例、挂中间件、注册异常处理器与路由 |
| 配置 | `core/config.py` | 所有可配置项集中在此，避免散落的硬编码 |
| 存储 | `core/db.py` | 连接管理 + 表结构；不做业务读写 |
| 模型 | `schemas/` | 请求体 / 响应体的校验与序列化 |
| 业务 | `services/` | 纯业务逻辑，抛领域异常（`core/errors.py`），不 import FastAPI |
| 路由 | `api/v1/router.py` | 汇总各业务模块的路由，统一挂到 `/api/v1` |
| 接口 | `api/v1/endpoints/*.py` | HTTP 层：解析入参、调用 service、返回模型 |
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
uv add python-multipart pillow      # 文件上传解析 + 图片尺寸读取与缩略图

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

> **注意**：测试客户端用的是 `httpx2` 而不是 `httpx`。starlette ≥ 1.7 起 `starlette.testclient` 已弃用 `httpx`，继续使用会在测试输出里刷 `StarletteDeprecationWarning`。

---

## 五、依赖管理方式

**核心原则：`pyproject.toml` 声明「需要什么」，`uv.lock` 锁定「实际装了什么」。**

### 1. 依赖声明（`pyproject.toml`）

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.143.0",
    "pillow>=12.3.0",           # 读取图片尺寸、生成缩略图
    "pydantic-settings>=2.15.0",
    "python-multipart>=0.0.32", # FastAPI 的 UploadFile 依赖它解析表单
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

## 六、数据存储

### 1. 存放位置

全部运行期数据都在 `server/data/` 下（已加入 `.gitignore`，不会误提交）：

```
server/data/
├─ tradinglog.db                     # SQLite 库（元数据）
└─ uploads/<album_id>/
   ├─ <image_id>.<ext>               # 原图
   └─ <image_id>.thumb.webp          # 预览缩略图（最长边 480px）
```

可通过 `.env` 的 `DATA_DIR` 改到别处（例如放到独立的数据盘）。

### 2. 表结构

| 表 | 关键字段 | 说明 |
| --- | --- | --- |
| `albums` | `id`, `symbol`, `trade_time`, `title`, `note`, `created_at`, `updated_at` | 图集。`trade_time` 精确到分钟，列表按它倒序 |
| `images` | `id`, `album_id`, `original_name`, `stored_name`, `thumb_name`, `mime`, `size`, `width`, `height`, `created_at` | 图片。按 `created_at` 升序即上传顺序 |
| `annotations` | `id`, `album_id`, `image_id`, `kind`, `seq`, `x`, `y`, `w`, `h`, `text`, `color`, `created_at` | 批注 |
| `preferences` | `key`, `value`, `updated_at` | 纯 UI 偏好的键值存储（JSON 字符串），目前存批注调色板的「最近使用颜色」 |

设计要点：

- **时间统一以 ISO 8601 字符串存储**，字典序即时间序，`ORDER BY` 可直接生效。约定使用**不带时区的本地时间**，前后端都不会有时区偏移。
- **批注坐标是归一化值（0~1）**，原点在图片左上角，因此任何显示尺寸下都能精确还原。
  - 点批注只使用 `(x, y)`；
  - 矩形批注的 `(x, y)` 是**拖拽起点**（序号图标位置），`(w, h)` 是**带符号**的跨度 —— 向左上拖动时为负。矩形范围 = `min(x, x+w)` 起、`|w| × |h|` 大小。前端据此把序号画在起点上。
- **批注颜色 `color` 存 `#rrggbb` 小写**，统一由 `services/annotations.py` 的 `normalize_color()` 归一化。
  - **空串是有意义的值**：表示「未指定颜色」，由前端回落到默认强调色。因此不能用空串去顶替 `None` 做「未提供」的判定。
  - 好处是**老数据无需回填**：加这一列之前的批注自动取默认值 `''`，前端照常渲染成默认色。
  - 接口层用 `COLOR_PATTERN` 校验格式，非法值直接 422。
- **`seq` 在同一图集内跨所有图片统一编号**，从 1 开始连续。新增时取全册 `MAX(seq) + 1`；删除后调用 `_compact_sequence()` 重新压实，不留空洞。
- 外键开启 `ON DELETE CASCADE`，删图集 / 删图片时批注自动清理；磁盘文件由服务层显式删除。
- 连接按请求创建（FastAPI 的同步接口跑在线程池里），开启 WAL 后并发读写不互相阻塞。

### 3. 表结构变更（轻量迁移）

表结构的唯一事实来源是 `core/db.py` 的 `SCHEMA` 常量，但 `CREATE TABLE IF NOT EXISTS` **不会**给已存在的表补列。因此 `init_db()` 里还有一步 `_migrate()`：按 `_ADDED_COLUMNS` 声明的「缺哪列补哪列」做幂等 `ALTER TABLE`。

新增列时只要两步：**① 改 `SCHEMA`（新库直接建出来）；② 在 `_ADDED_COLUMNS` 里登记（老库自动补上）**。

```python
_ADDED_COLUMNS = {
    "annotations": {"color": "TEXT NOT NULL DEFAULT ''"},
}
```

> 列还很少，一个几十行的函数就够了，暂时不引入 Alembic 之类的迁移框架。等出现「需要改列类型 / 数据回填」的诉求时再升级。
> 迁移逻辑有专门的测试：`tests/test_db_migration.py` 会先造一个「加列之前」的旧库，再验证补列成功、老数据完好、且重复执行不出错。

### 4. 图片处理

- 原图**按上传字节原样保存**，不做二次编码，避免画质损失；
- 缩略图统一转 WebP（Pillow 构建不带 WebP 编码器时自动退回 JPEG），透明区域铺白底；
- 读取尺寸时先做 `ImageOps.exif_transpose`，**以「旋转后」的尺寸为准** —— 与浏览器渲染原图时的显示尺寸一致，批注坐标才不会错位；
- 上传时校验真实图片格式（Pillow 解析而非只看扩展名）与体积上限，单个文件失败不影响同批其它文件。

---

## 七、接口一览

所有接口挂在 `/api/v1` 下，交互文档见 http://127.0.0.1:8000/docs 。

### 图集

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/albums` | 图集列表，按交易时间倒序，附带图片数与封面地址 |
| POST | `/albums` | 新建图集（`symbol` + `trade_time` 必填） |
| GET | `/albums/{id}` | 图集详情，**一次返回全部图片及其批注**（前端只需一次请求） |
| PATCH | `/albums/{id}` | 修改图集信息 |
| DELETE | `/albums/{id}` | 删除图集（连同图片文件、图片记录与批注） |

### 图片

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/albums/{id}/images` | 上传图片，multipart 字段名 `files`，可多张。返回 `{ saved: [...], failed: [{name, reason}] }` |
| GET | `/images/{id}/file` | 读取原图（长缓存） |
| GET | `/images/{id}/thumb` | 读取缩略图，缺缩略图时自动回退原图 |
| DELETE | `/images/{id}` | 删除图片，连同其批注，并重排该图集序号 |

### 批注

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/albums/{id}/annotations` | 新增批注，序号由服务端分配（不接受客户端传入）。可带 `color` |
| PATCH | `/annotations/{id}` | 修改文字说明、颜色或几何位置 |
| DELETE | `/annotations/{id}` | 删除批注并重排全册序号 |

### UI 偏好

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/preferences/annotation-colors` | 批注调色板的「最近使用颜色」，最近用过的排在最前 |
| POST | `/preferences/annotation-colors` | 记录一次颜色使用：去重、排到最前、上限 12 个 |

> 偏好类接口放在 `/preferences` 下，与业务数据分开 —— 它们描述的是「界面怎么显示」，不是「记录了什么」。`preferences` 表是通用键值表，后续要加别的 UI 偏好（如默认批注类型、列表排序方式）直接加 key 即可。

---

## 八、常用命令

```bash
cd server

# 启动开发服务器（读取 .env，RELOAD=true 时代码改动自动重载）
uv run uvicorn app.main:app --reload --port 8000
# 或使用配置好的命令行入口
uv run tradinglog-server
# 或
uv run python -m app

# 测试
uv run pytest              # 全量（会自动使用临时数据目录，不污染 server/data）
uv run pytest -v           # 详细输出
uv run pytest tests/test_albums.py::test_annotation_seq_is_shared_across_images

# 代码检查与格式化
uv run ruff check .        # 静态检查
uv run ruff check --fix .  # 自动修复
uv run ruff format .       # 格式化
```

> 想一次性把后端和前端都拉起来，双击仓库根目录的 `start_dev.cmd` 即可（内部就是这里的 `uv run tradinglog-server`，并默认带上 `RELOAD=true`）。

启动后：

- 接口：http://127.0.0.1:8000/api/v1/health
- Swagger 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

---

## 九、配置方式

配置由 `src/app/core/config.py` 中的 `Settings` 统一管理（基于 `pydantic-settings`），读取优先级为：

**环境变量 > `.env` 文件 > 代码中的默认值**

```bash
cp .env.example .env   # 按需修改；.env 已在 .gitignore 中忽略
```

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` / `APP_VERSION` | TradingLog API / 0.1.0 | 应用元信息 |
| `DEBUG` | `false` | 调试模式 |
| `HOST` / `PORT` / `RELOAD` | 127.0.0.1 / 8000 / false | 服务监听（`uv run tradinglog-server` 读取） |
| `API_V1_PREFIX` | `/api/v1` | 路由前缀 |
| `CORS_ORIGINS` | `["http://localhost:5173", ...]` | 跨域白名单（JSON 数组格式） |
| `DATA_DIR` | `server/data` | 数据根目录（SQLite 库 + 截图） |
| `MAX_IMAGE_BYTES` | `20971520`（20MB） | 单张图片体积上限 |
| `THUMBNAIL_MAX_SIDE` | `480` | 缩略图最长边（像素） |

新增配置项时，在 `Settings` 中加一个带默认值的字段即可：

```python
class Settings(BaseSettings):
    retention_days: int = 365
```

随后即可通过环境变量 `RETENTION_DAYS` 或 `.env` 覆盖。

---

## 十、与前端联调

前端已在 `vite.config.js` 中配好代理，前端代码统一用相对路径 `/api/...` 请求，**开发时无需处理跨域**：

```js
server: {
  port: 5173,
  proxy: {
    '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  },
},
```

后端的 `Settings.cors_origins` 默认也放行了 `http://localhost:5173`，因此即使不走代理、直接跨域请求也能通。生产环境由 Nginx 等网关承担同样的转发职责。

联调步骤：先 `uv run tradinglog-server` 起后端，再在仓库根目录 `npm run dev` 起前端，浏览器访问 http://localhost:5173 。
（两步合一：直接双击仓库根目录的 `start_dev.cmd`。）

---

## 十一、新增一个接口的步骤

以新增 `trades` 模块为例：

1. **模型**：在 `src/app/schemas/trade.py` 定义 Pydantic 模型；
2. **业务**：在 `src/app/services/trades.py` 写业务逻辑，只抛 `NotFoundError` / `ValidationError`，不要 import FastAPI；
3. **接口**：在 `src/app/api/v1/endpoints/trades.py` 定义 `router`：

   ```python
   from fastapi import APIRouter

   from app.schemas.trade import TradeRead
   from app.services import trades as trade_service

   router = APIRouter(prefix="/trades", tags=["trades"])


   @router.get("", response_model=list[TradeRead], summary="交易列表")
   def list_trades() -> list[dict]:
       return trade_service.list_trades()
   ```

4. **注册**：在 `src/app/api/v1/router.py` 中 `api_router.include_router(trades.router)`；
5. **测试**：在 `tests/` 下补对应测试（用 `client` 夹具即可，数据目录已隔离）。

领域异常已在 `main.py` 注册好处理器：`NotFoundError → 404`、`ValidationError → 400`，服务层直接抛即可。
