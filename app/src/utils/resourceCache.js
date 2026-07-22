/**
 * 本地资源(图片/音频)持久缓存 —— 仅 App 真机(android)生效。
 *
 * 为什么:App 是唯一阅读端,图片/音频每次走网络,二次进入/弱网体验差。
 * 这里把远程资源下载到应用私有沙箱 _doc/yinyu_cache/ 并记录 manifest,
 * 命中即返回本地绝对路径;超容量按 LRU 淘汰;文件丢失(用户清缓存)自动回退远程。
 *
 * 技术选型(App 端,已核实含 Android 13+ 约束):
 *  - plus.downloader.createDownload(url,{filename}) 一步下载到持久路径(filename 限 _doc/_downloads/_documents 开头)
 *  - _doc/ 解析为应用私有沙箱,Android 13+ Scoped Storage 下无需存储权限
 *  - plus.io.resolveLocalFileSystemURL 检测/删除文件
 *  - manifest 存 uni.setStorage(App 端底层 plus.storage 无单 key/总量限制)
 *  非 App 端(H5/小程序):降级为直接返回远程 URL(不缓存、不报错),保证不崩。
 *
 * 业务层无感知:getCachedResource(远程URL) → 返回可直接喂 <image>/InnerAudioContext.src 的路径。
 */

import { resourceUrl, isRemoteUrl } from '../config'

const DIR = '_doc/yinyu_cache/'
const MANIFEST_KEY = 'yinyu_res_manifest'
const MAX_BYTES = 200 * 1024 * 1024 // 总容量上限,可按需调整

function isHttp(s) {
  return /^https?:\/\//i.test(s)
}

/** 缓存键:剥离 query/fragment,避免 ?t=xxx 导致同资源重复缓存(uploads 当前无 token,但更健壮) */
function cacheKey(url) {
  return String(url).split('?')[0].split('#')[0]
}

/** djb2 哈希 → 幂等文件名(同 url 重下载覆盖而非堆积) */
function hashUrl(s) {
  let h = 5381
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0
  return h.toString(36)
}

/** 取扩展名;取不到按类型给默认,保证文件有后缀便于系统识别 mime */
function extOf(url, type) {
  const m = String(url).split('?')[0].match(/\.([a-zA-Z0-9]{2,5})$/)
  if (m) return '.' + m[1].toLowerCase()
  return type === 'audio' ? '.mp3' : '.bin'
}

function loadManifest() {
  try {
    return JSON.parse(uni.getStorageSync(MANIFEST_KEY) || '{}') || {}
  } catch (e) {
    return {}
  }
}

let manifest = loadManifest()
let totalBytes = 0
Object.keys(manifest).forEach((k) => {
  totalBytes += (manifest[k] && manifest[k].size) || 0
})

let persistTimer = null
function persistManifest() {
  clearTimeout(persistTimer)
  persistTimer = setTimeout(() => {
    try {
      uni.setStorageSync(MANIFEST_KEY, JSON.stringify(manifest))
    } catch (e) {
      /* ignore */
    }
  }, 500)
}

// 并发去重:同一 url 同时请求只下载一次
const inflight = new Map()

// #ifdef APP-PLUS
function fileExists(rel) {
  return new Promise((resolve) => {
    plus.io.resolveLocalFileSystemURL(rel, () => resolve(true), () => resolve(false))
  })
}

function removeFile(rel) {
  return new Promise((resolve) => {
    plus.io.resolveLocalFileSystemURL(
      rel,
      (entry) => entry.remove(() => resolve(), () => resolve()),
      () => resolve()
    )
  })
}

/** 下载并持久化;成功返回 { local, size } */
function downloadAndSave(remoteUrl, type) {
  return new Promise((resolve, reject) => {
    const rel = DIR + hashUrl(cacheKey(remoteUrl)) + extOf(remoteUrl, type)
    const task = plus.downloader.createDownload(remoteUrl, { filename: rel }, (d, status) => {
      if (status === 200 && d) {
        plus.io.resolveLocalFileSystemURL(
          d.filename,
          (entry) =>
            entry.file(
              (file) => resolve({ local: rel, size: (file && file.size) || 0 }),
              () => resolve({ local: rel, size: 0 })
            ),
          () => resolve({ local: rel, size: 0 })
        )
      } else {
        reject(new Error('download failed: ' + status))
      }
    })
    task.start()
  })
}

/** LRU:超容量按 lastUsed 升序淘汰,降到 90% 防抖动 */
function lruSweep() {
  if (totalBytes <= MAX_BYTES) return
  const entries = Object.keys(manifest)
    .map((k) => [k, manifest[k]])
    .sort((a, b) => (a[1].lastUsed || 0) - (b[1].lastUsed || 0))
  const tasks = []
  for (const item of entries) {
    if (totalBytes <= MAX_BYTES * 0.9) break
    const [k, e] = item
    if (!e) continue
    tasks.push(
      removeFile(e.local).then(() => {
        totalBytes -= e.size || 0
        delete manifest[k]
      })
    )
  }
  if (tasks.length) Promise.all(tasks).then(persistManifest)
}

