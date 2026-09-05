<template>
  <!-- 无渲染:承载 renderjs。clearSignal 变更时由视图层清除原生选区(逻辑层无 DOM) -->
  <view
    :clear-signal="clearSignal"
    :change:clear-signal="selProxy.onClearSignal"
    style="display: none"
  ></view>
</template>

<script>
/**
 * 选区观察者:把 selectionchange 从视图层带回逻辑层;并承接逻辑层的"清除选区"指令。
 *
 * 为什么必须 renderjs:App 端逻辑层运行在独立 JS 引擎,没有 document/window,
 * 直接 addEventListener 会 TypeError;renderjs 跑在页面 WebView(视图层)里,
 * 有完整 DOM,经 owner.callMethod 把选区文本 + 视口坐标回传。
 * H5 端 renderjs 同样工作(同一上下文)。小程序端 renderjs 被忽略 → 不发事件,无副作用。
 *
 * 双向通道:
 *   视图→逻辑:owner.callMethod(onRlSelection / onRlCleared)
 *   逻辑→视图:clearSignal prop 自增 → :change:clear-signal 触发 renderjs 清选区
 * (点摘抄/做卡片后必须清掉原生选区,否则选择手柄和系统复制菜单一直挂着)
 */
export default {
  props: {
    clearSignal: { type: Number, default: 0 }
  },
  methods: {
    onRlSelection(p) {
      this.$emit('selection', p)
    },
    onRlCleared() {
      this.$emit('cleared')
    }
  }
}
</script>

<script module="selProxy" lang="renderjs">
export default {
  methods: {
    /** 逻辑层要求清除原生选区:removeAllRanges 后手柄/高亮/系统菜单一起消失 */
    onClearSignal(val) {
      if (!val) return
      try {
        const sel = document.getSelection()
        if (sel) sel.removeAllRanges()
      } catch (e) {
        /* ignore */
      }
    }
  },
  mounted() {
    const owner = this.$ownerInstance
    let timer = null
    const check = () => {
      let text = ''
      let rect = null
      try {
        const sel = document.getSelection()
        text = sel ? String(sel.toString() || '').trim() : ''
        if (sel && sel.rangeCount > 0 && text) {
          rect = sel.getRangeAt(0).getBoundingClientRect()
        }
      } catch (e) {
        text = ''
      }
      if (text && text.length >= 2 && rect && rect.width > 0) {
        owner.callMethod('onRlSelection', {
          text: text.slice(0, 500),
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
          vw: window.innerWidth,
          vh: window.innerHeight
        })
      } else {
        owner.callMethod('onRlCleared')
      }
    }
    document.addEventListener('selectionchange', () => {
      clearTimeout(timer)
      timer = setTimeout(check, 200)
    })
  }
}
</script>
