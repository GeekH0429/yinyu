<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">每日一图</h2>
      <span class="grow"></span>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增排期</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column label="日期" width="130">
        <template #default="{ row }">
          <el-tag :type="dateTagType(row.publish_date)" size="small">
            {{ row.publish_date }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="图片" width="130">
        <template #default="{ row }">
          <el-image
            :src="row.image_url"
            style="width: 96px; height: 60px; border-radius: 4px"
            fit="cover"
            :preview-src-list="[row.image_url]"
            preview-teleported
          />
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button text type="danger" @click="onRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end; display: flex"
      @current-change="loadData"
      @size-change="loadData"
    />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑排期' : '新增排期'" width="480px">
      <el-alert
        v-if="formError"
        :title="formError"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
        <el-form-item label="日期" prop="publish_date">
          <el-date-picker
            v-model="form.publish_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择排期日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="图片" prop="image_url">
          <div class="image-zone upload-zone" ref="imageZoneRef" :class="{ 'is-dragover': imageDrag }">
            <el-upload
              :show-file-list="false"
              :before-upload="onImageUpload"
              accept="image/*"
            >
              <div v-if="form.image_url" class="img-preview">
                <img :src="form.image_url" alt="daily" />
              </div>
              <el-button v-else :icon="Picture" :loading="uploading">上传图片</el-button>
            </el-upload>
            <el-button v-if="form.image_url" link type="danger" @click="form.image_url = ''">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="给这张图起个名字" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            maxlength="500"
            show-word-limit
            placeholder="一句话描述(可留空)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { Plus, Picture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useImageDropPaste } from '@/composables/useImageDropPaste'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const uploading = ref(false)
const imageZoneRef = ref()
const formRef = ref()
const formError = ref('')
let formErrorTimer = null
function setFormError(msg) {
  clearTimeout(formErrorTimer)
  formError.value = msg
  // 5 秒后自动消失,不常驻;再次报错会刷新计时器
  formErrorTimer = setTimeout(() => {
    formError.value = ''
  }, 5000)
}
function clearFormError() {
  clearTimeout(formErrorTimer)
  formError.value = ''
}
onBeforeUnmount(clearFormError)
const form = reactive({
  publish_date: '',
  image_url: '',
  title: '',
  description: ''
})
const rules = {
  publish_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  image_url: [{ required: true, message: '请上传图片', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

// 与服务端一致:按北京时间算"今天"
function cnTodayStr() {
  const now = new Date()
  const cn = new Date(now.getTime() + (now.getTimezoneOffset() + 8 * 60) * 60000)
  const y = cn.getFullYear()
  const m = String(cn.getMonth() + 1).padStart(2, '0')
  const d = String(cn.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function dateTagType(d) {
  if (!d) return 'info'
  const today = cnTodayStr()
  if (d === today) return 'success'
  if (d > today) return 'warning'
  return 'info'
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.admin.dailyList({ page: page.value, page_size: pageSize.value })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.publish_date = ''
  form.image_url = ''
  form.title = ''
  form.description = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  clearFormError()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.publish_date = row.publish_date
  form.image_url = row.image_url
  form.title = row.title
  form.description = row.description || ''
  clearFormError()
  dialogVisible.value = true
}

async function onImageUpload(file) {
  uploading.value = true
  try {
    const data = await api.upload(file)
    form.image_url = data.url
  } catch {
    /* 拦截器已弹错误 */
  } finally {
    uploading.value = false
  }
  return false // 阻止 el-upload 自动上传
}

// 支持拖拽 / 粘贴上传(仅弹窗打开期间)
const { isDragover: imageDrag } = useImageDropPaste(imageZoneRef, onImageUpload, {
  enabled: () => dialogVisible.value
})

async function onSave() {
  await formRef.value.validate().catch(() => {})
  if (!form.publish_date || !form.image_url || !form.title) return
  saving.value = true
  clearFormError()
  try {
    const payload = {
      publish_date: form.publish_date,
      image_url: form.image_url,
      title: form.title,
      description: form.description || null
    }
    if (editingId.value) {
      await api.admin.dailyUpdate(editingId.value, payload, { __silent: true })
      ElMessage.success('已保存')
    } else {
      await api.admin.dailyCreate(payload, { __silent: true })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    const detail = e?.response?.data?.detail
    // 409 一般是日期冲突,把后端的可读信息直接放到表单顶部
    setFormError(detail ? `保存失败:${detail}` : '保存失败,请稍后重试')
  } finally {
    saving.value = false
  }
}

async function onRemove(row) {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.publish_date} 的每日一图?`, '提示', {
      type: 'warning'
    })
  } catch {
    return // 用户取消
  }
  try {
    await api.admin.dailyRemove(row.id, { __silent: true })
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    const detail = e?.response?.data?.detail
    ElMessage.error(detail ? `删除失败:${detail}` : '删除失败,请稍后重试')
  }
}

onMounted(loadData)
</script>

<style scoped>
.title {
  margin: 0;
  font-size: 18px;
}
.image-zone {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s, box-shadow 0.15s;
}
.image-zone.is-dragover {
  background: #fff8fb;
  box-shadow: 0 0 0 2px rgba(230, 122, 163, 0.25);
}
.img-preview img {
  width: 220px;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}
</style>
