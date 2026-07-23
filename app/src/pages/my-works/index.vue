<template>
  <view class="my-works">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title serif">我的作品</text>
      <view class="nav-placeholder"></view>
    </view>

    <!-- Tab 切换 -->
    <view class="tabs-wrapper">
      <view class="tabs-header">
        <view
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-item', { active: currentTab === tab.key }]"
          @tap="switchTab(tab.key)"
        >
          <text class="tab-text">{{ tab.label }}</text>
          <text class="tab-count">{{ tab.count }}</text>
        </view>
      </view>

      <swiper
        :current="currentTabIndex"
        @change="onSwiperChange"
        :duration="300"
        class="tabs-content"
        :style="{ height: swiperHeight }"
      >
        <!-- 我的图文 -->
        <swiper-item>
          <scroll-view
            scroll-y
            class="tab-content"
            refresher-enabled
            enable-back-to-top
            :refresher-triggered="artRefreshing"
            @refresherrefresh="onRefreshArticles"
            @scrolltolower="onReachArticles"
            :lower-threshold="120"
          >
            <view class="card mini-card" v-for="a in articles" :key="a.id" @tap="goRead(a.id)">
              <text class="mini-title">{{ a.title }}</text>
              <view class="mini-meta">
                <text>{{ a.status === 'published' ? '已发布' : '草稿' }} · ♡ {{ a.like_count }}</text>
                <view class="mini-right">
                  <text class="mini-edit" @tap.stop="goEdit(a)">编辑</text>
                  <text class="mini-time">{{ formatDate(a.created_at) }}</text>
                </view>
              </view>
            </view>
            <StateView
              v-if="artError && !articles.length"
              type="error"
              text="加载失败"
              retry
              @retry="retryArticles"
            />
            <view v-else-if="artLoading && !articles.length">
              <view v-for="n in 3" :key="'sk' + n" class="card mini-card">
                <view class="sk sk-line sk-mtitle"></view>
                <view class="sk sk-line sk-mmeta"></view>
              </view>
            </view>
            <view v-else-if="articles.length || artLoading" class="load-more">
              <text v-if="artLoading" class="load-text">加载中…</text>
              <text v-else-if="artNoMore" class="load-text">没有更多了 ✿</text>
            </view>
            <text v-else class="empty">还没有作品,去首页 ✎ 写一篇吧</text>
          </scroll-view>
        </swiper-item>

        <!-- 我的树洞 -->
        <swiper-item>
          <scroll-view
            scroll-y
            class="tab-content"
            refresher-enabled
            enable-back-to-top
            :refresher-triggered="thRefreshing"
            @refresherrefresh="onRefreshTreeholes"
            @scrolltolower="onReachTreeholes"
            :lower-threshold="120"
          >
            <view class="card mini-card" v-for="t in treeholes" :key="t.id">
              <view class="th-top">
                <text class="mini-title">{{ t.title || '无题的悄悄话' }}</text>
                <text :class="['th-status', { off: !t.is_active }]">{{ t.is_active ? '有效' : '已停用' }}</text>
              </view>
              <view class="th-code-row">
                <text class="th-code">{{ t.code }}</text>
                <view class="th-actions">
                  <text class="th-btn" @tap="editTreehole(t)">编辑</text>
                  <text class="th-btn" @tap="copy(t.code)">复制</text>
                  <text class="th-btn" @tap="refreshCode(t)">换暗号</text>
                </view>
              </view>
              <text class="mini-time">被阅读 {{ t.view_count }} 次</text>
            </view>
            <StateView
              v-if="thError && !treeholes.length"
              type="error"
              text="加载失败"
              retry
              @retry="retryTreeholes"
            />
            <view v-else-if="thLoading && !treeholes.length">
              <view v-for="n in 3" :key="'sk' + n" class="card mini-card">
                <view class="sk sk-line sk-mtitle"></view>
                <view class="sk sk-line sk-mmeta"></view>
              </view>
            </view>
            <view v-else-if="treeholes.length || thLoading" class="load-more">
              <text v-if="thLoading" class="load-text">加载中…</text>
              <text v-else-if="thNoMore" class="load-text">没有更多了 ✿</text>
            </view>
            <text v-else class="empty">还没有树洞,去写一封悄悄话吧</text>
          </scroll-view>
        </swiper-item>
      </swiper>
    </view>

    <!-- 编辑树洞(复用与「我的」页同一组件) -->
    <TreeholeEditor v-model:visible="thEditorVisible" :editing="thEditing" @updated="onThUpdated" />
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { formatDate } from '../../utils/format'
import { isLoggedIn } from '../../store/user'
import {
  articles, treeholes,
  artPage, artNoMore, thPage, thNoMore,
  hydrated, dirty, hydrateMeFromSnap, persistMeSnap, invalidateMe
} from '../../store/me'
import TreeholeEditor from '../../components/TreeholeEditor.vue'
import StateView from '../../components/StateView.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
// swiper 高度:视口减去状态栏 + 导航栏 + Tab 头
const swiperHeight = computed(
  () => `calc(100vh - ${statusBarHeight.value}px - 220rpx)`
)

// Tab 切换相关
const currentTab = ref('articles')
const pageSize = 20
const artLoading = ref(false)
const thLoading = ref(false)
const artError = ref(false)
const thError = ref(false)
const artRefreshing = ref(false)
const thRefreshing = ref(false)
const tabs = computed(() => [
  { key: 'articles', label: '我的图文', count: articles.value.length },
  { key: 'treeholes', label: '我的树洞', count: treeholes.value.length }
])
const currentTabIndex = computed(() => (currentTab.value === 'articles' ? 0 : 1))

