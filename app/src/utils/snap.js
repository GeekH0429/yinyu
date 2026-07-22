/**
 * 接口数据离线快照小工具(SWR 的 stale 层)。
 *
 * feed/me 列表在拉取成功后持久化一份;冷启动/弱网时先读快照立即展示,后台再刷新。
 * App 端 uni.setStorage 底层 plus.storage 无大小限制,列表数据可放心存。
 */
export const SNAP = {
  FEED: 'yinyu_snap_feed',
  ME: 'yinyu_snap_me'
}

/** 读快照;返回 { ts, data } 或 null */
export function readSnap(key) {
  try {
    const raw = uni.getStorageSync(key)
    if (!raw) return null
    const obj = JSON.parse(raw)
    return obj && obj.data ? obj : null
  } catch (e) {
    return null
  }
}

export function writeSnap(key, data) {
  try {
    uni.setStorageSync(key, JSON.stringify({ ts: Date.now(), data }))
  } catch (e) {
    /* ignore */
  }
}

/**
 * 防抖写入:列表每次触底加载都会调一次 persistXxxSnap,频繁同步写 storage 在弱机型上是卡顿源。
 * 按 key 记录最后一次 data,延迟 delay ms 后真正落盘;期间新调用覆盖旧 data。
 */
const debouncers = new Map()
export function writeSnapDebounced(key, data, delay = 500) {
  let entry = debouncers.get(key)
  if (entry) {
    clearTimeout(entry.timer)
  } else {
    entry = {}
    debouncers.set(key, entry)
  }
  entry.data = data
  entry.timer = setTimeout(() => {
    const d = entry.data
    try {
      uni.setStorageSync(key, JSON.stringify({ ts: Date.now(), data: d }))
    } catch (e) {
      /* ignore */
    }
    if (debouncers.get(key) === entry) debouncers.delete(key)
  }, delay)
}

export function clearSnap(key) {
  try {
    uni.removeStorageSync(key)
  } catch (e) {
    /* ignore */
  }
}
