<template>
  <view class="hole">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">树洞</text>
      <text class="header-sub">这里没有世间的繁华,只有你与世间的和解。</text>
    </view>

    <!-- 未解锁:暗号传送门 -->
    <view class="portal-wrap" v-if="!revealed">
      <view class="portal" :class="{ leaving: unlocking }">
        <view class="portal-glow"></view>
        <text class="portal-desc">树洞无形&nbsp;&nbsp;&nbsp;回声共鸣</text>

        <view class="pin-group" :class="{ confirm: unlocking, shake: pinShake }" @tap="focusInput">
          <view
            v-for="(d, i) in pinDigits"
            :key="i"
            :class="['pin-box', { filled: d !== '' }]"
          >
            <text v-if="d !== ''" class="pin-char">{{ d }}</text>
          </view>
        </view>

        <input
          class="hidden-input"
          v-model="code"
          type="number"
          :maxlength="6"
          :focus="focused"
          @input="onInput"
          @focus="focused = true"
          @blur="focused = false"
        />

        <view class="portal-bottom">
          <text v-if="loading" class="loading-text">正在解锁…</text>
          <text v-else class="portal-hint">输入 6 位数字暗号,打开那一篇</text>
        </view>
      </view>
    </view>

    <!-- 已解锁 -->
    <view class="revealed" v-else>
      <view class="revealed-head">
        <text class="badge">🔓 暗号 [{{ enteredCode }}] 解锁</text>
        <text class="relock" @tap="reset">返回</text>
      </view>

      <view class="hole-card">
        <text class="hole-title" v-if="revealed.title">{{ revealed.title }}</text>
        <text class="hole-from">— 一封来自远方的悄悄话 —</text>

        <!-- 音频播放器 -->
        <view class="rich-content">
          <AudioPlayer
            v-for="audio in parsedAudioList"
            :key="audio.id"
            :src="audio.fullSrc"
            :title="audio.title"
            :artist="audio.artist"
            :cover="audio.fullCover"
          />
          <mp-html
            class="rich"
            :content="parsedContent"
            selectable
            :domain="serverOrigin"
            :tag-style="richStyle"
            @imgtap="onImgTap"
          />
        </view>

        <view class="hole-foot">
          <text>已被阅读 {{ revealed.view_count }} 次</text>
        </view>
      </view>
    </view>

    <!-- 回声涟漪:输入暗号成功后的解锁动画 -->
    <view class="echo-ripple" v-if="unlocking">
      <view class="echo-flash"></view>
      <view class="ripple ripple-1"></view>
      <view class="ripple ripple-2"></view>
      <view class="ripple ripple-3"></view>
      <text class="echo-caption serif">回声抵达 ✦</text>
    </view>

    <!-- 写树洞浮动按钮 -->
    <view class="fab" @tap="publishVisible = true">
      <view class="fab-icon" v-html="planeSvg"></view>
    </view>

    <!-- 写 / 编辑树洞:暗号展示、纸飞机、音频信息均封装在组件内 -->
    <TreeholeEditor
      v-model:visible="publishVisible"
      @published="onPublished"
      @updated="onUpdated"
      @unlock="onUnlockFromCreate"
    />

    <TabBar />
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { api } from '../../api'
import { SERVER_ORIGIN, resourceUrl, isRemoteUrl } from '../../config'
import { extractAudio } from '../../utils/audioCard'
import { applyCachedImages, extractImgUrls, prefetch } from '../../utils/resourceCache'
import { invalidateMe } from '../../store/me'
import TabBar from '../../components/TabBar.vue'
import AudioPlayer from '../../components/AudioPlayer.vue'
import TreeholeEditor from '../../components/TreeholeEditor.vue'

const serverOrigin = SERVER_ORIGIN
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

/* ---- 解锁 ---- */
const code = ref('')
const focused = ref(false)
const loading = ref(false)
const revealed = ref(null)
const enteredCode = ref('')
const unlocking = ref(false)
const pinShake = ref(false) // 解锁失败时,6 个 PIN 格子整体 shake
let rippleTimer1 = null
let rippleTimer2 = null
let shakeTimer = null

