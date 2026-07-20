<template>
  <view class="home">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="header">
      <text class="header-title serif">隐语</text>
      <text class="header-sub">慢慢读,慢慢治愈</text>
    </view>

    <view class="filter-bar" v-if="tags.length">
      <scroll-view scroll-x class="tag-scroll" :show-scrollbar="false">
        <view class="tag-list">
          <text
            :class="['ftag', { active: !activeTag }]"
            @tap="setTag('')"
          >全部</text>
          <text
            v-for="t in tags"
            :key="t"
            :class="['ftag', { active: activeTag === t }]"
            @tap="setTag(t)"
          >{{ t }}</text>
        </view>
      </scroll-view>
    </view>

    <view class="list">
      <view
        v-for="a in articles"
        :key="a.id"
        class="card"
        @tap="goRead(a.id)"
      >
        <image
          v-if="a.cover_url"
          :src="resourceUrl(a.cover_url)"
          class="cover"
          mode="aspectFill"
          lazy-load
        />
        <view class="body">
          <text class="title serif">{{ a.title }}</text>
          <text class="desc" v-if="a.summary">{{ a.summary }}</text>
          <view class="meta">
            <text class="meta-left">{{ a.author?.nickname || '佚名' }} · {{ formatDate(a.published_at || a.created_at) }}</text>
            <text class="meta-right">♡ {{ a.like_count }}</text>
          </view>
          <view class="tags" v-if="a.tags && a.tags.length">
            <text v-for="t in a.tags" :key="t" class="tag">{{ t }}</text>
          </view>
        </view>
      </view>

      <view class="load-area">
        <text v-if="loading" class="load-text">加载中…</text>
        <text v-else-if="noMore" class="load-text">没有更多了,愿你也成为温暖的人 ✿</text>
        <text v-else-if="!articles.length" class="empty-text">这里还很安静,去写第一篇吧</text>
      </view>
    </view>

    <!-- 写作入口 -->
    <view class="fab" @tap="goWrite">
      <text class="fab-icon">✎</text>
    </view>

    <TabBar />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl } from '../../config'
import { formatDate } from '../../utils/format'
import { isLoggedIn, refreshUser } from '../../store/user'
import { feedDirty } from '../../store/feed'
import TabBar from '../../components/TabBar.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const articles = ref([])
const tags = ref([])
const activeTag = ref('')
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const noMore = ref(false)

onMounted(async () => {
  if (isLoggedIn()) refreshUser()
  await Promise.all([loadTags(), loadArticles()])
})

onShow(() => {
  // 仅在发布过新图文时刷新一次;平时切 tab 不重载(tab 页保活)
  if (feedDirty.value) {
    feedDirty.value = false
    page.value = 1
    noMore.value = false
    loadArticles(true)
  }
})

onReachBottom(() => loadArticles())

onPullDownRefresh(async () => {
  page.value = 1
  noMore.value = false
  await loadArticles(true)
  uni.stopPullDownRefresh()
})

async function loadTags() {
  try {
    const res = await api.articles.tags()
    tags.value = res.tags || []
  } catch {
    /* ignore */
  }
}

async function loadArticles(reset = false) {
  if (loading.value) return
  if (noMore.value && !reset) return
  loading.value = true
  try {
    if (reset) page.value = 1
    const params = { page: page.value, page_size: pageSize }
    if (activeTag.value) params.tag = activeTag.value
    const res = await api.articles.list(params)
    const items = res.items || []
    if (reset) articles.value = items
    else articles.value.push(...items)
    if (items.length < pageSize) noMore.value = true
    else page.value++
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

function setTag(t) {
  activeTag.value = t
  loadArticles(true)
}

function goRead(id) {
  uni.navigateTo({ url: '/pages/read/index?id=' + id })
}
function goWrite() {
  if (!isLoggedIn()) return uni.reLaunch({ url: '/pages/login/index' })
  uni.navigateTo({ url: '/pages/write/index' })
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #fdfbf7;
  padding-bottom: 140rpx;
}
.status-bar {
  width: 100%;
}
.header {
  padding: 16rpx 48rpx 12rpx;
}
.header-title {
  font-size: 56rpx;
  font-weight: 700;
  color: #c4a882;
  letter-spacing: 4rpx;
}
.header-sub {
  display: block;
  color: #b8b8b8;
  font-size: 24rpx;
  margin-top: 4rpx;
}
.filter-bar {
  padding: 12rpx 0 24rpx;
}
.tag-scroll {
  white-space: nowrap;
  padding: 0 48rpx;
}
.tag-list {
  display: inline-flex;
  gap: 16rpx;
}
.ftag {
  display: inline-block;
  padding: 10rpx 28rpx;
  background: #fff;
  color: #8d8d8d;
  border-radius: 30rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(196, 168, 130, 0.1);
}
.ftag.active {
  background: #c4a882;
  color: #fff;
}
.list {
  padding: 0 32rpx;
}
.card {
  background: #fff;
  border-radius: 48rpx;
  margin-bottom: 32rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 64rpx rgba(196, 168, 130, 0.15);
}
.cover {
  width: 100%;
  height: 320rpx;
}
.body {
  padding: 36rpx 40rpx 40rpx;
}
.title {
  font-size: 38rpx;
  font-weight: 600;
  color: #4a4a4a;
  line-height: 1.4;
}
.desc {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  color: #8d8d8d;
  line-height: 1.6;
}
.meta {
  display: flex;
  justify-content: space-between;
  margin-top: 24rpx;
  font-size: 22rpx;
  color: #b0b0b0;
}
.meta-right {
  color: #e0a8b0;
}
.tags {
  margin-top: 18rpx;
}
.load-area {
  padding: 30rpx 0 60rpx;
  text-align: center;
}
.load-text,
.empty-text {
  font-size: 24rpx;
  color: #b8b8b8;
}
.fab {
  position: fixed;
  right: 40rpx;
  bottom: 150rpx;
  width: 104rpx;
  height: 104rpx;
  border-radius: 52rpx;
  background: #c4a882;
  box-shadow: 0 8rpx 32rpx rgba(196, 168, 130, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 998;
}
.fab-icon {
  color: #fff;
  font-size: 48rpx;
}
</style>
