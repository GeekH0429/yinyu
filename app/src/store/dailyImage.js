/**
 * 每日一图状态:跟踪本次会话内是否已弹过今日图。
 *
 * 设计:
 *  - 不做"当天只弹一次"的限制 —— 每次启动 App 都能弹。
 *  - todayLoaded 仅在本次会话内为 true,防止 onShow 反复触发导致重复弹层
 *    (切 tab / 从子页 navigateBack 回首页都会触发 onShow)。
 *  - App 冷启动/进程重启时,模块重新加载,todayLoaded 自动重置为 false。
 *  - 不做 SWR 快照(数据量小、用户期望"今天最新的那张",缓存意义不大)。
 */
import { ref } from 'vue'

export const todayImage = ref(null) // { id, publish_date, image_url, title, description }
export const todayLoaded = ref(false) // 本次会话内是否已请求过今日接口

export function resetDaily() {
  todayImage.value = null
  todayLoaded.value = false
}
