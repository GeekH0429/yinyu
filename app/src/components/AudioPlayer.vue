<template>
  <view class="audio-player">
    <view class="player-card">
      <!-- 左侧信息 -->
      <view class="info-area">
        <view class="icon-wrapper" :class="{ playing: isPlaying }">
          <text class="music-icon">{{ isPlaying ? '🎵' : '🎶' }}</text>
        </view>
        <view class="text-info">
          <text class="audio-label">音频附件</text>
          <text class="time-display">{{ formatDuration(currentTime) }} / {{ formatDuration(duration) }}</text>
        </view>
      </view>

      <!-- 右侧控制 -->
      <view class="control-area">
        <view class="play-btn" @tap="togglePlay">
          <text class="play-icon">{{ loading ? '…' : (isPlaying ? '⏸' : '▶') }}</text>
        </view>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="progress-wrapper">
      <slider
        :value="progress"
        @change="onSeek"
        @changing="onSeeking"
        class="progress-slider"
        activeColor="#C4A882"
        backgroundColor="#EAE8E4"
        block-size="16"
      />
    </view>
  </view>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const props = defineProps({
  src: { type: String, required: true }
})

const isPlaying = ref(false)
const loading = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progress = ref(0)
const isSeeking = ref(false)

// InnerAudioContext 实例:懒创建(首次播放才 create + 赋 src),
// 避免一进文章就为每个音频预拉流。用普通变量而非 ref(实例本身不参与渲染)。
let ctx = null
let lastUiTick = 0

function ensureContext() {
  if (ctx) return ctx
  ctx = uni.createInnerAudioContext()
  ctx.src = props.src

  ctx.onCanplay(() => {
    if (duration.value === 0 && ctx) duration.value = ctx.duration || 0
  })

  ctx.onTimeUpdate(() => {
    if (!ctx || isSeeking.value) return
    // 节流:每 500ms 更新一次进度 UI,减少 slider 重绘与响应式开销
    const now = Date.now()
    if (now - lastUiTick < 500) return
    lastUiTick = now
    currentTime.value = ctx.currentTime || 0
    const d = ctx.duration || duration.value
    if (d > 0) {
      duration.value = d
      progress.value = (currentTime.value / d) * 100
    }
  })

  ctx.onPlay(() => { isPlaying.value = true; loading.value = false })
  ctx.onPause(() => { isPlaying.value = false })
  ctx.onEnded(() => {
    isPlaying.value = false
    currentTime.value = 0
    progress.value = 0
  })
  ctx.onError((err) => {
    console.error('音频播放错误', err)
    uni.showToast({ title: '音频加载失败', icon: 'none' })
    isPlaying.value = false
    loading.value = false
  })
  return ctx
}

function togglePlay() {
  const c = ensureContext()
  if (isPlaying.value) {
    c.pause()
  } else {
    loading.value = true
    c.play()
  }
}

function onSeek(e) {
  const seekTime = (e.detail.value / 100) * duration.value
  currentTime.value = seekTime
  progress.value = e.detail.value
  isSeeking.value = false
  if (ctx) ctx.seek(seekTime)
}

function onSeeking(e) {
  isSeeking.value = true
  progress.value = e.detail.value
}

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  const c = ctx
  ctx = null  // 先置空,避免卸载后的回调再访问
  if (!c) return
  // App 端原生 InnerAudioContext 的 offXxx() 无参调用会触发
  // "indexOf of undefined" 内部异常,故不手动 offXxx;监听由 destroy 自动清理。
  // stop / destroy 各自隔离,保证 destroy 一定执行。
  try { c.stop() } catch (e) { /* ignore */ }
  try { c.destroy() } catch (e) { /* ignore */ }
})
</script>

<style scoped>
.audio-player {
  margin: 24rpx 0;
}

.player-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx;
  background: #F9F8F6;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
}

.info-area {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.icon-wrapper {
  width: 60rpx;
  height: 60rpx;
  background: linear-gradient(135deg, #E8C4C4 0%, #C4A882 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-wrapper.playing {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.music-icon {
  font-size: 28rpx;
}

.text-info {
  display: flex;
  flex-direction: column;
}

.audio-label {
  font-size: 26rpx;
  color: #4A4A4A;
  font-weight: 500;
  margin-bottom: 4rpx;
}

.time-display {
  font-size: 22rpx;
  color: #AAA;
  font-family: 'Menlo', monospace;
}

.control-area {
  display: flex;
  align-items: center;
}

.play-btn {
  width: 56rpx;
  height: 56rpx;
  background: #88A07A;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(136, 160, 122, 0.3);
}

.play-icon {
  color: #fff;
  font-size: 20rpx;
  margin-left: 2rpx;
}

.progress-wrapper {
  padding: 0 8rpx;
}

.progress-slider {
  width: 100%;
  margin: 0;
}
</style>
