import { ref } from 'vue'

/**
 * 「我的」页列表状态(模块级缓存)。
 *
 * 自定义 tabBar + uni.reLaunch 切主页会重挂载页面、销毁组件内 ref,
 * 导致每次切回「我的」都全量重拉 3 个接口。模块顶层 ref 不随组件销毁,
 * 跨切 tab 缓存;发布/删除/换暗号后置 dirty,下次进页面才刷新(参考 store/feed.js)。
 */
export const articles = ref([])
export const treeholes = ref([])
export const hydrated = ref(false)
export const dirty = ref(false)

/** 失效缓存(发布图文/树洞、改资料后调用)。 */
export function invalidateMe() {
  dirty.value = true
}
