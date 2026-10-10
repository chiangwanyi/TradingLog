# TradingLog 项目备忘

## 项目定位（重要）

- 本工程是**纯脚手架/基础模板**，当前刻意保持最小化：**不放业务逻辑、示例数据、演示功能**。
- 曾经存在过的 `AboutView.vue`（介绍页/示例代码）与 `stores/user.js`（模拟登录）已按用户要求删除，**不要以「方便演示」为由重新加回**。
- 后续开发时业务代码应新加在 `src/views/`、`src/api/`、`src/stores/` 中，保持骨架文件干净。

## 技术栈与约定

- Vue 3.5 + Vite 8 + Vue Router 5 + Pinia 4 + Naive UI 2.45，**纯 JavaScript**（不使用 TypeScript）。
- 包管理器 npm；Node 要求 `^20.19.0 || >=22.12.0`。
- 路径别名：`@` -> `src`（vite `resolve.alias` + `jsconfig.json` `paths`）。
- 目录约定：
  - 路由表与侧边栏菜单**同源**于 `src/router/routes.js`（`routes` 的 children + `menuRoutes`）。
  - Store 放 `src/stores/*.js`，从 `src/stores/index.js` 统一导出。
  - 主题变量集中在 `src/theme/index.js`，改品牌色只需改这一处。
  - 页面放 `src/views/`，布局放 `src/layouts/`。
- 新增页面 = 建 `src/views/XxxView.vue` + 在 `routes.js` 的 children 与 `menuRoutes` 各加一项。

## 编码约定

- Naive UI 组件在模板中直接写 `<n-xxx>`，**不做全局注册**；`ref/computed/h`、`useRoute/useRouter`、`useMessage/useDialog` 依赖自动导入，不手写 import。
- 需要在 render 函数里返回组件时，避免与模板的自动引入产生重复导入 —— 优先返回原生节点 + 自己定义的 CSS 类。
- 在非组件环境（路由守卫、请求拦截器）使用 message/dialog，走 `getNaiveApi()`（`src/utils/naive.js`）。
- **涨跌配色遵循中国习惯：涨 = 红 `#d03050`，跌 = 绿 `#18a058`。**（骨架中未内置对应样式类，做行情/持仓相关 UI 时自行定义。）
- 主题切换需同时更新 `<html>` 上的 `data-theme` 与 `color-scheme`，`useAppStore.setThemeMode` 已封装。

## 常用命令

- `npm run dev` —— 开发服务器，http://localhost:5173
- `npm run build` —— 生产构建，产物在 `dist/`
- `npm run preview` —— 预览构建产物，http://localhost:4173
