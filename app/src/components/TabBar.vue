<template>
  <view class="tab-bar">
    <view
      v-for="(item, i) in tabs"
      :key="i"
      :class="['tab-item', { active: current === item.pagePath }]"
      @tap="onTap(item.pagePath)"
    >
      <view class="svg-icon" v-html="item.icon"></view>
      <text class="tab-text">{{ item.text }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const homeSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><path d="M49.6 515.3a34.9 34.9 0 0 1-23.6-60.6L488.4 29.6a35 35 0 0 1 47.3.1L995.4 454.7a34.9 34.9 0 1 1-47.4 51.3L511.9 102.8 73.2 506.1a34.8 34.8 0 0 1-23.6 9.2z" fill="currentColor"/><path d="M827.3 1001.8H196.7c-44.9 0-81.5-36.5-81.5-81.5V541.9a34.9 34.9 0 1 1 69.8 0v378.5a11.6 11.6 0 0 0 11.6 11.6h630.6a11.6 11.6 0 0 0 11.6-11.6V541.9a34.9 34.9 0 1 1 69.8 0v378.5c0 44.9-36.5 81.4-81.5 81.4z" fill="currentColor"/></svg>`
const planeSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><path d="M1007.9 7.2C1001.8 3 994.8.8 987.2.8c-6.6 0-12.6 1.7-18.3 5.2L18.9 554.1C5.9 561.4-.2 572.6.6 587.9c1 15.7 8.7 26.2 22.8 31.5l216.4 88.8c5.6 2.3 12 1.2 16.5-2.7L859.2 184.6 380.3 771.6c-9.3 11.4-14.4 25.7-14.4 40.5v176.3c0 7.7 2.3 14.6 6.7 20.9 4.3 6.4 10.2 10.7 17.4 13.4 3.6 1.5 7.8 2.3 12.7 2.3 11.8 0 21.1-4.2 28-13.1l115.5-141.3c8.9-10.9 23.8-14.6 36.8-9.3l236.7 96.8c4.9 1.9 9.5 2.9 13.7 2.9 6.4 0 12.4-1.7 17.7-4.9 8.9-5.2 14.3-13.1 16.4-23.2L1023.7 49.4c3.4-17.1-1.3-31.5-15.8-42.2z" fill="currentColor"/></svg>`
const mineSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><path d="M512 499.2c134.4 0 243.2-108.8 243.2-243.2S646.4 12.8 512 12.8 268.8 121.6 268.8 256s108.8 243.2 243.2 243.2z m0 64c-161.6 0-483.2 81.6-483.2 243.2v102.4c0 35.2 28.8 64 64 64h838.4c35.2 0 64-28.8 64-64v-102.4c0-161.6-321.6-243.2-483.2-243.2z" fill="currentColor"/></svg>`

const tabs = [
  { pagePath: 'pages/index/index', text: '阅读', icon: homeSvg },
  { pagePath: 'pages/treehole/index', text: '树洞', icon: planeSvg },
  { pagePath: 'pages/mine/index', text: '我的', icon: mineSvg }
]

const current = ref('pages/index/index')

function syncCurrent() {
  try {
    const pages = getCurrentPages()
    const top = pages[pages.length - 1]
    if (top && top.route) current.value = top.route.replace(/^\//, '')
  } catch (e) {
    /* ignore */
  }
}

onShow(syncCurrent)

function onTap(pagePath) {
  if (current.value === pagePath) return
  uni.reLaunch({ url: '/' + pagePath })
}
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 110rpx;
  display: flex;
  background: #fdfbf7;
  border-top: 1rpx solid rgba(196, 168, 130, 0.15);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 999;
  box-shadow: 0 -4rpx 20rpx rgba(196, 168, 130, 0.08);
}
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.svg-icon {
  width: 44rpx;
  height: 44rpx;
  color: #bdb5a8;
  margin-bottom: 4rpx;
}
.svg-icon :deep(svg) {
  width: 44rpx;
  height: 44rpx;
  display: block;
}
.tab-text {
  font-size: 22rpx;
  color: #8d8d8d;
}
.tab-item.active .svg-icon {
  color: #c4a882;
}
.tab-item.active .tab-text {
  color: #c4a882;
  font-weight: 600;
}
</style>
