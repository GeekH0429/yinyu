<template>
  <view class="life" :data-theme="effectiveTheme">
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>

    <view class="topbar">
      <text class="back" @tap="goBack">‹ 返回</text>
      <text class="topbar-title serif">人生时光轴</text>
      <view class="topbar-right"></view>
    </view>

    <!-- 未设置生日:引导 -->
    <view class="guide card anim-rise" v-if="!loading && !life.birthday">
      <text class="guide-line serif">rén shēng shí guāng zhóu</text>
      <text class="guide-sub">写下你的生日,看看这一生铺开的样子</text>
      <picker mode="date" :end="todayStr" @change="onPickBirthday">
        <view class="guide-btn">从生日开始 ✦</view>
      </picker>
    </view>

    <!-- 加载/错误态 -->
    <view class="load-area" v-else-if="loading || error">
      <StateView v-if="error" type="error" text="没能连上这个角落" retry @retry="reload" />
      <text v-else class="load-text">正在铺开时光…</text>
    </view>

    <!-- 时光轴主体 -->
    <view class="body" v-else>
      <!-- 概览 -->
      <view class="overview anim-rise">
        <view class="ov-left">
          <text class="ov-num serif">{{ progress }}<text class="ov-pct">%</text></text>
          <text class="ov-cap">的人生已经走过</text>
        </view>
        <view class="ov-right">
          <text class="ov-days serif">{{ livedDays.toLocaleString() }}</text>
          <text class="ov-cap">天</text>
        </view>
      </view>

      <!-- 设置行:生日 / 人生长度 -->
      <view class="settings anim-rise delay-1">
        <picker class="set-picker" mode="date" :value="life.birthday" :end="todayStr" @change="onPickBirthday">
          <view class="set-item pressable">
            <text class="set-label">生日</text>
            <text class="set-value">{{ life.birthday }}</text>
          </view>
        </picker>
        <picker class="set-picker" mode="selector" :range="yearRange" :value="life.lifespan_years - 60" @change="onPickLifespan">
          <view class="set-item pressable">
            <text class="set-label">人生长度</text>
            <text class="set-value">{{ life.lifespan_years }} 年 ›</text>
          </view>
        </picker>
      </view>

      <!-- 节点横条 -->
      <scroll-view scroll-x class="strip anim-rise delay-2" :show-scrollbar="false">
        <view class="strip-inner">
          <text class="strip-cake">🎂</text>
          <view
            v-for="(m, idx) in milestones"
            :key="m.label + idx"
            class="chip pressable"
            @tap="onTapChip(m)"
          >
            <view class="chip-head">
              <view class="chip-dot" :style="{ background: m.color }"></view>
              <text class="chip-label">{{ m.label }}</text>
            </view>
            <text class="chip-dates">{{ shortDate(m.start) }} ~ {{ shortDate(m.end) }}</text>
          </view>
          <view class="chip chip-add pressable" @tap="openEditor(null)">
            <view class="chip-head">
              <text class="chip-plus">＋</text>
              <text class="chip-label">添加节点</text>
            </view>
            <text class="chip-dates">标记一段日子</text>
          </view>
        </view>
      </scroll-view>

      <!-- 单位切换 + 图例 -->
      <view class="toolbar">
        <view class="units">
          <view
            v-for="u in units"
            :key="u.key"
            :class="['unit', { on: unit === u.key }]"
            @tap="setUnit(u.key)"
          >
            {{ u.label }}
          </view>
        </view>
        <!-- 日粒度:视角切换(总览格子墙 / 月历);其他粒度显示图例 -->
        <view class="vswitch" v-if="unit === 365">
          <view :class="['vbtn', { on: viewMode === 'overview' }]" @tap="setViewMode('overview')">总览</view>
          <view :class="['vbtn', { on: viewMode === 'calendar' }]" @tap="setViewMode('calendar')">日历</view>
        </view>
        <view class="legend" v-else>
          <view class="lg"><view class="lg-dot today"></view>今天</view>
          <view class="lg"><view class="lg-dot past"></view>已过</view>
          <view class="lg"><view class="lg-dot future"></view>未来</view>
          <view class="lg"><view class="lg-dot cap">✉</view>胶囊</view>
          <view class="lg"><view class="lg-dot art">✎</view>足迹</view>
        </view>
      </view>

      <!-- 格子墙:canvas 底层绘制,透明 scroll-view 上层接管手势 -->
      <view class="grid-area" id="gridArea">
        <!-- 月历视角(仅日粒度):一次一个月,箭头/左右滑动翻页(swiper 三页循环) -->
        <view class="calendar" v-if="unit === 365 && viewMode === 'calendar'">
          <view class="cal-nav">
            <text :class="['cal-arrow', { dim: !canPrevMonth }]" @tap="prevMonth">‹</text>
            <text class="cal-title serif">{{ calYear }} 年 {{ calMonth + 1 }} 月</text>
            <text :class="['cal-arrow', { dim: !canNextMonth }]" @tap="nextMonth">›</text>
          </view>
          <swiper class="cal-swiper" :current="swiperCurrent" @change="onSwiperChange">
            <swiper-item v-for="(p, pi) in threePages" :key="pi">
              <view class="cal-page" v-if="!p.out">
                <view class="cal-week">
                  <text class="cal-wd" v-for="w in weekNames" :key="w">{{ w }}</text>
                </view>
                <view class="cal-grid">
                  <view
                    v-for="(c, idx) in makeCells(p.year, p.month)"
                    :key="idx"
                    :class="['cal-cell', { blank: !c }]"
                    @tap="c && onTapDay(c, $event)"
                  >
                    <view v-if="c" class="cal-inner" :style="c.bg ? { background: c.bg } : {}">
                      <text :class="['cal-num', { today: c.isToday, future: c.future }]">{{ c.day }}</text>
                      <text class="cal-cake" v-if="c.isBirthday">🎂</text>
                      <view class="cal-marks">
                        <view class="cal-dot cap" v-if="c.hasCapsule"></view>
                        <view class="cal-dot art" v-if="c.hasArticle"></view>
                      </view>
                    </view>
                  </view>
                </view>
              </view>
              <view class="cal-out" v-else>
                <text class="cal-out-text">{{ p.off < 0 ? '故事要从生日之后才开始' : '把眼前的日子过好,就是在到未来了' }}</text>
              </view>
            </swiper-item>
          </swiper>
          <view class="cal-today pressable" @tap="backToToday">回到今天 ✦</view>
        </view>

        <!-- 总览格子墙(v-show:与月历互斥切换时不销毁画布) -->
        <canvas
          v-show="!(unit === 365 && viewMode === 'calendar')"
          canvas-id="lifeGrid"
          class="grid-canvas"
          :style="{ width: canvasW + 'px', height: canvasH + 'px' }"
        ></canvas>
        <scroll-view
          v-show="!(unit === 365 && viewMode === 'calendar')"
          class="grid-scroll"
          scroll-y
          :scroll-top="jumpTop"
          :style="{ height: canvasH + 'px' }"
          @scroll="onGridScroll"
          @tap="onGridTap"
        >
          <view :style="{ height: totalH + 'px' }"></view>
        </scroll-view>

        <!-- 格子气泡 -->
        <view class="bubble-mask" v-if="bubble.visible" @tap="closeBubble">
          <view
            class="bubble"
            :style="{ left: bubble.x + 'px', top: bubble.y + 'px' }"
            @tap.stop
          >
            <text class="bubble-date serif">{{ bubble.label }}</text>
            <view class="bubble-row" v-for="(m, i) in bubble.milestones" :key="'m' + i">
              <view class="chip-dot" :style="{ background: m.color }"></view>
              <text class="bubble-text">{{ m.label }}</text>
            </view>
            <view class="bubble-row" v-for="(c, i) in bubble.capsules" :key="'c' + i">
              <text class="bubble-icon">✉</text>
              <text class="bubble-text">{{ c.isFuture ? '这一天将开启:' : '已开启:' }}{{ c.title || '一封没有名字的信' }}</text>
            </view>
            <view
              class="bubble-row bubble-link"
              v-for="(a, i) in bubble.articles"
              :key="'a' + i"
              @tap="goArticle(a)"
            >
              <text class="bubble-icon">✎</text>
              <text class="bubble-text">{{ a.title }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 人生进度卡 -->
      <view class="foot">
        <view class="foot-btn pressable" @tap="makeCard">生成人生进度卡 ✦</view>
      </view>
    </view>

    <!-- 节点编辑弹层 -->
    <view class="editor-mask" v-if="editor.visible" @tap="closeEditor">
      <view class="editor" @tap.stop>
        <text class="editor-title serif">{{ editor.form.id != null ? '编辑节点' : '添加节点' }}</text>

        <view class="field">
          <text class="field-label">名字</text>
          <input class="field-input" v-model="editor.form.label" placeholder="比如:在杭州的日子" :maxlength="40" />
        </view>

        <view class="field">
          <text class="field-label">颜色</text>
          <view class="palette">
            <view
              v-for="c in palette"
              :key="c"
              :class="['swatch', { on: editor.form.color === c }]"
              :style="{ background: c }"
              @tap="editor.form.color = c"
            ></view>
          </view>
        </view>

        <view class="field field-row">
          <picker class="date-picker" mode="date" :value="editor.form.start" :end="editor.form.end" @change="(e) => (editor.form.start = e.detail.value)">
            <view class="date-box">
              <text class="field-label">开始</text>
              <text class="date-value">{{ editor.form.start }}</text>
            </view>
          </picker>
          <picker class="date-picker" mode="date" :value="editor.form.end" :start="editor.form.start" @change="(e) => (editor.form.end = e.detail.value)">
            <view class="date-box">
              <text class="field-label">结束</text>
              <text class="date-value">{{ editor.form.end }}</text>
            </view>
          </picker>
        </view>

        <view class="field">
          <text class="field-label">地点(可选)</text>
          <input class="field-input" v-model="editor.form.site" placeholder="比如:杭州" :maxlength="60" />
        </view>

        <view class="field">
          <text class="field-label">相册(可选,{{ editor.form.images.length }}/9)</text>
          <view class="imgs">
            <view class="img-box" v-for="(img, i) in editor.form.images" :key="i">
              <CachedImage class="img" :src="thumbUrl(img)" :fallback="img" mode="aspectFill" @tap="previewImg(i)" />
              <text class="img-del" @tap.stop="removeImg(i)">×</text>
            </view>
            <view class="img-box img-add" v-if="editor.form.images.length < 9" @tap="addImg">
              <text class="img-plus">＋</text>
            </view>
          </view>
        </view>

        <view class="editor-actions">
          <text class="act-del" v-if="editor.form.id != null" @tap="removeMilestone">删除</text>
          <view class="act-spacer"></view>
          <text class="act-cancel" @tap="closeEditor">取消</text>
          <view class="act-save pressable" @tap="saveMilestone">保存</view>
        </view>
      </view>
    </view>

    <!-- 进度卡预览浮层 -->
    <view class="card-mask" v-if="cardPreview.visible" @tap="cardPreview.visible = false">
      <view class="card-box" @tap.stop>
        <image class="card-img" :src="cardPreview.path" mode="widthFix" @tap="cardPreview.visible = false"></image>
        <view class="card-actions">
          <view class="card-btn" @tap="saveCard">保存</view>
          <view class="card-btn primary" @tap="shareCard">分享</view>
        </view>
      </view>
    </view>

    <!-- 离屏进度卡画布(fixed 视口外,不能 v-if) -->
    <canvas canvas-id="lifeCard" class="offscreen" style="width: 600px; height: 760px"></canvas>
  </view>
</template>

<script setup>
import { ref, reactive, computed, getCurrentInstance, nextTick } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { api } from '../../api'
import { effectiveTheme } from '../../store/theme'
import { formatDate } from '../../utils/format'
import StateView from '../../components/StateView.vue'
import CachedImage from '../../components/CachedImage.vue'
import { resourceUrl, thumbUrl } from '../../config'
import {
  UNITS,
  defaultMilestones,
  mergeMilestones,
  todayIndex,
  milestonesAt,
  buildMarkIndex,
  cellLabel,
  parseDate,
  lifeProgress,
  daysLived
} from '../../utils/lifeTimeline'
import { makeLifeCard } from '../../utils/lifeCard'
import { saveQuoteCard, shareQuoteCard } from '../../utils/quoteCard'

const proxy = getCurrentInstance().proxy
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 0)