// convertLocalFileSystemURL 返回无协议绝对路径(如 /storage/emulated/0/...),不带 file://。
// 必须补 file:// 前缀:
//  ① mp-html 的 getUrl 会对「不含 ://  的路径」二次拼接 domain → 请求错误地址 → 正文图挂;
//     补 file:// 后含 ://,getUrl 原样放行。
//  ② file:// 是标准本地文件 URL,<image> / InnerAudioContext 均可直接加载。
function convertUrl(rel) {
  return 'file://' + plus.io.convertLocalFileSystemURL(rel)
}

async function appGet(norm, type) {
  const key = hashUrl(cacheKey(norm))
  const entry = manifest[key]
  if (entry) {
    // 命中 manifest,先校验文件还在(用户清缓存会删文件但 manifest 留记录)
    if (await fileExists(entry.local)) {
      entry.lastUsed = Date.now()
      persistManifest()
      return convertUrl(entry.local)
    }
    // 文件丢失:删条目,落入下载
    totalBytes -= entry.size || 0
    delete manifest[key]
  }
  try {
    const { local, size } = await downloadAndSave(norm, type)
    manifest[key] = { local, size, lastUsed: Date.now(), type: type || 'image' }
    totalBytes += size
    lruSweep()
    persistManifest()
    return convertUrl(local)
  } catch (e) {
    // 下载失败:回退远程,不阻塞业务
    return norm
  }
}
// #endif

/**
 * 取资源的本地可渲染路径(命中缓存)或远程 URL(未命中/降级/失败)。
 * @param {string} remoteUrl 远程完整 URL(http/https);非 http 的本地/占位路径原样返回
 * @param {'image'|'audio'} type
 * @returns {Promise<string>} 可直接用于 <image src> / InnerAudioContext.src
 */
export function getCachedResource(remoteUrl, type = 'image') {
  const norm = remoteUrl
  if (!isHttp(norm)) return Promise.resolve(norm)

  // #ifndef APP-PLUS
  // 非 App 端(H5/小程序):不本地缓存,直接返回远程
  return Promise.resolve(norm)
  // #endif

  // #ifdef APP-PLUS
  if (inflight.has(norm)) return inflight.get(norm)
  const p = appGet(norm, type).finally(() => inflight.delete(norm))
  inflight.set(norm, p)
  return p
  // #endif
}

/** 预热(如文章详情加载后后台下载封面/音频),不阻塞渲染 */
export function prefetch(urls, type = 'image') {
  if (!Array.isArray(urls)) return
  urls.filter(Boolean).forEach((u) => {
    getCachedResource(u, type).catch(() => {})
  })
}

/** 清除全部资源缓存(设置页"清除缓存"用) */
export function clearAllResourceCache() {
  // #ifdef APP-PLUS
  const locals = Object.keys(manifest)
    .map((k) => manifest[k] && manifest[k].local)
    .filter(Boolean)
  manifest = {}
  totalBytes = 0
  persistManifest()
  locals.forEach((rel) => {
    removeFile(rel)
  })
  // #endif
}

/**
 * 同步查询本地缓存路径(仅查内存 manifest,不下载、不校验文件存在)。
 * 用于富文本 img src 的同步替换:命中即返回本地路径,未命中返回原 url。
 * 不做 fileExists 校验(那是异步的)——「清除缓存」会同步清 manifest,常规路径不裂图;
 * 极罕见的「manifest 有记录但文件被外部删除」会裂一次,后台 prefetch 会自愈。
 */
export function getCachedResourceSync(remoteUrl) {
  const norm = remoteUrl
  if (!isHttp(norm)) return norm
  // #ifndef APP-PLUS
  return norm
  // #endif
  // #ifdef APP-PLUS
  const entry = manifest[hashUrl(cacheKey(norm))]
  return entry ? convertUrl(entry.local) : norm
  // #endif
}

/** 提取 HTML 中所有 <img src> 的完整远程 URL(相对路径补全)。用于后台 prefetch 预热正文图。 */
export function extractImgUrls(html) {
  if (!html) return []
  const urls = []
  let m
  const re = /<img\b[^>]*\bsrc=["']([^"']+)["']/gi
  while ((m = re.exec(html)) !== null) {
    const url = m[1]
    if (url) urls.push(isRemoteUrl(url) ? url : resourceUrl(url))
  }
  return urls
}

/**
 * 把 HTML 里 <img src> 已缓存的远程图同步替换为本地路径(仅 App 端生效)。
 * 用于富文本(mp-html)正文图缓存:在 content 喂给 mp-html 之前调用。
 * 命中 manifest 的图换成本地路径(二次进入直接渲染本地、不再走网络);未命中保持远程。
 */
export function applyCachedImages(html) {
  if (!html) return html
  // #ifndef APP-PLUS
  return html
  // #endif
  // #ifdef APP-PLUS
  return html.replace(/<img\b[^>]*>/gi, (tag) =>
    tag.replace(/\bsrc=["']([^"']+)["']/i, (m, url) => {
      const full = isRemoteUrl(url) ? url : resourceUrl(url)
      const local = getCachedResourceSync(full)
      return local !== full ? m.replace(url, local) : m
    })
  )
  // #endif
}
