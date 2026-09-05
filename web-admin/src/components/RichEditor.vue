<template>
  <div class="tiptap-wrap" :class="{ 'is-dragover': isDragover }">
    <div v-if="editor" class="t-toolbar">
      <button type="button" class="tb" :class="{ active: editor.isActive('bold') }" @click="editor.chain().focus().toggleBold().run()" title="加粗"><b>B</b></button>
      <button type="button" class="tb" :class="{ active: editor.isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()" title="斜体"><i>I</i></button>
      <button type="button" class="tb" :class="{ active: editor.isActive('underline') }" @click="editor.chain().focus().toggleUnderline().run()" title="下划线"><u>U</u></button>
      <button type="button" class="tb" :class="{ active: editor.isActive('strike') }" @click="editor.chain().focus().toggleStrike().run()" title="删除线"><s>S</s></button>
      <span class="sep"></span>
      <button type="button" class="tb" :class="{ active: editor.isActive('heading', { level: 1 }) }" @click="editor.chain().focus().toggleHeading({ level: 1 }).run()">H1</button>
      <button type="button" class="tb" :class="{ active: editor.isActive('heading', { level: 2 }) }" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">H2</button>
      <button type="button" class="tb" :class="{ active: editor.isActive('heading', { level: 3 }) }" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">H3</button>
      <span class="sep"></span>
      <button type="button" class="tb" :class="{ active: editor.isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()" title="无序列表">• 列表</button>
      <button type="button" class="tb" :class="{ active: editor.isActive('orderedList') }" @click="editor.chain().focus().toggleOrderedList().run()" title="有序列表">1. 编号</button>
      <button type="button" class="tb" :class="{ active: editor.isActive('blockquote') }" @click="editor.chain().focus().toggleBlockquote().run()" title="引用">❝ 引用</button>
      <button type="button" class="tb" @click="onLink" title="链接">🔗 链接</button>
      <span class="sep"></span>
      <button type="button" class="tb" :class="{ uploading: batchTotal > batchDone }" @click="pickFile('image')" :title="batchTotal > batchDone ? `正在上传 ${batchDone}/${batchTotal} 张图片` : '上传图片（也可直接拖入）'">🖼 图片<span v-if="batchTotal > batchDone" class="count">({{ batchDone }}/{{ batchTotal }})</span></button>
      <button type="button" class="tb" :class="{ uploading: kind === 'audio' && uploading }" @click="pickFile('audio')" title="上传音频">🎵 音频</button>
      <button type="button" class="tb" @click="pickFile('video')" title="上传视频">🎬 视频</button>
      <span class="grow"></span>
      <button type="button" class="tb" @click="editor.chain().focus().undo().run()" :disabled="!editor.can().undo()" title="撤销">↶</button>
      <button type="button" class="tb" @click="editor.chain().focus().redo().run()" :disabled="!editor.can().redo()" title="重做">↷</button>
    </div>

    <EditorContent v-if="editor" :editor="editor" class="t-content" @dragleave="onDragLeave" />

    <!-- 大文件(音/视频)上传进度条;图片通常很快,不显示 -->
    <div v-if="uploadProgress.percent > 0 && uploadProgress.percent < 100" class="t-progress">
      <span class="t-progress-label">{{ uploadProgress.label }}</span>
      <el-progress
        :percentage="uploadProgress.percent"
        :stroke-width="6"
        :show-text="false"
        status="success"
      />
    </div>

    <input
      ref="fileInput"
      type="file"
      :accept="acceptMap[kind]"
      style="display: none"
      @change="onFile"
    />

    <!-- 音频信息填写:名称 / 歌手 / 封面(均可选) -->
    <el-dialog
      v-model="audioDialog.visible"
      title="音频信息"
      width="420px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form label-position="top" class="audio-form">
        <el-form-item label="音频名称">
          <el-input v-model="audioDialog.title" maxlength="100" placeholder="给这段音频起个名字(可选)" />
        </el-form-item>
        <el-form-item label="歌手 / 来源">
          <el-input v-model="audioDialog.artist" maxlength="60" placeholder="谁的作品?(可选)" />
        </el-form-item>
        <el-form-item label="封面图">
          <div class="audio-cover-wrap">
            <div class="cover-row upload-zone img-uploader img-uploader--square" ref="audioCoverZoneRef" :class="{ 'is-dragover': audioCoverDrag }">
              <el-upload
                :show-file-list="false"
                :before-upload="onCoverUpload"
                accept="image/*"
              >
                <div v-if="audioDialog.cover" class="img-uploader__filled">
                  <img :src="audioDialog.cover" alt="cover" />
                  <div class="img-uploader__mask">
                    <el-icon><Refresh /></el-icon>
                    <span>更换</span>
                  </div>
                </div>
                <div v-else class="img-uploader__empty">
                  <el-icon class="img-uploader__icon"><Picture /></el-icon>
                  <div class="img-uploader__title">上传封面</div>
                  <div class="img-uploader__hint">点击 / 拖拽 / 粘贴</div>
                </div>
              </el-upload>
            </div>
            <el-button v-if="audioDialog.cover" link type="danger" size="small" @click="audioDialog.cover = ''">移除封面</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="audioDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmAudio">插入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { Picture, Refresh } from '@element-plus/icons-vue'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { ElMessage, ElMessageBox } from 'element-plus'
