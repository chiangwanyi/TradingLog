/**
 * UI 偏好 store。
 *
 * 与 album store 不同，这里存的是「界面怎么显示」而不是业务记录，
 * 目前只有批注调色板的最近使用颜色，持久化在后端 preferences 表。
 */

import { defineStore } from 'pinia'

import { preferenceApi } from '@/api'
import { isAnnotationColor, normalizeAnnotationColor } from '@/utils/color'

/** 与后端 services/preferences.py 的 MAX_RECENT_COLORS 保持一致 */
const MAX_RECENT_COLORS = 12

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    recentAnnotationColors: [],
    loaded: false,
    loading: false,
  }),

  getters: {
    /** 新建批注时沿用的颜色：最近用过的那个 */
    preferredAnnotationColor: (state) => normalizeAnnotationColor(state.recentAnnotationColors[0]),
  },

  actions: {
    async loadRecentColors(force = false) {
      if (this.loading) return
      if (this.loaded && !force) return

      this.loading = true
      try {
        const { recent } = await preferenceApi.fetchRecentAnnotationColors()
        this.recentAnnotationColors = recent ?? []
        this.loaded = true
      } catch {
        // 调色板是锦上添花的能力，取不到就用空列表，不能因此拦着用户画批注
        this.recentAnnotationColors = []
      } finally {
        this.loading = false
      }
    },

    /**
     * 记录一次颜色使用。
     * 先本地乐观更新，让调色板立刻响应；再与后端返回的结果对齐。
     * 后端失败时静默忽略 —— 这只是个颜色记录，不该弹错误打断用户。
     */
    async rememberColor(color) {
      if (!isAnnotationColor(color)) return
      const normalized = normalizeAnnotationColor(color)

      this.recentAnnotationColors = [
        normalized,
        ...this.recentAnnotationColors.filter((item) => item !== normalized),
      ].slice(0, MAX_RECENT_COLORS)

      try {
        const { recent } = await preferenceApi.rememberAnnotationColor(normalized)
        if (Array.isArray(recent)) this.recentAnnotationColors = recent
        this.loaded = true
      } catch {
        // 忽略：本地已经更新过，不影响本次批注
      }
    },
  },
})
