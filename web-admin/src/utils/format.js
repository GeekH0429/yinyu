/** 时间格式化(各列表页共用)。 */
export function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}