import Audio from './tiptap/Audio'
import Video from './tiptap/Video'
import { api } from '@/api'
import { collectImages, useImageDropPaste } from '@/composables/useImageDropPaste'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

// emit 防抖:getHTML() 是整篇文档序列化,长文下每次击键都跑会拖慢输入。
// 300ms 合并;blur 立即 flush;保存时父组件可通过 ref 的 getHTML() 直读最新值兜底。
const EMIT_DEBOUNCE = 300
let emitTimer = null
function flushHTML() {
  clearTimeout(emitTimer)
  if (!editor.value) return
  emit('update:modelValue', editor.value.getHTML())
}
function scheduleEmit() {
  clearTimeout(emitTimer)
  emitTimer = setTimeout(flushHTML, EMIT_DEBOUNCE)
}

const editor = useEditor({
  content: props.modelValue || '',
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
      link: { openOnClick: false }
    }),
    Image.configure({ inline: false, allowBase64: true }),
    Placeholder.configure({ placeholder: '开始写作吧…把温柔的故事记下来。' }),
    Audio,
    Video
  ],
  editorProps: {
    handleDrop: (view, event) => {
      const files = collectImages(event.dataTransfer)
      if (files.length === 0) return false // 非图片交给默认处理（节点拖动等）
      event.preventDefault()
      const pos = view.posAtCoords({ left: event.clientX, top: event.clientY })?.pos ?? view.state.selection.to
      uploadImagesAt(files, pos)
      isDragover.value = false
      return true
    },
    handlePaste: (view, event) => {
      const files = collectImages(event.clipboardData)
      if (files.length === 0) return false // 非图片(纯文本等)交给默认粘贴
      event.preventDefault()
      uploadImagesAt(files, view.state.selection.to)
      return true
    },
    handleDragOver: (view, event) => {
      const items = Array.from(event.dataTransfer?.items || [])
      const hasImage = items.some(i => i.kind === 'file' && i.type.startsWith('image/'))
      if (hasImage) {
        event.preventDefault() // 允许 drop,否则不会触发 handleDrop
        isDragover.value = true
      }
    }
  },
  onUpdate: () => scheduleEmit(),
  // 失焦即 flush:点"保存"等按钮通常伴随失焦,赶在防抖窗口前同步最新值
  onBlur: () => flushHTML()
})

// 外部传入变化时同步(如加载已有文章),不触发回写
watch(
  () => props.modelValue,
  (val) => {
    if (!editor.value) return
    if (editor.value.getHTML() === val) return
    editor.value.commands.setContent(val || '', false)
  }
)

onBeforeUnmount(() => {
  clearTimeout(emitTimer)
  editor.value?.destroy()
})

// 供父组件在防抖窗口内直读最新 HTML(如保存按钮点击时),避免 300ms 内停笔丢尾部
defineExpose({ getHTML: () => editor.value?.getHTML() || '' })