// ---- 数据 ----
const life = reactive({ birthday: null, lifespan_years: 80, milestones: [], capsules: [], articles: [] })
const loading = ref(false)
const error = ref(false)
const units = UNITS
const unit = ref(12)
// 日粒度下的视角:overview 总览格子墙 / calendar 月历
const viewMode = ref('overview')
const weekNames = ['一', '二', '三', '四', '五', '六', '日']
const now = new Date()
const calYear = ref(now.getFullYear())
const calMonth = ref(now.getMonth())
const palette = ['#C4A882', '#A8C6A1', '#9CB8CE', '#E8B4A0', '#B5A8CE', '#D9A8C0', '#E5CD9A', '#CEA8A8', '#8FB8A8', '#A89CB8']
const yearRange = Array.from({ length: 61 }, (_, i) => String(i + 60))
const todayStr = (() => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
})()

const progress = computed(() => lifeProgress(life.birthday, life.lifespan_years))
const livedDays = computed(() => daysLived(life.birthday))
const milestones = computed(() => mergeMilestones(defaultMilestones(life.birthday), life.milestones))

// ---- 格子墙(canvas 窗口化渲染) ----
const canvasW = ref(0)
const canvasH = ref(0)
const scrollTop = ref(0)
// scroll-view 跳转锚点:只在主动定位时赋值(与滚动的 scrollTop 分离,
// 避免滚动回写绑定量在 iOS 上打断惯性滚动)
const jumpTop = ref(0)
let cellPx = 16
let gapPx = 4
let cols = 1
let rowH = 20
let totalH = 0
let gridCount = 0
let tIdx = -1
let capsuleMap = new Map()
let articleMap = new Map()
let areaRect = { left: 0, top: 0 }
let drawScheduled = false

