import { ref } from 'vue'
import { SNAP, readSnap, writeSnapDebounced as writeSnap } from '../utils/snap'

/**
 * 阅读页(图文 feed)列表状态。
 *
 * 为什么放模块级:底部 tabBar 已改用自定义组件 + uni.reLaunch 切换主页,
 * reLaunch 会重新挂载页面、销毁组件内的 ref,导致每次切回「阅读」都全量重载、
 * 丢失已加载内容和滚动位置。模块顶层的 ref 不随组件销毁,用作跨切 tab 的缓存。
 *
 * navigateBack 路径(write 发完帖返回)不会重挂载页面,组件内状态本就在;
 * 此时若 dirty=true,onShow 会触发一次刷新拉取新帖。
 *
 * 离线快照(SWR):拉取成功后 persistFeedSnap() 持久化;冷启动时 hydrateFeedFromSnap()
 * 先填上次内容立即展示,页面再后台静默刷新覆盖。hydrated/dirty 语义不变。
 */
export const articles = ref([])
export const keyword = ref('')
export const page = ref(1)
export const noMore = ref(false)
export const loading = ref(false)

export const scrollTop = ref(0)     // 离开页面时的滚动位置,reLaunch 回来后还原
export const hydrated = ref(false)  // 是否已加载过(决定 reLaunch 回来是「还原缓存」还是「首次拉取」)
export const dirty = ref(false)     // 失效标记:发布/删除图文后置 true,下次进阅读页时刷新

/** 失效缓存(发布新图文后调用)。 */
export function invalidateFeed() {
  dirty.value = true
}

/** 重置全部 feed 状态(登出换号时调用,避免看到上一账号的列表残留)。 */
export function resetFeed() {
  articles.value = []
  keyword.value = ''
  page.value = 1
  noMore.value = false
  loading.value = false
  scrollTop.value = 0
  hydrated.value = false
  dirty.value = false
}

/** 从持久快照水合列表(冷启动立即展示上次内容)。命中返回 true;不改动 hydrated 语义。 */
export function hydrateFeedFromSnap() {
  const s = readSnap(SNAP.FEED)
  if (!s) return false
  articles.value = s.data.articles || []
  keyword.value = s.data.keyword || ''
  return true
}

/** 持久化当前列表为快照(拉取成功后调用)。 */
export function persistFeedSnap() {
  writeSnap(SNAP.FEED, {
    articles: articles.value,
    keyword: keyword.value
  })
}