// ---- 文件上传 ----
const acceptMap = {
  image: 'image/*',
  audio: 'audio/*',
  video: 'video/*'
}
const kind = ref('image')
const uploading = ref(false)
const batchDone = ref(0) // 批量拖图上传进度:已完成 / 总数(工具栏显示 X/N)
const batchTotal = ref(0)
const isDragover = ref(false) // 拖入高亮
const fileInput = ref()
// 单文件上传进度(图片几乎瞬时,主要为音视频显示)。批量拖入图片不显示进度。
const uploadProgress = reactive({ percent: 0, label: '' })
const KIND_LABEL = { image: '图片', audio: '音频', video: '视频' }

function pickFile(k) {
  kind.value = k
  fileInput.value.value = ''
  fileInput.value.click()
}

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  // 大于 500KB 才显示进度条(图片通常很快)
  const showProgress = file.size > 500 * 1024
  if (showProgress) {
    uploadProgress.label = `${KIND_LABEL[kind.value] || '文件'}上传中`
    uploadProgress.percent = 1
  }
  try {
    const data = await api.upload(file, {
      onProgress: showProgress
        ? (p) => {
            uploadProgress.percent = p
          }
        : undefined
    })
    const url = data.url
    const ed = editor.value
    if (!ed) return
    if (kind.value === 'image') {
      ed.chain().focus().setImage({ src: url }).run()
    } else if (kind.value === 'audio') {
      // 音频上传成功后,弹出信息填写(名称/歌手/封面),确认再插入卡片
      audioDialog.src = url
      audioDialog.title = ''
      audioDialog.artist = ''
      audioDialog.cover = ''
      audioDialog.visible = true
    } else if (kind.value === 'video') {
      ed.chain().focus().setVideo({ src: url }).run()
    }
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
    uploadProgress.percent = 0
    uploadProgress.label = ''
  }
}

// 拖入多图:并发上传(总时长 ≈ 最慢一张,而非逐张累加),全部完成后
// 在 drop 位置按拖入顺序一次性插入 —— 单事务插入,顺序稳定且可整批撤销;
// 失败的单张跳过并提示,不影响其余。上传期间跳走页面则放弃插入。
async function uploadImagesAt(files, startPos) {
  const ed = editor.value
  if (!ed) return
  batchTotal.value = files.length
  batchDone.value = 0
  const urls = (
    await Promise.all(
      files.map((file) =>
        api
          .upload(file)
          .then((data) => data.url)
          .catch(() => {
            ElMessage.error(`图片 "${file.name}" 上传失败`)
            return null
          })
          .finally(() => {
            batchDone.value++
          })
      )
    )
  ).filter(Boolean)
  batchTotal.value = 0
  batchDone.value = 0
  const cur = editor.value
  if (!cur || !urls.length) return
  const chain = cur.chain().focus().setTextSelection(startPos)
  urls.forEach((url) => chain.setImage({ src: url }))
  chain.run()
}

// dragleave 在子元素间切换也会触发,只有真正离开 wrapper 才清除高亮
function onDragLeave(e) {
  const wrapper = e.currentTarget
  if (!wrapper || !wrapper.contains(e.relatedTarget)) {
    isDragover.value = false
  }
}

// ---- 音频信息弹窗 ----
const audioDialog = reactive({
  visible: false,
  src: '',
  title: '',
  artist: '',
  cover: ''
})
const coverUploading = ref(false)

async function uploadAudioCover(file) {
  coverUploading.value = true
  try {
    const data = await api.upload(file)
    audioDialog.cover = data.url
  } catch {
    ElMessage.error('封面上传失败')
  } finally {
    coverUploading.value = false
  }
}

function onCoverUpload(file) {
  uploadAudioCover(file)
  return false // 阻止 el-upload 自动上传
}

// 音频封面:支持拖拽/粘贴上传(仅弹窗打开期间)
const audioCoverZoneRef = ref()
const { isDragover: audioCoverDrag } = useImageDropPaste(
  audioCoverZoneRef,
  uploadAudioCover,
  { enabled: () => audioDialog.visible }
)

function confirmAudio() {
  const ed = editor.value
  if (!ed) {
    audioDialog.visible = false
    return
  }
  ed.chain().focus().setAudio({
    src: audioDialog.src,
    title: audioDialog.title.trim(),
    artist: audioDialog.artist.trim(),
    cover: audioDialog.cover || null
  }).run()
  audioDialog.visible = false
}

