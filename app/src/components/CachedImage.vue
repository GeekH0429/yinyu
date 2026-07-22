<template>
  <image :src="useSrc" @error="onErr" />
</template>

<script setup>
/**
 * 透明替换 <image>:套一层本地资源缓存(仅 App 真机生效)。
 *
 * 首屏先用远程 src 渲染(不阻塞),后台异步解析到本地路径后切换;
 * 缓存命中后,二次进入/冷启动即用本地。@error 兜底:本地文件失联回退远程并触发重缓存。
 *
 * 用法与 <image> 一致:mode / lazy-load / class / style 等自动透传到内部 <image>。
 *   <CachedImage :src="a.cover_url" mode="aspectFill" lazy-load class="cover" />
 */
import { ref, computed, watch, onMounted } from 'vue'
import { resourceUrl, isRemoteUrl } from '../config'
import { getCachedResource } from '../utils/resourceCache'

const props = defineProps({
  src: { type: String, default: '' }
})

const localPath = ref('')
// 远程完整 URL:相对路径补全,已是 http(或协议相对)的原样
const remote = computed(() => {
  const s = props.src
  if (!s) return ''
  return isRemoteUrl(s) ? s : resourceUrl(s)
})
const useSrc = computed(() => localPath.value || remote.value)

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
    resolve()
  }
)

onMounted(resolve)

function onErr() {
  // 本地文件读取失败兜底:回退远程,并后台重缓存(下次命中)
  if (localPath.value) {
    localPath.value = ''
    getCachedResource(remote.value, 'image').catch(() => {})
  }
}
</script>
