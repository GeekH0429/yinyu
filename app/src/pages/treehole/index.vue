<template>
  <view class="hole">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">树洞</text>
      <text class="header-sub">这里没有列表,只有你与暗号之间的秘密。</text>
    </view>

    <!-- 未解锁:暗号传送门 -->
    <view class="portal-wrap" v-if="!revealed">
      <view class="portal" :class="{ leaving: unlocking }">
        <view class="portal-glow"></view>
        <text class="portal-desc">树洞无形&nbsp;&nbsp;&nbsp;回声共鸣</text>

        <view class="pin-group" :class="{ confirm: unlocking }" @tap="focusInput">
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
        <text class="relock" @tap="reset">重新上锁</text>
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
    <view class="fab" @tap="openPublish">
      <view class="fab-icon" v-html="planeSvg"></view>
    </view>

    <!-- 发布树洞弹窗(暗黑) -->
    <view class="mask" v-if="publishVisible" @tap="closePublish">
      <view class="pub-modal" @tap.stop>
        <view class="pub-head">
          <text class="pub-title serif">写一封悄悄话</text>
          <text class="pub-close" @tap="closePublish">✕</text>
        </view>

        <!-- 发布成功:展示暗号 -->
        <view v-if="pubResult" class="pub-result">
          <text class="pub-result-tip">已藏好 ✿ 它的暗号是</text>
          <text class="pub-result-code">{{ pubResult }}</text>
          <text class="pub-result-sub">把暗号私下分享给想让他看到的人</text>
          <view class="pub-result-actions">
            <text class="r-btn" @tap="copyResult">复制</text>
            <text class="r-btn primary" @tap="unlockResult">立即查看</text>
          </view>
        </view>

        <!-- 编辑 -->
        <view v-else class="pub-form">
          <input class="pub-input" v-model="pub.title" placeholder="标题(可选)" />
          <textarea
            class="pub-textarea"
            v-model="pub.content_html"
            placeholder="说出心里话…"
            :maxlength="-1"
            auto-height
          />
          <view class="pub-media">
            <text class="pub-mbtn" @tap="pubInsertImage">🖼 图片</text>
            <text class="pub-mbtn" @tap="pubInsertAudio">🎵 音频</text>
            <text :class="['pub-mbtn', { rec: recording }]" @tap="toggleRecord">{{ recording ? '⏹ 停止' : '🎤 录音' }}</text>
            <text v-if="pubUploading" class="pub-up">上传中…</text>
          </view>
          <view class="pub-rec" v-if="recording">
            <text class="pub-rec-dot">●</text>
            <text class="pub-rec-time">{{ formatRecSecs(recSecs) }}</text>
            <text class="pub-rec-tip">录音中…点「停止」结束并插入正文</text>
          </view>
          <view class="pub-code-row">
            <input
              class="pub-code-input"
              v-model="pub.code"
              type="number"
              :maxlength="6"
              placeholder="留空随机生成 6 位暗号"
            />
            <text class="pub-random" @tap="randomCode">🎲</text>
          </view>
          <button class="pub-submit" :loading="pubSubmitting" @tap="pubSubmit">藏进树洞</button>
        </view>
      </view>
    </view>

    <!-- 纸飞机寄向远方:发布成功动画覆盖层 -->
    <FlyAwayOverlay :playing="flyPlaying" @done="onFlyDone" />

    <TabBar />

    <!-- 音频信息弹窗(z-index 2000,盖在发布弹窗 1000 之上) -->
    <AudioInfoPopup v-model:visible="audioPopup.visible" :src="audioPopup.src" @confirm="onAudioConfirm" />
  </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { api } from '../../api'
import { SERVER_ORIGIN, resourceUrl } from '../../config'
import { chooseImage, pickAudio } from '../../utils/pick'
import { extractAudio, buildAudioCard } from '../../utils/audioCard'
import { normalizeContentHtml } from '../../utils/content'
import { invalidateMe } from '../../store/me'
import { startRecord, stopRecord, cancelRecord } from '../../utils/recorder'
import TabBar from '../../components/TabBar.vue'
import AudioPlayer from '../../components/AudioPlayer.vue'
import FlyAwayOverlay from '../../components/FlyAwayOverlay.vue'
import AudioInfoPopup from '../../components/AudioInfoPopup.vue'

const serverOrigin = SERVER_ORIGIN
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

