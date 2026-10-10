# TradingLog 项目备忘

## 项目定位

- 本工程是**前后端分离的全栈脚手架 + 已实现的业务模块**。
- 骨架部分刻意保持最小化：首页 `HomeView.vue` 只有空状态，**不要以「方便演示」为由往首页加示例数据/演示功能**。
- 已实现的业务模块：**交易截图相册**（`/albums`、`/albums/:albumId`）。后续业务代码新加在 `src/views/`、`src/api/`、`src/stores/`、`src/components/<模块>/` 中。

## 前后端联调

- 后端 8000，前端 5173。**`vite.config.js` 已配 `/api` → `http://127.0.0.1:8000` 代理**，前端一律用相对路径 `/api/...`，不硬编码后端域名。
- 相册功能需要**两个服务都启动**才可用。
- 后端没有 `--reload` 时，改完后端代码必须**重启服务**才会生效（踩过：改了 `_decorate` 后旧进程仍在跑，导致字段缺失）。

## 后端模块（server/）

- 位置 `server/`，**FastAPI + uv** 的独立 Python 项目，与前端 `src/` 平级。不使用 npm，不用 `requirements.txt`。
- 依赖唯一事实来源：`server/pyproject.toml`（声明）+ `server/uv.lock`（锁定）。改依赖一律用 `uv add` / `uv add --dev` / `uv remove`，禁止手改 `uv.lock`。
- 开发依赖放 `[dependency-groups].dev`（PEP 735）。**测试客户端用 `httpx2`，不要换回 `httpx`**（starlette ≥1.7 已弃用 httpx，会报 StarletteDeprecationWarning）。
- 包名是 `app`（src-layout：`server/src/app/`），导入路径 `app.xxx`。因包名 ≠ 项目名，`pyproject.toml` 中必须有：
  ```toml
  [tool.uv.build-backend]
  module-name = "app"
  module-root = "src"
  ```
  改包名或目录时必须同步改这里，否则 uv_build 构建失败。
- 编写代码时的边界：接口实现放 `src/app/api/v1/endpoints/` 并在 `api/v1/router.py` 注册；配置项一律加在 `core/config.py` 的 `Settings` 里（环境变量 > `.env` > 默认值），不散落硬编码。
- 命令统一加 `uv run` 前缀：`uv run tradinglog-server` / `uv run pytest` / `uv run ruff check .` / `uv sync`。跨环境复现用 `uv sync --frozen --no-dev`。
- 后端默认端口 8000，前端 5173；CORS 白名单在 `Settings.cors_origins`。

### 相册模块的后端约定

- **分层**：`schemas/`（Pydantic 模型）→ `services/`（业务逻辑，**不 import FastAPI**，只抛 `core/errors.py` 的 `NotFoundError`/`ValidationError`）→ `api/v1/endpoints/`（HTTP 层）。异常在 `main.py` 注册处理器统一映射为 404/400。
- **数据库用标准库 `sqlite3`，不引 ORM**。`core/db.py` 里 `get_conn()` 是 contextmanager，按请求建连、WAL、`PRAGMA foreign_keys=ON`。表结构集中在 `db.SCHEMA`。
- **时间一律 ISO 8601 字符串、不带时区（本地时间）**，字典序即时间序。用 `services/common.py` 的 `now_iso()`。
- **批注坐标归一化 0~1**。矩形批注 `(x, y)` = 拖拽起点（序号落点），`w/h` **带符号**（向左上拖为负），所以 Pydantic 约束是 `ge=-1, le=1`。**不要改成 `ge=0`**。
- **`seq` 在同一图集内跨图片统一编号**，新增取全册 `MAX(seq)+1`，删除后 `_compact_sequence()` 重排为 1..N（删图片也一样）。
- 图片原图**按上传字节原样保存**，缩略图转 WebP 落 `data/uploads/<album_id>/`；读尺寸前必须 `ImageOps.exif_transpose`，否则批注错位。
- 新增运行时数据目录 `server/data/`（已 gitignore）。`Settings.data_dir` 默认 `SERVER_ROOT/data`。
- FastAPI 多文件上传参数写 `Annotated[list[UploadFile], File()]`，写成 `= File(...)` 会被 ruff B008 拦。
- **测试若要写入数据必须隔离**：`tests/conftest.py` 用 `tmp_path_factory` 设 `DATA_DIR` 环境变量再 `get_settings.cache_clear()`，否则会污染 `server/data/`。

## 技术栈与约定

