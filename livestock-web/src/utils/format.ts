/**
 * 时间格式化工具
 *
 * 后端返回的时间是 ISO 字符串（2026-10-18T17:33:50），直接展示会出现
 * 「T」分隔符，列宽不足时还会从「-」处折行成两行，中文界面统一转成
 * 「YYYY-MM-DD HH:mm:ss」显示。
 *
 * 注意：这里只做字符串替换、不做时区换算。后端存的已经是本地时间，
 * 走 new Date() 解析再输出反而可能因为时区偏移差 8 小时。
 */

/** 转成 YYYY-MM-DD HH:mm:ss；空值返回占位符（默认 '-'） */
export function formatDateTime(value?: string | null, placeholder = '-'): string {
  if (!value) return placeholder
  let s = String(value).trim()
  if (!s) return placeholder
  // 去掉毫秒与时区后缀（.123456 / Z / +08:00）
  s = s.replace(/\.\d+/, '').replace(/(Z|[+-]\d{2}:?\d{2})$/, '')
  s = s.replace('T', ' ')
  // 纯日期补零时间，保证列内格式一致
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return `${s} 00:00:00`
  return s
}

/** 只取日期部分 YYYY-MM-DD */
export function formatDate(value?: string | null, placeholder = '-'): string {
  if (!value) return placeholder
  return String(value).slice(0, 10)
}
