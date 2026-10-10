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

// ---------------------------------------------------------------- 相册模块

/** 相册：叠放的两张图片 */
export const IconAlbum = defineIcon('IconAlbum', () => [
  h('rect', { x: 3, y: 3, width: 18, height: 14, rx: 2 }),
  h('circle', { cx: 8.5, cy: 8.5, r: 1.6 }),
  h('path', { d: 'M3 14l4.5-4 4 3.5L15 10l6 5.5' }),
  h('path', { d: 'M6 21h12' }),
])

export const IconImage = defineIcon('IconImage', () => [
  h('rect', { x: 3, y: 4, width: 18, height: 16, rx: 2 }),
  h('circle', { cx: 8.5, cy: 9.5, r: 1.6 }),
  h('path', { d: 'M4 17l4.5-4 4 3.5L15.5 13 20 17.5' }),
])

export const IconPlus = defineIcon('IconPlus', () => [
  h('path', { d: 'M12 5v14M5 12h14' }),
])

export const IconRefresh = defineIcon('IconRefresh', () => [
  h('path', { d: 'M20 11a8 8 0 1 0-2.3 6.3' }),
  h('path', { d: 'M20 4.5V11h-6' }),
])

export const IconChevronLeft = defineIcon('IconChevronLeft', () => [
  h('path', { d: 'M15 5l-7 7 7 7' }),
])

export const IconChevronRight = defineIcon('IconChevronRight', () => [
  h('path', { d: 'M9 5l7 7-7 7' }),
])

export const IconArrowLeft = defineIcon('IconArrowLeft', () => [
  h('path', { d: 'M19 12H5' }),
  h('path', { d: 'M11 6l-6 6 6 6' }),
])

export const IconTrash = defineIcon('IconTrash', () => [
  h('path', { d: 'M4 7h16' }),
  h('path', { d: 'M10 11v6M14 11v6' }),
  h('path', { d: 'M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12' }),
  h('path', { d: 'M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2' }),
])

export const IconEdit = defineIcon('IconEdit', () => [
  h('path', { d: 'M4 20h4l10-10a2.1 2.1 0 0 0-3-3L5 17v3z' }),
  h('path', { d: 'M13.5 6.5l4 4' }),
])

export const IconUpload = defineIcon('IconUpload', () => [
  h('path', { d: 'M12 16V4' }),
  h('path', { d: 'M7 9l5-5 5 5' }),
  h('path', { d: 'M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2' }),
])

/** 查看模式：眼睛 */
export const IconEye = defineIcon('IconEye', () => [
  h('path', { d: 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z' }),
  h('circle', { cx: 12, cy: 12, r: 2.8 }),
])

/** 批注模式：记号笔 */
export const IconPen = defineIcon('IconPen', () => [
  h('path', { d: 'M15.5 4.5l4 4L8 20H4v-4z' }),
  h('path', { d: 'M13 7l4 4' }),
])

/** 点批注：圆点 + 定位感 */
export const IconPoint = defineIcon('IconPoint', () => [
  h('circle', { cx: 12, cy: 12, r: 4 }),
  h('circle', { cx: 12, cy: 12, r: 8.5, 'stroke-dasharray': '2 3' }),
])

/** 矩形批注：虚线框 */
export const IconRect = defineIcon('IconRect', () => [
  h('rect', { x: 3.5, y: 5.5, width: 17, height: 13, rx: 1.5, 'stroke-dasharray': '3 3' }),
])

/** 批注清单 */
export const IconList = defineIcon('IconList', () => [
  h('path', { d: 'M9 6h11M9 12h11M9 18h11' }),
  h('path', { d: 'M4.5 6h.01M4.5 12h.01M4.5 18h.01' }),
])

export const IconClose = defineIcon('IconClose', () => [
  h('path', { d: 'M6 6l12 12M18 6L6 18' }),
])

export const IconClipboard = defineIcon('IconClipboard', () => [
  h('rect', { x: 5, y: 4.5, width: 14, height: 16, rx: 2 }),
  h('path', { d: 'M9 4.5V3.5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1' }),
  h('path', { d: 'M9 11h6M9 15h4' }),
])

export default {
  IconDashboard,
  IconMenu,
  IconSun,
  IconMoon,
  IconAlbum,
  IconImage,
  IconPlus,
  IconRefresh,
  IconChevronLeft,
  IconChevronRight,
  IconArrowLeft,
  IconTrash,
  IconEdit,
  IconUpload,
  IconEye,
  IconPen,
  IconPoint,
  IconRect,
  IconList,
  IconClose,
  IconClipboard,
}
