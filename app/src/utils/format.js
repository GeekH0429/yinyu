export function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

export function formatDate(t) {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN')
}

/** 相对时间:<60s 刚刚 / <60min x 分钟前 / <24h x 小时前 / <7d x 天前 / 更早回退日期 */
export function formatRelative(t) {
  if (!t) return ''
  const d = new Date(t)
  const diff = Date.now() - d.getTime()
  if (Number.isNaN(diff)) return formatTime(t)
  if (diff < 0) return formatTime(t)
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return min + ' 分钟前'
  const hr = Math.floor(min / 60)
  if (hr < 24) return hr + ' 小时前'
  const day = Math.floor(hr / 24)
  if (day < 7) return day + ' 天前'
  return formatDate(t)
}
