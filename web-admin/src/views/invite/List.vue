<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 class="title">邀请码</h2>
      <span class="grow"></span>
      <el-button type="primary" :icon="Plus" @click="openCreate">生成邀请码</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column label="邀请码" width="180">
        <template #default="{ row }">
          <span class="code">{{ row.code }}</span>
          <el-button link :icon="CopyDocument" @click="copyText(row.code)" />
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column label="用量" width="130">
        <template #default="{ row }">{{ row.used_count }} / {{ row.max_uses }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '可用' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="过期时间" width="170">
        <template #default="{ row }">{{ row.expires_at ? formatTime(row.expires_at) : '永久' }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
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

    <el-dialog v-model="dialogVisible" title="生成邀请码" width="420px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="生成数量">
          <el-input-number v-model="form.count" :min="1" :max="50" />
        </el-form-item>
        <el-form-item label="可注册次数">
          <el-input-number v-model="form.max_uses" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" maxlength="120" placeholder="可留空" />
        </el-form-item>
      </el-form>
      <div v-if="lastCreated.length" class="created-box">
        <div class="created-title">已生成(点击复制)</div>
        <el-tag
          v-for="c in lastCreated"
          :key="c"
          class="created-tag"
          @click="copyText(c)"
        >{{ c }}</el-tag>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
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
const form = reactive({ count: 1, max_uses: 1, remark: '' })
const lastCreated = ref([])

async function loadData() {
  loading.value = true
  try {
    const res = await api.admin.inviteList({ page: page.value, page_size: pageSize.value })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.count = 1
  form.max_uses = 1
  form.remark = ''
  lastCreated.value = []
  dialogVisible.value = true
}

async function onCreate() {
  creating.value = true
  try {
    const res = await api.admin.inviteCreate({
      count: form.count,
      max_uses: form.max_uses,
      remark: form.remark || null
    })
    lastCreated.value = (res.items || []).map((i) => i.code)
    ElMessage.success(`已生成 ${lastCreated.value.length} 个`)
    loadData()
  } finally {
    creating.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.title {
  margin: 0;
  font-size: 18px;
}
.code {
  font-family: 'Consolas', monospace;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}
.created-box {
  margin-top: 12px;
  padding: 10px;
  background: #fafafa;
  border-radius: 6px;
}
.created-title {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}
.created-tag {
  margin: 4px;
  cursor: pointer;
  font-weight: 600;
}
</style>
