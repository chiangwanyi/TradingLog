/**
 * 批注颜色工具。
 *
 * 为什么要在 JS 里算 CSS 变量，而不是写死几个颜色类：
 * 颜色是「每个批注各自不同」的，CSS 类只能表达固定几种取值。
 * 这里把 `#rrggbb` 展开成一组带透明度的变量，以内联 style 下发给批注图形，
 * 让序号图标、矩形、清单里的小色块共用同一套取值规则。
 */

/** 默认强调色，与 styles/index.css 里的 --anno-accent 保持一致 */
export const DEFAULT_ANNOTATION_COLOR = '#f59e0b'

/** 预设色盘：挑的是在浅底 / 深底 K 线图上都足够醒目的颜色，默认色排第一位 */
export const PRESET_ANNOTATION_COLORS = [
  '#f59e0b', // 琥珀（默认）
  '#ef4444', // 红
  '#f97316', // 橘
  '#eab308', // 黄
  '#84cc16', // 黄绿
  '#22c55e', // 绿
  '#06b6d4', // 青
  '#3b82f6', // 蓝
  '#6366f1', // 靛
  '#a855f7', // 紫
  '#ec4899', // 粉
  '#f1f5f9', // 白
]

const HEX_RE = /^#[0-9a-f]{6}$/

/** 是否是合法颜色值（小写化后判断，大小写都接受） */
export function isAnnotationColor(value) {
  return HEX_RE.test(String(value ?? '').trim().toLowerCase())
}

/**
 * 任意输入 -> 合法的小写 hex。
 * 空串（后端表示「未指定颜色」）、脏数据都会回落到默认色，
 * 因此界面永远拿得到一个具体颜色，不需要到处判空。
 */
export function normalizeAnnotationColor(value) {
  const text = String(value ?? '').trim().toLowerCase()
  return HEX_RE.test(text) ? text : DEFAULT_ANNOTATION_COLOR
}

/**
 * 生成批注图形的内联 CSS 变量。
 *
 * --anno-color         主色（图标底色、矩形描边）
 * --anno-color-soft    柔和的矩形填充
 * --anno-color-strong  选中态的矩形填充
 * --anno-color-ring    选中 / 闪烁时的外发光
 * --anno-color-on      叠在主色上的前景色（序号数字）
 */
export function annotationColorVars(value) {
  const color = normalizeAnnotationColor(value)
  const { r, g, b } = toRgb(color)
  return {
    '--anno-color': color,
    '--anno-color-soft': `rgba(${r}, ${g}, ${b}, 0.18)`,
    '--anno-color-strong': `rgba(${r}, ${g}, ${b}, 0.32)`,
    '--anno-color-ring': `rgba(${r}, ${g}, ${b}, 0.5)`,
    '--anno-color-on': onColorFor(color),
  }
}

/**
 * 底色上该用深字还是浅字。
 * 用 sRGB 感知亮度近似公式（人眼对绿最敏感），阈值 0.68 ——
 * 这样默认的琥珀色仍然配白字（保持原有观感），而白/黄这类浅色会翻成深字，
 * 否则序号数字会糊在色块里看不见。
 */
export function onColorFor(value) {
  const { r, g, b } = toRgb(normalizeAnnotationColor(value))
  const brightness = (r * 299 + g * 587 + b * 114) / 255000
  return brightness > 0.68 ? '#1f2937' : '#ffffff'
}

function toRgb(color) {
  return {
    r: parseInt(color.slice(1, 3), 16),
    g: parseInt(color.slice(3, 5), 16),
    b: parseInt(color.slice(5, 7), 16),
  }
}
