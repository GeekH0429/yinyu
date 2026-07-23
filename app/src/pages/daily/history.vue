<template>
  <view class="daily-history">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title serif">每日一图</text>
      <text v-if="items.length" class="nav-counter">{{ currentIdx + 1 }} / {{ items.length }}</text>
      <view v-else class="nav-placeholder"></view>
    </view>

    <!-- 首屏状态:loading / error / empty -->
    <view v-if="!items.length" class="state-wrap">
      <view v-if="loading" class="card item-card">
        <view class="sk sk-cover"></view>
        <view class="sk-body">
          <view class="sk sk-line sk-title"></view>
          <view class="sk sk-line"></view>
        </view>
      </view>
      <StateView
        v-else-if="error"
        type="error"
        text="加载失败,稍后再试?"
        retry
        @retry="retry"
      />
      <StateView
        v-else
        type="empty"
        text="这里还很安静 ✿"
      />
    </view>

    <!-- 横向 swiper:每天一屏,左右滑动切换 -->
    <swiper
      v-else
      class="swiper"
      :current="currentIdx"
      @change="onChange"
      :duration="300"
      :circular="false"
      :style="{ height: swiperHeight }"
    >
      <swiper-item v-for="(d, i) in items" :key="d.id">
        <view class="slide">
          <CachedImage
            :src="d.image_url"
            class="slide-image"
            mode="aspectFill"
            @tap="previewImage(d)"
          />
          <view class="slide-overlay">
            <text class="slide-date">{{ d.publish_date }}</text>
            <text class="slide-title serif" v-if="d.title">{{ d.title }}</text>
            <text class="slide-desc" v-if="d.description">{{ d.description }}</text>
          </view>
          <!-- 末尾页提示(加载更多 / 没有更多) -->
          <view v-if="i === items.length - 1 && (loadingMore || noMore)" class="slide-tag">
            <text class="slide-tag-text">{{ loadingMore ? '加载更早的…' : '最早的已经是这里了 ✿' }}</text>
          </view>
        </view>
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl } from '../../config'
import CachedImage from '../../components/CachedImage.vue'
import StateView from '../../components/StateView.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
// swiper 高度:视口减去状态栏 + 导航栏
const swiperHeight = computed(
  () => `calc(100vh - ${statusBarHeight.value}px - 100rpx)`
)

const items = ref([])
const page = ref(1)
const pageSize = 10
const noMore = ref(false)
const loading = ref(false) // 首屏 / 重置加载
const loadingMore = ref(false) // 后续分页追加
const error = ref(false)
const currentIdx = ref(0)

onShow(() => {
  // 每次进入页面 reset 重拉(数据量小,不做 SWR)
  loadList(true)
})

async function loadList(reset = false) {
  if (reset) {
    if (loading.value) return
    loading.value = true
    try {
      page.value = 1
      noMore.value = false
      currentIdx.value = 0
      const res = await api.daily.history({ page: 1, page_size: pageSize })
      const list = res.items || []
      items.value = list
      if (list.length < pageSize) noMore.value = true
      else page.value++
      error.value = false
    } catch {
      if (!items.value.length) error.value = true
    } finally {
      loading.value = false
    }
  } else {
    // 加载更多:分页追加到末尾,不影响当前位置
    if (loadingMore.value) return
    if (noMore.value) return
    loadingMore.value = true
    try {
      const res = await api.daily.history({ page: page.value, page_size: pageSize })
      const list = res.items || []
      items.value.push(...list)
      if (list.length < pageSize) noMore.value = true
      else page.value++
    } catch {
      /* ignore:用户继续滑现有内容即可 */
    } finally {
      loadingMore.value = false
    }
  }
}

function onChange(e) {
  const idx = e.detail.current
  currentIdx.value = idx
  // 接近末尾(倒数第二张)自动加载下一页,避免滑到末尾才拉
  if (idx >= items.value.length - 2 && !noMore.value && !loadingMore.value) {
    loadList(false)
  }
}

function retry() {
  error.value = false
  loadList(true)
}

function previewImage(d) {
  const url = resourceUrl(d.image_url)
  // 把当前可视的所有图都传给 urls,用户可滑动预览(并支持双指缩放)
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
.nav-counter {
  font-size: 26rpx;
  color: #b8b8b8;
  letter-spacing: 4rpx;
  min-width: 56rpx;
  text-align: right;
}
.nav-placeholder {
  width: 56rpx;
}

/* 首屏状态区(loading / error / empty) */
.state-wrap {
  padding: 80rpx 32rpx;
}
.item-card {
  margin-bottom: 32rpx;
  padding: 0;
  overflow: hidden;
}

/* 横向 swiper 全屏沉浸 */
.swiper {
  width: 100%;
}
.slide {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
.slide-image {
  width: 100%;
  height: 100%;
}
.slide-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 96rpx 48rpx 72rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.62), rgba(0, 0, 0, 0));
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.slide-date {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.88);
  letter-spacing: 6rpx;
}
.slide-title {
  margin-top: 14rpx;
  font-size: 40rpx;
  font-weight: 600;
  color: #fff;
}
.slide-desc {
  margin-top: 14rpx;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.88);
  line-height: 1.7;
}
/* 末尾页加载/无更多提示 */
.slide-tag {
  position: absolute;
  top: 28rpx;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
}
.slide-tag-text {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(0, 0, 0, 0.36);
  padding: 8rpx 24rpx;
  border-radius: 24rpx;
}

/* 骨架屏(首屏 loading) */
.sk-cover {
  width: 100%;
  height: 480rpx;
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
</style>
