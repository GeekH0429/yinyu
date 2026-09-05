/**
 * 文字选中浮动菜单状态:长按(移动端)/拖选(桌面)出选区后,在选区上方弹小工具条。
 *
 * 选区检测在 components/SelectionObserver.vue 的 renderjs 里(App 端逻辑层没有
 * document,必须由视图层回传);本 composable 只管菜单状态、定位与动作取词:
 *  - handleSelection(payload) / handleCleared() 绑到 <SelectionObserver> 的事件
 *  - consumeSelection() 按钮动作入口:取最近一次选中文本快照并收起菜单
 *
 * 两个关键坑:
 *  - 手指点菜单按钮时,WebView 默认先清选区(selectionchange 先于 tap)→
 *    持续缓存最后一次非空选区,动作不依赖现场选区;菜单容器加 @touchstart.prevent。
 *  - 选区清空 → 菜单隐藏之间留 150ms 缓冲,给按钮点击留时间。
 */
import { ref } from 'vue'
import { onPageScroll } from '@dcloudio/uni-app'

const HIDE_DELAY = 150 // 选区清空后延迟隐藏,给按钮点击留时间
const MENU_W = 168 // 菜单尺寸(px,与页面样式保持一致)
const MENU_H = 40

export function useSelectionMenu() {
  const menu = ref({ visible: false, x: 0, y: 0, text: '' })

  let lastText = ''
  let acting = false // 按钮动作进行中:不响应隐藏
  let hideTimer = null

  /** renderjs 回传:选区文本 + 视口矩形(与菜单同一坐标系,直接定位) */
  function handleSelection(p) {
    if (acting || !p || !p.text) return
    lastText = String(p.text)
    // 选区上方居中;顶部放不下挪到下方;整体 clamp 进视口
    let x = p.left + (p.right - p.left) / 2 - MENU_W / 2
    let y = p.top - MENU_H - 12
    if (y < 10) y = p.bottom + 12
    x = Math.max(10, Math.min(x, p.vw - MENU_W - 10))
    y = Math.min(y, p.vh - MENU_H - 10)
    menu.value = { visible: true, x, y, text: lastText }
  }

  function handleCleared() {
    clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      if (!acting) menu.value.visible = false
    }, HIDE_DELAY)
  }

  // 滚动时选区通常已变/失效,直接收起
  onPageScroll(() => {
    menu.value.visible = false
  })

  /** 按钮动作入口:取走最近一次选中文本并收起菜单。 */
  function consumeSelection() {
    const t = lastText
    acting = true
    menu.value.visible = false
    setTimeout(() => {
      acting = false
    }, 600)
    return t
  }

  return { menu, consumeSelection, handleSelection, handleCleared }
}
