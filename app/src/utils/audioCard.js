import { resourceUrl } from '../config'

/**
 * 音频卡片 —— App 端的「构建 + 解析」单一源头。
 *
 * 卡片 HTML 契约(与 web-admin/src/components/tiptap/Audio.js 的 renderHTML 完全一致):
 *   <div class="yinyu-audio" data-src data-title data-artist data-cover style="...">
 *     <img|span占位> <span body> [名称 歌手 <audio>] </span>
 *   </div>
 *
 * 硬约束:外层只有一个 <div>,内部只用 <img>/<span>/<audio>,绝不嵌套 <div>。
 * 这样 extractAudio 的整段正则 /<div class="yinyu-audio"...>...<\/div>/ 才能可靠匹配。
 * App 端阅读时整张卡片被剥除交给 AudioPlayer 渲染,所以内联样式其实不参与 App 显示,
 * 但保留与 web 一致,以便文章在 Web 侧直接渲染或被 TipTap 回填编辑时样子正确。
 *
 * 样式常量必须与 web-admin/Audio.js 逐字一致(改一处记得两边同步)。
 */
const WRAP_STYLE =
  'display:flex;align-items:center;gap:12px;padding:12px;margin:10px 0;' +
  'border:1px solid #f3dce6;border-radius:12px;background:#fffafc;'
const COVER_STYLE =
  'width:64px;height:64px;border-radius:10px;object-fit:cover;flex:0 0 64px;background:#f6e3ec;'
const PLACEHOLDER_STYLE =
  'width:64px;height:64px;border-radius:10px;flex:0 0 64px;' +
  'background:linear-gradient(135deg,#f3dce6,#e7c9d8);display:flex;align-items:center;' +
  'justify-content:center;font-size:28px;line-height:1;'
const BODY_STYLE =
  'flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px;'
const TITLE_STYLE =
  'font-size:15px;font-weight:600;color:#4a3b42;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
const ARTIST_STYLE =
  'font-size:13px;color:#a98c96;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
const EL_STYLE = 'width:100%;margin-top:2px;'

// 转义:同时适用于双引号属性值与文本内容
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 构造一张音频卡片 HTML(可直接拼进 content_html)。
 * src 必填;title/artist/cover 可选。
 */
export function buildAudioCard({ src, title, artist, cover }) {
  const t = esc(title)
  const a = esc(artist)

  const body = []
  if (title) body.push(`<span style="${TITLE_STYLE}">${t}</span>`)
  if (artist) body.push(`<span style="${ARTIST_STYLE}">${a}</span>`)
  if (src) body.push(`<audio src="${esc(src)}" controls="controls" style="${EL_STYLE}"></audio>`)

  const left = cover
    ? `<img src="${esc(cover)}" alt="${t}" style="${COVER_STYLE}"/>`
    : `<span style="${PLACEHOLDER_STYLE}">🎵</span>`

  return (
    `<div class="yinyu-audio" data-src="${esc(src)}" data-title="${t}" ` +
    `data-artist="${a}" data-cover="${esc(cover || '')}" style="${WRAP_STYLE}">` +
    left +
    `<span style="${BODY_STYLE}">${body.join('')}</span>` +
    `</div>`
  )
}

// 解码常见 HTML 实体(buildAudioCard 会转义 data-* 属性值)
function decodeEntities(s) {
  if (!s) return ''
  return s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
}

function pickData(attrs, key) {
  const m = attrs.match(new RegExp('data-' + key + '=["\']([^"\']*)["\']', 'i'))
  return m ? decodeEntities(m[1]) : ''
}

/**
 * 从富文本中抽取所有音频卡片,并返回剥除卡片后的干净 HTML。
 * 由 AudioPlayer 负责渲染控件,mp-html 只渲染图文,避免双重渲染。
 */
export function extractAudio(html) {
  if (!html) return { audioList: [], html: '' }

  const audioList = []
  let id = 0
  let m

  // 整段匹配(无嵌套 div,首个 </div> 即卡片闭合)
  const cardRe = /<div\s+class="yinyu-audio"([^>]*)>([\s\S]*?)<\/div>/gi
  while ((m = cardRe.exec(html)) !== null) {
    const attrs = m[1]
    const src = pickData(attrs, 'src')
    if (!src) continue
    const cover = pickData(attrs, 'cover')
    audioList.push({
      id: id++,
      src,
      fullSrc: resourceUrl(src),
      title: pickData(attrs, 'title'),
      artist: pickData(attrs, 'artist'),
      cover: cover || null,
      fullCover: cover ? resourceUrl(cover) : null
    })
  }
  const cleaned = html.replace(cardRe, '')

  return { audioList, html: cleaned }
}
