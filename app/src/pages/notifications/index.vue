<template>
  <view class="noti">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="title">通知</text>
      <text class="action" @tap="markAllRead" v-if="items.length">全部已读</text>
      <text v-else class="action placeholder"></text>
    </view>

    <scroll-view
      scroll-y
      class="scroll"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="loadMore"
      :lower-threshold="120"
    >
      <view
        v-for="n in items"
        :key="n.id"
        :class="['noti-item', { unread: !n.is_read }]"
        @tap="onTap(n)"
      >
        <view class="dot-wrap">
          <view v-if="!n.is_read" class="unread-dot"></view>
        </view>
        <view class="body">
          <view class="avatar" v-if="n.actor">
            <image
              v-if="n.actor.avatar_url"
              class="avatar-img"
              :src="n.actor.avatar_url"
              mode="aspectFill"
            />
            <view v-else class="avatar-placeholder">
              {{ (n.actor.nickname || '?').slice(0, 1) }}
            </view>
          </view>
          <view class="text-block">
            <text class="line">{{ describe(n) }}</text>
            <text v-if="n.comment" class="snippet">{{ n.comment.snippet }}</text>
            <text class="time">{{ formatRelative(n.created_at) }}</text>
          </view>
        </view>
      </view>

      <StateView
        v-if="!loading && !items.length && !loadError"
        type="empty"
        text="还没有通知"
      />
      <StateView
        v-else-if="loadError && !items.length"
        type="error"
        text="加载失败"
        retry
        @retry="reload"
      />
      <view v-else-if="items.length" class="load-more">
        <text v-if="loading" class="load-text">加载中…</text>
        <text v-else-if="!hasMore" class="load-text">没有更多了 ✿</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { formatRelative } from '../../utils/format'
import { setUnread, decUnread } from '../../store/notifications'
import StateView from '../../components/StateView.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const items = ref([])
const loading = ref(false)
const loadError = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

const hasMore = computed(() => page.value * pageSize < total.value)

async function load(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
  }
  loading.value = reset
  loadError.value = false
  try {
    const res = await api.notifications.list({ page: page.value, page_size: pageSize })
    if (reset) items.value = res.items
    else items.value = items.value.concat(res.items)
    total.value = res.total || 0
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || !hasMore.value) return
  page.value++
  try {
    const res = await api.notifications.list({ page: page.value, page_size: pageSize })
    items.value = items.value.concat(res.items)
    total.value = res.total || 0
  } catch {
    page.value--
  }
}

function reload() {
  load(true)
}

async function onRefresh() {
  refreshing.value = true
  await load(true)
  refreshing.value = false
}

async function markAllRead() {
  try {
    await api.notifications.markAllRead()
    items.value.forEach((n) => (n.is_read = true))
    setUnread(0)
    uni.showToast({ title: '已全部标记为已读', icon: 'none' })
  } catch {
    /* ignore */
  }
}

async function onTap(n) {
  // 标记已读(本地 + 远端)
  if (!n.is_read) {
    n.is_read = true
    decUnread(1)
    try {
      await api.notifications.markRead(n.id)
    } catch {
      /* ignore */
    }
  }
  // 跳转到关联文章
  if (n.article) {
    uni.navigateTo({ url: '/pages/read/index?id=' + n.article.id })
  }
}

function describe(n) {
  const actor = n.actor?.nickname || '某人'
  switch (n.type) {
    case 'comment':
      return actor + ' 评论了你的《' + (n.article?.title || '图文') + '》'
    case 'reply':
      return actor + ' 回复了你的评论'
    case 'comment_like':
      return actor + ' 赞了你的评论'
    case 'mention':
      return actor + ' 在评论里 @ 了你'
    default:
      return actor + ' 与你有互动'
  }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.reLaunch({ url: '/pages/mine/index' })
}

onShow(() => {
  load(true)
})
</script>

<style scoped>
.noti {
  min-height: 100vh;
  background: #fdfbf7;
  display: flex;
  flex-direction: column;
}
.status-bar {
  width: 100%;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 40rpx 12rpx;
}
.back {
  width: 130rpx;
  color: #c4a882;
  font-size: 30rpx;
}
.title {
  font-size: 32rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.action {
  width: 130rpx;
  text-align: right;
  font-size: 26rpx;
  color: #c4a882;
}
.action.placeholder {
  visibility: hidden;
}
.scroll {
  flex: 1;
  padding: 0 32rpx;
}
.noti-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(196, 168, 130, 0.1);
}
.noti-item.unread {
  background: #fdf6ec;
}
.dot-wrap {
  width: 16rpx;
  flex-shrink: 0;
  padding-top: 8rpx;
}
.unread-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #e0a8b0;
}
.body {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  min-width: 0;
}
.avatar {
  flex-shrink: 0;
}
.avatar-img,
.avatar-placeholder {
  width: 64rpx;
  height: 64rpx;
  border-radius: 32rpx;
}
.avatar-placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}
.text-block {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.line {
  font-size: 28rpx;
  color: #4a4a4a;
  line-height: 1.5;
}
.snippet {
  font-size: 26rpx;
  color: #8d8d8d;
  background: #f5efe5;
  padding: 8rpx 16rpx;
  border-radius: 12rpx;
  line-height: 1.5;
  word-break: break-word;
}
.time {
  font-size: 22rpx;
  color: #b0b0b0;
  margin-top: 4rpx;
}
.load-more {
  text-align: center;
  padding: 32rpx 0 64rpx;
}
.load-text {
  color: #b0b0b0;
  font-size: 24rpx;
}
</style>
