<template>
  <view class="write">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 取消</text>
      <text class="topbar-title serif">{{ isEdit ? '编辑图文' : '写图文' }}</text>
      <text class="publish" @tap="onSubmit">{{ submitting ? '…' : isEdit ? '保存' : '发布' }}</text>
    </view>

    <view class="form" v-if="!loadingDetail">
      <input class="title-input serif" v-model="form.title" placeholder="标题" />

      <textarea
        class="content-input"
        v-model="form.content_html"
        placeholder="慢慢写,慢慢治愈…"
        :maxlength="-1"
        auto-height
      />

      <view class="media-bar">
        <text class="media-btn" @tap="insertImage">🖼 插入图片</text>
        <text class="media-btn" @tap="insertAudio">🎵 插入音频</text>
        <text v-if="uploading" class="media-tip">上传中…</text>
      </view>

      <view class="article-extra">
        <view class="row">
          <text class="row-label">封面</text>
          <image
            v-if="form.cover_url"
            class="cover-thumb"
            :src="resourceUrl(form.cover_url)"
            mode="aspectFill"
            @tap="chooseCover"
          />
          <text v-else class="cover-add" @tap="chooseCover">+ 选择封面</text>
        </view>
        <view class="row">
          <text class="row-label">摘要</text>
          <input class="row-input" v-model="form.summary" placeholder="一句话简介(可选)" />
        </view>
        <view class="row">
          <text class="row-label">标签</text>
          <input class="row-input" v-model="tagsText" placeholder="逗号分隔,如 治愈,夜读" />
        </view>
      </view>
    </view>

    <view class="loading" v-else>
      <text class="load-text">正在打开…</text>
    </view>

    <AudioInfoPopup v-model:visible="audioPopup.visible" :src="audioPopup.src" @confirm="onAudioConfirm" />
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '../../api'
import { resourceUrl } from '../../config'
import { chooseImage, pickAudio } from '../../utils/pick'
import { buildAudioCard } from '../../utils/audioCard'
import { normalizeContentHtml } from '../../utils/content'
import { invalidateFeed } from '../../store/feed'
import { invalidateMe } from '../../store/me'
import { setArticleSnap } from '../../utils/articleCache'
import AudioInfoPopup from '../../components/AudioInfoPopup.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)
const submitting = ref(false)
const uploading = ref(false)

const articleId = ref(null)
const isEdit = ref(false)
const loadingDetail = ref(false)

const form = reactive({
  title: '',
  content_html: '',
  cover_url: '',
  summary: ''
})
const tagsText = ref('')

// 音频信息弹窗:选完音频上传后弹出,填写 名称/歌手/封面 再插入卡片
const audioPopup = reactive({ visible: false, src: '' })

onLoad((opts) => {
  // 带 id 进入即编辑模式:拉取详情回显
  if (opts && opts.id) {
    articleId.value = Number(opts.id)
    isEdit.value = true
    loadDetail(articleId.value)
  }
})

async function loadDetail(id) {
  loadingDetail.value = true
  try {
    const a = await api.articles.get(id)
    form.title = a.title || ''
    form.content_html = a.content_html || ''
    form.cover_url = a.cover_url || ''
    form.summary = a.summary || ''
    tagsText.value = (a.tags || []).join(',')
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loadingDetail.value = false
  }
}

async function uploadPicked(path) {
  uploading.value = true
  try {
    return (await api.upload(path)).url
  } finally {
    uploading.value = false
  }
}

async function insertImage() {
  try {
    const url = await uploadPicked(await chooseImage())
    form.content_html += `<p><img src="${url}" style="max-width:100%;border-radius:12px"/></p>`
  } catch {
    /* user cancel */
  }
}

async function insertAudio() {
  try {
    const url = await uploadPicked(await pickAudio())
    // 上传成功后弹音频信息(名称/歌手/封面),确认再插入卡片
    audioPopup.src = url
    audioPopup.visible = true
  } catch {
    /* user cancel / unsupported */
  }
}

function onAudioConfirm({ title, artist, cover }) {
  form.content_html += buildAudioCard({ src: audioPopup.src, title, artist, cover })
  uni.showToast({ title: '已加入', icon: 'success' })
}

async function chooseCover() {
  try {
    form.cover_url = await uploadPicked(await chooseImage())
  } catch {
    /* ignore */
  }
}

async function onSubmit() {
  if (submitting.value) return
  if (!form.title) {
    return uni.showToast({ title: '请填写标题', icon: 'none' })
  }
  if (!form.content_html.trim()) {
    return uni.showToast({ title: '写点什么吧', icon: 'none' })
  }
  submitting.value = true
  try {
    const tags = tagsText.value
      .split(/[,，]/)
      .map((t) => t.trim())
      .filter(Boolean)
    const payload = {
      title: form.title,
      summary: form.summary || null,
      cover_url: form.cover_url || null,
      tags,
      content_html: normalizeContentHtml(form.content_html)
    }
    if (isEdit.value) {
      // 编辑:不传 status,保持原文(草稿/已发布)状态不变
      const fresh = await api.write.updateArticle(articleId.value, payload)
      setArticleSnap(articleId.value, fresh) // 阅读页 SWR 快照同步更新
      invalidateMe()
      invalidateFeed()
      uni.showToast({ title: '已保存', icon: 'success' })
    } else {
      await api.write.createArticle({ ...payload, status: 'published' })
      invalidateFeed()
      invalidateMe()
      uni.showToast({ title: '已发布', icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 500)
  } catch {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.write {
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
  padding: 16rpx 40rpx 16rpx;
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.12);
}
.back {
  width: 120rpx;
  color: #8d8d8d;
  font-size: 30rpx;
}
.topbar-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #4a4a4a;
}
.publish {
  width: 120rpx;
  text-align: right;
  color: #c4a882;
  font-size: 30rpx;
  font-weight: 600;
}
.form {
  padding: 32rpx 48rpx;
}
.title-input {
  width: 100%;
  font-size: 44rpx;
  font-weight: 700;
  color: #4a4a4a;
  padding: 12rpx 0;
}
.content-input {
  width: 100%;
  min-height: 360rpx;
  margin-top: 24rpx;
  font-size: 30rpx;
  line-height: 1.8;
  color: #4a4a4a;
  text-align: left;
}
.media-bar {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin: 32rpx 0;
  padding: 20rpx 0;
  border-top: 1rpx solid rgba(196, 168, 130, 0.12);
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.12);
}
.media-btn {
  padding: 12rpx 28rpx;
  background: #f3eee5;
  color: #88a07a;
  border-radius: 28rpx;
  font-size: 26rpx;
}
.media-tip {
  color: #c4a882;
  font-size: 24rpx;
}
.article-extra {
  margin-top: 8rpx;
}
.row {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.1);
}
.row-label {
  width: 160rpx;
  color: #8d8d8d;
  font-size: 28rpx;
}
.row-input {
  flex: 1;
  font-size: 28rpx;
  color: #4a4a4a;
}
.cover-thumb {
  width: 160rpx;
  height: 100rpx;
  border-radius: 16rpx;
}
.cover-add {
  color: #c4a882;
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
