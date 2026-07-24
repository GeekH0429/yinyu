<template>
  <view class="login-page">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="brand anim-rise">
      <text class="brand-title serif">隐语</text>
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
        <button class="submit" :loading="loading" @tap="onLogin">登 录</button>
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
        <button class="submit" :loading="loading" @tap="onRegister">注 册</button>
      </view>
    </view>

    <text class="footer-tip anim-fade delay-4">治愈,从一句悄悄话开始。</text>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { login } from '../../store/user'
import { api } from '../../api'

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
    setTimeout(() => uni.reLaunch({ url: '/pages/index/index' }), 300)
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
  min-height: 100vh;
  background: linear-gradient(160deg, #fdeef4 0%, #fdfbf7 45%, #eafaf3 100%);
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
.brand-title {
  font-size: 88rpx;
  font-weight: 700;
  color: #c4a882;
  letter-spacing: 8rpx;
}
.brand-sub {
  display: block;
  margin-top: 16rpx;
  color: #8d8d8d;
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
  color: #8d8d8d;
}
.tab.active {
  color: #c4a882;
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
  background: #c4a882;
  border-radius: 2rpx;
}
.field {
  margin-bottom: 28rpx;
}
.label {
  display: block;
  font-size: 24rpx;
  color: #8d8d8d;
  margin-bottom: 12rpx;
}
.input {
  width: 100%;
  height: 88rpx;
  background: #fdfbf7;
  border: 1rpx solid rgba(196, 168, 130, 0.25);
  border-radius: 24rpx;
  padding: 0 28rpx;
  font-size: 30rpx;
  color: #4a4a4a;
  box-sizing: border-box;
}
.submit {
  margin-top: 16rpx;
  width: 100%;
  height: 92rpx;
  line-height: 92rpx;
  background: #c4a882;
  color: #fff;
  border-radius: 46rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
}
.submit::after {
  border: none;
}
.footer-tip {
  margin-top: 60rpx;
  color: #c4a882;
  font-size: 24rpx;
  opacity: 0.8;
}
</style>
