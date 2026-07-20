<template>
  <view class="hole">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">树洞</text>
      <text class="header-sub">这里没有列表,只有你与暗号之间的秘密。</text>
    </view>

    <!-- 解锁前 -->
    <view class="card unlock-card" v-if="!revealed">
      <view class="lock-icon">✿</view>
      <text class="unlock-tip">输入 6 位数字暗号,打开那一篇</text>

      <view class="code-row">
        <input
          class="code-input"
          v-model="code"
          type="number"
          :maxlength="6"
          placeholder="······"
          placeholder-class="ph"
          confirm-type="done"
          @confirm="onUnlock"
        />
      </view>

      <button class="unlock-btn" :loading="loading" :disabled="code.length !== 6" @tap="onUnlock">
        打开树洞
      </button>
    </view>

    <!-- 解锁后 -->
    <view class="card revealed-card" v-else>
      <text class="revealed-title" v-if="revealed.title">{{ revealed.title }}</text>
      <text class="revealed-from">— 一封来自远方的悄悄话 —</text>
      <mp-html class="rich" :content="revealed.content_html" selectable :domain="serverOrigin" />
      <view class="revealed-meta">
        <text>已被阅读 {{ revealed.view_count }} 次</text>
        <text class="again" @tap="reset">解锁另一篇</text>
      </view>
    </view>

    <TabBar />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onMounted } from 'vue'
import { api } from '../../api'
import { SERVER_ORIGIN } from '../../config'
import TabBar from '../../components/TabBar.vue'

const serverOrigin = SERVER_ORIGIN
const statusBarHeight = ref(0)
const code = ref('')
const loading = ref(false)
const revealed = ref(null)

onMounted(() => {
  const sys = uni.getSystemInfoSync()
  statusBarHeight.value = sys.statusBarHeight || 0
})

async function onUnlock() {
  if (code.value.length !== 6) return
  loading.value = true
  try {
    revealed.value = await api.treeholes.unlock(code.value)
    uni.vibrateShort && uni.vibrateShort({ type: 'light' })
  } catch (err) {
    // request 拦截器已 toast(暗号无效 / 已锁定)
  } finally {
    loading.value = false
  }
}

function reset() {
  revealed.value = null
  code.value = ''
}
</script>

<style scoped>
.hole {
  min-height: 100vh;
  background: linear-gradient(170deg, #f6f1ea 0%, #fdfbf7 60%, #f3eee8 100%);
  padding-bottom: 160rpx;
}
.status-bar {
  width: 100%;
}
.header {
  padding: 16rpx 48rpx 36rpx;
}
.header-title {
  font-size: 56rpx;
  font-weight: 700;
  color: #88a07a;
  letter-spacing: 4rpx;
}
.header-sub {
  display: block;
  color: #b8b8b8;
  font-size: 24rpx;
  margin-top: 8rpx;
  line-height: 1.6;
}
.unlock-card {
  margin: 40rpx 48rpx;
  padding: 64rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.lock-icon {
  font-size: 72rpx;
  color: #88a07a;
  margin-bottom: 24rpx;
}
.unlock-tip {
  color: #8d8d8d;
  font-size: 26rpx;
  margin-bottom: 48rpx;
}
.code-row {
  width: 100%;
}
.code-input {
  width: 100%;
  text-align: center;
  font-size: 80rpx;
  letter-spacing: 48rpx;
  color: #4a4a4a;
  padding: 24rpx 0;
  border-bottom: 2rpx solid rgba(136, 160, 122, 0.4);
  margin-bottom: 48rpx;
}
.ph {
  color: #ddd6cc;
  letter-spacing: 48rpx;
}
.unlock-btn {
  width: 80%;
  height: 92rpx;
  line-height: 92rpx;
  background: #88a07a;
  color: #fff;
  border-radius: 46rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
}
.unlock-btn[disabled] {
  background: #c8d2bf;
  color: #fff;
}
.unlock-btn::after {
  border: none;
}
.revealed-card {
  margin: 20rpx 48rpx;
  padding: 48rpx;
}
.revealed-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #4a4a4a;
  display: block;
  margin-bottom: 16rpx;
}
.revealed-from {
  display: block;
  color: #b0b0b0;
  font-size: 24rpx;
  margin-bottom: 28rpx;
}
.rich {
  color: #4a4a4a;
  font-size: 30rpx;
  line-height: 1.9;
}
.revealed-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
  padding-top: 28rpx;
  border-top: 1rpx dashed rgba(196, 168, 130, 0.3);
  font-size: 24rpx;
  color: #b0b0b0;
}
.again {
  color: #88a07a;
}
</style>