/* ---- 解锁 ---- */
const code = ref('')
const focused = ref(false)
const loading = ref(false)
const revealed = ref(null)
const enteredCode = ref('')
const unlocking = ref(false)
let rippleTimer1 = null
let rippleTimer2 = null

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
const parsedContent = computed(() => richParsed.value.html)

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
    }, 600)
    rippleTimer2 = setTimeout(() => {
      unlocking.value = false
    }, 1100)
  } catch {
    code.value = ''
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

/* ---- 写树洞 ---- */
const planeSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><path d="M1007.9 7.2C1001.8 3 994.8.8 987.2.8c-6.6 0-12.6 1.7-18.3 5.2L18.9 554.1C5.9 561.4-.2 572.6.6 587.9c1 15.7 8.7 26.2 22.8 31.5l216.4 88.8c5.6 2.3 12 1.2 16.5-2.7L859.2 184.6 380.3 771.6c-9.3 11.4-14.4 25.7-14.4 40.5v176.3c0 7.7 2.3 14.6 6.7 20.9 4.3 6.4 10.2 10.7 17.4 13.4 3.6 1.5 7.8 2.3 12.7 2.3 11.8 0 21.1-4.2 28-13.1l115.5-141.3c8.9-10.9 23.8-14.6 36.8-9.3l236.7 96.8c4.9 1.9 9.5 2.9 13.7 2.9 6.4 0 12.4-1.7 17.7-4.9 8.9-5.2 14.3-13.1 16.4-23.2L1023.7 49.4c3.4-17.1-1.3-31.5-15.8-42.2z" fill="currentColor"/></svg>`

const publishVisible = ref(false)
const pub = reactive({ title: '', content_html: '', code: '' })
// 音频信息弹窗:选音频 / 录音上传后弹出,填写 名称/歌手/封面 再插入卡片
const audioPopup = reactive({ visible: false, src: '' })
const pubUploading = ref(false)
const pubSubmitting = ref(false)
const pubResult = ref('')
const flyPlaying = ref(false)
const recording = ref(false)
const recSecs = ref(0)

async function uploadPicked(path) {
  pubUploading.value = true
  try {
    return (await api.upload(path)).url
  } finally {
    pubUploading.value = false
  }
}

async function pubInsertImage() {
  try {
    const url = await uploadPicked(await chooseImage())
    pub.content_html += `<p><img src="${url}" style="max-width:100%;border-radius:12px"/></p>`
  } catch {
    /* cancel */
  }
}

async function pubInsertAudio() {
  try {
    const url = await uploadPicked(await pickAudio())
    // 上传成功后弹音频信息(名称/歌手/封面),确认再插入卡片
    audioPopup.src = url
    audioPopup.visible = true
  } catch {
    /* cancel / unsupported */
  }
}

function onAudioConfirm({ title, artist, cover }) {
  pub.content_html += buildAudioCard({ src: audioPopup.src, title, artist, cover })
  uni.showToast({ title: '已加入', icon: 'success' })
}

async function toggleRecord() {
  if (!recording.value) {
    try {
      recSecs.value = 0
      await startRecord({ onTick: (s) => (recSecs.value = s) })
      recording.value = true
    } catch {
      uni.showToast({ title: '无法访问麦克风', icon: 'none' })
    }
    return
  }
  // 停止 → 上传 → 弹音频信息(名称/歌手/封面)→ 确认插入卡片
  recording.value = false
  try {
    const r = await stopRecord()
    if (!r.duration) return
    pubUploading.value = true
    const data = await api.uploadRecorded(r)
    audioPopup.src = data.url
    audioPopup.visible = true
  } catch {
    /* ignore */
  } finally {
    pubUploading.value = false
    recSecs.value = 0
  }
}

function formatRecSecs(s) {
  const m = Math.floor(s / 60)
  const ss = s % 60
  return `${m}:${String(ss).padStart(2, '0')}`
}

function randomCode() {
  let s = ''
  for (let i = 0; i < 6; i++) s += Math.floor(Math.random() * 10)
  pub.code = s
}

async function pubSubmit() {
  if (!pub.content_html.trim()) {
    return uni.showToast({ title: '写点什么吧', icon: 'none' })
  }
  pubSubmitting.value = true
  try {
    const code = pub.code && /^\d{6}$/.test(pub.code) ? pub.code : null
    const res = await api.write.createTreehole({
      title: pub.title || null,
      content_html: normalizeContentHtml(pub.content_html),
      code
    })
    pubResult.value = res.code
    flyPlaying.value = true // 放飞纸飞机,动画结束后由 onFlyDone 复位
    invalidateMe() // 我的树洞新增一篇,回「我的」时刷新
  } catch {
    /* 拦截器已提示 */
  } finally {
    pubSubmitting.value = false
  }
}

function onFlyDone() {
  flyPlaying.value = false
}

function copyResult() {
  uni.setClipboardData({ data: pubResult.value })
}

function unlockResult() {
  // 用刚生成的暗号直接解锁查看
  code.value = pubResult.value
  publishVisible.value = false
  resetPub()
  onUnlock()
}

function resetPub() {
  pub.title = ''
  pub.content_html = ''
  pub.code = ''
  pubResult.value = ''
}

function openPublish() {
  resetPub()
  publishVisible.value = true
}

function closePublish() {
  if (recording.value) {
    recording.value = false
    cancelRecord()
  }
  flyPlaying.value = false
  publishVisible.value = false
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

/* 发布弹窗 */
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.pub-modal {
  width: 620rpx;
  max-height: 86vh;
  overflow-y: auto;
  background: #1a1a24;
  border-radius: 40rpx;
  padding: 48rpx 40rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.5);
}
.pub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}
.pub-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #e0e0e0;
}
.pub-close {
  font-size: 40rpx;
  color: #555568;
  padding: 0 8rpx;
}
.pub-input {
  width: 100%;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  color: #c8c8d8;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}
.pub-textarea {
  width: 100%;
  min-height: 280rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 24rpx;
  font-size: 30rpx;
  line-height: 1.7;
  color: #c8c8d8;
  box-sizing: border-box;
}
.pub-media {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 20rpx 0;
}
.pub-mbtn {
  padding: 12rpx 24rpx;
  background: rgba(123, 140, 196, 0.12);
  color: #7b8cc4;
  border-radius: 20rpx;
  font-size: 26rpx;
}
.pub-up {
  color: #7b8cc4;
  font-size: 24rpx;
}
.pub-mbtn.rec {
  background: rgba(224, 112, 112, 0.15);
  color: #e07070;
}
.pub-rec {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 16rpx;
  padding: 16rpx 20rpx;
  background: rgba(123, 140, 196, 0.08);
  border-radius: 16rpx;
}
.pub-rec-dot {
  color: #e07070;
  font-size: 24rpx;
  animation: recBlink 1s infinite;
}
@keyframes recBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.pub-rec-time {
  color: #c0c8e0;
  font-size: 28rpx;
  font-family: 'Menlo', monospace;
}
.pub-rec-tip {
  color: #555568;
  font-size: 22rpx;
}
.pub-code-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 28rpx;
}
.pub-code-input {
  flex: 1;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 0 24rpx;
  font-size: 32rpx;
  letter-spacing: 8rpx;
  color: #c8c8d8;
  box-sizing: border-box;
}
.pub-random {
  width: 80rpx;
  height: 80rpx;
  background: rgba(123, 140, 196, 0.12);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.pub-submit {
  width: 100%;
  height: 92rpx;
  line-height: 92rpx;
  background: linear-gradient(135deg, #3d4466 0%, #7b8cc4 100%);
  color: #fff;
  border-radius: 46rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
}
.pub-submit::after {
  border: none;
}

/* 发布成功 */
.pub-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 0;
}
.pub-result-tip {
  color: #7b8cc4;
  font-size: 28rpx;
}
.pub-result-code {
  font-size: 88rpx;
  font-weight: 700;
  letter-spacing: 16rpx;
  color: #c0c8e0;
  font-family: 'Menlo', monospace;
  margin: 24rpx 0 12rpx;
}
.pub-result-sub {
  color: #555568;
  font-size: 24rpx;
  text-align: center;
}
.pub-result-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}
.r-btn {
  padding: 16rpx 48rpx;
  border-radius: 36rpx;
  font-size: 28rpx;
  background: rgba(255, 255, 255, 0.06);
  color: #c8c8d8;
}
.r-btn.primary {
  background: linear-gradient(135deg, #3d4466 0%, #7b8cc4 100%);
  color: #fff;
}
</style>
