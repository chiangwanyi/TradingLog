import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'
import { getNaiveApi } from '@/utils/naive'

const BASE_TITLE = 'TradingLog'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,

  /**
   * 切换路由时的滚动行为：
   * 浏览器前进/后退恢复原位置，其余情况回到顶部
   */
  scrollBehavior(to, from, savedPosition) {
    return savedPosition ?? { top: 0, behavior: 'smooth' }
  },
})

/** 全局前置守卫：同步页面标题 + 顶部加载条 */
router.beforeEach((to) => {
  getNaiveApi().loadingBar?.start()

  const title = to.meta?.title
  document.title = title ? `${title} · ${BASE_TITLE}` : BASE_TITLE

  return true
})

/** 全局后置钩子：结束加载条动画 */
router.afterEach(() => {
  getNaiveApi().loadingBar?.finish()
})

export default router
