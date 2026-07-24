<template>
  <view v-if="playing" class="fly-overlay" @tap.stop>
    <!-- 光迹航线 + 纸飞机:整个 SVG 用 v-html 注入。
         飞机用 SMIL <animateMotion> 沿真实贝塞尔 path 飞行 ——
         单一缓动函数跑完整段,无 CSS keyframes 那种"段间 timing-function 重启"的卡顿。 -->
    <view class="fly-trail-wrap" v-html="flySvg"></view>

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

// 飞机 path 数据(原 viewBox 0 0 1024 1024,机头朝右上方)
const planePathD = 'M1007.9 7.2C1001.8 3 994.8.8 987.2.8c-6.6 0-12.6 1.7-18.3 5.2L18.9 554.1C5.9 561.4-.2 572.6.6 587.9c1 15.7 8.7 26.2 22.8 31.5l216.4 88.8c5.6 2.3 12 1.2 16.5-2.7L859.2 184.6 380.3 771.6c-9.3 11.4-14.4 25.7-14.4 40.5v176.3c0 7.7 2.3 14.6 6.7 20.9 4.3 6.4 10.2 10.7 17.4 13.4 3.6 1.5 7.8 2.3 12.7 2.3 11.8 0 21.1-4.2 28-13.1l115.5-141.3c8.9-10.9 23.8-14.6 36.8-9.3l236.7 96.8c4.9 1.9 9.5 2.9 13.7 2.9 6.4 0 12.4-1.7 17.7-4.9 8.9-5.2 14.3-13.1 16.4-23.2L1023.7 49.4c3.4-17.1-1.3-31.5-15.8-42.2z'

// SVG 整体:光迹 + 飞机(沿 path 飞行)。设计要点(都是踩过的坑,改时注意):
// 1. <animateMotion> 让飞机沿真实贝塞尔 path 移动 —— 单一缓动跑整段,
//    不会有 CSS keyframes "每段 timing-function 重启" 造成的卡顿。
// 2. 外层 <g class="fly-plane-group"> 的 transform 由 animateMotion 接管(translate + rotate auto)。
// 3. **嵌套顺序极其重要** —— 必须 scale 在外、translate 在内:
//      <g class="fly-plane-scale">              ← 外:CSS scale
//        <g transform="rotate(45) translate(-512 -512)">  ← 内:SVG attribute
//          <path />
//    SVG transform 从内向外复合:先 translate 把中心 (512,512) 移到 (0,0),
//    再 rotate(45) 把机头从朝右上(-45°)扳到正右(0°),
//    最后外层 CSS scale 以 (0,0) 为不动点缩小 —— 飞机中心保持在 (0,0),
//    animateMotion 才能把 (0,0) 准确对齐到 path 当前点。
//    (反过来 scale 在内的话,scale 先把中心缩成 (61,61),translate(-512,-512) 再推到 (-451,-451),
//     飞机就完全脱离光迹了 —— 上次飞机乱飞就是这个原因)
// 4. rotate(45) 预校正机头朝向:飞机原 SVG 机头朝右上方约 -45°,rotate(45) 让机头朝正右(0°),
//    这样 animateMotion 的 rotate="auto" 才能让机头严格沿切线方向(否则会偏上 45°,像侧飞)。
// 5. <path class="fly-plane-icon"> 用 CSS animation 控制 opacity 渐显渐隐。
// 6. 光迹 stroke 加粗 + drop-shadow 发光 —— App webview 抗锯齿弱,原 stroke-width:2.5 在手机上几乎看不见。
// 注:path 终点 (780, 40) 在 viewBox 750×1400 中略微超出右边(780>750),
//     配合 preserveAspectRatio="xMidYMid slice" 飞机会"飞出屏幕"消失,符合预期。
const flySvg = `
<svg class="fly-trail" viewBox="0 0 750 1400" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <path id="flyPath" d="M 375 1148 C 800 1100 700 350 780 40" />
  </defs>
  <path class="fly-trail-path" pathLength="100" d="M 375 1148 C 800 1100 700 350 780 40" />
  <g class="fly-plane-group">
    <g class="fly-plane-scale">
      <g transform="rotate(45) translate(-512 -512)">
        <path class="fly-plane-icon" d="${planePathD}" />
      </g>
    </g>
    <animateMotion dur="1.5s" begin="0.15s" fill="freeze" rotate="auto"
                   calcMode="spline" keyTimes="0;1" keyPoints="0;1"
                   keySplines="0 0 0.58 1">
      <mpath href="#flyPath" />
    </animateMotion>
  </g>
</svg>
`.trim()

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

/* ---- SVG 容器(SVG 通过 v-html 注入,内部元素需 :deep 匹配 scoped 样式) ---- */
.fly-trail-wrap {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.fly-trail-wrap :deep(.fly-trail) {
  width: 100%;
  height: 100%;
  display: block;
}
/* 光迹:加粗 + drop-shadow 发光。
   原值 stroke-width:2.5 + rgba alpha:0.55 在手机 webview 上几乎看不见 ——
   手机 webview 的抗锯齿比桌面 Chrome 弱,细+半透明的线条会被吃掉。
   drawTrail 的 timing 与飞机 animateMotion 完全对齐(都是 1.5s 0.15s ease-out),
   缓动曲线也一致(SMIL keySplines="0 0 0.58 1" 等价于 CSS ease-out),
   这样飞机始终贴在光迹"绘制前端",视觉上像飞机边飞边画出航线。 */
.fly-trail-wrap :deep(.fly-trail-path) {
  fill: none;
  stroke: rgba(180, 200, 255, 0.9);
  stroke-width: 5;
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  filter: drop-shadow(0 0 4px rgba(140, 165, 220, 0.7));
  animation: drawTrail 1.5s 0.1s ease-out both,
             fadeTrail 0.4s 1.7s ease-out both;
}
@keyframes drawTrail {
  to { stroke-dashoffset: 0; }
}
@keyframes fadeTrail {
  to { opacity: 0; }
}

/* ---- 飞机大小:CSS animation 控制 scale(位置和旋转由 SMIL animateMotion 接管) ---- */
.fly-trail-wrap :deep(.fly-plane-scale) {
  /* SVG 元素 CSS transform-origin 默认 (0,0),配合外层 translate(-512 -512)
     后飞机中心位于 (0,0),scale 以飞机中心为不动点 —— 正是要的效果。 */
  animation: planeScale 1.5s 0.15s cubic-bezier(0.34, 1.2, 0.5, 1) both;
}
@keyframes planeScale {
  0%   { transform: scale(0.001); }   /* 起飞前不可见 */
  16%  { transform: scale(0.12); }    /* 起飞弹出,略带 overshoot */
  28%  { transform: scale(0.1); }     /* 回到正常大小 (96 SVG 单位 ≈ 96rpx) */
  100% { transform: scale(0.014); }   /* 远去缩小到几乎不可见 */
}

/* ---- 飞机透明度渐显渐隐 ---- */
.fly-trail-wrap :deep(.fly-plane-icon) {
  fill: #e8e8ec;
  opacity: 0;
  animation: planeOpacity 1.5s 0.15s ease-out both;
}
@keyframes planeOpacity {
  0%   { opacity: 0; }
  16%  { opacity: 1; }
  75%  { opacity: 0.6; }
  100% { opacity: 0; }
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