const theme = { today: '#C4A882', future: '#FFFFFF', past: '#EAD9C2' }

function layout() {
  if (!life.birthday) return
  const availW = canvasW.value
  // 各粒度格子尺寸(逻辑 px):年大月中周小日密
  cellPx = { 1: 26, 12: 15, 52: 8.5, 365: 4.5 }[unit.value] || 15
  gapPx = { 1: 7, 12: 4.5, 52: 2.5, 365: 1.2 }[unit.value] || 4
  cols = Math.max(1, Math.floor(availW / (cellPx + gapPx)))
  rowH = cellPx + gapPx
  gridCount = life.lifespan_years * unit.value
  const rows = Math.ceil(gridCount / cols)
  totalH = rows * rowH
  tIdx = todayIndex(life.birthday, unit.value)
  capsuleMap = buildMarkIndex(
    life.capsules.map((c) => ({ ...c, cnDate: formatDate(c.unlock_at), isFuture: new Date(c.unlock_at).getTime() > Date.now() - 86400000 })),
    life.birthday, unit.value, gridCount
  )
  articleMap = buildMarkIndex(
    life.articles.map((a) => ({ ...a, cnDate: formatDate(a.published_at) })),
    life.birthday, unit.value, gridCount
  )
  scrollToToday()
  drawGrid()
}

/** 总览定位:把今天滚进可视区中间(周/日粒度格子多,从头看起太远)。 */
function scrollToToday() {
  if (tIdx < 0) return
  const target = Math.max(0, Math.min(Math.floor(tIdx / cols) * rowH - canvasH.value / 2, Math.max(0, totalH - canvasH.value)))
  scrollTop.value = target
  jumpTop.value = target
}

