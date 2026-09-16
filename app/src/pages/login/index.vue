<template>
  <view class="login-page" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="brand anim-rise">
      <view class="brand-title-row">
        <text class="brand-title serif">隐</text>
        <view class="brand-dot"></view>
        <text class="brand-title serif">语</text>
      </view>
      <text class="brand-sub">温暖治愈的精神角落</text>
    </view>

    <view class="card form-card anim-rise delay-2">
      <view class="tabs">
        <text :class="['tab', { active: mode === 'login' }]" @tap="mode = 'login'">登录</text>
        <text :class="['tab', { active: mode === 'register' }]" @tap="mode = 'register'">注册</text>
      </view>

      <!-- 登录 -->
      <view v-if="mode === 'login'" class="form">
        <view class="field">
          <text class="label">账号</text>
          <input v-model="form.username" class="input" placeholder="用户名" />
        </view>
        <view class="field">
          <text class="label">密码</text>
          <input v-model="form.password" class="input" password placeholder="密码" />
        </view>
        <button class="submit" :loading="loading" @tap="onLogin">登录</button>
      </view>

      <!-- 注册 -->
      <view v-else class="form">
        <view class="field">
          <text class="label">用户名</text>
          <input v-model="reg.username" class="input" placeholder="字母/数字,3 位以上" />
        </view>
        <view class="field">
          <text class="label">密码</text>
          <input v-model="reg.password" class="input" password placeholder="至少 6 位" />
        </view>
        <view class="field">
          <text class="label">邀请码</text>
          <input v-model="reg.invite_code" class="input" placeholder="请向邀请人索取" />
        </view>
        <view class="field">
          <text class="label">昵称(可选)</text>
          <input v-model="reg.nickname" class="input" placeholder="留空则用用户名" />
        </view>
        <button class="submit" :loading="loading" @tap="onRegister">注册</button>
      </view>
    </view>

    <text class="footer-tip anim-fade delay-4">治愈,从一句悄悄话开始。</text>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { login } from '../../store/user'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const mode = ref('login')
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const reg = reactive({ username: '', password: '', invite_code: '', nickname: '' })

async function onLogin() {
  if (!form.username || !form.password) {
    return uni.showToast({ title: '请填写账号密码', icon: 'none' })
  }
  loading.value = true
  try {
    await login(form.username, form.password)
    uni.showToast({ title: '欢迎回来', icon: 'success' })
    setTimeout(() => uni.switchTab({
      url: '/pages/index/index',
      fail: () => uni.reLaunch({ url: '/pages/index/index' })
    }), 300)
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  if (!reg.username || !reg.password || !reg.invite_code) {
    return uni.showToast({ title: '请填写完整', icon: 'none' })
  }
  loading.value = true
  try {
    await api.auth.register({
      username: reg.username,
      password: reg.password,
      invite_code: reg.invite_code,
      nickname: reg.nickname || undefined
    })
    uni.showToast({ title: '注册成功,请登录', icon: 'success' })
    form.username = reg.username
    form.password = reg.password
    mode.value = 'login'
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  /* 渐变取自系统色相:暮粉 tint → 暖白 → 苔绿 tint(原 #fdeef4/#eafaf3 是孤立色相,已收敛) */
  min-height: 100vh;
  background: linear-gradient(
    160deg,
    rgba(232, 196, 196, 0.32) 0%,
    var(--warm-white) 45%,
    rgba(136, 160, 122, 0.2) 100%
  );
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 60rpx;
}
.status-bar {
  width: 100%;
}
.brand {
  margin-top: 120rpx;
  text-align: center;
}
.brand-title-row {
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-title {
  font-size: 88rpx;
  font-weight: 700;
  color: var(--wood-bark);
}
.brand-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--wood-bark);
  margin: 0 16rpx;
  animation: yinyu-breath 3.2s var(--ease-soft) infinite;
}
.brand-sub {
  display: block;
  margin-top: 16rpx;
  color: var(--text-sec);
  font-size: 26rpx;
}
.form-card {
  width: 100%;
  margin-top: 80rpx;
  padding: 48rpx 40rpx;
}
.tabs {
  display: flex;
  margin-bottom: 40rpx;
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.2);
}
.tab {
  flex: 1;
  text-align: center;
  padding-bottom: 20rpx;
  font-size: 30rpx;
  color: var(--text-sec);
}
.tab.active {
  color: var(--wood-bark);
  font-weight: 600;
  position: relative;
}
.tab.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -1rpx;
  transform: translateX(-50%);
  width: 60rpx;
  height: 4rpx;
  background: var(--wood-bark);
  border-radius: 2rpx;
}
.field {
  margin-bottom: 28rpx;
}
.label {
  display: block;
  font-size: 24rpx;
  color: var(--text-sec);
  margin-bottom: 12rpx;
}
.input {
  width: 100%;
  height: 88rpx;
  background: var(--warm-white);
  border: 1rpx solid rgba(196, 168, 130, 0.25);
  border-radius: 24rpx;
  padding: 0 28rpx;
  font-size: 30rpx;
  color: var(--text-main);
  box-sizing: border-box;
}
.submit {
  margin-top: 16rpx;
  width: 100%;
  height: 92rpx;
  line-height: 92rpx;
  background: var(--wood-bark);
  color: #fff;
  border-radius: 46rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  /* 双字按钮的字距呼吸(替代旧的全角空格排印);text-indent 抵消尾字符的 trailing space */
  letter-spacing: 16rpx;
  text-indent: 16rpx;
}
.submit::after {
  border: none;
}
.footer-tip {
  margin-top: 60rpx;
  color: var(--bark-ink);
  font-size: 24rpx;
  opacity: 0.8;
}
</style>
