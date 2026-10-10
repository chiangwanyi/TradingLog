# TradingLog

交易记录与复盘工具。前后端分离的全栈工程：

- **前端**：Vue 3 + JavaScript + Naive UI，位于仓库根目录。
- **后端**：FastAPI + uv 的 Python 服务，位于 [`server/`](./server/README.md)。

当前已实现的功能模块：

| 模块 | 路由 | 说明 |
| --- | --- | --- |
| 首页 | `/home` | 空状态占位，业务开发入口 |
| **交易截图相册** | `/albums` | 图集管理、截图上传、点/矩形批注（详见第五节） |

除上述模块外，工程保持最小化：**不含占位数据与演示代码**，仅保留项目结构、基础配置与通用能力。

---

## 一、技术栈

| 分类 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | Vue 3.5 | Composition API + `<script setup>` |
| 构建 | Vite 8 | 极速冷启动、HMR、开发代理 |
| 路由 | Vue Router 5 | History 模式、路由懒加载、全局守卫 |
| 状态 | Pinia 4 | `app` store（主题 / 侧边栏）、`album` store（图集列表） |
| UI | Naive UI 2.45 | 组件与组合函数全部按需引入 |
| 语言 | JavaScript | 纯 JS，无 TypeScript |
| 代码风格 | EditorConfig | 2 空格缩进、LF 换行 |
| 后端框架 | FastAPI 0.143 | 异步 API，自动生成 OpenAPI/Swagger 文档 |
| 后端运行时 | Python 3.13 | 由 uv 管理，无需手动安装 |
| 后端依赖管理 | uv 0.12 | `pyproject.toml` 声明 + `uv.lock` 锁定 |
| 数据存储 | SQLite（标准库 `sqlite3`） | 元数据入库；截图原图与缩略图落盘 |
| 图片处理 | Pillow 12 | 读取尺寸、生成预览缩略图 |

---

## 二、环境要求

**前端：**

- **Node.js** `^20.19.0 || >=22.12.0`（Vite 8 的最低要求，推荐 22 LTS）
- **npm** `>=10`

**后端：**

