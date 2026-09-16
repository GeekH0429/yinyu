/**
 * 统一的功能性线性图标(24 viewBox,currentColor 继承文字色)。
 *
 * 背景:此前功能图标混用 unicode 字形(✎ ✦ ❝ × ‹ ♥/♡),各平台字形粗细不一,
 * 与 TabBar/搜索的内联 SVG 放在一起观感脱节。2026-09 起功能图标统一走这里,
 * unicode 仅保留在文案/toast 里当语气点缀(✦ 等)。
 *
 * 用法:配合 components/Icon.vue —— <Icon name="chevron-left" :size="28" />
 * 线性图标:stroke 2 / round cap(TabBar 的导航图标是独立的一套 filled 风格,不在此列)。
 */
const LINE_ATTRS =
  'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'

export const ICONS = {
  // ‹ 左箭头(返回/上一月)
  'chevron-left': `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M15 5l-7 7 7 7" ${LINE_ATTRS}/></svg>`,
  // › 右箭头(列表入口/下一月)
  'chevron-right': `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M9 5l7 7-7 7" ${LINE_ATTRS}/></svg>`,
  // ✎ 铅笔(写作 FAB)
  edit: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 20h9" ${LINE_ATTRS}/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" ${LINE_ATTRS}/></svg>`,
  // × 关闭/清空
  close: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6 6l12 12M18 6L6 18" ${LINE_ATTRS}/></svg>`,
  // ♡ 点赞(线性)
  heart: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21.2l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z" ${LINE_ATTRS}/></svg>`,
  // ♥ 点赞(实心,已赞态)
  'heart-filled': `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21.2l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z" fill="currentColor"/></svg>`,
  // ✦ 四角星(实心,选区菜单"卡片"/收藏页按钮)
  sparkle: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c.8 4.5 3.5 7.2 8 8-4.5.8-7.2 3.5-8 8-.8-4.5-3.5-7.2-8-8 4.5-.8 7.2-3.5 8-8z" fill="currentColor"/></svg>`,
  // ❝ 引号(实心,选区菜单"收藏")
  quote: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6 17h3l2-4V7H5v6h3l-2 4zm8 0h3l2-4V7h-6v6h3l-2 4z" fill="currentColor"/></svg>`
}
