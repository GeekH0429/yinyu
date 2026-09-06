/**
 * 人生时光轴核心计算(纯函数,无副作用):
 *   - 默认学制节点按生日推算(童年/幼儿园/…/大学 + 学业之后的「日常」)
 *   - 格子日期推算 / 今天索引 / 节点与标记(胶囊、写作足迹)的格子覆盖
 *
 * 移植自 lifetime-visualization 的 useMilestones,规则保留中国学制:
 * 9 月 1 日入学 —— 生日在 9 月及以后的孩子推后一年入学。
 * 默认节点不落库(生日的纯函数,改生日自动重算);自定义节点走 /me/life/milestones。
 */

// 单位:日/周/月/年 每年的格子数(由细到粗排列,日最常用在前)
export const UNITS = [
  { key: 365, label: '日' },
  { key: 52, label: '周' },
  { key: 12, label: '月' },
  { key: 1, label: '年' }
]

// 默认学制节点:名称与各阶段年数(童年3/幼儿园3/小学6/初中3/高中3/大学4)
const DEFAULT_STAGES = [
  { label: '童年', years: 3, color: '#A8C6A1' },
  { label: '幼儿园', years: 3, color: '#9CB8CE' },
  { label: '小学', years: 6, color: '#E8B4A0' },
  { label: '初中', years: 3, color: '#B5A8CE' },
  { label: '高中', years: 3, color: '#D9A8C0' },
  { label: '大学', years: 4, color: '#E5CD9A' }
]
export const AFTER_STAGE = { label: '日常', color: '#D9CBB4' }

/** 'YYYY-MM-DD' -> 本地 Date(避免 UTC 解析偏移) */
export function parseDate(s) {
  if (s instanceof Date) return s
  const [y, m, d] = String(s).slice(0, 10).split('-').map(Number)
  return new Date(y, (m || 1) - 1, d || 1)
}

/** 本地 Date -> 'YYYY-MM-DD' */
export function fmtDate(d) {
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

function addMonths(d, n) {
  return new Date(d.getFullYear(), d.getMonth() + n, d.getDate())
}

/**
 * 按生日推算默认学制节点(含学业结束后的「日常」,持续到今天)。
 * 返回 [{label, color, start: Date, end: Date, isDefault: true}]
 */
export function defaultMilestones(birthday) {
  const b = parseDate(birthday)
  const extraGap = b.getMonth() >= 8 ? 1 : 0 // 9 月及以后出生,次年入学
  const out = []
  let pastYears = 0
  for (let i = 0; i < DEFAULT_STAGES.length; i++) {
    const st = DEFAULT_STAGES[i]
    const start = i === 0 ? b : new Date(b.getFullYear() + pastYears + extraGap, 8, 1)
    const end = new Date(b.getFullYear() + st.years + pastYears + extraGap, 5, 1)
    out.push({ label: st.label, color: st.color, start, end, isDefault: true })
    pastYears += st.years
  }
  // 学业之后:从毕业那年 7/1 起至今(格子着「日常」底色)
  const after = new Date(b.getFullYear() + pastYears + extraGap, 6, 1)
  if (after < new Date()) {
    out.push({ label: AFTER_STAGE.label, color: AFTER_STAGE.color, start: after, end: new Date(), isDefault: true })
  }
  return out
}

/** 合并默认节点与库里的自定义节点(自定义优先,时间序) */
export function mergeMilestones(defaults, customs) {
  const list = [
    ...defaults,
    ...(customs || []).map((m) => ({
      id: m.id,
      label: m.label,
      color: m.color,
      start: parseDate(m.start_date),
      end: parseDate(m.end_date),
      site: m.site || '',
      images: m.images || [],
      isDefault: false
    }))
  ]
  list.sort((a, b) => a.start - b.start)
  return list
}

/** 格子 i 的代表日期(半开区间 [cell, nextCell) 由 unit 决定) */
export function cellDate(birthday, unit, i) {
  const b = parseDate(birthday)
  if (unit === 365) return new Date(b.getFullYear(), b.getMonth(), b.getDate() + i)
  if (unit === 52) return new Date(b.getFullYear(), b.getMonth(), b.getDate() + i * 7)
  if (unit === 12) return addMonths(b, i)
  return new Date(b.getFullYear() + i, b.getMonth(), b.getDate())
}

/** 今天落在第几格;返回 -1 表示生日未设置/今天不在跨度内 */
export function todayIndex(birthday, unit) {
  if (!birthday) return -1
  const today = new Date()
  let lo = 0
  let hi = unit === 1 ? 150 : 60000 // 二分上界宽裕即可
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (cellDate(birthday, unit, mid) <= today) lo = mid + 1
    else hi = mid
  }
  return lo - 1
}

