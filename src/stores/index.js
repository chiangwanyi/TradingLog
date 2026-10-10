import { createPinia } from 'pinia'

/** Pinia 实例，在 main.js 中通过 app.use(pinia) 注册 */
export const pinia = createPinia()

export * from './app'
export * from './album'

export default pinia
