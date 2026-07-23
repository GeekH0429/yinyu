<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">评论管理</h2>
      <span class="grow"></span>
      <el-input
        v-model="keyword"
        placeholder="搜索评论内容"
        clearable
        style="width: 240px"
        @clear="loadData"
        @keyup.enter="onSearch"
      />
      <el-input
        v-model="articleIdFilter"
        placeholder="按文章 ID 过滤"
        clearable
        style="width: 160px"
        @clear="onSearch"
        @keyup.enter="onSearch"
      />
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column label="内容" min-width="280">
        <template #default="{ row }">
          <span class="cmt-content">{{ row.content }}</span>
        </template>
      </el-table-column>
      <el-table-column label="文章" width="110">
        <template #default="{ row }">
          <el-link type="primary" @click="goArticle(row.article_id)">#{{ row.article_id }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="作者" width="130">
        <template #default="{ row }">{{ row.author?.nickname || row.author?.id }}</template>
      </el-table-column>
      <el-table-column label="回复目标" width="120">
        <template #default="{ row }">
          <span v-if="row.parent_id">→ #{{ row.parent_id }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="like_count" label="赞" width="70" />
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { formatTime } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const articleIdFilter = ref('')

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (articleIdFilter.value) {
      const id = parseInt(articleIdFilter.value, 10)
      if (!Number.isNaN(id)) params.article_id = id
    }
    const res = await api.admin.commentList(params)
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

function goArticle(id) {
  router.push(`/articles/${id}/edit`)
}

async function onRemove(row) {
  await ElMessageBox.confirm('确认删除该评论?相关回复与点赞将一并删除。', '提示', {
    type: 'warning'
  })
  await api.admin.commentRemove(row.id)
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
.cmt-content {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}
.muted {
  color: #c0c4cc;
}
</style>
