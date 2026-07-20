import { ref } from 'vue'

// 发布新图文后置 true,首页 onShow 检测到就刷新一次(避免每次切 tab 都重载)
export const feedDirty = ref(false)
