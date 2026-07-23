<template>
  <div class="stats-dashboard">
    <div class="toolbar">
      <h2 class="title">数据统计</h2>
      <span class="grow"></span>
      <el-radio-group v-model="timeRange" @change="onRangeChange">
        <el-radio-button label="7d">近 7 天</el-radio-button>
        <el-radio-button label="30d">近 30 天</el-radio-button>
        <el-radio-button label="90d">近 90 天</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 总体概览卡片 -->
    <el-row :gutter="16" class="overview-cards">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="label">总用户数</div>
          <div class="value">{{ overview.total_users?.toLocaleString() || 0 }}</div>
          <div class="delta">+{{ overview.new_users || 0 }} 新增</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="label">总文章数</div>
          <div class="value">{{ overview.total_articles?.toLocaleString() || 0 }}</div>
          <div class="delta">已发布 {{ overview.total_published || 0 }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="label">总树洞数</div>
          <div class="value">{{ overview.total_treeholes?.toLocaleString() || 0 }}</div>
          <div class="delta">+{{ overview.new_treeholes || 0 }} 新增</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="label">媒体文件</div>
          <div class="value">{{ overview.total_media?.toLocaleString() || 0 }}</div>
          <div class="delta">{{ formatBytes(overview.total_storage_bytes) }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 互动数据 -->
    <el-row :gutter="16" class="interaction-cards">
      <el-col :xs="24" :sm="12">
        <div class="stat-card stat-card-primary">
          <div class="label">总浏览量</div>
          <div class="value">{{ overview.total_views?.toLocaleString() || 0 }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12">
        <div class="stat-card stat-card-success">
          <div class="label">总点赞数</div>
          <div class="value">{{ overview.total_likes?.toLocaleString() || 0 }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势图表 -->
    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :lg="12">
        <div class="chart-container">
          <h3>用户增长趋势</h3>
          <v-chart
            v-if="trendData.users.length"
            :option="userTrendOption"
            :autoresize="true"
            style="height: 300px"
          />
          <el-empty v-else description="暂无数据" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="chart-container">
          <h3>内容发布趋势</h3>
          <v-chart
            v-if="trendData.articles.length || trendData.treeholes.length"
            :option="contentTrendOption"
            :autoresize="true"
            style="height: 300px"
          />
          <el-empty v-else description="暂无数据" />
        </div>
      </el-col>
    </el-row>

    <!-- 排行榜 -->
    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <div class="rank-container">
          <h3>热门文章 (Top {{ topArticles.length }})</h3>
          <el-table :data="topArticles" stripe size="small">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="author_name" label="作者" width="100" />
            <el-table-column prop="like_count" label="点赞" width="70" align="right" />
            <el-table-column prop="view_count" label="浏览" width="70" align="right" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="rank-container">
          <h3>活跃用户 (Top {{ activeUsers.length }})</h3>
          <el-table :data="activeUsers" stripe size="small">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="title" label="用户" min-width="150" />
            <el-table-column prop="like_count" label="文章数" width="80" align="right" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { api } from '@/api'
import { ElMessage } from 'element-plus'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const timeRange = ref('30d')
const overview = ref({})
const trendData = ref({
  users: [],
  articles: [],
  treeholes: []
})
const topArticles = ref([])
const activeUsers = ref([])

// 用户增长趋势配置
const userTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: trendData.value.users.map(p => p.date)
  },
  yAxis: { type: 'value' },
  series: [{
    name: '新增用户',
    type: 'line',
    data: trendData.value.users.map(p => p.count),
    smooth: true,
    areaStyle: { opacity: 0.3 },
    itemStyle: { color: '#409EFF' }
  }]
}))

// 内容发布趋势配置
const contentTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['文章', '树洞'] },
  xAxis: {
    type: 'category',
    data: [...new Set([
      ...trendData.value.articles.map(p => p.date),
      ...trendData.value.treeholes.map(p => p.date)
    ])].sort()
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '文章',
      type: 'line',
      data: trendData.value.articles.map(p => ({
        value: p.count,
        name: p.date
      })),
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '树洞',
      type: 'line',
      data: trendData.value.treeholes.map(p => p.count),
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    }
  ]
}))

async function loadOverview() {
  try {
    overview.value = await api.admin.statsOverview({ range: timeRange.value })
  } catch (error) {
    ElMessage.error('加载概览数据失败')
  }
}

async function loadTrends() {
  try {
    trendData.value = await api.admin.statsTrends({ range: timeRange.value })
  } catch (error) {
    ElMessage.error('加载趋势数据失败')
  }
}

async function loadRanks() {
  try {
    const [articles, users] = await Promise.all([
      api.admin.statsTopArticles({ range: timeRange.value, limit: 10 }),
      api.admin.statsActiveUsers({ range: timeRange.value, limit: 10 })
    ])
    topArticles.value = articles
    activeUsers.value = users
  } catch (error) {
    ElMessage.error('加载排行榜失败')
  }
}

function onRangeChange() {
  loadOverview()
  loadTrends()
  loadRanks()
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

onMounted(() => {
  loadOverview()
  loadTrends()
  loadRanks()
})
</script>

<style scoped>
.stats-dashboard {
  padding: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.title {
  margin: 0;
  font-size: 18px;
}

.grow {
  flex: 1;
}

.overview-cards,
.interaction-cards,
.charts-row {
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.stat-card-primary {
  background: linear-gradient(135deg, #409EFF 0%, #79bbff 100%);
  color: white;
}

.stat-card-success {
  background: linear-gradient(135deg, #67C23A 0%, #95d475 100%);
  color: white;
}

.stat-card .label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-card-primary .label,
.stat-card-success .label {
  color: rgba(255,255,255,0.8);
}

.stat-card .value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-card-primary .value,
.stat-card-success .value {
  color: white;
}

.stat-card .delta {
  font-size: 12px;
  color: #67C23A;
}

.stat-card-primary .delta,
.stat-card-success .delta {
  color: rgba(255,255,255,0.9);
}

.chart-container,
.rank-container {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  height: 100%;
}

.chart-container h3,
.rank-container h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
}
</style>