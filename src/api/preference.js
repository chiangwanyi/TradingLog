/**
 * UI 偏好接口。
 *
 * 目前只服务批注调色板：最近用过的颜色存在后端，
 * 这样换浏览器、清缓存之后调色板依然是熟悉的那几个颜色。
 */

import { http } from './request'

/** 最近使用的批注颜色，最近用过的排在最前 */
export function fetchRecentAnnotationColors() {
  return http.get('/preferences/annotation-colors')
}

/** 记录一次颜色使用（后端负责去重、排到最前并截断） */
export function rememberAnnotationColor(color) {
  return http.post('/preferences/annotation-colors', { color })
}