const richStyle = {
  p: 'color:#C8C8D8;line-height:1.9',
  h1: 'color:#E0E0E0',
  h2: 'color:#E0E0E0',
  h3: 'color:#E0E0E0',
  blockquote: 'color:#9aa0b8;border-left:3px solid #7B8CC4;padding-left:12px',
  li: 'color:#C8C8D8',
  a: 'color:#7B8CC4'
}

// 解析音频(提取出来交给 AudioPlayer,正文剥除 audio,避免 mp-html 与 AudioPlayer 双重渲染)
const richParsed = computed(() => extractAudio(revealed.value?.content_html))
const parsedAudioList = computed(() => richParsed.value.audioList)
const parsedContent = computed(() => applyCachedImages(richParsed.value.html))

const pinDigits = computed(() => {
  const arr = ['', '', '', '', '', '']
  for (let i = 0; i < code.value.length && i < 6; i++) arr[i] = code.value[i]
  return arr
})

function focusInput() {
  focused.value = true
}

function onInput() {
  code.value = code.value.replace(/\D/g, '').slice(0, 6)
  if (code.value.length === 6) onUnlock()
}

async function onUnlock() {
  if (loading.value) return
  loading.value = true
  try {
    const data = await api.treeholes.unlock(code.value)
    enteredCode.value = code.value
    focused.value = false
    // 回声涟漪:先涟漪扩散 + 传送门消散,再浮现树洞卡片
    unlocking.value = true
    clearTimeout(rippleTimer1)
    clearTimeout(rippleTimer2)
    rippleTimer1 = setTimeout(() => {
      revealed.value = data
      // 后台预热正文图,下次解锁同暗号时命中本地缓存
      prefetch(extractImgUrls(data.content_html), 'image')
    }, 600)
    rippleTimer2 = setTimeout(() => {
      unlocking.value = false
    }, 1100)
  } catch {
    // 暗号无效(或被限流):清空输入 + PIN 格子整体 shake,反馈更强
    code.value = ''
    pinShake.value = false
    nextTick(() => {
      pinShake.value = true
    })
    clearTimeout(shakeTimer)
    shakeTimer = setTimeout(() => {
      pinShake.value = false
    }, 450)
  } finally {
    loading.value = false
  }
}

function reset() {
  clearTimeout(rippleTimer1)
  clearTimeout(rippleTimer2)
  unlocking.value = false
  revealed.value = null
  enteredCode.value = ''
  code.value = ''
}

