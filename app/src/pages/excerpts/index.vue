<template>
  <view class="excerpts" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="topbar-title serif">摘抄本</text>
      <view class="topbar-right"></view>
    </view>

    <view class="intro">
      <text class="intro-line serif">那些舍不得忘记的句子</text>
    </view>

    <view class="list">
      <view
        v-for="(e, i) in items"
        :key="e.id"
        :class="['card', 'ex-card', i < 6 ? 'anim-rise delay-' + (i + 1) : '']"
      >
        <text class="ex-quote serif">{{ e.content }}</text>
        <view class="ex-meta">
          <text class="ex-from" v-if="e.article_title">《{{ e.article_title }}》</text>
          <text class="ex-time">{{ formatRelative(e.created_at) }}</text>
        </view>
        <view class="ex-actions">
          <view class="ex-btn card-btn" @tap="makeCard(e)">
            <text class="ex-btn-icon">✦</text>
            <text>做成卡片</text>
          </view>
          <view class="ex-btn del-btn" @tap="delExcerpt(e)">
            <text>删除</text>
          </view>
        </view>
      </view>

      <view class="load-area">
        <text v-if="loading && items.length" class="load-text">加载中…</text>
        <StateView v-else-if="error && !items.length" type="error" text="没能连上这个角落" retry @retry="reload" />
        <StateView
          v-else-if="!items.length"
          type="empty"
          text="还没有摘抄,阅读时点「摘抄」收藏喜欢的句子"
        />
        <text v-else-if="noMore" class="load-text">没有更多了 ✦</text>
      </view>
    </view>

    <!-- 卡片画布:离屏渲染(固定在视口外,不能 v-if,否则 H5 下取不到上下文) -->
    <canvas
      canvas-id="cardCanvas"
      class="card-canvas"
      :style="{ width: CARD_W + 'px', height: CARD_H + 'px' }"
    />

    <!-- 卡片预览弹层:转发 / 保存 -->
    <QuoteCardPreview :visible="cardPreview.visible" :src="cardPreview.src" @close="cardPreview.visible = false" />
  </view>
</template>

<script setup>
import { ref, getCurrentInstance } from 'vue'
import { onShow, onReachBottom } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import { formatRelative } from '../../utils/format'
import { makeQuoteCard, CARD_W, CARD_H } from '../../utils/quoteCard'
import StateView from '../../components/StateView.vue'
import QuoteCardPreview from '../../components/QuoteCardPreview.vue'

const inst = getCurrentInstance()
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const items = ref([])
const loading = ref(false)
const error = ref(false)
const page = ref(1)
const noMore = ref(false)

onShow(() => reload())
onReachBottom(() => loadMore())

async function reload() {
  page.value = 1
  noMore.value = false
  loading.value = true
  error.value = false
  try {
    const res = await api.excerpts.list({ page: 1, page_size: 20 })
    items.value = res.items || []
    if (items.value.length < 20) noMore.value = true
  } catch {
    if (!items.value.length) error.value = true
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || noMore.value) return
  loading.value = true
  try {
    const res = await api.excerpts.list({ page: page.value + 1, page_size: 20 })
    const list = res.items || []
    items.value.push(...list)
    if (list.length < 20) noMore.value = true
    else page.value++
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

function delExcerpt(e) {
  uni.showModal({
    title: '删除摘抄',
    content: '确定不再收藏这句话了吗?',
    confirmText: '删除',
    confirmColor: '#e0a8b0',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.excerpts.remove(e.id)
        items.value = items.value.filter((x) => x.id !== e.id)
      } catch {
        /* ignore */
      }
    }
  })
}

/* ---- 生成分享卡片(绘制逻辑在 utils/quoteCard.js,与阅读页选中菜单共用) ---- */
const cardPreview = ref({ visible: false, src: '' })

async function makeCard(e) {
  uni.showLoading({ title: '正在铺纸…' })
  try {
    const tempPath = await makeQuoteCard({
      canvasId: 'cardCanvas',
      proxy: inst.proxy,
      text: e.content,
      source: e.article_title || ''
    })
    uni.hideLoading()
    cardPreview.value = { visible: true, src: tempPath }
  } catch {
    uni.hideLoading()
    uni.showToast({ title: '卡片生成失败', icon: 'none' })
  }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/mine/index' })
}
</script>

<style scoped>
.excerpts {
  min-height: 100vh;
  background: #fdfbf7;
  padding-bottom: 120rpx;
}
.status-bar {
  width: 100%;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 40rpx 8rpx;
}
.back {
  width: 120rpx;
  color: #c4a882;
  font-size: 30rpx;
}
.topbar-title {
  font-size: 32rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.topbar-right {
  width: 120rpx;
}
.intro {
  padding: 20rpx 48rpx 28rpx;
}
.intro-line {
  font-size: 36rpx;
  color: #c4a882;
  letter-spacing: 2rpx;
}
.list {
  padding: 0 32rpx;
}
.ex-card {
  padding: 36rpx 40rpx;
}
.ex-quote {
  display: block;
  font-size: 30rpx;
  line-height: 1.8;
  color: #4a4a4a;
  word-break: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 6;
}
.ex-meta {
  margin-top: 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}
.ex-from {
  font-size: 22rpx;
  color: #b0b0b0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ex-time {
  font-size: 22rpx;
  color: #c8c8c8;
  flex-shrink: 0;
}
.ex-actions {
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid rgba(196, 168, 130, 0.12);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ex-btn {
  font-size: 24rpx;
  padding: 12rpx 28rpx;
  border-radius: 32rpx;
}
.ex-btn:active {
  transform: scale(0.94);
}
.card-btn {
  background: rgba(196, 168, 130, 0.14);
  color: #c4a882;
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.del-btn {
  color: #c8c8c8;
}
.load-area {
  padding: 30rpx 0 60rpx;
  text-align: center;
}
.load-text {
  font-size: 24rpx;
  color: #b8b8b8;
}
/* 离屏画布:固定在视口外参与渲染,不占布局 */
.card-canvas {
  position: fixed;
  left: -9999px;
  top: 0;
}
</style>
