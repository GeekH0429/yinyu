<template>
  <image
    :src="displaySrc"
    :lazy-load="lazyLoad"
    :style="ratioStyle"
    :class="['cached-img', { loaded: loaded }]"
    @load="onLoad"
    @error="onErr"
  />
</template>

<script setup>
/**
 * 透明替换 <image>:套一层本地资源缓存(仅 App 真机生效) + 加载占位/失败兜底 + 加载完成淡入。
 *
 * 首屏先用远程 src 渲染(不阻塞),后台异步解析到本地路径后切换;
 * 缓存命中后,二次进入/冷启动即用本地。@error 兜底链:
 *   本地失联 → 回退远程并重缓存;远程(如缩略档)失败且配了 fallback → 切原图重试;
 *   仍失败则切透明占位,露出暖色 background 作为兜底块(避免破图)。
 *
 * fallback 典型场景:src 传 thumbUrl(cover_url) 缩略档,历史图没有 _s 文件(404)时回原图。
 *
 * 加载完成淡入:图片 @load 后才 opacity:1,避免突兀出现;300ms 柔和过渡。
 *
 * 保持 <image> 为单根节点:mode / class / style 仍自动透传。
 * lazy-load 默认开(列表场景必备);首屏可见的大图可显式 :lazy-load="false"。
 * ratio(宽高比,如 16/9)给定时撑 aspect-ratio 占位,避免图片加载完才撑高造成布局抖动(CLS)。
 *   <CachedImage :src="thumbUrl(a.cover_url)" :fallback="a.cover_url" mode="aspectFill" :ratio="2" class="cover" />
 */
import { ref, computed, watch, onMounted } from 'vue'
import { resourceUrl, isRemoteUrl } from '../config'
import { getCachedResource } from '../utils/resourceCache'

const props = defineProps({
  src: { type: String, default: '' },
  // 主图远程失败时的回退地址(如缩略档 404 回原图);空则不回退
  fallback: { type: String, default: '' },
  lazyLoad: { type: Boolean, default: true },
  ratio: { type: Number, default: 0 }
})

// 1x1 透明占位:失败时切到它,露出 .cached-img 的暖色背景作为兜底块
const TRANSPARENT =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

const localPath = ref('')
const failed = ref(false)
const loaded = ref(false)
// 缩略档 404 时置 true,切到 fallback 地址(src 变化时复位)
const useFallback = ref(false)
// 远程完整 URL:相对路径补全,已是 http(或协议相对)的原样
const toRemote = (s) => (!s ? '' : isRemoteUrl(s) ? s : resourceUrl(s))
const remote = computed(() => toRemote(props.src))
const fallbackRemote = computed(() => toRemote(props.fallback))
// 当前生效的远程地址:回退开启且 fallback 可用(且确与主图不同)时用 fallback
const activeRemote = computed(() =>
  useFallback.value && fallbackRemote.value && fallbackRemote.value !== remote.value
    ? fallbackRemote.value
    : remote.value
)
const useSrc = computed(() => localPath.value || activeRemote.value)
const displaySrc = computed(() => (failed.value ? TRANSPARENT : useSrc.value))

// 宽高比占位:aspect-ratio 是现代 CSS 标准属性
// H5 现代浏览器完美支持;不支持的环境会降级为「图加载完才撑高」(原行为,不崩)
const ratioStyle = computed(() => (props.ratio > 0 ? `aspect-ratio:${props.ratio};` : ''))

function resolve() {
  const url = activeRemote.value
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

// 换主图时复位 fallback 标记(否则新图会跳过缩略档直接用 fallback;值未变时赋值不触发)
watch(
  () => props.src,
  () => {
    useFallback.value = false
  }
)

// activeRemote 变化 = 换主图或进入 fallback:统一复位状态并重新解析缓存
watch(activeRemote, () => {
  localPath.value = ''
  failed.value = false
  loaded.value = false
  resolve()
})

onMounted(resolve)

function onLoad() {
  loaded.value = true
}

function onErr() {
  // 本地文件读取失败兜底:回退远程,并后台重缓存(下次命中)
  if (localPath.value) {
    localPath.value = ''
    getCachedResource(activeRemote.value, 'image').catch(() => {})
    return
  }
  // 远程主图失败(如历史图无缩略档):切 fallback 原图重试(watch activeRemote 负责换源)
  if (!useFallback.value && fallbackRemote.value && fallbackRemote.value !== remote.value) {
    useFallback.value = true
    return
  }
  // 彻底失败:切透明占位,露出暖色背景作为兜底块,避免破图
  failed.value = true
}
</script>

<style scoped>
.cached-img {
  background: #efe9df;
  /* 初始透明,加载完成后淡入 */
  opacity: 0;
  transition: opacity 0.3s var(--ease-soft, cubic-bezier(0.25, 0.46, 0.45, 0.94));
}
.cached-img.loaded {
  opacity: 1;
}
</style>
