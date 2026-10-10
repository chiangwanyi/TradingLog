/**
 * 路由表
 * - 业务页面统一挂在 MainLayout 之下，共享侧边栏 / 顶栏
 * - 组件统一使用动态 import 做路由级懒加载
 * - meta.title 会被路由守卫用于设置 document.title
 *
 * 新增页面：
 *   1) 在 src/views/ 下创建组件
 *   2) 在下方 children 中追加路由，并在 menuRoutes 中补一条菜单项
 */

const MainLayout = () => import('@/layouts/MainLayout.vue')

export const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '首页' },
      },
    ],
  },

  // 兜底 404，必须放在最后
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面未找到' },
  },
]

/** 供侧边栏菜单使用的导航配置（与 routes 中的 children 保持一致） */
export const menuRoutes = [{ key: '/home', label: '首页', icon: 'dashboard' }]
