<template>
  <view class="write" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back pressable" @tap="goBack">‹ 取消</text>
      <text class="topbar-title serif">{{ isEdit ? '编辑图文' : '写图文' }}</text>
      <text class="publish pressable" @tap="onSubmit">{{ submitting ? '…' : scheduleMode ? '定时' : isEdit ? '保存' : '发布' }}</text>
    </view>

    <view class="form anim-fade" v-if="!loadingDetail">
      <input class="title-input serif" v-model="form.title" placeholder="标题" @input="markDirty" />

      <textarea
        class="content-input"
        v-model="form.content_html"
        placeholder="慢慢写,慢慢治愈…"
        :maxlength="-1"
        auto-height
        :cursor-spacing="120"
        :adjust-position="true"
        @input="markDirty"
      />

      <view class="media-bar">
        <text class="media-btn pressable" @tap="insertImage">🖼 插入图片</text>
        <text class="media-btn pressable" @tap="insertAudio">🎵 插入音频</text>
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
          <text v-else class="cover-add pressable" @tap="chooseCover">+ 选择封面</text>
        </view>
        <view class="row">
          <text class="row-label">摘要</text>
          <input class="row-input" v-model="form.summary" placeholder="一句话简介(可选)" @input="markDirty" />
        </view>
        <view class="row">
          <text class="row-label">标签</text>
          <input class="row-input" v-model="tagsText" placeholder="逗号分隔,如 治愈,夜读" @input="markDirty" />
        </view>
        <view v-if="scheduleMode" class="row">
          <text class="row-label">发布时间</text>
          <picker class="schedule-picker" mode="date" :value="scheduleDate" @change="onDateChange">
            <view class="picker-value">{{ scheduleDate || '选择日期' }}</view>
          </picker>
          <picker class="schedule-picker" mode="time" :value="scheduleTime" @change="onTimeChange">
            <view class="picker-value">{{ scheduleTime || '选择时间' }}</view>
          </picker>
          <text class="schedule-cancel pressable" @tap="cancelSchedule">取消</text>
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { onLoad, onBackPress } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
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
// 用户改动标记:取消离开时据此弹二次确认,防误触丢失内容
const dirty = ref(false)
function markDirty() {
  dirty.value = true
}

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

// 定时发布:actionSheet 选「定时发布」后展开时间行,填好后再点右上角提交
const scheduleMode = ref(false)
const scheduleDate = ref('')
const scheduleTime = ref('')

function onDateChange(e) {
  scheduleDate.value = e.detail.value
}
function onTimeChange(e) {
  scheduleTime.value = e.detail.value
}
function cancelSchedule() {
  scheduleMode.value = false
  scheduleDate.value = ''
  scheduleTime.value = ''
}

function buildScheduledAt() {
  // 'YYYY-MM-DD' + 'HH:mm' 按设备本地时区解析,toISOString() 自带 +08:00 offset
  const d = new Date(`${scheduleDate.value}T${scheduleTime.value}`)
  if (isNaN(d.getTime())) return null
  return d.toISOString()
}

// 音频信息弹窗:选完音频上传后弹出,填写 名称/歌手/封面 再插入卡片
const audioPopup = reactive({ visible: false, src: '' })

