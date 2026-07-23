<template>
  <view class="daily-history">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title serif">每日一图</text>
      <view class="nav-placeholder"></view>
    </view>

    <scroll-view
      scroll-y
      class="list"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onReach"
      :lower-threshold="120"
    >
      <view v-for="d in items" :key="d.id" class="card item-card">
        <CachedImage
          :src="d.image_url"
          class="item-image"
          mode="widthFix"
          :lazy-load="false"
          @tap="previewImage(d)"
        />
        <view class="item-body">
          <text class="item-title serif">{{ d.title }}</text>
          <text class="item-desc" v-if="d.description">{{ d.description }}</text>
          <text class="item-date">{{ d.publish_date }}</text>
        </view>
      </view>

      <view class="load-area">
        <view v-if="loading && !items.length">
          <view v-for="n in 2" :key="'sk' + n" class="card item-card">
            <view class="sk sk-cover"></view>
            <view class="sk-body">
              <view class="sk sk-line sk-title"></view>
              <view class="sk sk-line"></view>
            </view>
          </view>
        </view>
        <StateView
          v-else-if="error && !items.length"
          type="error"
          text="加载失败,稍后再试?"
          retry
          @retry="retry"
        />
        <StateView
          v-else-if="!items.length"
          type="empty"
          text="这里还很安静 ✿"
        />
        <text v-else-if="noMore" class="load-text">没有更多了 ✿</text>
        <text v-else-if="loading" class="load-text">加载中…</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl } from '../../config'
import CachedImage from '../../components/CachedImage.vue'
import StateView from '../../components/StateView.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const items = ref([])
const page = ref(1)
const pageSize = 10
const noMore = ref(false)
const loading = ref(false)
const refreshing = ref(false)
const error = ref(false)

onShow(() => {
  // 每次进入页面 reset 重拉(数据量小,不做 SWR)
  loadList(true)
})

async function loadList(reset = false) {
  if (loading.value) return
  if (noMore.value && !reset) return
  loading.value = true
  try {
    if (reset) {
      page.value = 1
      noMore.value = false
    }
    const res = await api.daily.history({ page: page.value, page_size: pageSize })
    const list = res.items || []
    if (reset) items.value = list
    else items.value.push(...list)
    if (list.length < pageSize) noMore.value = true
    else page.value++
    error.value = false
  } catch {
    if (!items.value.length) error.value = true
  } finally {
    loading.value = false
  }
}

function onReach() {
  loadList()
}
function onRefresh() {
  refreshing.value = true
  loadList(true).finally(() => {
    refreshing.value = false
  })
}
function retry() {
  error.value = false
  loadList(true)
}

function previewImage(d) {
  const url = resourceUrl(d.image_url)
  // 把当前可视的所有图都传给 urls,用户可滑动预览
  const urls = items.value
    .map((i) => resourceUrl(i.image_url))
    .filter(Boolean)
  uni.previewImage({
    current: url,
    urls: urls.length ? urls : [url]
  })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.daily-history {
  min-height: 100vh;
  background: #fdfbf7;
}
.status-bar {
  width: 100%;
}
.nav {
  padding: 16rpx 24rpx 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-back {
  padding: 12rpx;
}
.nav-back-icon {
  font-size: 56rpx;
  color: #c4a882;
}
.nav-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.nav-placeholder {
  width: 56rpx;
}

.list {
  height: calc(100vh - 100rpx);
  padding: 0 32rpx;
  box-sizing: border-box;
}
.item-card {
  margin-bottom: 32rpx;
  padding: 0;
  overflow: hidden;
}
.item-image {
  width: 100%;
}
.item-body {
  padding: 32rpx 36rpx 36rpx;
}
.item-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.item-desc {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  color: #8d8d8d;
  line-height: 1.7;
}
.item-date {
  display: block;
  margin-top: 20rpx;
  font-size: 22rpx;
  color: #c4a882;
  letter-spacing: 4rpx;
}

/* 骨架屏(与首页 .sk 全局类共用) */
.sk-cover {
  width: 100%;
  height: 360rpx;
}
.sk-body {
  padding: 32rpx 36rpx 36rpx;
}
.sk-title {
  height: 36rpx;
  width: 50%;
  border-radius: 18rpx;
  margin-bottom: 20rpx;
}

.load-area {
  padding: 30rpx 0 80rpx;
  text-align: center;
}
.load-text {
  font-size: 24rpx;
  color: #b8b8b8;
}
</style>