async function onLink() {
  try {
    const { value } = await ElMessageBox.prompt('输入链接地址(以 http(s):// 开头)', '插入链接', {
      inputPattern: /^https?:\/\/.+/,
      inputErrorMessage: '请输入合法的链接'
    })
    const ed = editor.value
    const { empty } = ed.state.selection
    if (empty) {
      ed.chain().focus().insertContent(`<a href="${value}">${value}</a>`).run()
    } else {
      ed.chain().focus().setLink({ href: value }).run()
    }
  } catch {
    /* user cancelled */
  }
}
</script>

<style scoped>
.tiptap-wrap {
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  overflow: hidden;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.tiptap-wrap:hover {
  border-color: var(--brand-primary-light);
}
.tiptap-wrap.is-dragover {
  border-color: #e67aa3;
  box-shadow: 0 0 0 2px rgba(230, 122, 163, 0.25);
}
.tiptap-wrap.is-dragover .t-content {
  background: #fff8fb;
}
.tb .count {
  margin-left: 2px;
  font-size: 12px;
}
.t-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--brand-primary-mist);
}
.t-toolbar .grow {
  flex: 1;
}
.t-toolbar .sep {
  width: 1px;
  height: 20px;
  background: var(--border-medium);
  margin: 0 6px;
}
.tb {
  border: 1px solid transparent;
  background: var(--bg-card);
  border-radius: 6px;
  padding: 4px 9px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  line-height: 1.4;
  transition: all 0.15s ease;
}
.tb:hover {
  background: var(--brand-primary-soft);
  color: var(--text-primary);
}
.tb.active {
  background: #ffe0ec;
  border-color: #f3b6cf;
  color: #c0447a;
}
.tb:disabled {
  color: #bbb;
  cursor: not-allowed;
}
.tb.uploading {
  color: #e67aa3;
}
.t-content {
  padding: 4px 0;
  background: #fff;
}
.t-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: var(--brand-primary-mist);
  border-top: 1px solid var(--border-soft);
  font-size: 12px;
  color: var(--text-secondary);
}
.t-progress-label {
  flex-shrink: 0;
}
.t-progress :deep(.el-progress) {
  flex: 1;
  max-width: 220px;
}
.t-content :deep(.ProseMirror) {
  min-height: 420px;
  padding: 12px 16px;
  outline: none;
}
.t-content :deep(.ProseMirror) img {
  max-width: 100%;
  border-radius: 4px;
}
.t-content :deep(.ProseMirror) audio {
  width: 100%;
}
.t-content :deep(.ProseMirror) .yinyu-audio audio {
  width: 100%;
  margin-top: 2px;
}
.t-content :deep(.ProseMirror) video {
  max-width: 100%;
  border-radius: 4px;
}
.t-content :deep(.ProseMirror) h1 {
  font-size: 1.6em;
  margin: 0.6em 0 0.3em;
}
.t-content :deep(.ProseMirror) h2 {
  font-size: 1.35em;
  margin: 0.6em 0 0.3em;
}
.t-content :deep(.ProseMirror) h3 {
  font-size: 1.15em;
  margin: 0.6em 0 0.3em;
}
.t-content :deep(.ProseMirror) blockquote {
  border-left: 3px solid #ffd6e7;
  padding-left: 12px;
  color: var(--text-secondary);
  margin: 0.5em 0;
}
.t-content :deep(.ProseMirror) ul,
.t-content :deep(.ProseMirror) ol {
  padding-left: 22px;
  margin: 0.4em 0;
}
.t-content :deep(.ProseMirror) a {
  color: #e67aa3;
}
/* 占位符 */
.t-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--text-tertiary);
  pointer-events: none;
  height: 0;
}
/* 音频信息弹窗 */
.audio-form {
  padding-bottom: 4px;
}
.upload-zone {
  border-radius: 12px;
  transition: background 0.15s, box-shadow 0.15s;
}
.audio-cover-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
/* cover-row 的尺寸/dragover 由全局 .img-uploader 控制 */
</style>
