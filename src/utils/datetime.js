/**
 * 时间工具。
 *
 * 后端与本前端约定：所有时间都用**不带时区的本地时间**传输（如 2026-10-09T09:31:00），
 * 避免跨时区解析带来的偏移。JS 对无 Z 的 ISO 字符串按本地时间解析，两边天然一致。
 */

const pad = (value) => String(value).padStart(2, '0')

/** Date -> 'YYYY-MM-DDTHH:mm:ss'（本地时间，用于提交给后端） */
export function toLocalIso(date) {
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  )
}

/** 后端时间字符串 -> Date（无效值时返回 null） */
export function fromApiTime(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

/** 后端时间字符串 -> Date（无效时回退到当前时间），用于回填日期选择器 */
export function toPickerValue(value) {
  return (fromApiTime(value) ?? new Date()).getTime()
}

/** 展示用：2026-10-09 09:31 */
export function formatDateTime(value) {
  const date = fromApiTime(value)
  if (!date) return '—'
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}`
  )
}

/** 展示用：09-31 这种更短的形式 */
export function formatShortDate(value) {
  const date = fromApiTime(value)
  if (!date) return '—'
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** 文件大小展示：1.2 MB */
export function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const size = bytes / 1024 ** index
  return `${size >= 10 || index === 0 ? Math.round(size) : size.toFixed(1)} ${units[index]}`
}
