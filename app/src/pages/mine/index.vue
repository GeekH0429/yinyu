<template>
  <view class="mine">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">我的</text>
      <view class="header-actions">
        <view class="header-action" @tap="goNotifications">
          <text class="bell">🔔</text>
          <view v-if="unreadCount > 0" class="badge-dot"></view>
        </view>
        <view class="header-action" @tap="goSettings">
          <text class="settings-gear">⚙</text>
        </view>
      </view>
    </view>

    <!-- 资料 -->
    <view class="card profile-card">
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
    <view class="card entry-card" @tap="goDailyHistory">
      <view class="entry-left">
        <text class="entry-title">每日一图 · 回忆</text>
        <text class="entry-sub">看看过去的每一天</text>
      </view>
      <text class="entry-arrow">›</text>
    </view>

    <!-- 我的作品入口(图文与树洞,内含 Tab) -->
    <view class="card entry-card" @tap="goMyWorks">
      <view class="entry-left">
        <text class="entry-title">我的作品</text>
        <text class="entry-sub">图文与树洞</text>
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
import { unreadCount, refreshUnread } from '../../store/notifications'
import TabBar from '../../components/TabBar.vue'
import CachedImage from '../../components/CachedImage.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const user = ref(getUser())

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
.header-title {
  font-size: 52rpx;
  font-weight: 700;
  color: #c4a882;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.header-action {
  position: relative;
  padding: 12rpx;
}
.bell {
  font-size: 42rpx;
  color: #c4a882;
}
.badge-dot {
  position: absolute;
  top: 6rpx;
  right: 6rpx;
  min-width: 16rpx;
  height: 16rpx;
  padding: 0 4rpx;
  border-radius: 8rpx;
  background: #e0a8b0;
  border: 2rpx solid #fdfbf7;
}
.settings-gear {
  font-size: 48rpx;
  color: #c4a882;
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
