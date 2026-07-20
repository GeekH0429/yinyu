<template>
  <view class="mine">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">我的</text>
    </view>

    <!-- 资料 -->
    <view class="card profile-card">
      <image
        v-if="user && user.avatar_url"
        class="avatar"
        :src="resourceUrl(user.avatar_url)"
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

    <!-- 我的图文 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title serif">我的图文</text>
        <text class="section-count">{{ articles.length }} 篇</text>
      </view>
      <view class="card mini-card" v-for="a in articles" :key="a.id" @tap="goRead(a.id)">
        <text class="mini-title">{{ a.title }}</text>
        <view class="mini-meta">
          <text>{{ a.status === 'published' ? '已发布' : '草稿' }} · ♡ {{ a.like_count }}</text>
          <text class="mini-time">{{ formatDate(a.created_at) }}</text>
        </view>
      </view>
      <text v-if="!articles.length" class="empty">还没有作品,去首页 ✎ 写一篇吧</text>
    </view>

    <!-- 我的树洞 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title serif">我的树洞</text>
        <text class="section-count">{{ treeholes.length }} 篇</text>
      </view>
      <view class="card mini-card" v-for="t in treeholes" :key="t.id">
        <view class="th-top">
          <text class="mini-title">{{ t.title || '无题的悄悄话' }}</text>
          <text :class="['th-status', { off: !t.is_active }]">{{ t.is_active ? '有效' : '已停用' }}</text>
        </view>
        <view class="th-code-row">
          <text class="th-code">{{ t.code }}</text>
          <view class="th-actions">
            <text class="th-btn" @tap="copy(t.code)">复制</text>
            <text class="th-btn" @tap="refreshCode(t)">换暗号</text>
          </view>
        </view>
        <text class="mini-time">被阅读 {{ t.view_count }} 次</text>
      </view>
      <text v-if="!treeholes.length" class="empty">还没有树洞,去写一封悄悄话吧</text>
    </view>

    <view class="logout-row" @tap="onLogout">
      <text>退出登录</text>
    </view>

    <TabBar />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl } from '../../config'
import { formatDate } from '../../utils/format'
import { getUser, refreshUser, logout, isLoggedIn } from '../../store/user'
import TabBar from '../../components/TabBar.vue'

const statusBarHeight = ref(0)
const user = ref(getUser())
const articles = ref([])
const treeholes = ref([])

;(() => {
  const sys = uni.getSystemInfoSync()
  statusBarHeight.value = sys.statusBarHeight || 0
})()

onShow(async () => {
  if (!isLoggedIn()) {
    return uni.reLaunch({ url: '/pages/login/index' })
  }
  user.value = await refreshUser()
  await Promise.all([loadArticles(), loadTreeholes()])
})

async function loadArticles() {
  try {
    const res = await api.me.myArticles({ page: 1, page_size: 20 })
    articles.value = res.items || []
  } catch {
    /* ignore */
  }
}

async function loadTreeholes() {
  try {
    const res = await api.me.myTreeholes({ page: 1, page_size: 20 })
    treeholes.value = res.items || []
  } catch {
    /* ignore */
  }
}

function goRead(id) {
  uni.navigateTo({ url: '/pages/read/index?id=' + id })
}

function copy(text) {
  uni.setClipboardData({ data: String(text) })
}

async function refreshCode(t) {
  uni.showModal({
    title: '换暗号',
    content: '重新生成随机暗号?旧暗号将立即失效。',
    success: async (r) => {
      if (!r.confirm) return
      try {
        const res = await api.treeholes.changeCode(t.id, null)
        t.code = res.code
        uni.showToast({ title: '已更新', icon: 'success' })
      } catch {
        /* ignore */
      }
    }
  })
}

function onLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要离开这个角落吗?',
    success: (r) => {
      if (!r.confirm) return
      logout()
      uni.reLaunch({ url: '/pages/login/index' })
    }
  })
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
}
.header-title {
  font-size: 52rpx;
  font-weight: 700;
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
.section {
  margin: 16rpx 32rpx;
}
.section-head {
  display: flex;
  align-items: baseline;
  margin: 24rpx 8rpx 16rpx;
}
.section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #4a4a4a;
}
.section-count {
  margin-left: 16rpx;
  font-size: 24rpx;
  color: #b0b0b0;
}
.mini-card {
  padding: 28rpx 32rpx;
  margin-bottom: 20rpx;
}
.mini-title {
  font-size: 30rpx;
  color: #4a4a4a;
  font-weight: 500;
}
.mini-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 14rpx;
  font-size: 22rpx;
  color: #b0b0b0;
}
.mini-time {
  font-size: 22rpx;
  color: #b0b0b0;
  margin-top: 8rpx;
  display: block;
}
.empty {
  display: block;
  text-align: center;
  padding: 40rpx;
  color: #c8c8c8;
  font-size: 26rpx;
}
.th-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.th-status {
  font-size: 22rpx;
  color: #88a07a;
  background: rgba(136, 160, 122, 0.15);
  padding: 4rpx 16rpx;
  border-radius: 16rpx;
}
.th-status.off {
  color: #b0b0b0;
  background: #f0f0f0;
}
.th-code-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18rpx;
}
.th-code {
  font-size: 44rpx;
  font-weight: 700;
  letter-spacing: 12rpx;
  color: #c4a882;
  font-family: 'Menlo', monospace;
}
.th-actions {
  display: flex;
  gap: 16rpx;
}
.th-btn {
  padding: 10rpx 24rpx;
  background: #f3eee5;
  color: #8d8d8d;
  border-radius: 24rpx;
  font-size: 24rpx;
}
.logout-row {
  margin: 40rpx 32rpx;
  padding: 30rpx 0;
  text-align: center;
  background: #fff;
  border-radius: 40rpx;
  color: #c4a882;
  font-size: 30rpx;
  box-shadow: 0 8rpx 32rpx rgba(196, 168, 130, 0.12);
}
</style>
