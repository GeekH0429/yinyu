<template>
  <view v-if="playing" class="fly-overlay" @tap.stop>
    <!-- 光迹航线:SVG 绘出,纸飞机寄出的"航线" -->
    <view class="fly-trail-wrap">
      <svg class="fly-trail" viewBox="0 0 750 1400" preserveAspectRatio="xMidYMid slice">
        <path
          class="fly-trail-path"
          pathLength="100"
          d="M 375 1148 C 470 880 600 520 780 40"
        />
      </svg>
    </view>

    <!-- 纸飞机本体(复用树洞页 FAB 同款 SVG) -->
    <view class="fly-plane" v-html="planeSvg"></view>

    <!-- 起飞点微光粒子 -->
    <view class="fly-particles">
      <view v-for="i in 6" :key="i" class="fly-dot" :class="'fly-dot-' + i"></view>
    </view>

    <!-- 意境文案 -->
    <text class="fly-caption serif">把心里的话,寄向远方 ✦</text>
  </view>
</template>

<script setup>
import { watch, onUnmounted } from 'vue'

const props = defineProps({
  playing: { type: Boolean, default: false }
})
const emit = defineEmits(['done'])

// 复用树洞页 FAB 同款纸飞机 SVG(currentColor),保证视觉统一
const planeSvg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="display:block"><path d="M1007.9 7.2C1001.8 3 994.8.8 987.2.8c-6.6 0-12.6 1.7-18.3 5.2L18.9 554.1C5.9 561.4-.2 572.6.6 587.9c1 15.7 8.7 26.2 22.8 31.5l216.4 88.8c5.6 2.3 12 1.2 16.5-2.7L859.2 184.6 380.3 771.6c-9.3 11.4-14.4 25.7-14.4 40.5v176.3c0 7.7 2.3 14.6 6.7 20.9 4.3 6.4 10.2 10.7 17.4 13.4 3.6 1.5 7.8 2.3 12.7 2.3 11.8 0 21.1-4.2 28-13.1l115.5-141.3c8.9-10.9 23.8-14.6 36.8-9.3l236.7 96.8c4.9 1.9 9.5 2.9 13.7 2.9 6.4 0 12.4-1.7 17.7-4.9 8.9-5.2 14.3-13.1 16.4-23.2L1023.7 49.4c3.4-17.1-1.3-31.5-15.8-42.2z" fill="currentColor"/></svg>`

// 动画总时长约 2.05s,留余量到 2.1s 通知父组件收尾
const FLY_MS = 2100
let timer = null
watch(
  () => props.playing,
  (v) => {
    clearTimeout(timer)
    if (v) timer = setTimeout(() => emit('done'), FLY_MS)
  }
)
onUnmounted(() => clearTimeout(timer))
</script>

<style scoped>
/* 覆盖层:盖过发布弹窗(1000)与 TabBar(999) */
.fly-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  overflow: hidden;
  background: radial-gradient(
    ellipse 60% 38% at 50% 82%,
    rgba(123, 140, 196, 0.14) 0%,
    #0d0d12 72%
  );
  animation: overlayIn 0.25s ease-out both, overlayOut 0.35s 1.7s ease-out both;
}
@keyframes overlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes overlayOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* ---- 光迹航线 ---- */
.fly-trail-wrap {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.fly-trail {
  width: 100%;
  height: 100%;
}
.fly-trail-path {
  fill: none;
  stroke: rgba(123, 140, 196, 0.55);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  animation: drawTrail 1.2s 0.25s ease-out both,
             fadeTrail 0.4s 1.3s ease-out both;
}
@keyframes drawTrail {
  to { stroke-dashoffset: 0; }
}
@keyframes fadeTrail {
  to { opacity: 0; }
}

/* ---- 纸飞机 ---- */
.fly-plane {
  position: absolute;
  left: 50%;
  bottom: 18%;
  width: 96rpx;
  height: 96rpx;
  margin-left: -48rpx;
  color: #e0e0e0;
  font-size: 0;
  line-height: 0;
  animation: flyAway 1.5s 0.15s cubic-bezier(0.45, 0.05, 0.7, 1) both;
  will-change: transform, opacity;
}
.fly-plane :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}
/* 沿右上弧线飞远:位移递增、缩小、随切线偏转、末段淡出 */
@keyframes flyAway {
  0% {
    transform: translate(0, 60rpx) scale(0.2) rotate(-18deg);
    opacity: 0;
  }
  14% {
    transform: translate(0, 0) scale(1.08) rotate(-18deg);
    opacity: 1;
  }
  20% {
    transform: translate(10rpx, -30rpx) scale(1) rotate(-20deg);
    opacity: 1;
  }
  40% {
    transform: translate(95rpx, -250rpx) scale(0.82) rotate(-26deg);
    opacity: 1;
  }
  64% {
    transform: translate(225rpx, -540rpx) scale(0.58) rotate(-32deg);
    opacity: 0.92;
  }
  84% {
    transform: translate(360rpx, -830rpx) scale(0.34) rotate(-37deg);
    opacity: 0.4;
  }
  100% {
    transform: translate(445rpx, -1040rpx) scale(0.14) rotate(-41deg);
    opacity: 0;
  }
}

/* ---- 起飞点光点粒子 ---- */
.fly-particles {
  position: absolute;
  left: 50%;
  bottom: 18%;
  width: 0;
  height: 0;
}
.fly-dot {
  position: absolute;
  left: 0;
  top: 0;
  width: 8rpx;
  height: 8rpx;
  margin-left: -4rpx;
  margin-top: -4rpx;
  border-radius: 50%;
  background: #c0c8e0;
  opacity: 0;
}
.fly-dot-1 { animation: dot1 1.3s 0.3s ease-out both; }
.fly-dot-2 { animation: dot2 1.5s 0.35s ease-out both; background: #e8c4c4; }
.fly-dot-3 { animation: dot3 1.4s 0.28s ease-out both; }
.fly-dot-4 { animation: dot4 1.6s 0.4s ease-out both; background: #e8c4c4; }
.fly-dot-5 { animation: dot5 1.3s 0.32s ease-out both; }
.fly-dot-6 { animation: dot6 1.5s 0.38s ease-out both; }
@keyframes dot1 {
  0% { transform: translate(0,0) scale(.4); opacity: 0; }
  25% { opacity: .9; }
  100% { transform: translate(-44rpx, -130rpx) scale(1); opacity: 0; }
}
@keyframes dot2 {
  0% { transform: translate(0,0) scale(.4); opacity: 0; }
  25% { opacity: .9; }
  100% { transform: translate(34rpx, -150rpx) scale(1); opacity: 0; }
}
@keyframes dot3 {
  0% { transform: translate(0,0) scale(.5); opacity: 0; }
  30% { opacity: .8; }
  100% { transform: translate(-22rpx, -190rpx) scale(.8); opacity: 0; }
}
@keyframes dot4 {
  0% { transform: translate(0,0) scale(.4); opacity: 0; }
  25% { opacity: .9; }
  100% { transform: translate(54rpx, -110rpx) scale(1); opacity: 0; }
}
@keyframes dot5 {
  0% { transform: translate(0,0) scale(.5); opacity: 0; }
  30% { opacity: .75; }
  100% { transform: translate(-58rpx, -95rpx) scale(.9); opacity: 0; }
}
@keyframes dot6 {
  0% { transform: translate(0,0) scale(.4); opacity: 0; }
  25% { opacity: .85; }
  100% { transform: translate(16rpx, -205rpx) scale(.7); opacity: 0; }
}

/* ---- 意境文案 ---- */
.fly-caption {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 8%;
  text-align: center;
  color: #7b8cc4;
  font-size: 30rpx;
  letter-spacing: 4rpx;
  opacity: 0;
  animation: capIn 0.5s 0.25s ease-out both,
             capOut 0.4s 1.3s ease-out both;
}
@keyframes capIn {
  from { opacity: 0; transform: translateY(16rpx); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes capOut {
  to { opacity: 0; }
}
</style>