function drawGrid() {
  if (!life.birthday || !canvasW.value) return
  const ctx = uni.createCanvasContext('lifeGrid', proxy)
  const ms = milestones.value
  const firstRow = Math.max(0, Math.floor(scrollTop.value / rowH) - 1)
  const lastRow = Math.ceil((scrollTop.value + canvasH.value) / rowH) + 1
  for (let row = firstRow; row <= lastRow; row++) {
    for (let col = 0; col < cols; col++) {
      const i = row * cols + col
      if (i >= gridCount) break
      const x = col * (cellPx + gapPx)
      const y = row * rowH - scrollTop.value
      // 底色:节点覆盖 > 今天 > 未来 > 已过
      let c1 = theme.past
      let c2 = null
      if (i === tIdx) c1 = theme.today
      else if (i > tIdx) c1 = theme.future
      else {
        const hit = milestonesAt(ms, life.birthday, unit.value, i)
        if (hit.length) {
          c1 = hit[0].color
          c2 = hit[1] ? hit[1].color : null
        }
      }
      if (c2) {
        // 两节点叠加:上下各半
        ctx.setFillStyle(c1)
        ctx.fillRect(x, y, cellPx, cellPx / 2)
        ctx.setFillStyle(c2)
        ctx.fillRect(x, y + cellPx / 2, cellPx, cellPx / 2)
      } else {
        ctx.setFillStyle(c1)
        ctx.fillRect(x, y, cellPx, cellPx)
      }
      // 未来格描边(白格在米白底上可见)
      if (i > tIdx) {
        ctx.setStrokeStyle('rgba(196,168,130,0.25)')
        ctx.setLineWidth(0.5)
        ctx.strokeRect(x + 0.25, y + 0.25, cellPx - 0.5, cellPx - 0.5)
      }
      // 今天:白描边突出
      if (i === tIdx) {
        ctx.setStrokeStyle('#FFFFFF')
        ctx.setLineWidth(1.2)
        ctx.strokeRect(x + 0.6, y + 0.6, cellPx - 1.2, cellPx - 1.2)
      }
      // 胶囊标记:格子中央金点
      if (capsuleMap.has(i)) {
        ctx.setFillStyle('#D4A95C')
        ctx.beginPath()
        ctx.arc(x + cellPx / 2, y + cellPx / 2, Math.max(1, cellPx * 0.18), 0, Math.PI * 2)
        ctx.fill()
      }
      // 写作足迹:右上角小点
      if (articleMap.has(i)) {
        ctx.setFillStyle('#8D7B64')
        ctx.beginPath()
        ctx.arc(x + cellPx - Math.max(0.8, cellPx * 0.12), y + Math.max(0.8, cellPx * 0.12), Math.max(0.8, cellPx * 0.12), 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }
  ctx.draw()
}

function onGridScroll(e) {
  scrollTop.value = e.detail.scrollTop
  // 合并高频滚动重绘(16ms)
  if (drawScheduled) return
  drawScheduled = true
  setTimeout(() => {
    drawScheduled = false
    drawGrid()
  }, 16)
}

function onGridTap(e) {
  if (!life.birthday) return
  const x = e.detail.x - areaRect.left
  const y = e.detail.y - areaRect.top + scrollTop.value
  if (x < 0 || y < 0) return
  const col = Math.floor(x / (cellPx + gapPx))
  const row = Math.floor(y / rowH)
  if (col >= cols) return
  const i = row * cols + col
  if (i < 0 || i >= gridCount) return
  const hitMs = milestonesAt(milestones.value, life.birthday, unit.value, i)
  const caps = capsuleMap.get(i) || []
  const arts = articleMap.get(i) || []
  showBubble(e, cellLabel(life.birthday, unit.value, i), hitMs, caps, arts)
}

/** 弹格子气泡:总览与月历共用。e 的 detail.x/y 是页面坐标(页面无外滚,近似视口)。 */
function showBubble(e, label, hitMs, caps, arts) {
  const bw = 280
  const left = Math.min(Math.max(12, e.detail.x - bw / 2), uni.getSystemInfoSync().windowWidth - bw - 12)
  const top = Math.max(80, e.detail.y - 190)
  bubble.value = { visible: true, x: left, y: top, label, milestones: hitMs, capsules: caps, articles: arts }
}

function setUnit(u) {
  unit.value = u
  uni.setStorageSync('life_unit', u)
  // 不清 viewMode:月历只在 unit===365 时渲染(模板 v-if 保证),
  // 切回「日」时沿用用户上次的视角偏好(无偏好则 onLoad 已默认 calendar)
  layout()
}

// ---- 视角切换 & 月历(日粒度) ----
function setViewMode(v) {
  viewMode.value = v
  uni.setStorageSync('life_view_mode', v)
  if (v === 'calendar') {
    // 进月历默认落在今天所在月
    const t = new Date()
    calYear.value = t.getFullYear()
    calMonth.value = t.getMonth()
  } else {
    // 总览画布在月历期间被 v-show 隐藏,内容仍在;切回重绘一次保险
    drawGrid()
  }
}

// 月历可翻页边界:[生日所在月, 人生终点月]
const calBounds = computed(() => {
  if (!life.birthday) return null
  const b = parseDate(life.birthday)
  const end = new Date(b.getFullYear() + life.lifespan_years, b.getMonth(), 1)
  return { start: new Date(b.getFullYear(), b.getMonth(), 1), end }
})
const canPrevMonth = computed(() => {
  if (!calBounds.value) return false
  return new Date(calYear.value, calMonth.value, 1) > calBounds.value.start
})
const canNextMonth = computed(() => {
  if (!calBounds.value) return false
  return new Date(calYear.value, calMonth.value, 1) < calBounds.value.end
})

function prevMonth() {
  if (!canPrevMonth.value) return
  shiftMonth(-1)
}

function nextMonth() {
  if (!canNextMonth.value) return
  shiftMonth(1)
}

/** 月份步进(处理跨年) */
function shiftMonth(n) {
  let y = calYear.value
  let m = calMonth.value + n
  y += Math.floor(m / 12)
  m = ((m % 12) + 12) % 12
  calYear.value = y
  calMonth.value = m
}

// ---- 月历 swiper(三页循环:[上月, 当月, 下月],滑完归位中间页) ----
const swiperCurrent = ref(1)

const threePages = computed(() => {
  if (!life.birthday) return []
  return [-1, 0, 1].map((off) => {
    let y = calYear.value
    let m = calMonth.value + off
    y += Math.floor(m / 12)
    m = ((m % 12) + 12) % 12
    return { off, year: y, month: m, out: monthOutOfRange(y, m) }
  })
})

function monthOutOfRange(y, m) {
  const b = calBounds.value
  if (!b) return true
  const cur = new Date(y, m, 1)
  return cur < b.start || cur > b.end
}

function onSwiperChange(e) {
  const idx = e.detail.current
  // 归位重置触发的 change(current 回到 1)直接忽略,防循环
  if (idx === 1) return
  // ① 先把 props 同步到 swiper 内部所在页(值 1→0/2 才有变化),
  //    否则下一步归位赋 1 是同值赋值,Vue 不更新,swiper 不会跳回中间页
  swiperCurrent.value = idx
  if (idx === 0) {
    if (canPrevMonth.value) shiftMonth(-1)
  } else if (canNextMonth.value) {
    shiftMonth(1)
  }
  // ② 三页内容随月份移位后,把 current 瞬切回中间页(页 1 内容 = 刚滑到的月,视觉无缝)
  nextTick(() => {
    swiperCurrent.value = 1
  })
}

function backToToday() {
  const t = new Date()
  calYear.value = t.getFullYear()
  calMonth.value = t.getMonth()
}

// 标记索引:cnDate -> 命中(月历按日期直查,不需要格子墙的 cellIndex Map)
const capsuleDaySet = computed(() => new Set(life.capsules.map((c) => formatDate(c.unlock_at))))
const articleDaySet = computed(() => new Set(life.articles.map((a) => formatDate(a.published_at))))

// 月历格子:前置空白 + 指定月每天 {day, iso, isToday, future, isBirthday, bg, hasCapsule, hasArticle}
// (swiper 三页各自调用,按参数生成)
function makeCells(y, m) {
  const lead = (new Date(y, m, 1).getDay() + 6) % 7 // 周一开头
  const days = new Date(y, m + 1, 0).getDate()
  const ms = milestones.value
  const cells = []
  for (let i = 0; i < lead; i++) cells.push(null)
  for (let d = 1; d <= days; d++) {
    const date = new Date(y, m, d)
    const iso = fmtISO(date)
    const isToday = iso === todayStr
    const future = iso > todayStr
    // 着色:节点覆盖(取首个,色值带透明度做淡染) > 已过暖沙 > 未来留白
    let bg = ''
    if (!isToday) {
      const hit = ms.filter((mm) => date >= mm.start && date <= mm.end)
      bg = hit.length ? hit[0].color + '4D' : future ? '' : '#EAD9C2' + '40'
    }
    cells.push({
      day: d,
      iso,
      isToday,
      future,
      isBirthday: iso === life.birthday,
      bg,
      hasCapsule: capsuleDaySet.value.has(iso),
      hasArticle: articleDaySet.value.has(iso)
    })
  }
  return cells
}

function onTapDay(c, e) {
  const d = parseDate(c.iso)
  const hitMs = milestones.value.filter((m) => d >= m.start && d <= m.end)
  const caps = life.capsules
    .filter((x) => formatDate(x.unlock_at) === c.iso)
    .map((x) => ({ ...x, isFuture: new Date(x.unlock_at).getTime() > Date.now() }))
  const arts = life.articles.filter((x) => formatDate(x.published_at) === c.iso)
  showBubble(e, c.iso, hitMs, caps, arts)
}

async function measure() {
  await nextTick()
  const info = await new Promise((resolve) => {
    uni.createSelectorQuery().in(proxy).select('#gridArea').boundingClientRect((r) => resolve(r)).exec()
  })
  if (!info) return
  areaRect = { left: info.left, top: info.top }
  canvasW.value = Math.floor(info.width)
  canvasH.value = Math.floor(info.height)
  layout()
}

// ---- 数据加载 / 设置 ----
async function reload() {
  loading.value = true
  error.value = false
  try {
    const res = await api.life.get()
    Object.assign(life, res)
    // 先让主体渲染出 grid-area,再测量尺寸绘制(loading 态下节点不存在)
    loading.value = false
    await measure()
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

async function onPickBirthday(e) {
  const v = e.detail.value
  if (!v) return
  try {
    await api.life.updateSettings({ birthday: v })
    life.birthday = v
    // guide 态 -> 主体态:等 grid-area 渲染出来再测量
    await measure()
    uni.showToast({ title: '时光已铺开 ✦', icon: 'none' })
  } catch {
    /* request 层已 toast */
  }
}

async function onPickLifespan(e) {
  const v = Number(e.detail.value)
  if (!v) return
  try {
    life.lifespan_years = v
    await api.life.updateSettings({ lifespan_years: v })
    layout()
  } catch {
    /* ignore */
  }
}

// ---- 格子气泡 ----
const bubble = ref({ visible: false, x: 0, y: 0, label: '', milestones: [], capsules: [], articles: [] })

function closeBubble() {
  bubble.value.visible = false
}

// ---- 节点编辑 ----
const editor = reactive({
  visible: false,
  form: { id: null, label: '', color: '#C4A882', start: todayStr, end: todayStr, site: '', images: [] }
})

function openEditor(m) {
  if (m == null) {
    editor.form = { id: null, label: '', color: palette[Math.floor(Math.random() * palette.length)], start: todayStr, end: todayStr, site: '', images: [] }
  } else {
    editor.form = {
      id: m.id,
      label: m.label,
      color: m.color,
      start: fmtISO(m.start),
      end: fmtISO(m.end),
      site: m.site || '',
      images: [...(m.images || [])]
    }
  }
  editor.visible = true
}

function fmtISO(d) {
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

function onTapChip(m) {
  if (m.isDefault) {
    uni.showToast({ title: '学制节点随生日自动推算,想标记别的日子就添加一个节点吧', icon: 'none', duration: 2500 })
    return
  }
  openEditor(m)
}

function closeEditor() {
  editor.visible = false
}

async function saveMilestone() {
  const f = editor.form
  if (!f.label.trim()) {
    uni.showToast({ title: '给这段日子起个名字吧', icon: 'none' })
    return
  }
  if (f.end < f.start) {
    uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
    return
  }
  const payload = {
    label: f.label.trim(),
    color: f.color,
    start_date: f.start,
    end_date: f.end,
    site: f.site.trim() || null,
    images: f.images
  }
  try {
    if (f.id != null) await api.life.updateMilestone(f.id, payload)
    else await api.life.createMilestone(payload)
    editor.visible = false
    await reload()
  } catch {
    /* request 层已 toast */
  }
}

function removeMilestone() {
  const id = editor.form.id
  uni.showModal({
    title: '删除节点',
    content: '删除后这段日子的着色与相册都会消失,确定吗?',
    confirmText: '删除',
    confirmColor: '#e0a8b0',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.life.removeMilestone(id)
        editor.visible = false
        await reload()
      } catch {
        /* ignore */
      }
    }
  })
}

// ---- 节点相册(P3) ----
function addImg() {
  uni.chooseImage({
    count: 9 - editor.form.images.length,
    sizeType: ['compressed'],
    success: async (res) => {
      uni.showLoading({ title: '上传中…' })
      try {
        for (const p of res.tempFilePaths) {
          const r = await api.upload(p)
          if (r && r.url) editor.form.images.push(r.url)
        }
      } catch {
        uni.showToast({ title: '上传失败,再试一次?', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    }
  })
}

function removeImg(i) {
  editor.form.images.splice(i, 1)
}

function previewImg(i) {
  uni.previewImage({
    urls: editor.form.images.map((u) => resourceUrl(u)),
    current: i
  })
}

// ---- 进度卡(P3) ----
const cardPreview = reactive({ visible: false, path: '' })

async function makeCard() {
  if (!life.birthday) return
  uni.showLoading({ title: '绘制中…' })
  const remainYears = life.lifespan_years - (Date.now() - new Date(life.birthday).getTime()) / (365.25 * 86400000)
  const leftText =
    remainYears > 0.5
      ? '还有约 ' + Math.round(remainYears) + ' 年,慢慢走'
      : '每一天都是礼物'
  try {
    const path = await makeLifeCard({
      canvasId: 'lifeCard',
      proxy,
      progress: progress.value,
      daysLived: livedDays.value,
      bornText: '生于 ' + String(life.birthday).slice(0, 7),
      leftText
    })
    cardPreview.path = path
    cardPreview.visible = true
  } catch {
    uni.showToast({ title: '绘制失败,再试一次?', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

function saveCard() {
  if (cardPreview.path) saveQuoteCard(cardPreview.path)
}

function shareCard() {
  if (cardPreview.path) shareQuoteCard(cardPreview.path)
}

// ---- 杂项 ----
function shortDate(d) {
  const s = fmtISO(d)
  return s.slice(2).replace(/-/g, '.')
}

function goArticle(a) {
  closeBubble()
  uni.navigateTo({ url: '/pages/read/index?id=' + a.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/mine/index' })
}

onLoad(() => {
  // 默认落在最常用的「日 · 日历」视角;用户切换单位/视角后记住偏好
  unit.value = uni.getStorageSync('life_unit') || 365
  viewMode.value = uni.getStorageSync('life_view_mode') || 'calendar'
})

onShow(() => {
  reload()
})
</script>

<style scoped>
.life {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fdfbf7;
  overflow: hidden;
}
.status-bar {
  width: 100%;
  flex-shrink: 0;
}
.topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 40rpx 8rpx;
}
.back {
  width: 120rpx;
  color: #c4a882;
  font-size: 30rpx;
}
.topbar-title {
  font-size: 32rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.topbar-right {
  width: 120rpx;
}

/* 引导 */
.guide {
  margin: 120rpx 64rpx;
  padding: 80rpx 56rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.guide-line {
  font-size: 34rpx;
  color: #c4a882;
  letter-spacing: 3rpx;
}
.guide-sub {
  margin-top: 20rpx;
  font-size: 26rpx;
  color: #b8b8b8;
}
.guide-btn {
  margin-top: 64rpx;
  padding: 22rpx 72rpx;
  background: #c4a882;
  color: #fff;
  border-radius: 48rpx;
  font-size: 30rpx;
  box-shadow: 0 8rpx 28rpx rgba(196, 168, 130, 0.45);
}
.load-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.load-text {
  font-size: 26rpx;
  color: #b8b8b8;
}

/* 主体 */
.body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0 32rpx;
}
.overview {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12rpx 12rpx 20rpx;
}
.ov-num {
  font-size: 72rpx;
  font-weight: 700;
  color: #c4a882;
  line-height: 1;
}
.ov-pct {
  font-size: 34rpx;
}
.ov-cap {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #b8b8b8;
}
.ov-right {
  text-align: right;
}
.ov-days {
  font-size: 44rpx;
  color: #4a4a4a;
  font-weight: 600;
}

/* 设置行 */
.settings {
  flex-shrink: 0;
  display: flex;
  gap: 20rpx;
  margin-bottom: 20rpx;
}
.set-picker {
  flex: 1;
}
.set-item {
  background: #fffdf8;
  border: 1rpx solid rgba(196, 168, 130, 0.25);
  border-radius: 20rpx;
  padding: 18rpx 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.set-label {
  font-size: 24rpx;
  color: #b8b8b8;
}
.set-value {
  font-size: 26rpx;
  color: #4a4a4a;
  font-weight: 500;
}

/* 节点横条 */
.strip {
  flex-shrink: 0;
  width: 100%;
  white-space: nowrap;
  margin-bottom: 20rpx;
}
.strip-inner {
  display: inline-flex;
  align-items: flex-start;
  gap: 16rpx;
  padding-bottom: 8rpx;
}
.strip-cake {
  font-size: 44rpx;
  line-height: 76rpx;
  margin-right: 4rpx;
}
.chip {
  display: inline-flex;
  flex-direction: column;
  gap: 6rpx;
  background: #fffdf8;
  border: 1rpx solid rgba(196, 168, 130, 0.3);
  border-radius: 18rpx;
  padding: 14rpx 22rpx;
  flex-shrink: 0;
}
.chip-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
}
.chip-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 6rpx;
}
.chip-label {
  font-size: 26rpx;
  color: #4a4a4a;
  font-weight: 500;
}
.chip-dates {
  font-size: 20rpx;
  color: #b8b8b8;
}
.chip-plus {
  color: #c4a882;
  font-size: 28rpx;
}
.chip-add {
  border-style: dashed;
}

/* 工具行 */
.toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}
.units {
  display: flex;
  background: #f2ece1;
  border-radius: 16rpx;
  padding: 4rpx;
}
.unit {
  padding: 8rpx 24rpx;
  font-size: 24rpx;
  color: #8d8d8d;
  border-radius: 13rpx;
}
.unit.on {
  background: #fffdf8;
  color: #c4a882;
  font-weight: 600;
}
.legend {
  display: flex;
  gap: 14rpx;
}
.lg {
  display: flex;
  align-items: center;
  gap: 6rpx;
  font-size: 20rpx;
  color: #b8b8b8;
}
.lg-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 5rpx;
}
.lg-dot.today { background: #c4a882; }
.lg-dot.past { background: #ead9c2; }
.lg-dot.future { background: #fff; border: 1rpx solid rgba(196, 168, 130, 0.5); }
.lg-dot.cap,
.lg-dot.art {
  width: auto;
  height: auto;
  background: none;
  border: none;
  font-size: 22rpx;
}
.lg-dot.cap { color: #d4a95c; }
.lg-dot.art { color: #8d7b64; }

/* 格子墙 */
.grid-area {
  flex: 1;
  min-height: 0;
  position: relative;
  background: #fffdf8;
  border: 1rpx solid rgba(196, 168, 130, 0.2);
  border-radius: 20rpx;
  overflow: hidden;
}
.grid-canvas {
  position: absolute;
  left: 0;
  top: 0;
}
.grid-scroll {
  position: absolute;
  inset: 0;
  width: 100%;
}

/* 视角切换 */
.vswitch {
  display: flex;
  background: #f2ece1;
  border-radius: 16rpx;
  padding: 4rpx;
}
.vbtn {
  padding: 8rpx 22rpx;
  font-size: 24rpx;
  color: #8d8d8d;
  border-radius: 13rpx;
}
.vbtn.on {
  background: #fffdf8;
  color: #c4a882;
  font-weight: 600;
}

/* 月历视角 */
.calendar {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: 20rpx 20rpx 12rpx;
}
.cal-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4rpx 8rpx 14rpx;
}
.cal-arrow {
  font-size: 44rpx;
  color: #c4a882;
  padding: 0 24rpx;
  line-height: 1;
}
.cal-arrow.dim {
  opacity: 0.22;
}
.cal-title {
  font-size: 30rpx;
  color: #4a4a4a;
  font-weight: 600;
}
.cal-swiper {
  flex: 1;
  min-height: 0;
}
.cal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.cal-out {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 60rpx;
}
.cal-out-text {
  font-size: 24rpx;
  color: #c9c2b4;
  line-height: 1.8;
  text-align: center;
}
.cal-week {
  display: flex;
  padding-bottom: 10rpx;
  border-bottom: 1rpx solid rgba(196, 168, 130, 0.18);
}
.cal-wd {
  flex: 1;
  text-align: center;
  font-size: 22rpx;
  color: #b8b8b8;
}
.cal-grid {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  padding-top: 10rpx;
}
.cal-cell {
  width: 14.2857%;
  height: 96rpx;
  display: flex;
  justify-content: center;
  padding: 4rpx;
  box-sizing: border-box;
}
.cal-inner {
  position: relative;
  width: 100%;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-num {
  font-size: 26rpx;
  color: #4a4a4a;
}
.cal-num.future {
  color: #cfc8bb;
}
.cal-num.today {
  width: 48rpx;
  height: 48rpx;
  line-height: 48rpx;
  text-align: center;
  background: #c4a882;
  color: #fff;
  border-radius: 24rpx;
  font-weight: 700;
}
.cal-cake {
  position: absolute;
  top: 2rpx;
  right: 8rpx;
  font-size: 20rpx;
}
.cal-marks {
  position: absolute;
  bottom: 8rpx;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  gap: 8rpx;
}
.cal-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 5rpx;
}
.cal-dot.cap {
  background: #d4a95c;
}
.cal-dot.art {
  background: #8d7b64;
}
.cal-today {
  align-self: center;
  margin-top: 8rpx;
  padding: 10rpx 40rpx;
  font-size: 22rpx;
  color: #c4a882;
  background: #f2ece1;
  border-radius: 30rpx;
}

/* 格子气泡 */
.bubble-mask {
  position: fixed;
  inset: 0;
  z-index: 1200;
}
.bubble {
  position: fixed;
  width: 280px;
  max-width: 86vw;
  background: #fffdf8;
  border-radius: 20rpx;
  box-shadow: 0 10rpx 44rpx rgba(0, 0, 0, 0.16);
  padding: 24rpx 28rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  z-index: 1201;
}
.bubble-date {
  font-size: 30rpx;
  font-weight: 700;
  color: #4a4a4a;
}
.bubble-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.bubble-icon {
  font-size: 24rpx;
  color: #c4a882;
}
.bubble-text {
  font-size: 24rpx;
  color: #6d6d6d;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bubble-link .bubble-text {
  color: #c4a882;
  text-decoration: underline;
}

/* 底部按钮 */
.foot {
  flex-shrink: 0;
  padding: 20rpx 0 28rpx;
  display: flex;
  justify-content: center;
}
.foot-btn {
  padding: 18rpx 64rpx;
  background: #f2ece1;
  color: #c4a882;
  border-radius: 44rpx;
  font-size: 26rpx;
}

/* 编辑弹层 */
.editor-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 26, 0.55);
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}
.editor {
  width: 100%;
  max-height: 82vh;
  overflow-y: auto;
  background: #fffdf8;
  border-radius: 32rpx;
  padding: 40rpx 40rpx 32rpx;
  display: flex;
  flex-direction: column;
}
.editor-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #4a4a4a;
  margin-bottom: 28rpx;
}
.field {
  margin-bottom: 26rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.field-row {
  flex-direction: row;
  gap: 20rpx;
}
.field-row .date-picker {
  flex: 1;
}
.field-label {
  font-size: 24rpx;
  color: #b8b8b8;
}
.field-input {
  background: #fdfbf7;
  border: 1rpx solid rgba(196, 168, 130, 0.3);
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
  font-size: 28rpx;
  color: #4a4a4a;
}
.date-box {
  background: #fdfbf7;
  border: 1rpx solid rgba(196, 168, 130, 0.3);
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.date-value {
  font-size: 26rpx;
  color: #4a4a4a;
}
.palette {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}
.swatch {
  width: 52rpx;
  height: 52rpx;
  border-radius: 16rpx;
  border: 4rpx solid transparent;
}
.swatch.on {
  border-color: #4a4a4a;
}
.imgs {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.img-box {
  position: relative;
  width: 140rpx;
  height: 140rpx;
}
.img {
  width: 100%;
  height: 100%;
  border-radius: 16rpx;
}
.img-del {
  position: absolute;
  top: -12rpx;
  right: -12rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-add {
  border: 2rpx dashed rgba(196, 168, 130, 0.6);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-plus {
  font-size: 48rpx;
  color: #c4a882;
}
.editor-actions {
  display: flex;
  align-items: center;
  gap: 28rpx;
  margin-top: 8rpx;
}
.act-spacer {
  flex: 1;
}
.act-del {
  font-size: 26rpx;
  color: #e0a8b0;
}
.act-cancel {
  font-size: 26rpx;
  color: #b8b8b8;
}
.act-save {
  padding: 16rpx 56rpx;
  background: #c4a882;
  color: #fff;
  border-radius: 40rpx;
  font-size: 28rpx;
}

/* 进度卡预览 */
.card-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 26, 0.65);
  z-index: 1002;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 48rpx;
}
.card-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28rpx;
}
.card-img {
  width: 560rpx;
  border-radius: 16rpx;
  box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.35);
}
.card-actions {
  display: flex;
  gap: 24rpx;
}
.card-btn {
  padding: 16rpx 64rpx;
  border-radius: 40rpx;
  background: rgba(255, 253, 248, 0.9);
  color: #4a4a4a;
  font-size: 28rpx;
}
.card-btn.primary {
  background: #c4a882;
  color: #fff;
}

/* 离屏画布 */
.offscreen {
  position: fixed;
  left: -9999px;
  top: 0;
}
</style>
