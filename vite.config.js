import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),

    /**
     * 1) 组合式 API / Naive UI 组合函数自动按需引入
     *    - 'vue' / 'vue-router' 预设：ref、computed、useRoute、useRouter ...
     *    - naive-ui：useMessage / useDialog / useNotification / useLoadingBar
     *    使用时无需手写 import，构建时按需注入。
     */
    AutoImport({
      imports: [
        'vue',
        'vue-router',
        {
          'naive-ui': ['useDialog', 'useMessage', 'useNotification', 'useLoadingBar'],
        },
      ],
      // 纯 JS 工程不生成 d.ts；如需编辑器提示可改为 'auto-imports.d.ts'
      dts: false,
      eslintrc: { enabled: false },
    }),

    /**
     * 2) Naive UI 组件按需引入
     *    模板里直接写 <n-button /> <n-card />，由 NaiveUiResolver 自动解析并按需打包，
     *    无需在 main.js 中全量 app.use(naive)。
     */
    Components({
      resolvers: [NaiveUiResolver()],
      dts: false,
    }),
  ],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    port: 5173,
    // 如需启动后自动打开浏览器，把下一行改为 open: true
    open: false,
    /**
     * 开发代理：前端统一以 /api 开头请求，由 Vite 转发到本机 FastAPI 服务。
     * 这样浏览器眼里是同源请求，既不用处理跨域，生产环境换个网关也不会改前端代码。
     */
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    // Naive UI 体积较大，放宽告警阈值避免噪音
    chunkSizeWarningLimit: 1500,
  },
})
