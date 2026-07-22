<template>
  <view>
    <!-- 写 / 编辑树洞弹窗(暗黑) -->
    <view class="mask" v-if="visible" @tap="close">
      <view class="pub-modal" @tap.stop>
        <view class="pub-head">
          <text class="pub-title serif">{{ isEdit ? '编辑悄悄话' : '写一封悄悄话' }}</text>
          <text class="pub-close" @tap="close">✕</text>
        </view>

        <!-- 创建成功:展示暗号(仅创建模式) -->
        <view v-if="!isEdit && pubResult" class="pub-result">
          <text class="pub-result-tip">已藏好 ✿ 它的暗号是</text>
          <text class="pub-result-code">{{ pubResult }}</text>
          <text class="pub-result-sub">把暗号私下分享给想让他看到的人</text>
          <view class="pub-result-actions">
            <text class="r-btn" @tap="copyResult">复制</text>
            <text class="r-btn primary" @tap="unlockResult">立即查看</text>
          </view>
        </view>

        <!-- 编辑 / 表单 -->
        <view v-else class="pub-form">
          <input class="pub-input" v-model="pub.title" placeholder="标题(可选)" />
          <textarea
            class="pub-textarea"
            v-model="pub.content_html"
            placeholder="说出心里话…"
            :maxlength="-1"
            auto-height
          />
          <view class="pub-media">
            <text class="pub-mbtn" @tap="pubInsertImage">🖼 图片</text>
            <text class="pub-mbtn" @tap="pubInsertAudio">🎵 音频</text>
            <text :class="['pub-mbtn', { rec: recording }]" @tap="toggleRecord">{{ recording ? '⏹ 停止' : '🎤 录音' }}</text>
            <text v-if="pubUploading" class="pub-up">上传中…</text>
          </view>
          <view class="pub-rec" v-if="recording">
            <text class="pub-rec-dot">●</text>
            <text class="pub-rec-time">{{ formatRecSecs(recSecs) }}</text>
            <text class="pub-rec-tip">录音中…点「停止」结束并插入正文</text>
          </view>
          <!-- 暗号仅创建时可设;编辑模式下暗号由「换暗号」单独管理 -->
          <view class="pub-code-row" v-if="!isEdit">
            <input
              class="pub-code-input"
              v-model="pub.code"
              type="number"
              :maxlength="6"
              placeholder="留空随机生成 6 位暗号"
            />
            <text class="pub-random" @tap="randomCode">🎲</text>
          </view>
          <button class="pub-submit" :loading="pubSubmitting" @tap="pubSubmit">{{ isEdit ? '保存修改' : '藏进树洞' }}</button>
        </view>
      </view>
    </view>

    <!-- 纸飞机寄向远方:仅创建成功动画 -->
    <FlyAwayOverlay v-if="!isEdit" :playing="flyPlaying" @done="onFlyDone" />

    <!-- 音频信息弹窗(z-index 2000,盖在发布弹窗 1000 之上) -->
    <AudioInfoPopup v-model:visible="audioPopup.visible" :src="audioPopup.src" @confirm="onAudioConfirm" />
  </view>
</template>

<script setup>
/**
 * 树洞写作 / 编辑共用组件。
 * - editing 为空 → 创建模式:原发布流程(暗号展示 + 纸飞机 + 立即查看)。
 * - editing = {id,title,content_html} → 编辑模式:回显,提交走 updateTreehole,
 *   无暗号展示 / 无纸飞机,成功 Toast「已保存」并关闭。
 *
 * 由 treehole 页(创建)与 mine 页(编辑)共用,避免两处重复一套上传/录音/音频逻辑。
 */
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { chooseImage, pickAudio } from '../utils/pick'
import { buildAudioCard } from '../utils/audioCard'
import { normalizeContentHtml } from '../utils/content'
import { startRecord, stopRecord, cancelRecord } from '../utils/recorder'
import FlyAwayOverlay from './FlyAwayOverlay.vue'
import AudioInfoPopup from './AudioInfoPopup.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  editing: { type: Object, default: null } // {id, title, content_html}
})
const emit = defineEmits(['update:visible', 'published', 'updated', 'unlock'])

