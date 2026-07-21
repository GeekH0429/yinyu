<template>
  <view class="read">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="topbar-title">阅读</text>
      <text class="topbar-right"></text>
    </view>

    <view class="content" v-if="article">
      <text class="title serif">{{ article.title }}</text>
      <view class="author">
        <image
          v-if="article.author && article.author.avatar_url"
          class="avatar"
          :src="resourceUrl(article.author.avatar_url)"
          mode="aspectFill"
        />
        <view v-else class="avatar placeholder">
          {{ (article.author?.nickname || '?').slice(0, 1) }}
        </view>
        <view class="author-info">
          <text class="author-name">{{ article.author?.nickname || '佚名' }}</text>
          <text class="author-time">{{ formatTime(article.published_at || article.created_at) }} · 浏览 {{ article.view_count }}</text>
        </view>
      </view>

      <view class="tags" v-if="article.tags && article.tags.length">
        <text v-for="t in article.tags" :key="t" class="tag">{{ t }}</text>
      </view>

      <view class="rich-content">
        <AudioPlayer
          v-for="audio in parsedAudioList"
          :key="audio.id"
          :src="audio.fullSrc"
        />
        <mp-html
          :content="parsedContent"
          selectable
          :domain="serverOrigin"
        />
      </view>

      <view class="actions">
        <view :class="['like-btn', { liked }]" @tap="onLike">
          <text class="like-icon">{{ liked ? '♥' : '♡' }}</text>
          <text class="like-text">{{ article.like_count }}</text>
        </view>
      </view>
    </view>

    <view class="loading" v-else-if="loading">
      <text class="load-text">轻轻翻开…</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl, SERVER_ORIGIN } from '../../config'
import { formatTime } from '../../utils/format'
import AudioPlayer from '../../components/AudioPlayer.vue'

const serverOrigin = SERVER_ORIGIN
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const article = ref(null)
const liked = ref(false)
const loading = ref(true)

// 解析音频列表
const parsedAudioList = computed(() => {
  if (!article.value?.content_html) return []

  const audioList = []
  const regex = /<audio[^>]*src=["']([^"']*)["'][^>]*>/gi
  let match
  let id = 0

  while ((match = regex.exec(article.value.content_html)) !== null) {
    const src = match[1]
    // 转换为完整 URL
    const fullSrc = resourceUrl(src)
    audioList.push({
      id: id++,
      src: src,
      fullSrc: fullSrc
    })
  }

  return audioList
})

// 移除 audio 标签后的内容
const parsedContent = computed(() => {
  if (!article.value?.content_html) return ''

  // 移除所有 audio 标签，但保留其周围的内容
  return article.value.content_html.replace(/<audio[^>]*>.*?<\/audio>|<audio[^>]*\/>/gi, (match) => {
    // 如果 audio 标签在 <p> 标签内，且没有其他内容，移除整个 <p> 标签
    if (match.startsWith('<p>')) {
      return ''
    }
    return match
  }).replace(/<p>\s*<\/p>/gi, '') // 移除空的 p 标签
})

onLoad((opts) => {
  if (opts.id) load(opts.id)
})

async function load(id) {
  loading.value = true
  try {
    article.value = await api.articles.get(id)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function onLike() {
  try {
    const res = await api.articles.like(article.value.id)
    liked.value = res.liked
    article.value.like_count += res.liked ? 1 : -1
  } catch {
    /* ignore */
  }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.reLaunch({ url: '/pages/index/index' })
}
</script>

<style scoped>
.read {
  min-height: 100vh;
  background: #fdfbf7;
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
  font-size: 30rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.topbar-right {
  width: 120rpx;
}
.content {
  padding: 24rpx 48rpx 120rpx;
}
.title {
  font-size: 48rpx;
  font-weight: 700;
  color: #4a4a4a;
  line-height: 1.4;
}
.author {
  display: flex;
  align-items: center;
  margin-top: 32rpx;
}
.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 32rpx;
}
.avatar.placeholder {
  background: #e8c4c4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
}
.author-info {
  margin-left: 18rpx;
  display: flex;
  flex-direction: column;
}
.author-name {
  font-size: 26rpx;
  color: #4a4a4a;
  font-weight: 500;
}
.author-time {
  font-size: 22rpx;
  color: #b0b0b0;
  margin-top: 4rpx;
}
.tags {
  margin: 28rpx 0 8rpx;
}
.rich-content {
  margin-top: 24rpx;
  color: #4a4a4a;
  font-size: 30rpx;
  line-height: 1.85;
}

.rich-content :deep(.mp-html) {
  color: #4a4a4a;
  font-size: 30rpx;
  line-height: 1.85;
}
.actions {
  margin-top: 48rpx;
  display: flex;
  justify-content: center;
}
.like-btn {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 18rpx 56rpx;
  background: #fff;
  border-radius: 48rpx;
  box-shadow: 0 8rpx 32rpx rgba(196, 168, 130, 0.18);
  color: #b0b0b0;
}
.like-btn.liked {
  color: #e0a8b0;
}
.like-icon {
  font-size: 36rpx;
}
.like-text {
  font-size: 28rpx;
}
.loading {
  padding: 200rpx 0;
  text-align: center;
}
.load-text {
  color: #b8b8b8;
  font-size: 26rpx;
}
</style>
