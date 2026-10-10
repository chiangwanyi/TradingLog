/**
 * 图集 store。
 *
 * 只负责「图集列表」这一份全局状态：列表页用它渲染，增删改之后统一重新拉取，
 * 让后端的排序规则（按交易时间倒序）成为唯一事实来源。
 * 图集**详情**（图片 + 批注）是页面级状态，放在 AlbumDetailView 内部维护。
 */

import { defineStore } from 'pinia'

import { albumApi } from '@/api'

export const useAlbumStore = defineStore('album', {
  state: () => ({
    albums: [],
    loading: false,
    loaded: false,
    error: '',
  }),

  getters: {
    total: (state) => state.albums.length,
    /** 已成功加载过、但一条都没有 —— 用于区分「空相册」与「还没加载」 */
    isEmpty: (state) => state.loaded && state.albums.length === 0,
  },

  actions: {
    async load({ force = false } = {}) {
      if (this.loading) return
      if (this.loaded && !force) return

      this.loading = true
      this.error = ''
      try {
        this.albums = await albumApi.fetchAlbums()
        this.loaded = true
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    refresh() {
      return this.load({ force: true })
    },

    /** 以下三个动作都会在成功后刷新列表，保证页面与后端一致 */
    async create(payload) {
      const album = await albumApi.createAlbum(payload)
      await this.refresh()
      return album
    },

    async update(albumId, payload) {
      const album = await albumApi.updateAlbum(albumId, payload)
      await this.refresh()
      return album
    },

    async remove(albumId) {
      await albumApi.deleteAlbum(albumId)
      await this.refresh()
    },
  },
})
