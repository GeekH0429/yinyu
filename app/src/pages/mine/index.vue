<template>
  <view class="mine" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <view class="header-action" @tap="goSettings">
        <view class="svg-icon" v-html="settingsSvg"></view>
      </view>
      <view class="header-action" @tap="goNotifications">
        <view class="svg-icon" v-html="mailSvg"></view>
        <view v-if="unreadCount > 0" class="badge-dot"></view>
      </view>
    </view>

    <!-- 资料 -->
    <view class="card profile-card anim-rise">
      <CachedImage
        v-if="user && user.avatar_url"
        class="avatar"
        :src="user.avatar_url"
        mode="aspectFill"
      />
      <view v-else class="avatar placeholder">
        {{ (user?.nickname || user?.username || '?').slice(0, 1) }}
      </view>
      <view class="profile-info">
        <text class="nickname">{{ user?.nickname || user?.username || '未登录' }}</text>
        <text class="bio">{{ user?.bio || '这个角落还很安静' }}</text>
        <text class="role" v-if="user?.role === 'admin'">管理员</text>
      </view>
    </view>

    <!-- 每日一图·回忆入口 -->
    <view class="card entry-card pressable anim-rise delay-1" @tap="goDailyHistory">
      <view class="entry-left">
        <text class="entry-title">每日一图 · 回忆</text>
        <text class="entry-sub">看看过去的每一天</text>
      </view>
      <text class="entry-arrow">›</text>
    </view>

    <!-- 我的作品入口(图文与树洞,内含 Tab) -->
    <view class="card entry-card pressable anim-rise delay-2" @tap="goMyWorks">
      <view class="entry-left">
        <text class="entry-title">我的作品</text>
        <text class="entry-sub">图文与树洞</text>
      </view>
      <text class="entry-arrow">›</text>
    </view>

    <!-- 暖话入口 -->
    <view class="card entry-card pressable anim-rise delay-3" @tap="goWarmWords">
      <view class="entry-left">
        <text class="entry-title">暖话</text>
        <text class="entry-sub">一句温柔的话</text>
      </view>
      <text class="entry-arrow">›</text>
    </view>

    <TabBar />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getUser, refreshUser, isLoggedIn } from '../../store/user'
import { effectiveTheme } from '../../store/theme'
import { unreadCount, refreshUnread } from '../../store/notifications'
import TabBar from '../../components/TabBar.vue'
import CachedImage from '../../components/CachedImage.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const user = ref(getUser())

// 头部图标(细线风格,currentColor 跟随 .svg-icon 配色)
const settingsSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="100%" height="100%"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`
const mailSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="100%" height="100%"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`

onShow(async () => {
  user.value = getUser()
  if (!isLoggedIn()) {
    return uni.reLaunch({ url: '/pages/login/index' })
  }
  refreshUnread() // 后台拉未读数,不打断现有加载逻辑
  user.value = await refreshUser()
})

function goSettings() {
  uni.navigateTo({ url: '/pages/settings/index' })
}

function goNotifications() {
  uni.navigateTo({ url: '/pages/notifications/index' })
}

function goDailyHistory() {
  uni.navigateTo({ url: '/pages/daily/history' })
}

function goMyWorks() {
  uni.navigateTo({ url: '/pages/my-works/index' })
}

function goWarmWords() {
  if (!isLoggedIn()) return uni.reLaunch({ url: '/pages/login/index' })
  uni.navigateTo({ url: '/pages/warm-words/index' })
}
</script>

<style scoped>
.mine {
  min-height: 100vh;
  background: #fdfbf7;
  padding-bottom: 160rpx;
}
.status-bar {
  width: 100%;
}
.header {
  padding: 16rpx 48rpx 12rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-action {
  position: relative;
  padding: 12rpx;
  /* 按下反馈 */
  transition: transform var(--t-fast, 0.2s) var(--ease-healing, cubic-bezier(0.34, 1.56, 0.64, 1));
}
.header-action:active {
  transform: scale(0.86);
}
.svg-icon {
  width: 44rpx;
  height: 44rpx;
  color: #c4a882;
  display: block;
}
.badge-dot {
  position: absolute;
  top: 10rpx;
  right: 10rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #e74c3c;
  border: 2rpx solid #fdfbf7;
}
.profile-card {
  margin: 24rpx 32rpx;
  display: flex;
  align-items: center;
}
.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
}
.avatar.placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
}
.profile-info {
  margin-left: 28rpx;
  display: flex;
  flex-direction: column;
}
.nickname {
  font-size: 36rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.bio {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #8d8d8d;
}
.role {
  align-self: flex-start;
  margin-top: 12rpx;
  padding: 4rpx 16rpx;
  background: rgba(196, 168, 130, 0.18);
  color: #c4a882;
  border-radius: 16rpx;
  font-size: 22rpx;
}

/* 通用入口卡片(每日一图/我的图文/我的树洞共用) */
.entry-card {
  margin: 0 32rpx 24rpx;
  padding: 32rpx 36rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.entry-left {
  display: flex;
  flex-direction: column;
}
.entry-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #4a4a4a;
}
.entry-sub {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #b8b8b8;
}
.entry-arrow {
  font-size: 48rpx;
  color: #c4a882;
}
</style>