// 树洞编辑弹窗
const thEditorVisible = ref(false)
const thEditing = ref(null)

onShow(async () => {
  if (!isLoggedIn()) {
    return uni.reLaunch({ url: '/pages/login/index' })
  }
  // ① 内存缓存命中(切 tab 回来):数据+分页状态都在,直接还原
  if (hydrated.value && !dirty.value) return
  // ② 冷启动:从持久快照水合(含分页状态),立即展示
  const hasSnap = hydrateMeFromSnap()
  hydrated.value = true
  const wasDirty = dirty.value
  dirty.value = false
  if (!hasSnap || wasDirty) {
    // 无快照(首次) 或 已失效(发布/编辑后):reset 重拉第一页;
    // 有快照且未失效则直接展示,触底继续加载(不后台覆盖,保留已分页内容)
    await Promise.all([loadArticles(true), loadTreeholes(true)])
  }
  persistMeSnap()
})

async function loadArticles(reset = false) {
  if (artLoading.value) return
  if (artNoMore.value && !reset) return
  artLoading.value = true
  try {
    if (reset) {
      artPage.value = 1
      artNoMore.value = false
    }
    const res = await api.me.myArticles({ page: artPage.value, page_size: pageSize })
    const items = res.items || []
    if (reset) articles.value = items
    else articles.value.push(...items)
    if (items.length < pageSize) artNoMore.value = true
    else artPage.value++
    persistMeSnap()
    artError.value = false
  } catch {
    if (!articles.value.length) artError.value = true
  } finally {
    artLoading.value = false
  }
}

async function loadTreeholes(reset = false) {
  if (thLoading.value) return
  if (thNoMore.value && !reset) return
  thLoading.value = true
  try {
    if (reset) {
      thPage.value = 1
      thNoMore.value = false
    }
    const res = await api.me.myTreeholes({ page: thPage.value, page_size: pageSize })
    const items = res.items || []
    if (reset) treeholes.value = items
    else treeholes.value.push(...items)
    if (items.length < pageSize) thNoMore.value = true
    else thPage.value++
    persistMeSnap()
    thError.value = false
  } catch {
    if (!treeholes.value.length) thError.value = true
  } finally {
    thLoading.value = false
  }
}

function goRead(id) {
  uni.navigateTo({ url: '/pages/read/index?id=' + id })
}

function goEdit(a) {
  uni.navigateTo({ url: '/pages/write/index?id=' + a.id })
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

function editTreehole(t) {
  // 先设 editing 再开 visible,组件 watch(visible) 时才能拿到待编辑数据
  thEditing.value = { id: t.id, title: t.title, content_html: t.content_html }
  thEditorVisible.value = true
}

async function onThUpdated() {
  // 弹窗关闭不会触发 onShow,这里手动刷新当前列表(覆盖式重拉第一页)
  invalidateMe()
  await loadTreeholes(true)
}

// Tab 切换
function switchTab(key) {
  currentTab.value = key
}

function onSwiperChange(e) {
  const index = e.detail.current
  currentTab.value = index === 0 ? 'articles' : 'treeholes'
}

// 触底加载更多
function onReachArticles() {
  loadArticles()
}
function onReachTreeholes() {
  loadTreeholes()
}
function retryArticles() {
  artError.value = false
  loadArticles(true)
}
function retryTreeholes() {
  thError.value = false
  loadTreeholes(true)
}
// 下拉刷新
async function onRefreshArticles() {
  artRefreshing.value = true
  await loadArticles(true)
  artRefreshing.value = false
}
async function onRefreshTreeholes() {
  thRefreshing.value = true
  await loadTreeholes(true)
  thRefreshing.value = false
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.my-works {
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

/* Tab 样式 */
.tabs-wrapper {
  margin: 16rpx 32rpx 0;
}
.tabs-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32rpx;
  margin-bottom: 24rpx;
}
.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 40rpx;
  border-radius: 32rpx;
  background: #fff;
  box-shadow: 0 4rpx 16rpx rgba(196, 168, 130, 0.08);
  transition: all 0.3s;
}
.tab-item.active {
  background: linear-gradient(135deg, rgba(196, 168, 130, 0.95), rgba(196, 168, 130, 0.85));
  box-shadow: 0 8rpx 24rpx rgba(196, 168, 130, 0.2);
}
.tab-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #8d8d8d;
}
.tab-item.active .tab-text {
  color: #fff;
}
.tab-count {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #b0b0b0;
}
.tab-item.active .tab-count {
  color: rgba(255, 255, 255, 0.85);
}
.tabs-content {
  /* height 由 inline style 注入 */
}
.tab-content {
  height: 100%;
  padding: 0 0 60rpx;
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
.mini-right {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.mini-edit {
  font-size: 22rpx;
  color: #c4a882;
  padding: 4rpx 18rpx;
  background: rgba(196, 168, 130, 0.14);
  border-radius: 16rpx;
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

/* 骨架屏(mini 卡片) */
.sk-mtitle {
  height: 32rpx;
  width: 50%;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
}
.sk-mmeta {
  height: 22rpx;
  width: 30%;
  border-radius: 11rpx;
}

.load-more {
  padding: 24rpx 0 60rpx;
  text-align: center;
}
.load-text {
  font-size: 24rpx;
  color: #c8c8c8;
}
</style>
