/**
 * Naive UI 全局 API 注册中心
 *
 * 背景：useMessage / useDialog / useNotification / useLoadingBar
 * 必须在其对应 Provider 的后代组件中调用，无法直接在路由守卫、axios 拦截器
 * 等非组件环境里使用。这里由 NaiveApiBridge.vue 在 Provider 内部完成注册，
 * 之后任何地方都能通过 getNaiveApi() 拿到实例。
 */

const api = {
  message: null,
  dialog: null,
  notification: null,
  loadingBar: null,
}

export function registerNaiveApi(instance = {}) {
  Object.keys(api).forEach((key) => {
    if (instance[key]) api[key] = instance[key]
  })
}

export function getNaiveApi() {
  return api
}

export default api
