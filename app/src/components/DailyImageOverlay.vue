<template>
  <view v-if="visible" class="daily-overlay" @tap="close">
    <!-- 暖色渐变背景 -->
    <view class="daily-bg"></view>

    <!-- 内容卡片:点卡片内不关闭,只在点空白处关闭 -->
    <view class="daily-card" @tap.stop>
      <view class="daily-image-wrap" @tap="preview">
        <image
          :src="fullImageUrl"
          class="daily-image"
          mode="aspectFit"
          @longpress="preview"
        />
      </view>
      <text v-if="image?.title" class="daily-title serif">{{ image.title }}</text>
      <text v-if="image?.description" class="daily-desc">{{ image.description }}</text>
      <text v-if="image?.publish_date" class="daily-date">{{ image.publish_date }}</text>
    </view>

    <!-- 右上角关闭按钮:top 用 statusBarHeight 精确避开系统状态栏(env 在 App/小程序里不可靠) -->
    <view class="daily-close" :style="{ top: statusBarHeight + 24 + 'rpx' }" @tap.stop="close">
      <text class="daily-close-icon">×</text>
    </view>

    <!-- 底部轻提示 -->
    <text class="daily-hint">轻点图片可查看大图,点空白处关闭 ✦</text>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { resourceUrl } from '../config'

const props = defineProps({
  visible: { type: Boolean, default: false },
  image: { type: Object, default: null }
})
const emit = defineEmits(['close'])

// 系统状态栏高度(px):关闭按钮 top 用它精确避让
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

const fullImageUrl = computed(() => {
  if (!props.image?.image_url) return ''
  return resourceUrl(props.image.image_url)
})

function close() {
  emit('close')
}

function preview() {
  if (!fullImageUrl.value) return
  uni.previewImage({
    current: fullImageUrl.value,
    urls: [fullImageUrl.value]
  })
}
</script>

<style scoped>
/* 覆盖层:盖过 TabBar(999)与 FAB(998) */
.daily-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64rpx 48rpx;
  box-sizing: border-box;
  animation: dailyFadeIn 0.35s ease-out both;
}
.daily-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    ellipse 80% 60% at 50% 50%,
    rgba(196, 168, 130, 0.18) 0%,
    rgba(253, 251, 247, 0.96) 60%,
    #fdfbf7 100%
  );
  z-index: -1;
}
@keyframes dailyFadeIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.daily-card {
  width: 100%;
  max-width: 640rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: dailyCardIn 0.5s 0.1s ease-out both;
}
@keyframes dailyCardIn {
  from {
    opacity: 0;
    transform: translateY(40rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.daily-image-wrap {
  width: 100%;
  max-width: 640rpx;
  /* 固定高度容器:限制卡片总高,避免长图把卡片撑出屏幕、
     flex 居中时顶部钻到状态栏后面被遮挡。
     aspectFit 保持原图比例不裁剪,留白处用暖色兜底融入整体氛围。 */
  height: 66vh;
  border-radius: 32rpx;
  overflow: hidden;
  background: rgba(196, 168, 130, 0.1);
  box-shadow: 0 16rpx 64rpx rgba(196, 168, 130, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}
.daily-image {
  width: 100%;
  height: 100%;
  display: block;
}

.daily-title {
  margin-top: 36rpx;
  font-size: 44rpx;
  font-weight: 600;
  color: #4a4a4a;
  text-align: center;
  letter-spacing: 2rpx;
}
.daily-desc {
  margin-top: 18rpx;
  font-size: 28rpx;
  color: #8d8d8d;
  line-height: 1.7;
  text-align: center;
  padding: 0 24rpx;
}
.daily-date {
  margin-top: 24rpx;
  font-size: 24rpx;
  color: #c4a882;
  letter-spacing: 4rpx;
}

.daily-close {
  position: absolute;
  right: 48rpx;
  width: 72rpx;
  height: 72rpx;
  border-radius: 36rpx;
  background: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.daily-close-icon {
  font-size: 56rpx;
  color: #8d8d8d;
}

.daily-hint {
  position: absolute;
  bottom: calc(48rpx + env(safe-area-inset-bottom, 0));
  left: 0;
  right: 0;
  text-align: center;
  font-size: 24rpx;
  color: #b8b8b8;
}
</style>
