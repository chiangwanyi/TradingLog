import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { pinia, useAppStore } from './stores'

import './styles/index.css'

const app = createApp(App)

app.use(pinia)
app.use(router)

// 应用初始主题（读取 localStorage / 系统偏好，并写入 <html>）
const appStore = useAppStore()
appStore.setThemeMode(appStore.themeMode)

app.mount('#app')
