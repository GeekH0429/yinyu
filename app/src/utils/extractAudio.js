import { resourceUrl } from '../config'

/**
 * 从富文本中提取音频,并返回剥除 <audio> 后的干净 HTML。
 *
 * 由 AudioPlayer 负责渲染音频控件,mp-html 只渲染图文,
 * 避免两者各渲染一次 → 同一段音频出现两个播放器。
 */
export function extractAudio(html) {
  if (!html) return { audioList: [], html: '' }

  // 1) 收集所有音频 src(保留出现顺序)
  const audioList = []
  const srcRe = /<audio[^>]*\ssrc=["']([^"']*)["'][^>]*>/gi
  let m
  let id = 0
  while ((m = srcRe.exec(html)) !== null) {
    audioList.push({ id: id++, src: m[1], fullSrc: resourceUrl(m[1]) })
  }

  // 2) 剥除 audio 标签:<p> 单独包裹的整段优先,再清裸 audio / 自闭合,最后清残留空 <p>
  const cleaned = html
    .replace(/<p>\s*<audio[^>]*>[\s\S]*?<\/audio>\s*<\/p>/gi, '')
    .replace(/<p>\s*<audio[^>]*\/>\s*<\/p>/gi, '')
    .replace(/<audio[^>]*>[\s\S]*?<\/audio>/gi, '')
    .replace(/<audio[^>]*\/>/gi, '')
    .replace(/<audio[^>]*>/gi, '')
    .replace(/<p>\s*<\/p>/gi, '')

  return { audioList, html: cleaned }
}
