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

    <!-- SWR 离线提示:后台静默刷新失败但本地有旧数据时,告诉用户当前是缓存内容 -->
    <view class="offline-banner" v-if="offlineStale" @tap="dismissOffline">
      <text class="offline-text">网络不太通,显示的是上次的内容 ✦</text>
      <text class="offline-close">×</text>
    </view>

    <view class="list">
      <!-- 骨架屏:首次加载且无数据 -->
      <view v-if="loading && !articles.length">
        <view v-for="n in 3" :key="'sk'+n" class="card sk-card">
          <view class="sk sk-cover"></view>
          <view class="sk-body">
            <view class="sk sk-line sk-title"></view>
            <view class="sk sk-line"></view>
            <view class="sk sk-line short"></view>
          </view>
        </view>
      </view>
      <view
        v-for="a in articles"
        :key="a.id"
        class="card"
        @tap="goRead(a.id)"
      >
        <CachedImage
          v-if="a.cover_url"
          :src="a.cover_url"
          class="cover"
          mode="aspectFill"
          :ratio="2"
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
        <text v-if="loading && articles.length" class="load-text">加载中…</text>
        <StateView
          v-else-if="feedError && !articles.length"
          type="error"
          text="没能连上这个角落,稍后再试?"
          retry
          @retry="retryFeed"
        />
        <StateView
          v-else-if="!articles.length"
          type="empty"
          text="这里还很安静,去写第一篇吧"
        />
        <text v-else-if="noMore" class="load-text">没有更多了,愿你也成为温暖的人 ✿</text>
      </view>
    </view>

    <!-- 写作入口 -->
    <view class="fab" @tap="goWrite">
      <text class="fab-icon">✎</text>
    </view>

    <!-- 每日一图:启动后首次 onShow 触发,当天只弹一次 -->
    <DailyImageOverlay
      :visible="dailyOverlayVisible"
      :image="todayImage"
      @close="onCloseDaily"
    />

    <TabBar />
  </view>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { onShow, onReachBottom, onPullDownRefresh, onPageScroll } from '@dcloudio/uni-app'
import { api } from '../../api'
import { formatDate } from '../../utils/format'
import { isLoggedIn, refreshUser } from '../../store/user'
import {
  articles, tags, activeTag, page, noMore, loading,
  scrollTop, hydrated, dirty, hydrateFeedFromSnap, persistFeedSnap
} from '../../store/feed'
import TabBar from '../../components/TabBar.vue'
import CachedImage from '../../components/CachedImage.vue'
import StateView from '../../components/StateView.vue'
import DailyImageOverlay from '../../components/DailyImageOverlay.vue'
import { todayImage, todayLoaded } from '../../store/dailyImage'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const pageSize = 10
const feedError = ref(false) // 首次加载失败且无数据时,展示错误占位 + 重试
const offlineStale = ref(false) // SWR:后台刷新失败但本地有数据时,顶部轻提示
const dailyOverlayVisible = ref(false) // 每日一图弹层显隐

// 标签切换:防抖 + reqId race 防护(连续点按不同标签只发最后一次请求,过期响应丢弃)
let tagDebounce = null
let listReqId = 0

onMounted(async () => {
  if (isLoggedIn()) refreshUser()
  // ① reLaunch 重挂载、内存缓存命中:还原滚动、不重载
  if (hydrated.value && !dirty.value) {
    restoreScroll()
    return
  }
  // ② 冷启动:先从持久快照水合,立即展示上次内容
  const hasSnap = hydrateFeedFromSnap()
  restoreScroll()
  if (hasSnap && !dirty.value) {
    // 有快照、未失效:后台静默刷新(不显示"加载中"),成功覆盖快照,失败保留快照
    backgroundRefresh()
  } else {
    // ③ 无快照或已失效:前台带 spinner 拉取
    loading.value = true
    await Promise.all([loadTags(), loadArticles(true)])
    persistFeedSnap()
  }
  hydrated.value = true
  dirty.value = false
})

/** 后台静默刷新(SWR revalidate):不显示 loading,成功后覆盖快照,失败时给顶部提示 */
function backgroundRefresh() {
  Promise.all([loadTags(), loadArticles(true, true)])
    .then(() => {
      offlineStale.value = false
      persistFeedSnap()
    })
    .catch(() => {
      // 弱网:有旧数据则提示「这是上次的内容」,没旧数据则交给前台错误占位
      if (articles.value.length) offlineStale.value = true
    })
}

