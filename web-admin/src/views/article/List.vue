<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">{{ auth.isAdmin ? '图文管理(全部)' : '我的图文' }}</h2>
      <span class="grow"></span>
      <el-input
        v-model="keyword"
        placeholder="搜索标题/摘要(仅公开 feed)"
        clearable
        style="width: 240px"
        @clear="loadData"
        @keyup.enter="onSearch"
      />
      <el-select
        v-model="statusFilter"
        placeholder="状态"
        clearable
        style="width: 130px"
        @change="onSearch"
      >
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
      </el-select>
      <el-button type="primary" :icon="EditPen" @click="goNew">写新图文</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="title" label="标题" min-width="220">
        <template #default="{ row }">
          <el-link type="primary" @click="goEdit(row.id)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="作者" width="130" v-if="auth.isAdmin">
        <template #default="{ row }">{{ row.author?.nickname || row.author?.id }}</template>
      </el-table-column>
      <el-table-column label="标签" min-width="160">
        <template #default="{ row }">
          <el-tag
            v-for="t in row.tags"
            :key="t"
            size="small"
            style="margin-right: 4px"
            effect="plain"
          >{{ t }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'published'" type="success" size="small">已发布</el-tag>
          <el-tag v-else type="info" size="small">草稿</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="view_count" label="浏览" width="80" />
      <el-table-column prop="like_count" label="赞" width="70" />
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="goEdit(row.id)">编辑</el-button>
          <el-button
            text
            :type="row.status === 'published' ? 'warning' : 'success'"
            @click="togglePublish(row)"
          >
            {{ row.status === 'published' ? '转草稿' : '发布' }}
          </el-button>
          <el-button text type="danger" @click="onRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end; display: flex"
      @size-change="loadData"
      @current-change="loadData"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { EditPen } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatTime } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref('')

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const res = auth.isAdmin
      ? await api.articles.adminList(params)
      : await api.me.myArticles(params)
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadData()
}
function goNew() {
  router.push('/articles/new')
}
function goEdit(id) {
  router.push(`/articles/${id}/edit`)
}

async function togglePublish(row) {
  const next = row.status === 'published' ? 'draft' : 'published'
  await api.articles.update(row.id, { status: next })
  ElMessage.success(next === 'published' ? '已发布' : '已转为草稿')
  loadData()
}

async function onRemove(row) {
  await ElMessageBox.confirm(`确认删除《${row.title}》?`, '提示', { type: 'warning' })
  await api.articles.remove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)</script>

<style scoped>
.title {
  margin: 0;
  font-size: 18px;
}
</style>
