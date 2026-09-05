import { ref, watch, onBeforeUnmount, onActivated, onDeactivated, unref } from 'vue'

/**
 * 从 DataTransfer 收集图片文件(paste/drop 共用)
 * 优先用 items.getAsFile()(paste 场景下 files 可能为空)
 */
export function collectImages(dt) {
  if (!dt) return []
  const items = Array.from(dt.items || [])
  const picks = items
    .filter(i => i.kind === 'file' && i.type.startsWith('image/'))
    .map(i => i.getAsFile())
    .filter(Boolean)
  if (picks.length) return picks
  return Array.from(dt.files || []).filter(f => f.type.startsWith('image/'))
}

/**
 * 在目标元素上启用拖拽上传,并在 document 上监听粘贴上传(组件激活期间)
 * 仅处理 image/* 文件
 *
 * @param {Ref<HTMLElement|null>} targetRef  drag 事件作用元素(如包裹 el-upload 的 div)
 * @param {(file: File) => void | Promise<void>} onImage  收到图片回调
 * @param {{ enabled?: Ref<boolean>|boolean, paste?: boolean }} opts
 *   enabled  是否启用(弹窗场景传 v-model 的 ref,关闭时不响应)
 *   paste    是否监听 document paste,默认 true
 * @returns {{ isDragover: Ref<boolean> }}
 */
export function useImageDropPaste(targetRef, onImage, opts = {}) {
  const isDragover = ref(false)
  let depth = 0
  let el = null

  const enabled = typeof opts.enabled === 'function'
    ? opts.enabled
    : () => (opts.enabled === undefined ? true : !!unref(opts.enabled))
  const usePaste = opts.paste !== false

  const hasImage = (dt) =>
    Array.from(dt?.items || []).some(i => i.kind === 'file' && i.type.startsWith('image/'))

  function onDragOver(e) {
    if (!enabled() || !hasImage(e.dataTransfer)) return
    e.preventDefault() // 必须,否则 drop 不触发
    isDragover.value = true
  }
  function onDragEnter(e) {
    if (!enabled() || !hasImage(e.dataTransfer)) return
    e.preventDefault()
    depth++
    isDragover.value = true
  }
  function onDragLeave() {
    depth = Math.max(0, depth - 1)
    if (depth === 0) isDragover.value = false
  }
  function onDrop(e) {
    const imgs = collectImages(e.dataTransfer)
    if (!enabled() || !imgs.length) return
    e.preventDefault()
    e.stopPropagation()
    depth = 0
    isDragover.value = false
    imgs.forEach(onImage)
  }
  function onPaste(e) {
    if (!enabled() || e.defaultPrevented) return // 编辑器等已处理则跳过,避免双重插入
    const dt = e.clipboardData
    // 剪贴板同时含文本(如从 Word 复制图文)时让默认 paste 优先,避免抢断文本粘贴
    const hasText = Array.from(dt?.items || []).some(i => i.kind === 'string')
    if (hasText) return
    const imgs = collectImages(dt)
    if (!imgs.length) return
    e.preventDefault()
    e.stopPropagation()
    imgs.forEach(onImage)
  }

  let listening = false

  function attach() {
    if (!el || listening) return
    el.addEventListener('dragenter', onDragEnter)
    el.addEventListener('dragover', onDragOver)
    el.addEventListener('dragleave', onDragLeave)
    el.addEventListener('drop', onDrop)
    if (usePaste) document.addEventListener('paste', onPaste)
    listening = true
  }
  function detach() {
    if (!listening) return
    el?.removeEventListener('dragenter', onDragEnter)
    el?.removeEventListener('dragover', onDragOver)
    el?.removeEventListener('dragleave', onDragLeave)
    el?.removeEventListener('drop', onDrop)
    if (usePaste) document.removeEventListener('paste', onPaste)
    listening = false
  }
  function bind(target) {
    detach()
    el = target
    attach()
  }
  function unbind() {
    detach()
    el = null
  }

  // 弹窗场景下 targetRef 在 dialog 首次打开后才指向真实 DOM
  watch(targetRef, (t) => bind(t), { immediate: true })
  onBeforeUnmount(unbind)
  // keep-alive 场景:页面被缓存(切走但未卸载)时解绑 document 级监听,
  // 避免隐藏页面的 paste 监听抢断其它页面的粘贴;回来时重绑。
  // 非 keep-alive 组件这两个钩子不会触发,行为不变。
  onActivated(attach)
  onDeactivated(detach)

  return { isDragover }
}
