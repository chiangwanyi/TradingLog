/**
 * 极简 HTTP 封装。
 *
 * 只依赖浏览器原生 fetch，不引入 axios：
 * 统一拼 /api/v1 前缀、统一 JSON 序列化、统一把后端的 detail 字段转成 Error 消息。
 */

const BASE_URL = '/api/v1'

/** 带 HTTP 状态码的错误，页面可据此区分「没找到」和「网络异常」 */
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** 把后端的错误响应转成可读文案：FastAPI 的 detail 可能是字符串或校验错误数组 */
async function toApiError(response) {
  let message = `请求失败（HTTP ${response.status}）`
  try {
    const body = await response.json()
    const detail = body?.detail
    if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail) && detail.length > 0) {
      message = detail[0]?.msg ?? message
    }
  } catch {
    // 响应体不是 JSON（如网关返回的 HTML），保留默认提示
  }
  return new ApiError(message, response.status)
}

export async function request(path, options = {}) {
  const { method = 'GET', body, signal } = options
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData

  const headers = {}
  if (body !== undefined && !isFormData) headers['Content-Type'] = 'application/json'

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    // FormData 交给浏览器自动带 boundary，手动设 Content-Type 反而会坏掉
    body: isFormData ? body : body === undefined ? undefined : JSON.stringify(body),
    signal,
  })

  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return null
  return response.json()
}

export const http = {
  get: (path, options) => request(path, { ...options, method: 'GET' }),
  post: (path, body, options) => request(path, { ...options, method: 'POST', body }),
  patch: (path, body, options) => request(path, { ...options, method: 'PATCH', body }),
  delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
}
