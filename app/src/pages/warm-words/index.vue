<template>
  <view class="warm" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <!-- 场景选择视图 -->
    <template v-if="view === 'scenes'">
      <view class="topbar">
        <text class="back pressable" @tap="goBack">‹ 返回</text>
        <text class="topbar-title serif">暖话</text>
        <text class="action placeholder"></text>
      </view>

      <view class="guide anim-fade">
        <text class="guide-text serif">今天，你想听到怎样的话？</text>
      </view>

      <view class="scene-grid">
        <view
          v-for="(s, i) in scenes"
          :key="s.scene"
          :class="['scene-card', 'pressable', 'anim-rise', 'delay-' + (i + 1)]"
          @tap="onPickScene(s)"
        >
          <text class="scene-label serif">{{ s.label }}</text>
          <text class="scene-count">{{ s.count }} 句</text>
        </view>
      </view>
    </template>

    <!-- 结果视图 -->
    <template v-else>
      <view class="topbar">
        <text class="back pressable" @tap="backToScenes">‹ 选场景</text>
        <text class="topbar-title serif">{{ currentLabel }}</text>
        <text class="action pressable" @tap="drawAnother">换一条</text>
      </view>

      <view class="result-wrap">
        <!-- 假生成动画 -->
        <view v-if="generating" class="loading">
          <view class="dot"></view>
          <view class="dot"></view>
          <view class="dot"></view>
          <text class="loading-text">正在为你挑一句…</text>
        </view>

        <!-- 暖话卡片 -->
        <view v-else-if="currentWord" class="card result-card anim-pop">
          <text class="scene-tag">{{ currentLabel }} · 今日暖话</text>
          <text class="warm-text serif">{{ currentWord.text }}</text>
          <view class="actions">
            <text class="act-btn pressable" @tap="goWrite">✎ 写成图文</text>
            <text class="act-btn ghost pressable" @tap="drawAnother">换一条</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import { isLoggedIn } from '../../store/user'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

// view: 'scenes' | 'result'
const view = ref('scenes')
const scenes = ref([])
const currentScene = ref(null)
const currentWord = ref(null)
const generating = ref(false)

const currentLabel = computed(() => {
  const s = scenes.value.find((x) => x.scene === currentScene.value)
  return s ? s.label : ''
})

async function loadScenes() {
  try {
    const list = await api.warmWords.scenes()
    scenes.value = list || []
  } catch {
    /* 拦截器已提示 */
  }
}

async function onPickScene(s) {
  if (s.count === 0) {
    return uni.showToast({ title: '该场景暂无暖话', icon: 'none' })
  }
  currentScene.value = s.scene
  view.value = 'result'
  await drawAnother()
}

async function drawAnother() {
  if (!currentScene.value || generating.value) return
  generating.value = true
  currentWord.value = null
  // 短伪生成动画,给情绪一个缓冲(不阻塞请求,叠加显示)
  const animPromise = new Promise((r) => setTimeout(r, 800))
  try {
    const [res] = await Promise.all([api.warmWords.random(currentScene.value), animPromise])
    currentWord.value = res
  } catch {
    /* 拦截器已提示;429 超限等错误后留在结果视图但无内容,用户可返回重选 */
  } finally {
    generating.value = false
  }
}

function backToScenes() {
  view.value = 'scenes'
  currentWord.value = null
  generating.value = false
}

function goWrite() {
  if (!currentWord.value) return
  const text = '「' + currentWord.value.text + '」'
  uni.navigateTo({
    url: '/pages/write/index?prefill=' + encodeURIComponent(text)
  })
}

function goBack() {
  // 直接刷新 / URL 进入时栈里只有自己,navigateBack 会静默失败
  if (getCurrentPages().length > 1) {
    uni.navigateBack()
  } else {
    uni.switchTab({
      url: '/pages/mine/index',
      fail: () => uni.reLaunch({ url: '/pages/mine/index' })
    })
  }
}

onShow(() => {
  if (!isLoggedIn()) return uni.reLaunch({ url: '/pages/login/index' })
  loadScenes()
})
</script>

<style scoped>
.warm {
  min-height: 100vh;
  background: #fdfbf7;
  display: flex;
  flex-direction: column;
}
.status-bar {
  width: 100%;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 40rpx 12rpx;
}
.back {
  width: 130rpx;
  color: #c4a882;
  font-size: 30rpx;
}
.topbar-title {
  font-size: 32rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.action {
  width: 130rpx;
  text-align: right;
  font-size: 26rpx;
  color: #c4a882;
}
.action.placeholder {
  visibility: hidden;
}

/* 场景选择 */
.guide {
  padding: 56rpx 48rpx 32rpx;
  text-align: center;
}
.guide-text {
  font-size: 36rpx;
  color: #4a4a4a;
  line-height: 1.6;
}
.scene-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24rpx;
  padding: 16rpx 32rpx;
}
.scene-card {
  background: #ffffff;
  border-radius: 32rpx;
  padding: 44rpx 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8rpx 64rpx rgba(196, 168, 130, 0.15);
}
.scene-label {
  font-size: 34rpx;
  color: #4a4a4a;
  font-weight: 500;
}
.scene-count {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #b0b0b0;
}

/* 结果视图 */
.result-wrap {
  flex: 1;
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.loading .dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #c4a882;
  margin: 6rpx 0;
  opacity: 0.4;
  animation: pulse 1s ease-in-out infinite;
}
.loading .dot:nth-child(1) { animation-delay: 0s; }
.loading .dot:nth-child(2) { animation-delay: 0.15s; }
.loading .dot:nth-child(3) { animation-delay: 0.3s; }
.loading-text {
  margin-top: 24rpx;
  font-size: 26rpx;
  color: #b0b0b0;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%      { opacity: 1;   transform: scale(1.2); }
}

.result-card {
  width: 100%;
  padding: 56rpx 44rpx;
  display: flex;
  flex-direction: column;
}
.scene-tag {
  font-size: 22rpx;
  color: #c4a882;
  letter-spacing: 2rpx;
}
.warm-text {
  margin-top: 32rpx;
  font-size: 36rpx;
  line-height: 1.8;
  color: #4a4a4a;
  text-align: left;
}
.actions {
  margin-top: 48rpx;
  display: flex;
  gap: 20rpx;
}
.act-btn {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  border-radius: 32rpx;
  background: #c4a882;
  color: #fff;
  font-size: 28rpx;
}
.act-btn.ghost {
  background: #f3eee5;
  color: #88a07a;
}
</style>
