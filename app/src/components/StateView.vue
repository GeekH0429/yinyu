<template>
  <view class="state-view">
    <text class="sv-icon">{{ icon }}</text>
    <text class="sv-text">{{ text }}</text>
    <text v-if="retry" class="sv-retry" @tap="emit('retry')">{{ retryText }}</text>
    <slot />
  </view>
</template>

<script setup>
/**
 * 空 / 错误 状态占位。
 *   <StateView type="empty" text="这里还很安静" />
 *   <StateView type="error" text="没能连上" retry @retry="reload" />
 * 底部 <slot> 可放引导按钮等额外内容。
 */
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'empty' }, // 'empty' | 'error'
  text: { type: String, default: '' },
  retry: { type: Boolean, default: false },
  retryText: { type: String, default: '点此重试' }
})
const emit = defineEmits(['retry'])

const icon = computed(() => (props.type === 'error' ? '🍂' : '🌿'))
</script>

<style scoped>
.state-view {
  padding: 72rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sv-icon {
  font-size: 72rpx;
  margin-bottom: 20rpx;
  opacity: 0.85;
}
.sv-text {
  font-size: 26rpx;
  color: #b8b8b8;
  text-align: center;
  line-height: 1.6;
}
.sv-retry {
  margin-top: 28rpx;
  padding: 14rpx 44rpx;
  background: rgba(196, 168, 130, 0.14);
  color: #c4a882;
  border-radius: 32rpx;
  font-size: 26rpx;
}
.sv-retry:active {
  opacity: 0.7;
}
</style>