const isEdit = computed(() => !!(props.editing && props.editing.id))

const pub = reactive({ title: '', content_html: '', code: '' })
const audioPopup = reactive({ visible: false, src: '' })
const pubUploading = ref(false)
const pubSubmitting = ref(false)
const pubResult = ref('')
const flyPlaying = ref(false)
const recording = ref(false)
const recSecs = ref(0)

// 打开时按模式回显(编辑)或重置(创建)。调用方需先设 editing 再置 visible=true。
watch(
  () => props.visible,
  (v) => {
    if (!v) return
    if (isEdit.value) {
      pub.title = props.editing.title || ''
      pub.content_html = props.editing.content_html || ''
      pub.code = ''
      pubResult.value = ''
    } else {
      resetPub()
    }
  }
)

function close() {
  if (recording.value) {
    recording.value = false
    cancelRecord()
  }
  flyPlaying.value = false
  emit('update:visible', false)
}

async function uploadPicked(path) {
  pubUploading.value = true
  try {
    return (await api.upload(path)).url
  } finally {
    pubUploading.value = false
  }
}

async function pubInsertImage() {
  try {
    const url = await uploadPicked(await chooseImage())
    pub.content_html += `<p><img src="${url}" style="max-width:100%;border-radius:12px"/></p>`
  } catch {
    /* cancel */
  }
}

async function pubInsertAudio() {
  try {
    const url = await uploadPicked(await pickAudio())
    // 上传成功后弹音频信息(名称/歌手/封面),确认再插入卡片
    audioPopup.src = url
    audioPopup.visible = true
  } catch {
    /* cancel / unsupported */
  }
}

function onAudioConfirm({ title, artist, cover }) {
  pub.content_html += buildAudioCard({ src: audioPopup.src, title, artist, cover })
  uni.showToast({ title: '已加入', icon: 'success' })
}

async function toggleRecord() {
  if (!recording.value) {
    try {
      recSecs.value = 0
      await startRecord({ onTick: (s) => (recSecs.value = s) })
      recording.value = true
    } catch {
      uni.showToast({ title: '无法访问麦克风', icon: 'none' })
    }
    return
  }
  // 停止 → 上传 → 弹音频信息(名称/歌手/封面)→ 确认插入卡片
  recording.value = false
  try {
    const r = await stopRecord()
    if (!r.duration) return
    pubUploading.value = true
    const data = await api.uploadRecorded(r)
    audioPopup.src = data.url
    audioPopup.visible = true
  } catch {
    /* ignore */
  } finally {
    pubUploading.value = false
    recSecs.value = 0
  }
}

function formatRecSecs(s) {
  const m = Math.floor(s / 60)
  const ss = s % 60
  return `${m}:${String(ss).padStart(2, '0')}`
}

function randomCode() {
  let s = ''
  for (let i = 0; i < 6; i++) s += Math.floor(Math.random() * 10)
  pub.code = s
}

