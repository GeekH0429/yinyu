<template>
  <image
    :src="displaySrc"
    :lazy-load="lazyLoad"
    :style="ratioStyle"
    class="cached-img"
    @error="onErr"
  />
</template>

<script setup>
/**
 * 透明替换 <image>:套一层本地资源缓存(仅 App 真机生效) + 加载占位/失败兜底。
 *
 * 首屏先用远程 src 渲染(不阻塞),后台异步解析到本地路径后切换;
 * 缓存命中后,二次进入/冷启动即用本地。@error 兜底:本地失联回退远程并重缓存;
 * 远程仍失败则切透明占位,露出暖色 background 作为兜底块(避免破图)。
 *
 * 保持 <image> 为单根节点:mode / class / style 仍自动透传。
 * lazy-load 默认开(列表场景必备);首屏可见的大图可显式 :lazy-load="false"。
 * ratio(宽高比,如 16/9)给定时撑 aspect-ratio 占位,避免图片加载完才撑高造成布局抖动(CLS)。
 *   <CachedImage :src="a.cover_url" mode="aspectFill" ratio="1.6" class="cover" />
 */
import { ref, computed, watch, onMounted } from 'vue'
import { resourceUrl, isRemoteUrl } from '../config'
import { getCachedResource } from '../utils/resourceCache'

const props = defineProps({
  src: { type: String, default: '' },
  lazyLoad: { type: Boolean, default: true },
  ratio: { type: Number, default: 0 }
})

// 1x1 透明占位:失败时切到它,露出 .cached-img 的暖色背景作为兜底块
const TRANSPARENT =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

const localPath = ref('')
const failed = ref(false)
// 远程完整 URL:相对路径补全,已是 http(或协议相对)的原样
const remote = computed(() => {
  const s = props.src
  if (!s) return ''
  return isRemoteUrl(s) ? s : resourceUrl(s)
})
const useSrc = computed(() => localPath.value || remote.value)
const displaySrc = computed(() => (failed.value ? TRANSPARENT : useSrc.value))

// 宽高比占位:aspect-ratio 是现代 CSS 标准属性
// H5 现代浏览器完美支持;不支持的环境会降级为「图加载完才撑高」(原行为,不崩)
const ratioStyle = computed(() => (props.ratio > 0 ? `aspect-ratio:${props.ratio};` : ''))

function resolve() {
  const url = remote.value
  if (!url) {
    localPath.value = ''
    return
  }
  getCachedResource(url, 'image')
    .then((p) => {
      // 命中本地(返回值与远程不同)才切换;否则保持远程
      if (p && p !== url) localPath.value = p
    })
    .catch(() => {})
}

watch(
  () => props.src,
  () => {
    localPath.value = ''
    failed.value = false
    resolve()
  }
)

onMounted(resolve)

function onErr() {
  // 本地文件读取失败兜底:回退远程,并后台重缓存(下次命中)
  if (localPath.value) {
    localPath.value = ''
    getCachedResource(remote.value, 'image').catch(() => {})
    return
  }
  // 远程也失败:切透明占位,露出暖色背景作为兜底块,避免破图
  failed.value = true
}
</script>

<style scoped>
.cached-img {
  background: #efe9df;
}
</style>
