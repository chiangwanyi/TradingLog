import { defineStore } from 'pinia'

const THEME_KEY = 'tradinglog:theme'
const SIDER_KEY = 'tradinglog:sider-collapsed'

/** 首次进入时优先读取本地缓存，其次跟随系统偏好 */
function resolveInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * 应用级全局状态：主题模式、侧边栏折叠
 */
export const useAppStore = defineStore('app', {
  state: () => ({
    /** 'light' | 'dark' */
    themeMode: resolveInitialTheme(),
    siderCollapsed: localStorage.getItem(SIDER_KEY) === '1',
  }),

  getters: {
    isDark: (state) => state.themeMode === 'dark',
    themeLabel: (state) => (state.themeMode === 'dark' ? '深色模式' : '浅色模式'),
  },

  actions: {
    setThemeMode(mode) {
      this.themeMode = mode === 'dark' ? 'dark' : 'light'
      localStorage.setItem(THEME_KEY, this.themeMode)
      // 同步到 <html>，便于全局 CSS 与浏览器原生控件（滚动条 / 表单）跟随主题
      document.documentElement.dataset.theme = this.themeMode
      document.documentElement.style.colorScheme = this.themeMode
    },

    toggleTheme() {
      this.setThemeMode(this.isDark ? 'light' : 'dark')
    },

    setSiderCollapsed(collapsed) {
      this.siderCollapsed = Boolean(collapsed)
      localStorage.setItem(SIDER_KEY, this.siderCollapsed ? '1' : '0')
    },

    toggleSider() {
      this.setSiderCollapsed(!this.siderCollapsed)
    },
  },
})
