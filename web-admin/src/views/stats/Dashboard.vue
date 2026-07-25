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
          <div class="stat-head">
            <div class="stat-icon stat-icon-user">
              <el-icon><User /></el-icon>
            </div>
            <div class="label">总用户数</div>
          </div>
          <div class="value">{{ overview.total_users?.toLocaleString() || 0 }}</div>
          <div class="delta">+{{ overview.new_users || 0 }} 新增</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="stat-head">
            <div class="stat-icon stat-icon-doc">
              <el-icon><Document /></el-icon>
            </div>
            <div class="label">总文章数</div>
          </div>
          <div class="value">{{ overview.total_articles?.toLocaleString() || 0 }}</div>
          <div class="delta">已发布 {{ overview.total_published || 0 }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="stat-head">
            <div class="stat-icon stat-icon-tree">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="label">总树洞数</div>
          </div>
          <div class="value">{{ overview.total_treeholes?.toLocaleString() || 0 }}</div>
          <div class="delta">+{{ overview.new_treeholes || 0 }} 新增</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <div class="stat-card">
          <div class="stat-head">
            <div class="stat-icon stat-icon-media">
              <el-icon><Picture /></el-icon>
            </div>
            <div class="label">媒体文件</div>
          </div>
          <div class="value">{{ overview.total_media?.toLocaleString() || 0 }}</div>
          <div class="delta">{{ formatBytes(overview.total_storage_bytes) }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 互动数据 -->
    <el-row :gutter="16" class="interaction-cards">
      <el-col :xs="24" :sm="12">
        <div class="stat-card stat-card-primary">
          <div class="stat-head">
            <div class="stat-icon-bg stat-icon-view">
              <el-icon><View /></el-icon>
            </div>
            <div class="label">总浏览量</div>
          </div>
          <div class="value">{{ overview.total_views?.toLocaleString() || 0 }}</div>
          <div class="delta">温柔的注视</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12">
        <div class="stat-card stat-card-success">
          <div class="stat-head">
            <div class="stat-icon-bg stat-icon-like">
              <el-icon><Star /></el-icon>
            </div>
            <div class="label">总点赞数</div>
          </div>
          <div class="value">{{ overview.total_likes?.toLocaleString() || 0 }}</div>
          <div class="delta">心意的回响</div>
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
            <el-table-column prop="nickname" label="用户" min-width="150" />
            <el-table-column prop="article_count" label="文章数" width="80" align="right" />
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
import {
  User,
  Document,
  ChatDotRound,
  Picture,
  View,
  Star
} from '@element-plus/icons-vue'
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

// 暖色主题色(与 CSS 变量保持一致,echarts canvas 不读 CSS 故硬编码)
const COLOR_PRIMARY = '#b8825a'   // 暖棕焦糖
const COLOR_SUCCESS = '#7fa86b'   // 雾绿
const COLOR_WARNING = '#d99557'   // 暖橙

// 用户增长趋势配置
const userTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: trendData.value.users.map(p => p.date),
    axisLine: { lineStyle: { color: '#d8c9b3' } },
    axisLabel: { color: '#7a6553' }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: '#ece3d6', type: 'dashed' } },
    axisLabel: { color: '#7a6553' }
  },
  series: [{
    name: '新增用户',
    type: 'line',
    data: trendData.value.users.map(p => p.count),
    smooth: true,
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(184, 130, 90, 0.35)' },
          { offset: 1, color: 'rgba(184, 130, 90, 0.02)' }
        ]
      }
    },
    lineStyle: { color: COLOR_PRIMARY, width: 2 },
    itemStyle: { color: COLOR_PRIMARY }
  }]
}))

// 内容发布趋势配置
const contentTrendOption = computed(() => {
  // 以并集日期作为 x 轴,通过 Map 对齐两个 series,缺失日期补 0
  const dates = [...new Set([
    ...trendData.value.articles.map(p => p.date),
    ...trendData.value.treeholes.map(p => p.date)
  ])].sort()
  const am = new Map(trendData.value.articles.map(p => [p.date, p.count]))
  const tm = new Map(trendData.value.treeholes.map(p => [p.date, p.count]))
  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['文章', '树洞'],
      icon: 'roundRect',
      textStyle: { color: '#7a6553' }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#d8c9b3' } },
      axisLabel: { color: '#7a6553' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#ece3d6', type: 'dashed' } },
      axisLabel: { color: '#7a6553' }
    },
    series: [
      {
        name: '文章',
        type: 'line',
        data: dates.map(d => am.get(d) ?? 0),
        smooth: true,
        lineStyle: { color: COLOR_SUCCESS, width: 2 },
        itemStyle: { color: COLOR_SUCCESS }
      },
      {
        name: '树洞',
        type: 'line',
        data: dates.map(d => tm.get(d) ?? 0),
        smooth: true,
        lineStyle: { color: COLOR_WARNING, width: 2 },
        itemStyle: { color: COLOR_WARNING }
      }
    ]
  }
})

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
  margin-bottom: 20px;
}

.title {
  margin: 0;
}

.grow {
  flex: 1;
}

.overview-cards,
.interaction-cards,
.charts-row {
  margin-bottom: 16px;
}

/* ============================================================
 * 数据卡片:奶油底 + 圆形图标徽章
 * ============================================================ */
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  padding: 20px 22px;
  border-radius: 14px;
  box-shadow: var(--shadow-card);
  margin-bottom: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

.stat-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: var(--brand-primary-mist);
  color: var(--brand-primary);
}

/* 不同概览卡图标色调微调(都用暖色系) */
.stat-icon-user { background: #f5e6d3; color: #b8825a; }
.stat-icon-doc  { background: #ebf3e6; color: #7fa86b; }
.stat-icon-tree { background: #f9ede0; color: #d99557; }
.stat-icon-media { background: #f6e6e6; color: #c66b6b; }

.stat-card .label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-card .value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
  font-family: var(--font-serif);
  letter-spacing: 0.5px;
}

.stat-card .delta {
  font-size: 12px;
  color: var(--brand-primary);
  letter-spacing: 0.3px;
}

/* 互动卡片:渐变底 + 反白文字 */
.stat-card-primary {
  background: linear-gradient(135deg, #b8825a 0%, #d4a373 100%);
  color: #fff;
  border-color: transparent;
}

.stat-card-success {
  background: linear-gradient(135deg, #7fa86b 0%, #a3c088 100%);
  color: #fff;
  border-color: transparent;
}

.stat-card-primary .label,
.stat-card-success .label {
  color: rgba(255, 255, 255, 0.9);
}

.stat-card-primary .value,
.stat-card-success .value {
  color: #fff;
}

.stat-card-primary .delta,
.stat-card-success .delta {
  color: rgba(255, 255, 255, 0.85);
}

/* 互动卡内的图标徽章反白 */
.stat-icon-bg {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.stat-icon-view { background: rgba(255, 255, 255, 0.25); }
.stat-icon-like { background: rgba(255, 255, 255, 0.25); }

/* ============================================================
 * 图表/排行榜容器
 * ============================================================ */
.chart-container,
.rank-container {
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  padding: 20px 22px;
  border-radius: 14px;
  box-shadow: var(--shadow-card);
  height: 100%;
  margin-bottom: 16px;
}

.chart-container h3,
.rank-container h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-serif);
  letter-spacing: 0.5px;
  position: relative;
  padding-left: 12px;
}

.chart-container h3::before,
.rank-container h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  background: var(--brand-primary);
  border-radius: 2px;
}
</style>
