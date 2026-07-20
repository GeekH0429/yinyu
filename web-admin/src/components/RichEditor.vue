<template>
  <div class="tiptap-wrap">
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
      <button type="button" class="tb" @click="pickFile('image')" title="上传图片">🖼 图片</button>
      <button type="button" class="tb" :class="{ uploading: kind === 'audio' && uploading }" @click="pickFile('audio')" title="上传音频">🎵 音频</button>
      <button type="button" class="tb" @click="pickFile('video')" title="上传视频">🎬 视频</button>
      <span class="grow"></span>
      <button type="button" class="tb" @click="editor.chain().focus().undo().run()" :disabled="!editor.can().undo()" title="撤销">↶</button>
      <button type="button" class="tb" @click="editor.chain().focus().redo().run()" :disabled="!editor.can().redo()" title="重做">↷</button>
    </div>

    <EditorContent v-if="editor" :editor="editor" class="t-content" />

    <input
      ref="fileInput"
      type="file"
      :accept="acceptMap[kind]"
      style="display: none"
      @change="onFile"
    />
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { ElMessage, ElMessageBox } from 'element-plus'
import Audio from './tiptap/Audio'
import Video from './tiptap/Video'
import { api } from '@/api'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

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
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
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
  editor.value?.destroy()
})

// ---- 文件上传 ----
const acceptMap = {
  image: 'image/*',
  audio: 'audio/*',
  video: 'video/*'
}
const kind = ref('image')
const uploading = ref(false)
const fileInput = ref()

function pickFile(k) {
  kind.value = k
  fileInput.value.value = ''
  fileInput.value.click()
}

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const data = await api.upload(file)
    const url = data.url
    const ed = editor.value
    if (!ed) return
    if (kind.value === 'image') {
      ed.chain().focus().setImage({ src: url }).run()
    } else if (kind.value === 'audio') {
      ed.chain().focus().setAudio({ src: url }).run()
    } else if (kind.value === 'video') {
      ed.chain().focus().setVideo({ src: url }).run()
    }
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
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

defineExpose({
  getHTML: () => editor.value?.getHTML()
})
</script>

<style scoped>
.tiptap-wrap {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}
.t-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-bottom: 1px solid #ececec;
  background: #fafafa;
}
.t-toolbar .grow {
  flex: 1;
}
.t-toolbar .sep {
  width: 1px;
  height: 20px;
  background: #ddd;
  margin: 0 6px;
}
.tb {
  border: 1px solid transparent;
  background: #fff;
  border-radius: 4px;
  padding: 4px 9px;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  line-height: 1.4;
}
.tb:hover {
  background: #f0f0f0;
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
  color: #666;
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
  color: #aaa;
  pointer-events: none;
  height: 0;
}
</style>