/* ---- 写树洞(写作/编辑逻辑封装进 TreeholeEditor,这里只控制显隐与刷新) ---- */
const planeSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><path d="M1007.9 7.2C1001.8 3 994.8.8 987.2.8c-6.6 0-12.6 1.7-18.3 5.2L18.9 554.1C5.9 561.4-.2 572.6.6 587.9c1 15.7 8.7 26.2 22.8 31.5l216.4 88.8c5.6 2.3 12 1.2 16.5-2.7L859.2 184.6 380.3 771.6c-9.3 11.4-14.4 25.7-14.4 40.5v176.3c0 7.7 2.3 14.6 6.7 20.9 4.3 6.4 10.2 10.7 17.4 13.4 3.6 1.5 7.8 2.3 12.7 2.3 11.8 0 21.1-4.2 28-13.1l115.5-141.3c8.9-10.9 23.8-14.6 36.8-9.3l236.7 96.8c4.9 1.9 9.5 2.9 13.7 2.9 6.4 0 12.4-1.7 17.7-4.9 8.9-5.2 14.3-13.1 16.4-23.2L1023.7 49.4c3.4-17.1-1.3-31.5-15.8-42.2z" fill="currentColor"/></svg>`

const publishVisible = ref(false)

function onPublished() {
  // 新增一篇,回「我的」时刷新
  invalidateMe()
}

function onUpdated() {
  invalidateMe()
}

function onUnlockFromCreate(c) {
  // 创建后「立即查看」:复用页面的解锁动画
  code.value = c
  onUnlock()
}

// 正文图片点击 → 全屏预览(可左右滑动浏览本篇所有图)
function onImgTap(e) {
  const tapped = e?.detail?.src || e?.src || ''
  if (!tapped) return
  const urls = extractImgUrls(revealed.value?.content_html || '').map((u) =>
    isRemoteUrl(u) ? u : resourceUrl(u)
  )
  const current =
    urls.find((u) => tapped === u || tapped.indexOf(u) >= 0 || u.indexOf(tapped) >= 0) ||
    urls[0] ||
    tapped
  uni.previewImage({ current, urls: urls.length ? urls : [tapped] })
}
</script>

<style scoped>
.hole {
  min-height: 100vh;
  background: #0d0d12;
  display: flex;
  flex-direction: column;
}
.status-bar {
  width: 100%;
  background: #0d0d12;
}
.header {
  padding: 16rpx 48rpx 24rpx;
}
.header-title {
  font-size: 52rpx;
  font-weight: 700;
  color: #e0e0e0;
  letter-spacing: 4rpx;
}
.header-sub {
  display: block;
  color: #666680;
  font-size: 24rpx;
  margin-top: 8rpx;
}

/* 传送门 */
.portal-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 48rpx 160rpx;
}
.portal {
  width: 100%;
  background: linear-gradient(135deg, #1a1a24 0%, #22222e 100%);
  border-radius: 48rpx;
  padding: 80rpx 48rpx;
  text-align: center;
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.5);
  border: 2rpx solid rgba(255, 255, 255, 0.06);
  position: relative;
  overflow: hidden;
}
.portal.leaving {
  animation: portalLeave 0.55s ease-in 0.05s both;
}
@keyframes portalLeave {
  0% { opacity: 1; transform: scale(1); filter: blur(0); }
  100% { opacity: 0; transform: scale(0.92); filter: blur(6rpx); }
}
.portal-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(100, 120, 200, 0.15) 0%, transparent 60%);
  animation: portalGlow 6s infinite;
}
@keyframes portalGlow {
  0%, 100% { transform: translate(-10%, -10%); }
  50% { transform: translate(10%, 10%); }
}
.portal-desc {
  font-size: 28rpx;
  color: #666680;
  display: block;
  margin-bottom: 60rpx;
  position: relative;
  z-index: 1;
}
.pin-group {
  display: flex;
  justify-content: center;
  gap: 24rpx;
  margin-bottom: 48rpx;
  position: relative;
  z-index: 1;
}
.pin-box {
  width: 88rpx;
  height: 110rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 3rpx solid #333348;
  border-radius: 24rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;
}
.pin-box.filled {
  border-color: #6c7ba0;
  background: rgba(108, 123, 160, 0.12);
}
.pin-group.confirm .pin-box {
  border-color: #7b8cc4;
  background: rgba(123, 140, 196, 0.22);
  animation: pinConfirm 0.45s ease-out both;
}
@keyframes pinConfirm {
  0% { transform: scale(1); box-shadow: 0 0 0 rgba(123, 140, 196, 0); }
  45% { transform: scale(1.14); box-shadow: 0 0 28rpx rgba(123, 140, 196, 0.6); }
  100% { transform: scale(1); box-shadow: 0 0 0 rgba(123, 140, 196, 0); }
}
/* 解锁失败:6 个格子整体 shake,类似 macOS 密码错误的反馈 */
.pin-group.shake {
  animation: pinShake 0.42s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}
@keyframes pinShake {
  0%, 100% { transform: translateX(0); }
  15% { transform: translateX(-14rpx); }
  30% { transform: translateX(12rpx); }
  45% { transform: translateX(-10rpx); }
  60% { transform: translateX(8rpx); }
  75% { transform: translateX(-6rpx); }
  90% { transform: translateX(4rpx); }
}
.pin-char {
  font-size: 44rpx;
  color: #c0c8e0;
  font-weight: 600;
}
.hidden-input {
  position: absolute;
  opacity: 0;
  height: 0;
  width: 0;
}
.portal-bottom {
  position: relative;
  z-index: 1;
}
.portal-hint {
  font-size: 24rpx;
  color: #555568;
}
.loading-text {
  font-size: 26rpx;
  color: #7b8cc4;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* 回声涟漪(解锁动画) */
.echo-ripple {
  position: fixed;
  left: 50%;
  top: 42%;
  z-index: 1001;
  pointer-events: none;
  transform: translate(-50%, -50%);
}
.echo-flash {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 320rpx;
  height: 320rpx;
  margin: -160rpx 0 0 -160rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(123, 140, 196, 0.55) 0%, rgba(123, 140, 196, 0.15) 40%, transparent 70%);
  opacity: 0;
  animation: echoFlash 0.7s 0.05s ease-out both;
}
@keyframes echoFlash {
  0% { opacity: 0; transform: scale(0.4); }
  35% { opacity: 1; }
  100% { opacity: 0; transform: scale(1.6); }
}
.ripple {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 80rpx;
  height: 80rpx;
  margin: -40rpx 0 0 -40rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(123, 140, 196, 0.65);
  opacity: 0;
}
.ripple-1 { animation: rippleOut 1s 0.1s ease-out both; }
.ripple-2 { animation: rippleOut 1s 0.3s ease-out both; }
.ripple-3 { animation: rippleOut 1s 0.5s ease-out both; }
@keyframes rippleOut {
  0% { transform: scale(0.3); opacity: 0; border-width: 5rpx; }
  15% { opacity: 0.85; }
  100% { transform: scale(9); opacity: 0; border-width: 1rpx; }
}
.echo-caption {
  position: absolute;
  left: 50%;
  top: 100%;
  white-space: nowrap;
  color: #7b8cc4;
  font-size: 28rpx;
  letter-spacing: 4rpx;
  opacity: 0;
  animation: echoCap 1s 0.35s ease-out both;
}
@keyframes echoCap {
  0% { opacity: 0; transform: translate(-50%, 60rpx); }
  45% { opacity: 1; transform: translate(-50%, 48rpx); }
  75% { opacity: 1; }
  100% { opacity: 0; transform: translate(-50%, 36rpx); }
}

/* 解锁后 */
.revealed {
  flex: 1;
  padding: 16rpx 48rpx 160rpx;
}
.revealed-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
  animation: headFade 0.5s 0.1s ease-out both;
}
@keyframes headFade {
  from { opacity: 0; }
  to { opacity: 1; }
}
.badge {
  font-size: 26rpx;
  color: #7b8cc4;
  font-weight: 600;
}
.relock {
  font-size: 24rpx;
  color: #666680;
  background: rgba(255, 255, 255, 0.06);
  padding: 12rpx 24rpx;
  border-radius: 40rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.08);
}
.hole-card {
  background: #1a1a24;
  border-radius: 36rpx;
  padding: 48rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.4);
  animation: cardEnter 0.55s 0.15s ease-out both;
}
@keyframes cardEnter {
  0% { opacity: 0; transform: translateY(48rpx) scale(0.95); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
.hole-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 40rpx;
  font-weight: 700;
  color: #e0e0e0;
  display: block;
  margin-bottom: 16rpx;
}
.hole-from {
  display: block;
  color: #555568;
  font-size: 24rpx;
  margin-bottom: 28rpx;
}
.rich {
  font-size: 30rpx;
}

.rich-content {
  margin-top: 16rpx;
}
.hole-foot {
  margin-top: 36rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.06);
  font-size: 24rpx;
  color: #555568;
}

/* 写树洞 FAB */
.fab {
  position: fixed;
  right: 40rpx;
  bottom: 150rpx;
  width: 104rpx;
  height: 104rpx;
  border-radius: 52rpx;
  background: linear-gradient(135deg, #3d4466 0%, #7b8cc4 100%);
  box-shadow: 0 8rpx 32rpx rgba(123, 140, 196, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 998;
}
.fab-icon {
  width: 52rpx;
  height: 52rpx;
  color: #fff;
}
.fab-icon :deep(svg) {
  width: 52rpx;
  height: 52rpx;
  display: block;
}
</style>
