<template>
  <view class="capsule" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="topbar-title serif">时光胶囊</text>
      <view class="topbar-right"></view>
    </view>

    <view class="intro">
      <text class="intro-line serif">把今天的心事封存起来</text>
      <text class="intro-sub">到了那一天,回来见一见写下它的自己</text>
    </view>

    <!-- 胶囊列表 -->
    <view class="list">
      <view
        v-for="(c, i) in items"
        :key="c.id"
        :class="['card', 'cap-card', 'pressable', i < 6 ? 'anim-rise delay-' + (i + 1) : '']"
        @tap="onTapCard(c)"
        @longpress="onLongPress(c)"
      >
        <view class="cap-top">
          <text class="cap-title serif">{{ c.title || '一封没有名字的信' }}</text>
          <text :class="['cap-state', { open: c.is_unlocked }]">
            {{ c.is_unlocked ? '✦ 已开启' : '🔒 封存中' }}
          </text>
        </view>
        <text class="cap-date">
          {{ c.is_unlocked ? '开启于 ' + fmtDate(c.unlock_at) : fmtDate(c.unlock_at) + ' 开启' }}
          <text v-if="!c.is_unlocked" class="cap-countdown">· 还有 {{ daysUntil(c.unlock_at) }} 天</text>
        </text>
      </view>

      <view class="load-area">
        <text v-if="loading && items.length" class="load-text">加载中…</text>
        <StateView v-else-if="error && !items.length" type="error" text="没能连上这个角落" retry @retry="reload" />
        <StateView v-else-if="!items.length" type="empty" text="还没有胶囊,封存第一封吧" />
        <text v-else-if="noMore" class="load-text">没有更多了 ✦</text>
      </view>
    </view>

    <!-- 封存一封 -->
    <view class="fab" @tap="goWrite">
      <text class="fab-icon">✎</text>
    </view>

    <!-- 已开启的信:信纸阅读浮层 -->
    <view class="letter-mask" v-if="letter.visible" @tap="closeLetter">
      <view class="letter" @tap.stop>
        <view class="letter-head">
          <text class="letter-title serif">{{ letter.title || '一封没有名字的信' }}</text>
          <text class="letter-close" @tap="closeLetter">×</text>
        </view>
        <text class="letter-meta">
          写于 {{ fmtDate(letter.createdAt) }} · {{ fmtDate(letter.unlockAt) }} 开启
        </text>
        <scroll-view scroll-y class="letter-body">
          <text class="letter-content serif">{{ letter.content }}</text>
        </scroll-view>
        <view class="letter-foot">
          <text class="letter-del" @tap="delFromLetter">删除这枚胶囊</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow, onReachBottom } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import StateView from '../../components/StateView.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const items = ref([])
const loading = ref(false)
const error = ref(false)
const page = ref(1)
const noMore = ref(false)

// 信纸浮层
const letter = ref({ visible: false, title: '', content: '', createdAt: '', unlockAt: '', id: null })

onShow(() => {
  // 从写作页回来 / 首次进入:重拉列表(数据量小,不做增量)
  reload()
})

onReachBottom(() => loadMore())

async function reload() {
  page.value = 1
  noMore.value = false
  loading.value = true
  error.value = false
  try {
    const res = await api.capsules.list({ page: 1, page_size: 20 })
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
    const res = await api.capsules.list({ page: page.value + 1, page_size: 20 })
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

function fmtDate(t) {
  if (!t) return ''
  const d = new Date(t)
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

function daysUntil(t) {
  const ms = new Date(t).getTime() - Date.now()
  return Math.max(0, Math.ceil(ms / 86400000))
}

async function onTapCard(c) {
  if (!c.is_unlocked) {
    uni.showToast({ title: '还没到时候,再等等 ✦', icon: 'none' })
    return
  }
  // 列表无 content,拉详情取信件正文
  try {
    const d = await api.capsules.get(c.id)
    if (d.sealed || d.content == null) {
      // 竞态:刚好跨过分界线,刷新列表状态
      c.is_unlocked = false
      uni.showToast({ title: '还没到时候,再等等 ✦', icon: 'none' })
      return
    }
    letter.value = {
      visible: true,
      id: c.id,
      title: d.title,
      content: d.content,
      createdAt: d.created_at,
      unlockAt: d.unlock_at
    }
  } catch {
    /* request 层已 toast */
  }
}

function onLongPress(c) {
  uni.showModal({
    title: '删除胶囊',
    content: '封存中的信删除后将永远无法开启,确定删除吗?',
    confirmText: '删除',
    confirmColor: '#e0a8b0',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.capsules.remove(c.id)
        items.value = items.value.filter((x) => x.id !== c.id)
        uni.showToast({ title: '已删除', icon: 'none' })
      } catch {
        /* ignore */
      }
    }
  })
}

function delFromLetter() {
  const id = letter.value.id
  uni.showModal({
    title: '删除胶囊',
    content: '确定删除这封已经开启的信吗?',
    confirmText: '删除',
    confirmColor: '#e0a8b0',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.capsules.remove(id)
        items.value = items.value.filter((x) => x.id !== id)
        closeLetter()
      } catch {
        /* ignore */
      }
    }
  })
}

function closeLetter() {
  letter.value.visible = false
}

function goWrite() {
  uni.navigateTo({ url: '/pages/capsule/write' })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/mine/index' })
}
</script>

<style scoped>
.capsule {
  min-height: 100vh;
  background: #fdfbf7;
  padding-bottom: 160rpx;
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
  padding: 24rpx 48rpx 32rpx;
}
.intro-line {
  display: block;
  font-size: 40rpx;
  color: #c4a882;
  letter-spacing: 2rpx;
}
.intro-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #b8b8b8;
}
.list {
  padding: 0 32rpx;
}
.cap-card {
  padding: 36rpx 40rpx;
}
.cap-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cap-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.cap-state {
  font-size: 22rpx;
  color: #b0b0b0;
}
.cap-state.open {
  color: #c4a882;
}
.cap-date {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: #b0b0b0;
}
.cap-countdown {
  color: #c4a882;
}
.load-area {
  padding: 30rpx 0 60rpx;
  text-align: center;
}
.load-text {
  font-size: 24rpx;
  color: #b8b8b8;
}
.fab {
  position: fixed;
  right: 40rpx;
  bottom: 120rpx;
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
.fab:active {
  transform: scale(0.88);
}
.fab-icon {
  color: #fff;
  font-size: 48rpx;
}
/* 信纸浮层 */
.letter-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 26, 0.55);
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}
.letter {
  width: 100%;
  max-height: 78vh;
  background: #fffdf8;
  border-radius: 32rpx;
  padding: 40rpx 44rpx;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.25);
  animation: letterIn 0.35s var(--ease-soft, ease-out) both;
}
@keyframes letterIn {
  from { opacity: 0; transform: translateY(40rpx) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.letter-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.letter-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #4a4a4a;
}
.letter-close {
  font-size: 44rpx;
  color: #b8b8b8;
  padding: 0 8rpx;
}
.letter-meta {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #b0b0b0;
}
.letter-body {
  flex: 1;
  margin-top: 28rpx;
  min-height: 200rpx;
}
.letter-content {
  font-size: 30rpx;
  line-height: 1.9;
  color: #4a4a4a;
  white-space: pre-wrap;
  word-break: break-word;
}
.letter-foot {
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid rgba(196, 168, 130, 0.15);
  text-align: center;
}
.letter-del {
  font-size: 24rpx;
  color: #e0a8b0;
}
</style>
