/**
 * 全局主题(浅色 / 深色 / 跟随系统)。
 *
 * 实现思路:
 *  - 用 CSS 变量在 App.vue 的 page 上声明两套色板;[data-theme="dark"] 覆盖一组变量。
 *  - H5:document.documentElement.setAttribute('data-theme', eff),CSS 选择器生效。
 *  - App/小程序:page 元素的 data-attr 框架不一定透传,降级为各页面根 view 上的 :data-theme
 *    (由 effectiveTheme ref 暴露,各页面按需绑定);变量定义一致,只是触发方式不同。
 *  - 树洞页强制暗色:TabBar.vue 与 treehole/index.vue 自身已是深色,主题切换不影响它。
 */
import { ref } from 'vue'

const KEY = 'yinyu_theme'
const ANIM_KEY = 'yinyu_animations'

export const THEME_OPTIONS = [
  { value: 'auto', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' }
]

// 用户偏好(auto / light / dark)
export const themePref = ref(uni.getStorageSync(KEY) || 'auto')
// 实际生效(light / dark)—— 各页面读这个决定是否给根节点加暗色类
export const effectiveTheme = ref('light')

/* 动画开关(默认开)。用户在设置页主动关闭后,App.vue 全局 CSS 把所有 animation/transition
 * 压成瞬态。这里只存偏好和应用 class,不写硬编码 CSS(那部分在 App.vue)。
 * 注意:不响应系统的 prefers-reduced-motion —— 那是辅助功能,默认开/关由用户在 App 内选择。 */
function readAnimPref() {
  try {
    const v = uni.getStorageSync(ANIM_KEY)
    // 未设置过(undefined / '' )→ 默认开(true)
    if (v === undefined || v === null || v === '') return true
    return v === true || v === 'true'
  } catch (e) {
    return true
  }
}
export const animationsEnabled = ref(readAnimPref())

function detectSystemDark() {
  // #ifdef H5
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  return false
  // #endif
  // #ifndef H5
  try {
    const info = uni.getSystemInfoSync()
    return info && info.theme === 'dark'
  } catch (e) {
    return false
  }
  // #endif
}

export function applyTheme() {
  const eff =
    themePref.value === 'auto' ? (detectSystemDark() ? 'dark' : 'light') : themePref.value
  effectiveTheme.value = eff
  // #ifdef H5
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.setAttribute('data-theme', eff)
    // 动画开关:H5 给 <html> 加 class 触发 App.vue 的全局降级规则
    document.documentElement.classList.toggle('animations-off', !animationsEnabled.value)
  }
  // #endif
  // 非 H5 端:页面通过 effectiveTheme ref 自行绑 :data-theme 或 :class 到根 view
}

export function setTheme(pref) {
  themePref.value = pref
  try {
    uni.setStorageSync(KEY, pref)
  } catch (e) {
    /* ignore */
  }
  applyTheme()
}

/** 设置动画开关(默认 true)。持久化 + 立即应用。 */
export function setAnimationsEnabled(v) {
  const enabled = !!v
  animationsEnabled.value = enabled
  try {
    uni.setStorageSync(ANIM_KEY, enabled)
  } catch (e) {
    /* ignore */
  }
  applyTheme()
}

// 监听系统主题实时变化(仅 H5 端有效;App 端需监听 uni.onThemeChange,留作后续)
// #ifdef H5
if (typeof window !== 'undefined' && window.matchMedia) {
  try {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const cb = () => {
      if (themePref.value === 'auto') applyTheme()
    }
    if (mq.addEventListener) mq.addEventListener('change', cb)
    else if (mq.addListener) mq.addListener(cb)
  } catch (e) {
    /* ignore */
  }
}
// #endif

// #ifdef APP-PLUS
try {
  uni.onThemeChange && uni.onThemeChange(() => {
    if (themePref.value === 'auto') applyTheme()
  })
} catch (e) {
  /* 老版本 uni 可能没有 onThemeChange,忽略 */
}
// #endif

// 模块加载时立即应用一次,保证冷启动就生效
applyTheme()
