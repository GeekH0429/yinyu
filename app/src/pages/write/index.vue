<template>
  <view class="write">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 取消</text>
      <view class="type-switch">
        <text :class="['sw', { active: type === 'article' }]" @tap="type = 'article'">图文</text>
        <text :class="['sw', { active: type === 'treehole' }]" @tap="type = 'treehole'">树洞</text>
      </view>
      <text class="publish" @tap="onSubmit">{{ submitting ? '…' : '发布' }}</text>
    </view>

    <view class="form">
      <input class="title-input serif" v-model="form.title" :placeholder="type === 'treehole' ? '给这封悄悄话起个名字(可选)' : '标题'" />

      <textarea
        class="content-input"
        v-model="form.content_html"
        :placeholder="type === 'treehole' ? '写下心里话…插入的图片/音频会随正文保存' : '慢慢写,慢慢治愈…'"
        :maxlength="-1"
        auto-height
      />

      <view class="media-bar">
        <text class="media-btn" @tap="insertImage">🖼 插入图片</text>
        <text class="media-btn" @tap="insertAudio">🎵 插入音频</text>
        <text v-if="uploading" class="media-tip">上传中…</text>
      </view>

      <!-- 图文专属 -->
      <view v-if="type === 'article'" class="article-extra">
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

      <!-- 树洞专属 -->
      <view v-else class="treehole-extra">
        <view class="row">
          <text class="row-label">自定义暗号</text>
          <input class="row-input" v-model="customCode" type="number" :maxlength="6" placeholder="留空则系统随机生成 6 位" />
        </view>
        <text class="tip">树洞全量隐匿,仅凭暗号解锁;发布后请把暗号私下分享给想让他看到的人。</text>
      </view>
    </view>

    <!-- 树洞发布成功,展示暗号 -->
    <view class="mask" v-if="resultCode" @tap="resultCode = ''">
      <view class="result-card" @tap.stop>
        <text class="result-title">悄悄话已藏好 ✿</text>
        <text class="result-code">{{ resultCode }}</text>
        <text class="result-tip">这是解锁暗号,请妥善保存并私下分享</text>
        <view class="result-actions">
          <text class="r-btn" @tap="copyCode">复制暗号</text>
          <text class="r-btn primary" @tap="finish">完成</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../../api'
import { resourceUrl } from '../../config'

const statusBarHeight = ref(0)
const type = ref('article')
const submitting = ref(false)
const uploading = ref(false)
const resultCode = ref('')

const form = reactive({
  title: '',
  content_html: '',
  cover_url: '',
  summary: ''
})
const tagsText = ref('')
const customCode = ref('')

;(() => {
  const sys = uni.getSystemInfoSync()
  statusBarHeight.value = sys.statusBarHeight || 0
})()

function chooseImage() {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      success: (res) => resolve(res.tempFilePaths[0]),
      fail: reject
    })
  })
}

function pickAudio() {
  return new Promise((resolve, reject) => {
    if (typeof uni.chooseMessageFile === 'function') {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        success: (res) => resolve(res.tempFiles[0].path || res.tempFiles[0]),
        fail: reject
      })
    } else if (typeof uni.chooseFile === 'function') {
      uni.chooseFile({
        count: 1,
        success: (res) => {
          if (res.tempFilePaths) resolve(res.tempFilePaths[0])
          else resolve(res.tempFiles[0].path || res.tempFiles[0])
        },
        fail: reject
      })
    } else {
      uni.showToast({ title: '当前环境暂不支持选择音频', icon: 'none' })
      reject(new Error('no audio picker'))
    }
  })
}

async function insertImage() {
  try {
    const path = await chooseImage()
    uploading.value = true
    const data = await api.upload(path)
    form.content_html += `<p><img src="${data.url}" style="max-width:100%;border-radius:12px"/></p>`
  } catch {
    /* user cancel */
  } finally {
    uploading.value = false
  }
}

async function insertAudio() {
  try {
    const path = await pickAudio()
    uploading.value = true
    const data = await api.upload(path)
    form.content_html += `<p><audio controls src="${data.url}" style="max-width:100%"></audio></p>`
  } catch {
    /* user cancel / unsupported */
  } finally {
    uploading.value = false
  }
}

async function chooseCover() {
  try {
    const path = await chooseImage()
    uploading.value = true
    const data = await api.upload(path)
    form.cover_url = data.url
  } catch {
    /* ignore */
  } finally {
    uploading.value = false
  }
}

async function onSubmit() {
  if (submitting.value) return
  if (!form.title && type.value === 'article') {
    return uni.showToast({ title: '请填写标题', icon: 'none' })
  }
  if (!form.content_html.trim()) {
    return uni.showToast({ title: '写点什么吧', icon: 'none' })
  }
  submitting.value = true
  try {
    if (type.value === 'article') {
      const tags = tagsText.value
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean)
      await api.write.createArticle({
        title: form.title,
        summary: form.summary || null,
        cover_url: form.cover_url || null,
        tags,
        content_html: form.content_html,
        status: 'published'
      })
      uni.showToast({ title: '已发布', icon: 'success' })
      setTimeout(finish, 500)
    } else {
      const code = customCode.value && /^\d{6}$/.test(customCode.value) ? customCode.value : null
      const res = await api.write.createTreehole({
        title: form.title || null,
        content_html: form.content_html,
        code
      })
      resultCode.value = res.code
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}

function copyCode() {
  uni.setClipboardData({ data: resultCode.value })
}

function finish() {
  resultCode.value = ''
  uni.navigateBack()
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
.publish {
  width: 120rpx;
  text-align: right;
  color: #c4a882;
  font-size: 30rpx;
  font-weight: 600;
}
.type-switch {
  display: flex;
  background: #f3eee5;
  border-radius: 30rpx;
  padding: 6rpx;
}
.sw {
  padding: 8rpx 32rpx;
  font-size: 26rpx;
  color: #8d8d8d;
  border-radius: 24rpx;
}
.sw.active {
  background: #c4a882;
  color: #fff;
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
.article-extra,
.treehole-extra {
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
.tip {
  display: block;
  margin-top: 20rpx;
  color: #b0b0b0;
  font-size: 24rpx;
  line-height: 1.7;
}
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.result-card {
  width: 560rpx;
  background: #fff;
  border-radius: 48rpx;
  padding: 56rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.result-title {
  font-size: 32rpx;
  color: #88a07a;
  margin-bottom: 32rpx;
}
.result-code {
  font-size: 88rpx;
  font-weight: 700;
  color: #c4a882;
  letter-spacing: 16rpx;
  font-family: 'Menlo', monospace;
}
.result-tip {
  margin-top: 16rpx;
  color: #b0b0b0;
  font-size: 24rpx;
}
.result-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}
.r-btn {
  padding: 16rpx 48rpx;
  border-radius: 36rpx;
  font-size: 28rpx;
  background: #f3eee5;
  color: #8d8d8d;
}
.r-btn.primary {
  background: #c4a882;
  color: #fff;
}
</style>
