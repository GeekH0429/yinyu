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
          <text class="play-icon">{{ isPlaying ? '⏸' : '▶' }}</text>
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
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  }
})

const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progress = ref(0)
const isSeeking = ref(false)

const innerAudioContext = ref(null)

onMounted(() => {
  // 使用 uni.createInnerAudioContext API（支持 H5/小程序/APP）
  innerAudioContext.value = uni.createInnerAudioContext()
  innerAudioContext.value.src = props.src

  // 获取时长
  innerAudioContext.value.onCanplay(() => {
    if (duration.value === 0) {
      duration.value = innerAudioContext.value.duration || 0
    }
  })

  // 时间更新
  innerAudioContext.value.onTimeUpdate(() => {
    if (!isSeeking.value) {
      currentTime.value = innerAudioContext.value.currentTime || 0
      const currentDuration = innerAudioContext.value.duration || duration.value
      if (currentDuration > 0) {
        duration.value = currentDuration
        progress.value = (currentTime.value / duration.value) * 100
      }
    }
  })

  // 播放状态
  innerAudioContext.value.onPlay(() => {
    isPlaying.value = true
  })

  innerAudioContext.value.onPause(() => {
    isPlaying.value = false
  })

  // 播放结束
  innerAudioContext.value.onEnded(() => {
    isPlaying.value = false
    currentTime.value = 0
    progress.value = 0
  })

  // 错误处理
  innerAudioContext.value.onError((err) => {
    console.error('音频播放错误', err)
    uni.showToast({ title: '音频加载失败', icon: 'none' })
    isPlaying.value = false
  })
})

onUnmounted(() => {
  if (innerAudioContext.value) {
    try {
      innerAudioContext.value.stop()
      innerAudioContext.value.offCanplay()
      innerAudioContext.value.offTimeUpdate()
      innerAudioContext.value.offPlay()
      innerAudioContext.value.offPause()
      innerAudioContext.value.offEnded()
      innerAudioContext.value.offError()
      innerAudioContext.value.destroy()
    } catch (e) {
      console.warn('[音频播放器] 清理资源时出错:', e)
    } finally {
      innerAudioContext.value = null
    }
  }
})

function togglePlay() {
  if (isPlaying.value) {
    innerAudioContext.value.pause()
  } else {
    innerAudioContext.value.play()
  }
}

function onSeek(e) {
  const seekTime = (e.detail.value / 100) * duration.value
  currentTime.value = seekTime
  progress.value = e.detail.value
  isSeeking.value = false

  if (innerAudioContext.value) {
    innerAudioContext.value.seek(seekTime)
  }
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
