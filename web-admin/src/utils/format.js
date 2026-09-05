// 时间呈现统一用北京时间(UTC+8):把时刻平移 8h 后按 UTC 读取,不依赖浏览器时区。
const CN_OFFSET_MS = 8 * 3600 * 1000

/** 时间格式化(各列表页共用)。北京时间 年月日 时分:YYYY-MM-DD HH:mm */
export function formatTime(t) {
  if (!t) return ''
  const u = new Date(new Date(t).getTime() + CN_OFFSET_MS)
  if (isNaN(u.getTime())) return ''
  const p = (n) => String(n).padStart(2, '0')
  return (
    u.getUTCFullYear() + '-' + p(u.getUTCMonth() + 1) + '-' + p(u.getUTCDate()) +
    ' ' + p(u.getUTCHours()) + ':' + p(u.getUTCMinutes())
  )
}

/**
 * el-date-picker 等按浏览器本地时区渲染/取值的控件,想显示北京时间需做墙上时钟平移:
 * toBeijingWall 把真实时刻转成"本地渲染出来恰为北京墙上时间"的 Date,fromBeijingWall 反向还原。
 */
export function toBeijingWall(d) {
  return d ? new Date(d.getTime() + CN_OFFSET_MS + d.getTimezoneOffset() * 60000) : d
}

export function fromBeijingWall(w) {
  return w ? new Date(w.getTime() - CN_OFFSET_MS - w.getTimezoneOffset() * 60000) : w
}