- Vue 3.5 + Vite 8 + Vue Router 5 + Pinia 4 + Naive UI 2.45，**纯 JavaScript**（不使用 TypeScript）。
- 包管理器 npm；Node 要求 `^20.19.0 || >=22.12.0`。
- 路径别名：`@` -> `src`（vite `resolve.alias` + `jsconfig.json` `paths`）。
- 目录约定：
  - 路由表与侧边栏菜单**同源**于 `src/router/routes.js`（`routes` 的 children + `menuRoutes`）。
  - Store 放 `src/stores/*.js`，从 `src/stores/index.js` 统一导出。
  - 主题变量集中在 `src/theme/index.js`，改品牌色只需改这一处。
  - 页面放 `src/views/`，布局放 `src/layouts/`。
  - 接口调用放 `src/api/`，统一走 `request.js`（自带 `/api/v1` 前缀与 detail→Error 归一化），不直接用 fetch。
  - 模块化组件放 `src/components/<模块>/`。
- 新增页面 = 建 `src/views/XxxView.vue` + 在 `routes.js` 的 children 与 `menuRoutes` 各加一项。
- 详情类页面用 `meta.activeMenu` 让父级菜单保持高亮、`meta.parent` 生成可点击面包屑（参考 `/albums/:albumId`）。

## 编码约定

- Naive UI 组件在模板中直接写 `<n-xxx>`，**不做全局注册**；`ref/computed/h`、`useRoute/useRouter`、`useMessage/useDialog` 依赖自动导入，不手写 import。
- **不要依赖 Naive UI 的内部 CSS 变量名**：它用 `--n-` 前缀且部分变量（`--n-text-color-3`、`--n-primary-color`）是运行时动态生成的，grep 不到字面量。业务样式一律用 `src/styles/index.css` 里自定义的语义变量：`--brand-primary` / `--tl-board` / `--tl-surface` / `--tl-surface-border` / `--tl-text-muted` / `--tl-text-dim`，按 `html[data-theme]` 切换。批注强调色 `--anno-accent`（`#f59e0b`）刻意不随主题变（它叠在截图上，需要在浅底/深底 K 线图上都醒目）。
- 需要在 render 函数里返回组件时，避免与模板的自动引入产生重复导入 —— 优先返回原生节点 + 自己定义的 CSS 类。
- 在非组件环境（路由守卫、请求拦截器）使用 message/dialog，走 `getNaiveApi()`（`src/utils/naive.js`）。
- **涨跌配色遵循中国习惯：涨 = 红 `#d03050`，跌 = 绿 `#18a058`。**（骨架中未内置对应样式类，做行情/持仓相关 UI 时自行定义。）
- 主题切换需同时更新 `<html>` 上的 `data-theme` 与 `color-scheme`，`useAppStore.setThemeMode` 已封装。**测试时不要用 eval 直接改 `data-theme`**，那会绕过 Pinia 导致 Naive UI 不跟随（假象），要点顶栏按钮。

### 相册模块的前端约定（`components/album/ImageStage.vue`）

- 批注层必须与**图片实际渲染矩形**完全重合：按图片原始宽高比在容器内等比内缩算出 `box(left/top/width/height)`，把 `<img>` 与批注层贴到同一个 box（都用 `layerStyle`）。**不要**让批注层铺满整个容器，否则 object-fit 留白会让批注错位。
- 图片用 `object-fit: contain`，保证**绝不被拉伸变形**（K 线图变形是致命的）。
- 指针交互统一用 `pointerdown/pointermove/pointerup` + `setPointerCapture`；点批注要求位移 <0.02、矩形要求 `|w|,|h| >= 0.012` 才算有效，防误触。
- 说明编辑框绝对定位贴序号图标，`x > 0.58` 自动左翻、纵向按 `canvasSize` 夹紧。
- 选中态由父组件 `selectedId` 驱动；ImageStage 内**只能用一个 watcher 同时盯 `[image.id, selectedId]`** —— 拆成两个会在「从批注清单跳图并选中」时把刚打开的编辑框又关掉。
- 上传三路（粘贴 / 文件选择 / 拖拽）共用同一个 `upload()`；`paste` 监听 window，但在 INPUT/TEXTAREA/contenteditable 内不抢。
- 图集列表的封面地址由后端拼好（`cover_url` / `cover_thumb_url`），前端不自己拼接口路径。

## 常用命令

- `npm run dev` —— 开发服务器，http://localhost:5173
- `npm run build` —— 生产构建，产物在 `dist/`
- `npm run preview` —— 预览构建产物，http://localhost:4173
