<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">树洞管理</h2>
      <span class="grow"></span>
      <span class="muted">树洞无列表、全量隐匿;此处为后台视角</span>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建树洞</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column label="暗号" width="120">
        <template #default="{ row }">
          <span class="code">{{ row.code }}</span>
          <el-button link :icon="CopyDocument" @click="copyText(row.code)" />
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '有效' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="view_count" label="浏览" width="80" />
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="refreshCode(row)">换暗号</el-button>
          <el-button text @click="customCode(row)">自定义</el-button>
          <el-button
            text
            :type="row.is_active ? 'warning' : 'success'"
            @click="toggleActive(row)"
          >{{ row.is_active ? '停用' : '启用' }}</el-button>
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
    />

    <!-- 新建 -->
    <el-dialog v-model="dialogVisible" title="新建树洞" width="780px" destroy-on-close>
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="createForm.title" maxlength="200" placeholder="可留空" />
        </el-form-item>
        <el-form-item label="正文">
          <RichEditor v-if="dialogVisible" v-model="createForm.content_html" />
        </el-form-item>
        <el-form-item label="自定义暗号">
          <el-input
            v-model="createForm.code"
            maxlength="6"
            placeholder="留空则系统随机生成 6 位数字"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import RichEditor from '@/components/RichEditor.vue'
import { api } from '@/api'
import { formatTime } from '@/utils/format'
import { copyText } from '@/utils/clipboard'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const creating = ref(false)
const createForm = reactive({ title: '', content_html: '', code: '' })

async function loadData() {
  loading.value = true
  try {
    const res = await api.treeholes.adminList({ page: page.value, page_size: pageSize.value })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createForm.title = ''
  createForm.content_html = ''
  createForm.code = ''
  dialogVisible.value = true
}

async function onCreate() {
  if (createForm.code && !/^\d{6}$/.test(createForm.code)) {
    ElMessage.warning('自定义暗号需为 6 位数字')
    return
  }
  creating.value = true
  try {
    await api.treeholes.create({
      title: createForm.title || null,
      content_html: createForm.content_html,
      code: createForm.code || null
    })
    ElMessage.success('已创建')
    dialogVisible.value = false
    loadData()
  } finally {
    creating.value = false
  }
}

async function refreshCode(row) {
  await ElMessageBox.confirm('确认重新生成随机暗号?旧暗号将立即失效。', '提示', {
    type: 'warning'
  })
  const res = await api.treeholes.changeCode(row.id, null)
  row.code = res.code
  ElMessage.success(`新暗号:${res.code}`)
}

async function customCode(row) {
  const { value } = await ElMessageBox.prompt('输入新的 6 位数字暗号', '自定义暗号', {
    inputPattern: /^\d{6}$/,
    inputErrorMessage: '请输入 6 位数字'
  })
  const res = await api.treeholes.changeCode(row.id, value)
  row.code = res.code
  ElMessage.success('暗号已更新')
}

async function toggleActive(row) {
  await api.treeholes.update(row.id, { is_active: !row.is_active })
  row.is_active = !row.is_active
}

async function onRemove(row) {
  await ElMessageBox.confirm('确认删除该树洞?', '提示', { type: 'warning' })
  await api.treeholes.remove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.title {
  margin: 0;
  font-size: 18px;
}
.muted {
  color: #999;
  font-size: 13px;
}
.code {
  font-family: 'Consolas', monospace;
  font-size: 16px;
  letter-spacing: 2px;
  font-weight: 600;
  color: #e67aa3;
}
</style>
