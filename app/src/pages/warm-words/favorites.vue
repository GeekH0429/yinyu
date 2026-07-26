<template>
  <view class="fav" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back pressable" @tap="goBack">‹ 返回</text>
      <text class="topbar-title serif">我的收藏</text>
      <text class="action placeholder"></text>
    </view>

    <scroll-view
      scroll-y
      class="scroll"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onReachBottom"
    >
      <!-- 加载骨架(首次) -->
      <view v-if="loading && !items.length" class="skeleton-list">
        <view v-for="i in 4" :key="i" class="card sk-card">
          <view class="sk sk-line" style="width: 30%"></view>
          <view class="sk sk-line" style="width: 90%; margin-top: 24rpx"></view>
          <view class="sk sk-line" style="width: 40%; margin-top: 16rpx"></view>
        </view>
      </view>

      <!-- 列表 -->
      <template v-else>
        <view
          v-for="(it, i) in items"
          :key="it.id"
          :class="['card', 'fav-card', 'pressable', i < 6 ? 'anim-rise delay-' + (i + 1) : '']"
          @tap="onItemTap(it)"
        >
          <text class="scene-tag">{{ sceneLabel(it.scene) }}</text>
          <text class="warm-text serif">{{ it.text }}</text>
          <view class="card-foot">
            <text class="foot-time">{{ formatTime(it.created_at) }}</text>
            <text class="foot-action" @tap.stop="onRemove(it)">取消收藏</text>
          </view>
        </view>

        <view v-if="!loading && !items.length" class="empty">
          <text class="empty-text serif">还没有收藏</text>
          <text class="empty-sub">在暖话里遇到的温柔,可以留在这里</text>
        </view>

        <view v-if="loadingMore" class="loading-more">加载中…</view>
        <view v-else-if="!hasMore && items.length" class="loading-more">没有更多了</view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import { isLoggedIn } from '../../store/user'

// 场景 key → 中文 label(前端硬编码,后端 scenes 接口也是同源 SCENES dict)
const SCENE_LABELS = {
  anxiety: '焦虑',
  lonely: '孤独',
  insomnia: '失眠',
  self_doubt: '自我怀疑',
  encourage_self: '鼓励自己',
  to_partner: '想对恋人说'
}

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

const items = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const hasMore = ref(true)

const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)

function sceneLabel(scene) {
  return SCENE_LABELS[scene] || scene
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + ' 天前'
  const m = (d.getMonth() || 0) + 1
  const day = d.getDate()
  return `${m}月${day}日`
}

async function load(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
    hasMore.value = true
    loading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const res = await api.warmWords.favorites({ page: page.value, page_size: pageSize })
    const list = res.items || []
    total.value = res.total || 0
    if (reset) {
      items.value = list
    } else {
      items.value = items.value.concat(list)
    }
    hasMore.value = items.value.length < total.value
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function onRefresh() {
  refreshing.value = true
  await load(true)
  refreshing.value = false
}

function onReachBottom() {
  if (loadingMore.value || !hasMore.value) return
  page.value++
  load(false)
}

function onItemTap(it) {
  const text = '「' + it.text + '」'
  uni.navigateTo({
    url: '/pages/write/index?prefill=' + encodeURIComponent(text)
  })
}

async function onRemove(it) {
  // 乐观删除
  const idx = items.value.findIndex((x) => x.id === it.id)
  if (idx === -1) return
  const snapshot = items.value[idx]
  items.value.splice(idx, 1)
  total.value = Math.max(0, total.value - 1)
  try {
    await api.warmWords.unfavorite(it.warm_word_id)
    uni.showToast({ title: '已取消收藏', icon: 'none' })
  } catch {
    // 回滚
    items.value.splice(idx, 0, snapshot)
    total.value += 1
  }
}

function goBack() {
  // 直接刷新 / URL 进入时栈里只有自己,navigateBack 会静默失败
  if (getCurrentPages().length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/pages/mine/index' })
  }
}

onShow(() => {
  if (!isLoggedIn()) return uni.reLaunch({ url: '/pages/login/index' })
  load(true)
})
</script>

<style scoped>
.fav {
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
.topbar-title {
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
  padding: 16rpx 32rpx 48rpx;
}

/* 列表卡片 */
.fav-card {
  padding: 36rpx 40rpx;
  margin-bottom: 24rpx;
  display: flex;
  flex-direction: column;
}
.scene-tag {
  font-size: 22rpx;
  color: #c4a882;
  letter-spacing: 2rpx;
}
.warm-text {
  margin-top: 24rpx;
  font-size: 32rpx;
  line-height: 1.8;
  color: #4a4a4a;
}
.card-foot {
  margin-top: 32rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.foot-time {
  font-size: 22rpx;
  color: #b0b0b0;
}
.foot-action {
  font-size: 24rpx;
  color: #c4a882;
  padding: 8rpx 20rpx;
  border-radius: 24rpx;
  background: rgba(196, 168, 130, 0.1);
}

/* 骨架 */
.sk {
  background: linear-gradient(90deg, #efe9df 25%, #f7f2ea 37%, #efe9df 63%);
  background-size: 400% 100%;
  border-radius: 12rpx;
}
.sk-card {
  margin-bottom: 24rpx;
  padding: 36rpx 40rpx;
}
.sk-line {
  height: 28rpx;
  animation: sk-shimmer 1.4s ease infinite;
}
@keyframes sk-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

/* 空态 */
.empty {
  padding: 200rpx 0;
  text-align: center;
}
.empty-text {
  display: block;
  font-size: 36rpx;
  color: #8d8d8d;
}
.empty-sub {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #b0b0b0;
}

.loading-more {
  text-align: center;
  padding: 32rpx 0;
  color: #b8b8b8;
  font-size: 24rpx;
}
</style>
