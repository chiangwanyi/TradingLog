# TradingLog

前后端分离的全栈工程：

- **前端**：Vue 3 + JavaScript + Naive UI，已完成路由、状态管理、UI 按需引入与主题配置，位于仓库根目录。
- **后端**：FastAPI + uv 的 Python 服务，位于 [`server/`](./server/README.md)。

两端均保持最小化的初始状态：**不含任何业务逻辑、示例数据与演示功能**，仅保留项目结构与基础配置，可直接在此基础上开发。

---

## 一、技术栈

| 分类 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | Vue 3.5 | Composition API + `<script setup>` |
| 构建 | Vite 8 | 极速冷启动、HMR |
| 路由 | Vue Router 5 | History 模式、路由懒加载、全局守卫 |
| 状态 | Pinia 4 | `app` store（主题 / 侧边栏） |
| UI | Naive UI 2.45 | 组件与组合函数全部按需引入 |
| 语言 | JavaScript | 纯 JS，无 TypeScript |
| 代码风格 | EditorConfig | 2 空格缩进、LF 换行 |
| 后端框架 | FastAPI 0.143 | 异步 API，自动生成 OpenAPI/Swagger 文档 |
| 后端运行时 | Python 3.13 | 由 uv 管理，无需手动安装 |
| 后端依赖管理 | uv 0.12 | `pyproject.toml` 声明 + `uv.lock` 锁定 |

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

```bash
# 1. 进入项目目录
cd TradingLog

# 2. 安装依赖
npm install

# 3. 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 4. 生产环境构建，产物输出到 dist/
npm run build

# 5. 本地预览构建产物（http://localhost:4173）
npm run preview
```

> 若 `npm install` 较慢，可切换镜像源：
> `npm config set registry https://registry.npmmirror.com`

### 后端（server/）

后端是独立的 Python 项目，用 [uv](https://docs.astral.sh/uv/) 管理，**不使用 npm**：

```bash
cd server

uv sync                      # 按 uv.lock 安装依赖（首次会自动创建 .venv）

cp .env.example .env         # 可选：按需修改配置

uv run tradinglog-server     # 启动服务（等价于 uvicorn app.main:app --reload）
uv run pytest                # 跑测试
```

启动后接口为 http://127.0.0.1:8000/api/v1/health ，交互文档在 http://127.0.0.1:8000/docs 。
依赖管理与配置方式的完整说明见 [`server/README.md`](./server/README.md)。

---

## 四、目录结构

```
TradingLog/
├─ index.html                 # 应用入口 HTML
├─ vite.config.js             # Vite 配置：别名、按需引入、开发服务器
├─ jsconfig.json              # 编辑器路径别名提示（@ -> src）
├─ .editorconfig              # 统一代码风格
├─ public/
│  └─ favicon.svg
└─ src/
   ├─ main.js                 # 应用入口：注册 Pinia / Router / 全局样式
   ├─ App.vue                 # 根组件：NConfigProvider + 各 Provider 装配
   ├─ router/
   │  ├─ index.js             # 创建路由实例、全局守卫、滚动行为
   │  └─ routes.js            # 路由表 + 侧边栏菜单配置
   ├─ stores/                 # Pinia 状态管理
   │  ├─ index.js             # pinia 实例与统一导出
   │  └─ app.js               # 主题模式、侧边栏折叠
   ├─ theme/
   │  └─ index.js             # 品牌色与深浅主题变量覆盖
   ├─ layouts/
   │  └─ MainLayout.vue       # 侧边栏 + 顶栏 + 内容区
   ├─ views/
   │  ├─ HomeView.vue         # 首页（空状态占位）
   │  └─ NotFoundView.vue     # 404
   ├─ components/
   │  ├─ NaiveApiBridge.vue   # 在 Provider 内部注册全局 message/dialog 等
   │  └─ icons.js             # 轻量内联 SVG 图标组件
   ├─ utils/
   │  └─ naive.js             # 全局 Naive UI API 注册中心
   └─ styles/
      └─ index.css            # 全局重置、过渡动画、通用类
```

### 后端模块（server/）

```
server/
├─ pyproject.toml             # 依赖声明 + 工具配置（唯一配置入口）
├─ uv.lock                    # 依赖锁文件，保证可复现安装
├─ .python-version            # 锁定的 Python 版本（3.13）
├─ .env.example               # 环境变量模板
├─ src/
│  └─ app/                    # 应用包（导入路径 app.xxx）
│     ├─ main.py              # 应用工厂 create_app() + ASGI 实例
│     ├─ __main__.py          # 命令行入口
│     ├─ core/config.py       # 配置中心（pydantic-settings）
│     └─ api/v1/              # 路由汇总与各业务模块接口
└─ tests/                     # 后端测试
```

完整说明见 [`server/README.md`](./server/README.md)。

---

## 五、关键配置说明

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
- 明暗模式由 `useAppStore` 管理并持久化到 `localStorage`，首次进入会跟随系统偏好，顶栏右侧按钮可实时切换。

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

---

## 六、如何扩展

**新增一个页面（3 步）：**

1. 在 `src/views/` 下新建 `XxxView.vue`；
2. 在 `src/router/routes.js` 的 `children` 中追加路由（含 `meta.title`）；
3. 在 `src/router/routes.js` 的 `menuRoutes` 中补一条菜单项，侧边栏即会出现入口。

**新增一个 store：** 在 `src/stores/` 下新建文件，用 `defineStore` 定义后，从 `src/stores/index.js` 导出即可。

**新增一个接口层：** 建议在 `src/api/` 下按模块建文件，配合 `utils/naive.js` 里注册的 `message` 做统一错误提示。

---

## 七、常见问题

| 问题 | 原因与解决 |
| --- | --- |
| `n-xxx` 组件不生效 / 控制台报未知组件 | 确认 `vite.config.js` 中已配置 `Components({ resolvers: [NaiveUiResolver()] })`，修改配置后需重启 dev server |
| 调用 `useMessage()` 报错 `No outer <n-message-provider />` | 该组合函数只能在 Provider 后代中调用；跨组件场景请改用 `getNaiveApi()` |
| 编辑器不识别 `@/` 别名 | 确认 `jsconfig.json` 存在且重启编辑器（VS Code 需 Volar 插件） |
| Node 版本报错 `EBADENGINE` | 升级到 Node 20.19+ / 22.12+ 后重新 `npm install` |
