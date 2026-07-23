<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">{{ isEdit ? '编辑图文' : '写新图文' }}</h2>
      <span class="grow"></span>
      <el-button @click="$router.push('/articles')">返回</el-button>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      v-loading="loading"
    >
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="给这篇图文起个名字" />
      </el-form-item>

      <el-form-item label="摘要">
        <el-input
          v-model="form.summary"
          type="textarea"
          :rows="2"
          maxlength="500"
          show-word-limit
          placeholder="一句话简介(可留空)"
        />
      </el-form-item>

      <el-form-item label="封面">
        <div class="cover-zone upload-zone" ref="coverZoneRef" :class="{ 'is-dragover': coverDrag }">
          <el-upload
            :show-file-list="false"
            :before-upload="onCoverUpload"
            accept="image/*"
          >
            <div v-if="form.cover_url" class="cover-preview">
              <img :src="form.cover_url" alt="cover" />
            </div>
            <el-button v-else :icon="Picture" :loading="coverUploading">上传封面</el-button>
          </el-upload>
          <el-button v-if="form.cover_url" link type="danger" @click="form.cover_url = ''">移除</el-button>
        </div>
      </el-form-item>

      <el-form-item label="标签">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="选择或新建标签"
          style="width: 100%"
        >
          <el-option v-for="t in tagOptions" :key="t" :label="t" :value="t" />
        </el-select>
      </el-form-item>

      <el-form-item label="正文">
        <RichEditor ref="editorRef" v-model="form.content_html" style="width: 100%" />
      </el-form-item>

      <el-form-item label="状态">
        <el-radio-group v-model="form.status">
          <el-radio value="draft">草稿</el-radio>
          <el-radio value="published">发布</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">
          {{ isEdit ? '保存修改' : '创建' }}
        </el-button>
        <el-button @click="$router.push('/articles')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import RichEditor from '@/components/RichEditor.vue'
import { api } from '@/api'
import { useImageDropPaste } from '@/composables/useImageDropPaste'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const saving = ref(false)
const coverUploading = ref(false)
const coverZoneRef = ref()
const editorRef = ref()
const formRef = ref()
const tagOptions = ref([])

const form = reactive({
  title: '',
  summary: '',
  cover_url: '',
  tags: [],
  content_html: '',
  status: 'draft'
})
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

async function loadTags() {
  try {
    const res = await api.articles.tags()
    tagOptions.value = res.tags || []
  } catch {
    /* ignore */
  }
}

async function loadArticle() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const data = await api.articles.get(route.params.id)
    form.title = data.title
    form.summary = data.summary || ''
    form.cover_url = data.cover_url || ''
    form.tags = data.tags || []
    form.content_html = data.content_html || ''
    form.status = data.status
  } finally {
    loading.value = false
  }
}

async function onCoverUpload(file) {
  coverUploading.value = true
  try {
    const data = await api.upload(file)
    form.cover_url = data.url
  } catch {
    ElMessage.error('封面上传失败')
  } finally {
    coverUploading.value = false
  }
  return false
}

// 支持拖拽 / 粘贴上传封面
const { isDragover: coverDrag } = useImageDropPaste(coverZoneRef, onCoverUpload)

async function onSave() {
  await formRef.value.validate().catch(() => {})
  if (!form.title) return
  saving.value = true
  try {
    const payload = {
      title: form.title,
      summary: form.summary || null,
      cover_url: form.cover_url || null,
      tags: form.tags,
      content_html: form.content_html,
      status: form.status
    }
    if (isEdit.value) {
      await api.articles.update(route.params.id, payload)
      ElMessage.success('已保存')
    } else {
      await api.articles.create(payload)
      ElMessage.success('已创建')
    }
    router.push('/articles')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTags()
  loadArticle()
})
</script>

<style scoped>
.title {
  margin: 0;
  font-size: 18px;
}
.cover-zone {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s, box-shadow 0.15s;
}
.cover-zone.is-dragover {
  background: #fff8fb;
  box-shadow: 0 0 0 2px rgba(230, 122, 163, 0.25);
}
.cover-preview img {
  width: 220px;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}
</style>
