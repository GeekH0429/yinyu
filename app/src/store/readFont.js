/**
 * 阅读字号档位(阅读页 Aa + 设置页「阅读字号」共用)。
 *
 * 设计:
 *  - 六档:小/中/大/较大/特大/超大,size 非均匀递增(大字号区间感知差异阈值更高)。
 *  - 模块级 fontIdx ref + computed fontLevel/fontSize/fontLine,两处引用同一份状态,
 *    任一页改动,另一页再进入时自动同步(本身两页不会同时挂载,reload 也读 storage)。
 *  - storage 只存 size 数值(不存 index),即使将来档位顺序/数量调整,旧值能命中就命中,
 *    命中不了就回退默认「大」。
 */
import { ref, computed } from 'vue'

const KEY = 'yinyu_read_font'

export const FONT_LEVELS = [
  { label: '小',   size: 32, line: 1.85 },
  { label: '中',   size: 38, line: 1.9 },
  { label: '大',   size: 44, line: 2.0 },
  { label: '较大', size: 52, line: 2.1 },
  { label: '特大', size: 60, line: 2.2 },
  { label: '超大', size: 68, line: 2.3 }
]

const DEFAULT_IDX = 2 // 默认「大」

function readStoredIdx() {
  const stored = uni.getStorageSync(KEY)
  if (typeof stored === 'number') {
    const i = FONT_LEVELS.findIndex((l) => l.size === stored)
    if (i >= 0) return i
  }
  return DEFAULT_IDX
}

export const fontIdx = ref(readStoredIdx())
export const fontLevel = computed(() => FONT_LEVELS[fontIdx.value])
export const fontSize = computed(() => fontLevel.value.size)
export const fontLine = computed(() => fontLevel.value.line)

/** 同时改内存值 + 落盘(拖动场景应分别调用 setFontIdxLive + setFontIdxCommit 控制 IO) */
export function setFontIdx(idx) {
  fontIdx.value = idx
  uni.setStorageSync(KEY, fontLevel.value.size)
}

/** 拖动中:只改内存,不落盘 */
export function setFontIdxLive(idx) {
  fontIdx.value = idx
}

/** 释放:落盘当前档位 */
export function setFontIdxCommit(idx) {
  fontIdx.value = idx
  uni.setStorageSync(KEY, fontLevel.value.size)
}
