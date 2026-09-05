// 时间呈现统一用北京时间(UTC+8):把时刻平移 8h 后按 UTC 读取,
// 不依赖设备时区(App 逻辑层 JS 引擎的 Intl 支持不可靠,故手工计算)。
const CN_OFFSET_MS = 8 * 3600 * 1000

function cnFields(t) {
  if (!t) return null
  const u = new Date(new Date(t).getTime() + CN_OFFSET_MS)
  if (isNaN(u.getTime())) return null
  const p = (n) => String(n).padStart(2, '0')
  return {
    date: u.getUTCFullYear() + '-' + p(u.getUTCMonth() + 1) + '-' + p(u.getUTCDate()),
    hm: p(u.getUTCHours()) + ':' + p(u.getUTCMinutes())
  }
}

/** 北京时间 年月日 时分:YYYY-MM-DD HH:mm */
export function formatTime(t) {
  const f = cnFields(t)
  return f ? f.date + ' ' + f.hm : ''
}

/** 北京时间 年月日:YYYY-MM-DD */
export function formatDate(t) {
  const f = cnFields(t)
  return f ? f.date : ''
}

/** 北京时间 时分:HH:mm */
export function formatHM(t) {
  const f = cnFields(t)
  return f ? f.hm : ''
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