- **uv** `>= 0.12`（Python 项目管理器，[安装说明](https://docs.astral.sh/uv/getting-started/installation/)）
- **Python** 3.13 —— 由 uv 自动下载管理，无需手动安装

查看当前版本：

```bash
node -v && npm -v
uv --version
```

---

## 三、安装与运行

### 前端

```bash
cd TradingLog

npm install          # 安装依赖
npm run dev          # 开发服务器 http://localhost:5173
npm run build        # 生产构建，产物在 dist/
npm run preview      # 预览构建产物 http://localhost:4173
```

> 若 `npm install` 较慢，可切换镜像源：
> `npm config set registry https://registry.npmmirror.com`

### 后端（server/）

后端是独立的 Python 项目，用 [uv](https://docs.astral.sh/uv/) 管理，**不使用 npm**：

```bash
cd server

uv sync                      # 按 uv.lock 安装依赖（首次会自动创建 .venv）
cp .env.example .env         # 可选：按需修改配置
uv run tradinglog-server     # 启动服务 http://127.0.0.1:8000
uv run pytest                # 跑测试
```

> **两个服务都要启动**，相册功能才能正常使用。前端在开发环境下把 `/api` 请求代理到 `127.0.0.1:8000`（见第五节第 6 条），因此浏览器只需访问 http://localhost:5173 。

启动后：

- 前端 http://localhost:5173
- 后端接口 http://127.0.0.1:8000/api/v1/health
- Swagger 交互文档 http://127.0.0.1:8000/docs

依赖管理与配置方式的完整说明见 [`server/README.md`](./server/README.md)。

---

## 四、目录结构

```
TradingLog/
├─ index.html                 # 应用入口 HTML
├─ vite.config.js             # Vite 配置：别名、按需引入、开发服务器与 /api 代理
├─ jsconfig.json              # 编辑器路径别名提示（@ -> src）
├─ .editorconfig              # 统一代码风格
├─ public/
│  └─ favicon.svg
├─ src/
│  ├─ main.js                 # 应用入口：注册 Pinia / Router / 全局样式
│  ├─ App.vue                 # 根组件：NConfigProvider + 各 Provider 装配
│  ├─ api/                    # 接口层
│  │  ├─ index.js             # 统一导出
│  │  ├─ request.js           # fetch 封装：拼前缀、JSON 序列化、错误归一化
│  │  └─ album.js             # 交易相册相关接口
│  ├─ router/
│  │  ├─ index.js             # 创建路由实例、全局守卫、滚动行为
│  │  └─ routes.js            # 路由表 + 侧边栏菜单配置
│  ├─ stores/                 # Pinia 状态管理
│  │  ├─ index.js             # pinia 实例与统一导出
│  │  ├─ app.js               # 主题模式、侧边栏折叠
│  │  └─ album.js             # 图集列表
│  ├─ theme/
│  │  └─ index.js             # 品牌色与深浅主题变量覆盖
│  ├─ layouts/
│  │  └─ MainLayout.vue       # 侧边栏 + 顶栏 + 内容区
│  ├─ views/
│  │  ├─ HomeView.vue         # 首页（空状态占位）
│  │  ├─ AlbumsView.vue       # 相册页：图集列表与新建 / 编辑 / 删除
│  │  ├─ AlbumDetailView.vue  # 图集详情：浏览、上传、批注
│  │  └─ NotFoundView.vue     # 404
│  ├─ components/
│  │  ├─ NaiveApiBridge.vue   # 在 Provider 内部注册全局 message/dialog 等
│  │  ├─ icons.js             # 轻量内联 SVG 图标组件
│  │  └─ album/
│  │     ├─ AlbumFormDialog.vue  # 新建 / 编辑图集表单
│  │     ├─ ImageStage.vue       # 图片查看器 + 批注绘制层（核心）
│  │     └─ ThumbnailStrip.vue   # 底部缩略图条
│  ├─ utils/
│  │  ├─ naive.js             # 全局 Naive UI API 注册中心
│  │  └─ datetime.js          # 时间格式化与本地 ISO 互转
│  └─ styles/
│     └─ index.css            # 全局重置、主题变量、过渡动画、通用类
└─ server/                    # 后端服务，详见 server/README.md
```

---

## 五、交易截图相册

### 1. 数据层级

```
图集（Album）     交易时间（精确到分钟）+ 标的
└─ 图片（Image）   按上传时间排序
   └─ 批注（Annotation）  点批注 / 矩形批注，可附文字说明
```

**批注序号在同一图集内跨所有图片统一编号**（1、2、3…）：新增时取全册最大序号 +1，删除后自动压实，不留空洞。

### 2. 页面

- **`/albums` 相册页**：卡片式展示全部图集，按交易时间倒序；封面取该图集第一张截图的缩略图；支持新建 / 编辑 / 删除。
- **`/albums/:albumId` 图集详情**：横向图片查看器 + 左右切换控件 + 底部缩略图条（点击定位、显示各图批注数），右侧为全册批注清单。

### 3. 添加截图（三种方式）

| 方式 | 操作 |
| --- | --- |
| 剪贴板粘贴 | 截图后直接 `Ctrl + V`（在输入框内打字时不会误触发） |
| 文件选择 | 点「添加截图」按钮，可多选 |
| 拖拽 | 把图片文件拖到页面内松开 |

批量上传时单个文件失败不影响其它文件，失败原因逐条提示。图片按上传时间排序。

### 4. 批注

| 模式 | 行为 |
| --- | --- |
| **查看模式** | 只浏览；点序号图标可查看 / 修改说明 |
| **批注模式** | 顶部出现工具选择，可绘制新批注 |

- **点批注**：左键单击图片任意位置 → 在该处落下圆形序号图标，随即弹出说明编辑框。
- **矩形批注**：左键按住拖动绘制矩形 → 序号图标落在**单击起点**，随即弹出说明编辑框。

序号图标可点击选中，编辑框贴图标显示（靠近右/下边缘会自动翻转或夹紧，不会被裁掉），可修改文字或删除。删除批注后全册序号自动重排。

### 5. 坐标系设计（关键实现）

批注几何量全部以**归一化值（0~1）**存储，原点在图片左上角：

- 点批注：`(x, y)`
- 矩形批注：`(x, y)` 是拖拽起点（序号落点），`(w, h)` 是**带符号**的宽高 —— 向左上拖时为负，矩形范围由 `min(x, x+w)` 起、`|w| × |h|` 大小还原。

前端 `ImageStage.vue` 按图片原始宽高比在容器内等比内缩，算出图片的精确渲染矩形，再把 `<img>` 与批注层贴到同一矩形上。因此**缩放窗口、更换分辨率、换设备查看，批注位置都不会漂移**。

### 6. 数据存储

元数据存 SQLite，截图以文件落盘，均在 `server/data/`（已加入 `.gitignore`）：

```
server/data/
├─ tradinglog.db                     # albums / images / annotations 三张表
└─ uploads/<album_id>/
   ├─ <image_id>.<ext>               # 原图（按上传字节原样保存，不二次编码）
   └─ <image_id>.thumb.webp          # 预览缩略图（最长边 480px）
```

删除图集或图片时，磁盘文件与数据库记录（含批注）会一并清理。

---

## 六、关键配置说明

### 1. Naive UI 按需引入

`vite.config.js` 中通过 `unplugin-vue-components` 的 `NaiveUiResolver` 实现：模板里写 `<n-button>`、`<n-card>` 即可，构建时自动按需打包，**无需在 `main.js` 全量注册**。

```js
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'

Components({ resolvers: [NaiveUiResolver()] })
```

### 2. 组合式 API 自动导入

`unplugin-auto-import` 自动注入 `ref` / `computed` / `useRoute` / `useRouter`，以及 Naive UI 的 `useMessage` / `useDialog` / `useNotification` / `useLoadingBar`。

```js
AutoImport({
  imports: ['vue', 'vue-router', { 'naive-ui': ['useDialog', 'useMessage', 'useNotification', 'useLoadingBar'] }],
})
```

> 本工程为纯 JS 工程，`dts` 设为 `false` 不生成类型声明文件。
> 若希望获得编辑器自动补全提示，可将两处 `dts` 改为 `'auto-imports.d.ts'` / `'components.d.ts'`，并在 `jsconfig.json` 的 `include` 中加入这两个文件。

### 3. 主题配置

- 品牌色、圆角等变量集中在 `src/theme/index.js`，**改一处即全局换肤**；
- `App.vue` 通过 `NConfigProvider` 的 `theme` / `theme-overrides` 注入，中文语言包 `zhCN` 也已接入；
- 明暗模式由 `useAppStore` 管理并持久化到 `localStorage`，首次进入会跟随系统偏好，顶栏右侧按钮可实时切换；
- 业务样式用的语义变量（`--tl-surface`、`--tl-board` 等）定义在 `src/styles/index.css`，按 `html[data-theme]` 切换，**不依赖 Naive UI 的内部 CSS 变量命名**。

### 4. Provider 与全局 API

`useMessage()` 等只能在对应 Provider 的后代组件中调用。`src/components/NaiveApiBridge.vue` 位于所有 Provider 内部，会把实例注册进 `src/utils/naive.js`，因此在**路由守卫、请求拦截器等非组件环境**也能使用：

```js
import { getNaiveApi } from '@/utils/naive'
getNaiveApi().message?.error('请求失败')
```

### 5. 路径别名

`@` 指向 `src`（`vite.config.js` 的 `resolve.alias` + `jsconfig.json` 的 `paths`），例如：

```js
import { useAppStore } from '@/stores'
```

### 6. 开发代理

`vite.config.js` 已把 `/api` 转发到后端，前端代码里只写相对路径，不硬编码后端域名：

```js
server: {
  port: 5173,
  proxy: {
    '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  },
},
```

生产环境由 Nginx 等网关承担同样的转发职责。

---

## 七、如何扩展

**新增一个页面（3 步）：**

1. 在 `src/views/` 下新建 `XxxView.vue`；
2. 在 `src/router/routes.js` 的 `children` 中追加路由（含 `meta.title`）；
3. 在 `src/router/routes.js` 的 `menuRoutes` 中补一条菜单项，侧边栏即会出现入口。

> 详情类页面可用 `meta.activeMenu` 让父级菜单保持高亮，用 `meta.parent` 在顶栏生成可点击的上级面包屑（参考 `/albums/:albumId`）。

**新增一个 store：** 在 `src/stores/` 下新建文件，用 `defineStore` 定义后，从 `src/stores/index.js` 导出即可。

**新增一个接口层：** 在 `src/api/` 下按模块建文件，统一走 `request.js`，错误消息由调用方配合 `useMessage()` 提示。

**新增一个后端模块：** 见 [`server/README.md`](./server/README.md) 第九节。

---

## 八、常见问题

| 问题 | 原因与解决 |
| --- | --- |
| `n-xxx` 组件不生效 / 控制台报未知组件 | 确认 `vite.config.js` 中已配置 `Components({ resolvers: [NaiveUiResolver()] })`，修改配置后需重启 dev server |
| 调用 `useMessage()` 报错 `No outer <n-message-provider />` | 该组合函数只能在 Provider 后代中调用；跨组件场景请改用 `getNaiveApi()` |
| 编辑器不识别 `@/` 别名 | 确认 `jsconfig.json` 存在且重启编辑器（VS Code 需 Volar 插件） |
| Node 版本报错 `EBADENGINE` | 升级到 Node 20.19+ / 22.12+ 后重新 `npm install` |
| 相册页一直转圈 / 报「请求失败」 | 后端没启动。执行 `cd server && uv run tradinglog-server` |
| 上传大图失败 | 单张上限 20MB，可在 `.env` 中调 `MAX_IMAGE_BYTES` |
| 图片在别的电脑上看不到 | 数据存在后端 `server/data/` 下（已忽略版本库），需要迁移时整体拷贝该目录 |
