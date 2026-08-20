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
        <div class="cover-wrap">
          <div
            class="cover-zone upload-zone img-uploader img-uploader--landscape"
            ref="coverZoneRef"
            :class="{ 'is-dragover': coverDrag }"
          >
            <el-upload
              :show-file-list="false"
              :before-upload="onCoverUpload"
              accept="image/*"
            >
              <div v-if="form.cover_url" class="img-uploader__filled">
                <img :src="form.cover_url" alt="cover" />
                <div class="img-uploader__mask">
                  <el-icon><Refresh /></el-icon>
                  <span>更换封面</span>
                </div>
              </div>
              <div v-else class="img-uploader__empty">
                <el-icon class="img-uploader__icon"><Picture /></el-icon>
                <div class="img-uploader__title">点击上传封面</div>
                <div class="img-uploader__hint">支持拖拽到此处 · Ctrl+V 粘贴</div>
              </div>
            </el-upload>
          </div>
          <el-button
            v-if="form.cover_url"
            link
            type="danger"
            size="small"
            @click="form.cover_url = ''"
          >移除封面</el-button>
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
        <RichEditor v-model="form.content_html" style="width: 100%" />
      </el-form-item>

      <el-form-item label="状态">
        <el-radio-group v-model="form.status">
          <el-radio value="draft">草稿</el-radio>
          <el-radio value="published">发布</el-radio>
          <el-radio value="scheduled">定时发布</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.status === 'scheduled'" label="发布时间">
        <div class="schedule-wrap">
          <el-date-picker
            v-model="scheduledAt"
            type="datetime"
            placeholder="选择定时发布时间"
            :disabled-date="(d) => d.getTime() < Date.now() - 86400000"
          />
          <div class="schedule-hint">到设定时间后自动发布,期间文章仅自己可见</div>
        </div>
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
import { Picture, Refresh } from '@element-plus/icons-vue'
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
const scheduledAt = ref(null)
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
    scheduledAt.value = data.scheduled_at ? new Date(data.scheduled_at) : null
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
  if (form.status === 'scheduled') {
    if (!scheduledAt.value) return ElMessage.warning('请选择定时发布时间')
    if (scheduledAt.value.getTime() <= Date.now() + 60000) {
      return ElMessage.warning('定时发布时间需晚于当前时间 1 分钟')
    }
  }
  saving.value = true
  try {
    const payload = {
      title: form.title,
      summary: form.summary || null,
      cover_url: form.cover_url || null,
      tags: form.tags,
      content_html: form.content_html,
      status: form.status,
      scheduled_at: form.status === 'scheduled' ? scheduledAt.value.toISOString() : null
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
.cover-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
.cover-zone {
  /* 尺寸/dragover 由全局 .img-uploader 控制 */
}
.schedule-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.schedule-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