function dismissOffline() {
  offlineStale.value = false
}

// navigateBack(write 发完帖返回)不重挂载页面,用 onShow 处理失效刷新
onShow(() => {
  if (dirty.value) {
    dirty.value = false
    loadArticles(true).then(() => persistFeedSnap()).catch(() => {})
  }
  // 每日一图:今日首次打开触发弹层
  maybeShowDaily()
})

/** 每日一图:每次 App 启动进入首页时弹一次(本次会话内不重复弹,避免 onShow 反复触发)。
 *  不做"当天只弹一次"的限制 —— 用户每次打开 App 都能看到今日图。 */
async function maybeShowDaily() {
  // 本次会话已弹过:跳过(切 tab/返回子页触发的 onShow 不再重复弹)
  if (todayLoaded.value) return
  try {
    const res = await api.daily.today()
    todayImage.value = res
    dailyOverlayVisible.value = true
  } catch {
    // 404 今日未排期:静默
    todayImage.value = null
  } finally {
    todayLoaded.value = true
  }
}

function onCloseDaily() {
  dailyOverlayVisible.value = false
}

onPageScroll((e) => {
  scrollTop.value = e.scrollTop
})

onReachBottom(() => loadArticles())

onPullDownRefresh(async () => {
  await loadArticles(true)
  uni.stopPullDownRefresh()
})

function restoreScroll() {
  if (scrollTop.value <= 0) return
  // 等列表渲染稳定再还原(H5 下需 DOM 就绪)
  nextTick(() => setTimeout(() => uni.pageScrollTo({ scrollTop: scrollTop.value, duration: 0 }), 50))
}

async function loadTags() {
  try {
    const res = await api.articles.tags()
    tags.value = res.tags || []
  } catch {
    /* ignore */
  }
}

async function loadArticles(reset = false, silent = false) {
  // reset 由标签切换/下拉刷新触发,允许并发(用 reqId 仲裁);触底不 reset 时仍守卫
  if (loading.value && !reset) return
  if (noMore.value && !reset) return
  const reqId = ++listReqId
  if (!silent) loading.value = true
  try {
    if (reset) {
      page.value = 1
      noMore.value = false
    }
    const params = { page: page.value, page_size: pageSize }
    if (activeTag.value) params.tag = activeTag.value
    const res = await api.articles.list(params)
    if (reqId !== listReqId) return // 已被后续请求取代,丢弃过期响应
    const items = res.items || []
    if (reset) articles.value = items
    else articles.value.push(...items)
    if (items.length < pageSize) noMore.value = true
    else page.value++
    feedError.value = false
  } catch {
    if (reqId !== listReqId) return
    // 静默刷新失败不提示;仅"无任何数据 + 非静默"时显示错误占位(有旧数据则保留)
    if (!silent && !articles.value.length) feedError.value = true
  } finally {
    // 仅当前请求是最新的时才解除 loading,避免被新请求接管时误清
    if (reqId === listReqId && !silent) loading.value = false
  }
}

function setTag(t) {
  if (activeTag.value === t) return
  activeTag.value = t
  // 立即清空旧内容,展示骨架(避免旧标签内容闪一下)
  articles.value = []
  noMore.value = false
  offlineStale.value = false
  // 防抖:连续切多个标签只发最后一次(250ms 内的连点合并)
  clearTimeout(tagDebounce)
  loading.value = true
  tagDebounce = setTimeout(() => {
    loadArticles(true)
  }, 250)
}

function retryFeed() {
  feedError.value = false
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
/* SWR 离线提示条 */
.offline-banner {
  margin: 0 32rpx 16rpx;
  padding: 18rpx 28rpx;
  background: rgba(196, 168, 130, 0.12);
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.offline-text {
  font-size: 24rpx;
  color: #c4a882;
}
.offline-close {
  font-size: 32rpx;
  color: #c4a882;
  padding-left: 16rpx;
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
/* 骨架屏 */
.sk-card {
  margin-bottom: 32rpx;
  overflow: hidden;
}
.sk-cover {
  width: 100%;
  height: 320rpx;
}
.sk-body {
  padding: 36rpx 40rpx 40rpx;
}
.sk-line {
  height: 26rpx;
  border-radius: 13rpx;
  margin-bottom: 18rpx;
}
.sk-line.sk-title {
  height: 40rpx;
  width: 55%;
  border-radius: 20rpx;
  margin-bottom: 26rpx;
}
.sk-line.short {
  width: 40%;
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
