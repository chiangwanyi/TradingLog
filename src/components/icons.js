import { h } from 'vue'

/**
 * 轻量图标组件集
 *
 * 采用「函数式组件 + 内联 SVG + currentColor」方案，不引入额外图标库，
 * 颜色会自动继承父级文本色，因而能跟随 Naive UI 主题（含选中态高亮）。
 * 组件同时也可直接放进 NButton / NMenu 的图标插槽。
 */

const svgProps = {
  xmlns: 'http://www.w3.org/2000/svg',
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 1.8,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
}

/** 每次渲染都重新生成子节点，避免复用 vnode 造成更新异常 */
const defineIcon = (name, renderChildren) => ({
  name,
  render: () => h('svg', { ...svgProps }, renderChildren()),
})

export const IconDashboard = defineIcon('IconDashboard', () => [
  h('rect', { x: 3, y: 3, width: 7, height: 7, rx: 1.6 }),
  h('rect', { x: 14, y: 3, width: 7, height: 7, rx: 1.6 }),
  h('rect', { x: 3, y: 14, width: 7, height: 7, rx: 1.6 }),
  h('rect', { x: 14, y: 14, width: 7, height: 7, rx: 1.6 }),
])

export const IconMenu = defineIcon('IconMenu', () => [
  h('path', { d: 'M4 7h16' }),
  h('path', { d: 'M4 12h16' }),
  h('path', { d: 'M4 17h16' }),
])

export const IconSun = defineIcon('IconSun', () => [
  h('circle', { cx: 12, cy: 12, r: 4 }),
  h('path', {
    d: 'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
  }),
])

export const IconMoon = defineIcon('IconMoon', () => [
  h('path', { d: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z' }),
])

export default {
  IconDashboard,
  IconMenu,
  IconSun,
  IconMoon,
}
