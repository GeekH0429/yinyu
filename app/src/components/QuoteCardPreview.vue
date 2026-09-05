<template>
  <view class="qc-mask" v-if="visible" @tap="close">
    <view class="qc-pop" @tap.stop>
      <text class="qc-title serif">卡片已生成 ✦</text>

      <!-- 点图片全屏查看;H5 长按亦可保存 -->
      <image class="qc-img" :src="src" mode="widthFix" @tap="previewFull" />

      <view class="qc-actions">
        <view class="qc-btn qc-share" @tap="onShare">
          <text class="qc-btn-text">转发给朋友</text>
        </view>
        <view class="qc-btn qc-save" :class="{ done: saved }" @tap="onSave">
          <text class="qc-btn-text">{{ saved ? '已保存 ✓' : '保存' }}</text>
        </view>
      </view>
      <text class="qc-hint">点图片可全屏查看</text>
    </view>
  </view>
</template>

<script setup>
/**
 * 卡片预览弹层:canvas 生成完毕后展示成品,提供「转发 / 保存」。
 * 转发 = utils/quoteCard.js 的 shareQuoteCard(App 系统分享面板 / H5 Web Share);
 * 保存 = saveQuoteCard(App 相册 / H5 下载)。
 */
import { ref, watch } from 'vue'
import { saveQuoteCard, shareQuoteCard } from '../utils/quoteCard'

const props = defineProps({
  visible: { type: Boolean, default: false },
  src: { type: String, default: '' }
})
const emit = defineEmits(['close'])

const saved = ref(false)
// 每次打开新卡片复位保存态
watch(
  () => props.visible,
  (v) => {
    if (v) saved.value = false
  }
)

function close() {
  emit('close')
}

function previewFull() {
  if (!props.src) return
  uni.previewImage({ urls: [props.src] })
}

function onShare() {
  if (!props.src) return
  shareQuoteCard(props.src)
}

function onSave() {
  if (!props.src || saved.value) return
  saved.value = true
  saveQuoteCard(props.src)
}
</script>

<style scoped>
.qc-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 26, 0.6);
  z-index: 1003;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}
.qc-pop {
  width: 100%;
  background: #fffdf8;
  border-radius: 32rpx;
  padding: 36rpx 36rpx 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: qcIn 0.3s var(--ease-soft, ease-out) both;
}
@keyframes qcIn {
  from { opacity: 0; transform: translateY(40rpx) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.qc-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #c4a882;
  margin-bottom: 24rpx;
}
.qc-img {
  width: 560rpx;
  border-radius: 16rpx;
  box-shadow: 0 12rpx 48rpx rgba(0, 0, 0, 0.18);
}
.qc-actions {
  margin-top: 32rpx;
  display: flex;
  gap: 24rpx;
  width: 100%;
}
.qc-btn {
  flex: 1;
  padding: 22rpx 0;
  border-radius: 44rpx;
  text-align: center;
}
.qc-btn:active {
  transform: scale(0.96);
}
.qc-share {
  background: #c4a882;
  box-shadow: 0 6rpx 24rpx rgba(196, 168, 130, 0.4);
}
.qc-share .qc-btn-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 600;
}
.qc-save {
  background: rgba(196, 168, 130, 0.14);
}
.qc-save.done {
  opacity: 0.6;
}
.qc-save .qc-btn-text {
  color: #c4a882;
  font-size: 28rpx;
}
.qc-hint {
  margin-top: 20rpx;
  font-size: 22rpx;
  color: #b8b8b8;
}
</style>
