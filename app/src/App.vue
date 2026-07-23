<script>
import { isLoggedIn } from './store/user'
import { applyTheme } from './store/theme'

export default {
  onLaunch() {
    // 主题:尽早应用,避免首屏闪白/闪黑
    applyTheme()
    // 全局登录守卫:未登录直接进登录页
    if (!isLoggedIn()) {
      uni.reLaunch({ url: '/pages/login/index' })
    }
  }
}
</script>

<style>
/* 全局暖色基底 */
page {
  background-color: #FDFBF7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
    'Noto Sans', sans-serif;
  color: #4A4A4A;
  font-size: 30rpx;
  line-height: 1.8;
}

/* 色彩/圆角/阴影 —— CSS 变量,供各页面引用 */
page {
  --warm-white: #FDFBF7;
  --warm-surface: #ffffff;
  --warm-surface-2: #f3eee5;
  --wood-bark: #C4A882;
  --moss-green: #88A07A;
  --sunset-pink: #E8C4C4;
  --text-main: #4A4A4A;
  --text-sec: #8D8D8D;
  --text-mute: #b0b0b0;
  --border-soft: rgba(196, 168, 130, 0.12);
  --shadow-soft: 0 8rpx 64rpx rgba(196, 168, 130, 0.15);
  --radius-lg: 48rpx;
  --radius-md: 32rpx;
}

/* 暗色模式:复用树洞页深夜蓝色板
   - H5:由 store/theme.js 在 <html>(:root) 上设 data-theme="dark",CSS 变量向下继承
   - App/小程序:setAttribute 无效,降级为浅色(各页面可用 effectiveTheme ref 自行绑 :class)
   - 树洞页固定深色,不受全局主题影响 */
:root[data-theme="dark"] {
  --warm-white: #14141a;
  --warm-surface: #1f1f28;
  --warm-surface-2: #2a2a36;
  --wood-bark: #C4A882;
  --moss-green: #88A07A;
  --sunset-pink: #E8C4C4;
  --text-main: #D8D8E0;
  --text-sec: #9a9ab0;
  --text-mute: #6e6e86;
  --border-soft: rgba(255, 255, 255, 0.08);
  --shadow-soft: 0 8rpx 64rpx rgba(0, 0, 0, 0.4);
}
:root[data-theme="dark"] page,
:root[data-theme="dark"] .home,
:root[data-theme="dark"] .mine,
:root[data-theme="dark"] .read,
:root[data-theme="dark"] .write,
:root[data-theme="dark"] .settings,
:root[data-theme="dark"] .login {
  background-color: #14141a !important;
  color: #D8D8E0 !important;
}

.status-bar-spacer {
  width: 100%;
}

/* 顶部状态栏占位:custom navigationStyle 下,系统状态栏会盖在 y=0 上,
   此元素撑出与状态栏等高的空白避免内容被遮。
   sticky + 不透明背景(继承各页面根容器底色):滚动时粘在顶部,
   防止正文"穿过"状态栏区域被系统 UI 视觉遮挡。
   - 大多数页面继承 .home/.mine/.read 等的 #FDFBF7
   - 树洞页继承 .hole 的 #0d0d12
   - 暗色模式下,各页面根容器会重写 background,这里跟着继承 */
.status-bar {
  width: 100%;
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: inherit;
}

/* 公共工具类 */
.container {
  padding: 0 48rpx;
}

.card {
  background: var(--warm-surface);
  border-radius: 48rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: var(--shadow-soft);
}

.tag {
  display: inline-block;
  padding: 6rpx 18rpx;
  background: rgba(136, 160, 122, 0.15);
  color: #88A07A;
  border-radius: 24rpx;
  font-size: 22rpx;
  margin-right: 12rpx;
}

.tag-pink {
  background: rgba(232, 196, 196, 0.25);
  color: #B88A8A;
}

.serif {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
}

/* 骨架屏 shimmer 基础类:各页面用 .sk + 自定尺寸 class */
.sk {
  background: linear-gradient(90deg, #efe9df 25%, #f7f2ea 37%, #efe9df 63%);
  background-size: 400% 100%;
  animation: sk-shimmer 1.4s ease infinite;
}
@keyframes sk-shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
}

* {
  -webkit-tap-highlight-color: transparent;
}

view,
text {
  -webkit-user-select: none;
  user-select: none;
}

input,
textarea {
  -webkit-user-select: text;
  user-select: text;
}

/* 富文本区允许选中复制(mp-html 容器 + 自定义渲染的 rich-content)
   覆盖上面 view/text 的 user-select:none,否则 mp-html 的 selectable 失效 */
.rich-content,
.mp-html,
.rich {
  -webkit-user-select: text;
  user-select: text;
}

/* 暗色模式穿透覆盖:scoped style 里硬编码的颜色,通过高特异性选择器穿透覆盖。
   折中:不为每个页面全面 CSS 变量化,而是用 :root[data-theme=dark] 前缀穿透 scoped。
   仅 H5 端完全生效;App/小程序 scoped style 不被 :root 选择器穿透,降级为浅色。 */
:root[data-theme="dark"] .card,
:root[data-theme="dark"] .ftag,
:root[data-theme="dark"] .like-btn,
:root[data-theme="dark"] .tab-item,
:root[data-theme="dark"] .dialog,
:root[data-theme="dark"] .logout-btn {
  background: #1f1f28 !important;
  color: #D8D8E0 !important;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.4) !important;
}
:root[data-theme="dark"] .title,
:root[data-theme="dark"] .topbar-title,
:root[data-theme="dark"] .header-title,
:root[data-theme="dark"] .nav-title,
:root[data-theme="dark"] .nickname,
:root[data-theme="dark"] .row-label,
:root[data-theme="dark"] .mini-title,
:root[data-theme="dark"] .dialog-title {
  color: #E8E8F0 !important;
}
:root[data-theme="dark"] .desc,
:root[data-theme="dark"] .meta,
:root[data-theme="dark"] .bio,
:root[data-theme="dark"] .header-sub,
:root[data-theme="dark"] .row-text,
:root[data-theme="dark"] .author-time,
:root[data-theme="dark"] .mini-time {
  color: #8888A0 !important;
}
:root[data-theme="dark"] .row,
:root[data-theme="dark"] .media-bar {
  border-bottom-color: rgba(255, 255, 255, 0.08) !important;
}
:root[data-theme="dark"] .dialog-input,
:root[data-theme="dark"] .media-btn,
:root[data-theme="dark"] .th-btn {
  background: #2a2a36 !important;
  color: #C0C0D0 !important;
}

/* 动画开关:由用户在设置页主动选择(store/theme.js 的 animationsEnabled)。
   - 默认开,不响应系统的 prefers-reduced-motion(那是辅助功能,交给系统级开关;
     Windows 默认开启「减少动画」会全员误伤,故 App 内独立控制)。
   - 关闭时给 <html> 加 .animations-off,把所有 animation/transition 压成瞬态;
     作用范围是「整页」,符合用户「我不要动画」的预期。
   - 非 H5 端 classList.toggle 无效:降级为不动(small trade-off,后续按页面单独处理)。 */
:root.animations-off *,
:root.animations-off *::before,
:root.animations-off *::after {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
  scroll-behavior: auto !important;
}
</style>
