import { ref } from 'vue'
import { SNAP, readSnap, writeSnap } from '../utils/snap'

/**
 * 「我的」页列表状态(模块级缓存)。
 *
 * 自定义 tabBar + uni.reLaunch 切主页会重挂载页面、销毁组件内 ref,
 * 导致每次切回「我的」都全量重拉 3 个接口。模块顶层 ref 不随组件销毁,
 * 跨切 tab 缓存;发布/删除/换暗号后置 dirty,下次进页面才刷新(参考 store/feed.js)。
 *
 * 离线快照(SWR):拉取成功后 persistMeSnap() 持久化;冷启动 hydrateMeFromSnap()
 * 先填上次内容,后台再刷新。
 */
export const articles = ref([])
export const treeholes = ref([])
export const hydrated = ref(false)
export const dirty = ref(false)

/** 失效缓存(发布图文/树洞、改资料后调用)。 */
export function invalidateMe() {
  dirty.value = true
}

/** 从持久快照水合(冷启动立即展示)。命中返回 true。 */
export function hydrateMeFromSnap() {
  const s = readSnap(SNAP.ME)
  if (!s) return false
  articles.value = s.data.articles || []
  treeholes.value = s.data.treeholes || []
  return true
}

/** 持久化当前列表为快照(拉取成功后调用)。 */
export function persistMeSnap() {
  writeSnap(SNAP.ME, {
    articles: articles.value,
    treeholes: treeholes.value
  })
}