/**
 * 半开区间相交判定:格子 [cell, nextCell) 是否覆盖 [start, end](闭)。
 * 月/周粒度下格子跨度大于一天,用相交而非点判定更准。
 */
function cellIntersects(cell, nextCell, start, end) {
  return nextCell > start && cell <= end
}

/** 命中格子的节点列表(自定义 + 默认) */
export function milestonesAt(milestones, birthday, unit, i) {
  const cell = cellDate(birthday, unit, i)
  const nextCell = cellDate(birthday, unit, i + 1)
  return milestones.filter((m) => cellIntersects(cell, nextCell, m.start, m.end))
}

/**
 * 日期 → 格子索引(该日期所在格)。二分,供胶囊/文章标记建 Map 用;
 * 日期在生日之前返回 -1,在跨度之外返回 count(越界,调用方忽略)。
 */
export function cellIndexOf(birthday, unit, dateLike, count) {
  const d = dateLike instanceof Date ? dateLike : parseDate(dateLike)
  let lo = 0
  let hi = count
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (cellDate(birthday, unit, mid) <= d) lo = mid + 1
    else hi = mid
  }
  return lo - 1
}

/** 构建「格子索引 → 命中标记」索引;marks 元素须带 cnDate(北京日期 'YYYY-MM-DD') */
export function buildMarkIndex(marks, birthday, unit, count) {
  const map = new Map()
  for (const m of marks || []) {
    const i = cellIndexOf(birthday, unit, m.cnDate, count)
    if (i < 0 || i >= count) continue
    if (!map.has(i)) map.set(i, [])
    map.get(i).push(m)
  }
  return map
}

/** 人生已过百分比(0~100,保留 1 位;按天精确计) */
export function lifeProgress(birthday, lifespanYears) {
  if (!birthday) return 0
  const b = parseDate(birthday)
  const total = lifespanYears * 365.25
  const lived = (Date.now() - b.getTime()) / 86400000
  return Math.max(0, Math.min(100, +((lived / total) * 100).toFixed(1)))
}

/** 已过天数(整数) */
export function daysLived(birthday) {
  if (!birthday) return 0
  return Math.max(0, Math.floor((Date.now() - parseDate(birthday).getTime()) / 86400000))
}

/**
 * 格子着色:返回颜色数组(1~2 个;2 个时上下渐变,近似原版多节点叠加)。
 * today=今天高亮色,future=未来格底色,pastEmpty=已过无节点底色。
 */
export function cellColors(milestones, birthday, unit, i, todayIdx, theme) {
  if (i === todayIdx) return [theme.today]
  const cell = cellDate(birthday, unit, i)
  if (cell > new Date()) return [theme.future]
  const hit = milestonesAt(milestones, birthday, unit, i)
  if (!hit.length) return [theme.past]
  // 多节点覆盖:取前两个做上下渐变
  return [hit[0].color, hit[1] ? hit[1].color : hit[0].color]
}

/** 气泡文案的日期格式(随粒度) */
export function cellLabel(birthday, unit, i) {
  const d = cellDate(birthday, unit, i)
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  if (unit === 1) return y + ' 年'
  if (unit === 12) return y + ' 年 ' + m + ' 月'
  if (unit === 52) return y + ' 年 第 ' + (i + 1) + ' 周'
  return y + '-' + String(m).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}