onLoad((opts) => {
  // 带 id 进入即编辑模式:拉取详情回显
  if (opts && opts.id) {
    articleId.value = Number(opts.id)
    isEdit.value = true
    loadDetail(articleId.value)
  } else if (opts && opts.prefill) {
    // 来自「暖话」:把文本预填到正文,方便以此为开头展开
    form.content_html = decodeURIComponent(opts.prefill)
    markDirty()
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
    if (a.status === 'scheduled' && a.scheduled_at) {
      const d = new Date(a.scheduled_at)
      const pad = (n) => String(n).padStart(2, '0')
      scheduleMode.value = true
      scheduleDate.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
      scheduleTime.value = `${pad(d.getHours())}:${pad(d.getMinutes())}`
    }
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
    markDirty()
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
  markDirty()
  uni.showToast({ title: '已加入', icon: 'success' })
}

async function chooseCover() {
  try {
    form.cover_url = await uploadPicked(await chooseImage())
    markDirty()
  } catch {
    /* ignore */
  }
}

function onSubmit() {
  if (submitting.value) return
  if (!form.title) {
    return uni.showToast({ title: '请填写标题', icon: 'none' })
  }
  if (!form.content_html.trim()) {
    return uni.showToast({ title: '写点什么吧', icon: 'none' })
  }
  // 已选「定时发布」:填好时间后再次点右上角即提交
  if (scheduleMode.value) {
    submitWith('scheduled')
    return
  }
  uni.showActionSheet({
    itemList: ['立即发布', '定时发布', '存草稿'],
    success: ({ tapIndex }) => {
      if (tapIndex === 0) submitWith('published')
      else if (tapIndex === 1) {
        scheduleMode.value = true
        uni.showToast({ title: '请选择发布时间', icon: 'none' })
      } else submitWith('draft')
    }
  })
}

async function submitWith(status) {
  let scheduledAt = null
  if (status === 'scheduled') {
    if (!scheduleDate.value || !scheduleTime.value) {
      return uni.showToast({ title: '请选择日期和时间', icon: 'none' })
    }
    scheduledAt = buildScheduledAt()
    if (!scheduledAt || new Date(scheduledAt).getTime() <= Date.now() + 60000) {
      return uni.showToast({ title: '时间需晚于当前 1 分钟', icon: 'none' })
    }
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
      content_html: normalizeContentHtml(form.content_html),
      status,
      scheduled_at: scheduledAt
    }
    const doneMsg =
      status === 'scheduled' ? '已定时' : status === 'draft' ? '已存草稿' : '已发布'
    if (isEdit.value) {
      const fresh = await api.write.updateArticle(articleId.value, payload)
      setArticleSnap(articleId.value, fresh) // 阅读页 SWR 快照同步更新
      invalidateMe()
      invalidateFeed()
      uni.showToast({ title: doneMsg, icon: 'success' })
    } else {
      await api.write.createArticle(payload)
      invalidateFeed()
      invalidateMe()
      uni.showToast({ title: doneMsg, icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 500)
  } catch {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}

function goBack() {
  if (!dirty.value) return uni.navigateBack()
  uni.showModal({
    title: '还没保存',
    content: '离开会丢失已写的内容,确定吗?',
    confirmText: '离开',
    cancelText: '继续写',
    success: (r) => {
      if (r.confirm) uni.navigateBack()
    }
  })
}

// App 端:拦截物理返回 / 系统返回手势,触发与「取消」按钮一致的二次确认
// H5 端 onBackPress 不触发 SPA 内的后退,改用 beforeunload 兜底(关闭/刷新提示)
onBackPress((e) => {
  // e.from === 'navigateBack' 时是上面 goBack 已经 confirm 后主动 navigateBack,
  // 此时不要再拦,否则会循环。其它来源(backbutton)按 dirty 判断
  if (e && e.from === 'navigateBack') return false
  if (!dirty.value) return false
  goBack()
  return true // 拦截,自己处理
})

// H5 兜底:用户改动后关闭/刷新页面时,浏览器原生确认(SPA 内的后退浏览器不允许真正拦截)
function onBeforeUnload(e) {
  // #ifdef H5
  if (!dirty.value) return
  e.preventDefault()
  e.returnValue = ''
  // #endif
}
onMounted(() => {
  // #ifdef H5
  if (typeof window !== 'undefined') window.addEventListener('beforeunload', onBeforeUnload)
  // #endif
})
onUnmounted(() => {
  // #ifdef H5
  if (typeof window !== 'undefined') window.removeEventListener('beforeunload', onBeforeUnload)
  // #endif
})
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
  border-bottom: 2rpx solid transparent;
  transition: border-color var(--t-fast, 0.2s) var(--ease-soft, cubic-bezier(0.25, 0.46, 0.45, 0.94));
}
.title-input:focus {
  border-bottom-color: rgba(196, 168, 130, 0.4);
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
.schedule-picker {
  margin-right: 24rpx;
}
.picker-value {
  padding: 8rpx 20rpx;
  background: #f3eee5;
  color: #4a4a4a;
  border-radius: 12rpx;
  font-size: 26rpx;
}
.schedule-cancel {
  margin-left: auto;
  color: #8d8d8d;
  font-size: 26rpx;
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
