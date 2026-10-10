/**
 * 交易截图相册的接口调用。
 *
 * 后端接口一览：
 *   GET    /albums                          图集列表（按交易时间倒序）
 *   POST   /albums                          新建图集
 *   GET    /albums/{id}                     图集详情（含图片与批注）
 *   PATCH  /albums/{id}                     修改图集
 *   DELETE /albums/{id}                     删除图集
 *   POST   /albums/{id}/images              上传图片（multipart，可多张）
 *   DELETE /images/{id}                     删除图片
 *   GET    /images/{id}/file | /thumb       读取原图 / 缩略图
 *   POST   /albums/{id}/annotations         新增批注（序号由后端分配）
 *   PATCH  /annotations/{id}                修改批注
 *   DELETE /annotations/{id}                删除批注
 */

import { http } from './request'

// ---------------------------------------------------------------- 图集

export function fetchAlbums() {
  return http.get('/albums')
}

export function fetchAlbum(albumId) {
  return http.get(`/albums/${albumId}`)
}

export function createAlbum(payload) {
  return http.post('/albums', payload)
}

export function updateAlbum(albumId, payload) {
  return http.patch(`/albums/${albumId}`, payload)
}

export function deleteAlbum(albumId) {
  return http.delete(`/albums/${albumId}`)
}

// ---------------------------------------------------------------- 图片

/**
 * 上传图片。
 * 同一个字段名 `files` 重复追加即可一次传多张，后端按上传顺序入库。
 */
export function uploadImages(albumId, files) {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file, file.name || 'screenshot.png')
  }
  return http.post(`/albums/${albumId}/images`, form)
}

export function deleteImage(imageId) {
  return http.delete(`/images/${imageId}`)
}

// ---------------------------------------------------------------- 批注

export function createAnnotation(albumId, payload) {
  return http.post(`/albums/${albumId}/annotations`, payload)
}

export function updateAnnotation(annotationId, payload) {
  return http.patch(`/annotations/${annotationId}`, payload)
}

export function deleteAnnotation(annotationId) {
  return http.delete(`/annotations/${annotationId}`)
}
