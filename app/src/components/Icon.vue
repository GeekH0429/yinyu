<template>
  <view class="yo-icon" :style="'width:' + size + 'rpx;height:' + size + 'rpx;'" v-html="svg"></view>
</template>

<script setup>
/**
 * 统一功能图标渲染器:utils/icons.js 的 SVG 字符串 → v-html(TabBar 同款模式,
 * H5/App 均已验证)。SVG 用 currentColor,颜色跟随元素的 color 继承。
 */
import { computed } from 'vue'
import { ICONS } from '../utils/icons'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 36 } // rpx
})

const svg = computed(() => ICONS[props.name] || '')
</script>

<style scoped>
.yo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.yo-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