async function pubSubmit() {
  if (!pub.content_html.trim()) {
    return uni.showToast({ title: '写点什么吧', icon: 'none' })
  }
  pubSubmitting.value = true
  try {
    if (isEdit.value) {
      const res = await api.write.updateTreehole(props.editing.id, {
        title: pub.title || null,
        content_html: normalizeContentHtml(pub.content_html)
      })
      uni.showToast({ title: '已保存', icon: 'success' })
      emit('updated', res)
      close()
    } else {
      const code = pub.code && /^\d{6}$/.test(pub.code) ? pub.code : null
      const res = await api.write.createTreehole({
        title: pub.title || null,
        content_html: normalizeContentHtml(pub.content_html),
        code
      })
      pubResult.value = res.code
      flyPlaying.value = true // 放飞纸飞机,动画结束后由 onFlyDone 复位
      emit('published', res.code)
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    pubSubmitting.value = false
  }
}

function onFlyDone() {
  flyPlaying.value = false
}

function copyResult() {
  uni.setClipboardData({ data: pubResult.value })
}

function unlockResult() {
  // 用刚生成的暗号触发外层解锁(由树洞页执行解锁动画)
  const code = pubResult.value
  emit('unlock', code)
  close()
}

function resetPub() {
  pub.title = ''
  pub.content_html = ''
  pub.code = ''
  pubResult.value = ''
}
</script>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.pub-modal {
  width: 620rpx;
  max-height: 86vh;
  overflow-y: auto;
  background: #1a1a24;
  border-radius: 40rpx;
  padding: 48rpx 40rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.5);
}
.pub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}
.pub-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #e0e0e0;
}
.pub-close {
  font-size: 40rpx;
  color: #555568;
  padding: 0 8rpx;
}
.pub-input {
  width: 100%;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  color: #c8c8d8;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}
.pub-textarea {
  width: 100%;
  min-height: 280rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 24rpx;
  font-size: 30rpx;
  line-height: 1.7;
  color: #c8c8d8;
  box-sizing: border-box;
}
.pub-media {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 20rpx 0;
}
.pub-mbtn {
  padding: 12rpx 24rpx;
  background: rgba(123, 140, 196, 0.12);
  color: #7b8cc4;
  border-radius: 20rpx;
  font-size: 26rpx;
}
.pub-up {
  color: #7b8cc4;
  font-size: 24rpx;
}
.pub-mbtn.rec {
  background: rgba(224, 112, 112, 0.15);
  color: #e07070;
}
.pub-rec {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 16rpx;
  padding: 16rpx 20rpx;
  background: rgba(123, 140, 196, 0.08);
  border-radius: 16rpx;
}
.pub-rec-dot {
  color: #e07070;
  font-size: 24rpx;
  animation: recBlink 1s infinite;
}
@keyframes recBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.pub-rec-time {
  color: #c0c8e0;
  font-size: 28rpx;
  font-family: 'Menlo', monospace;
}
.pub-rec-tip {
  color: #555568;
  font-size: 22rpx;
}
.pub-code-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 28rpx;
}
.pub-code-input {
  flex: 1;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.04);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  padding: 0 24rpx;
  font-size: 32rpx;
  letter-spacing: 8rpx;
  color: #c8c8d8;
  box-sizing: border-box;
}
.pub-random {
  width: 80rpx;
  height: 80rpx;
  background: rgba(123, 140, 196, 0.12);
  border: 2rpx solid #333348;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.pub-submit {
  width: 100%;
  height: 92rpx;
  line-height: 92rpx;
  background: linear-gradient(135deg, #3d4466 0%, #7b8cc4 100%);
  color: #fff;
  border-radius: 46rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
}
.pub-submit::after {
  border: none;
}

/* 发布成功 */
.pub-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 0;
}
.pub-result-tip {
  color: #7b8cc4;
  font-size: 28rpx;
}
.pub-result-code {
  font-size: 88rpx;
  font-weight: 700;
  letter-spacing: 16rpx;
  color: #c0c8e0;
  font-family: 'Menlo', monospace;
  margin: 24rpx 0 12rpx;
}
.pub-result-sub {
  color: #555568;
  font-size: 24rpx;
  text-align: center;
}
.pub-result-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}
.r-btn {
  padding: 16rpx 48rpx;
  border-radius: 36rpx;
  font-size: 28rpx;
  background: rgba(255, 255, 255, 0.06);
  color: #c8c8d8;
}
.r-btn.primary {
  background: linear-gradient(135deg, #3d4466 0%, #7b8cc4 100%);
  color: #fff;
}
</style>
