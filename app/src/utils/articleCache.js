/**
 * 文章详情离线快照:per-id 存储 + 30 篇 LRU。
 *
 * 为什么 per-id 而非单 key:content_html 单篇可能几十 KB,进阅读页只读当前 id,
 * 避免每次加载都解析 MB 级 JSON。超过上限按最后访问时间淘汰最旧篇。
 */
const PREFIX = 'yinyu_article_'
const IDX_KEY = 'yinyu_article_idx'
const MAX_ARTICLES = 30

function readIdx() {
  try {
    return JSON.parse(uni.getStorageSync(IDX_KEY) || '{}') || {}
  } catch (e) {
    return {}
  }
}
function writeIdx(idx) {
  try {
    uni.setStorageSync(IDX_KEY, JSON.stringify(idx))
  } catch (e) {
    /* ignore */
  }
}

export function getArticleSnap(id) {
  try {
    return JSON.parse(uni.getStorageSync(PREFIX + id) || 'null') || null
  } catch (e) {
    return null
  }
}

export function setArticleSnap(id, data) {
  try {
    uni.setStorageSync(PREFIX + id, JSON.stringify(data))
    const idx = readIdx()
    idx[id] = Date.now()
    // 超上限:按时间升序淘汰最旧
    const keys = Object.keys(idx).sort((a, b) => idx[a] - idx[b])
    while (keys.length > MAX_ARTICLES) {
      const old = keys.shift()
      uni.removeStorageSync(PREFIX + old)
      delete idx[old]
    }
    writeIdx(idx)
  } catch (e) {
    /* ignore */
  }
}

export function clearArticleSnaps() {
  try {
    const idx = readIdx()
    Object.keys(idx).forEach((id) => uni.removeStorageSync(PREFIX + id))
    uni.removeStorageSync(IDX_KEY)
  } catch (e) {
    /* ignore */
  }
}
