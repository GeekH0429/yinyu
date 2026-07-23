/**
 * 通知未读数共享 store(mine 页铃铛 + notifications 页共用)。
 *
 * 设计:
 *  - 模块级 unreadCount ref,两处引用同一份状态。
 *  - refreshUnread 从服务端拉取真实值(供 mine 页 onShow 调用)。
 *  - setUnread / decUnread / incUnread 用于本地校正(标记已读后即时反馈)。
 */
import { ref } from 'vue'
import { api } from '../api'

export const unreadCount = ref(0)

export async function refreshUnread() {
  try {
    const r = await api.notifications.unreadCount()
    unreadCount.value = r.count || 0
  } catch {
    /* 静默:未登录或网络问题不打扰 */
  }
}

export function setUnread(n) {
  unreadCount.value = Math.max(0, n || 0)
}

export function decUnread(by = 1) {
  unreadCount.value = Math.max(0, unreadCount.value - by)
}

export function incUnread(by = 1) {
  unreadCount.value += by
}
