// 自定义"音频"原子节点 —— 渲染为带封面/名称/歌手的治愈系音频卡片
//
// 关键约定:卡片结构必须是「扁平」的 —— 外层一个 <div class="yinyu-audio">,
// 内部只用 <img>/<span>/<audio>,绝不嵌套 <div>。这样 App 端 extractAudio 的
// 正则 /<div class="yinyu-audio"...>...<\/div>/ 才能可靠地整段匹配并剥除,
// 避免封面/名称/歌手残留进 mp-html 造成重复渲染。
// 所有元信息以 data-* 形式冗余写在外层,供 App 正则解析(网页端则走 parseHTML)。
import { Node } from '@tiptap/core'

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

export const Audio = Node.create({
  name: 'audio',
  group: 'block',
  atom: true,
  selectable: true,
  draggable: true,

  addAttributes() {
    return {
      src: { default: null },
      title: { default: '' },
      artist: { default: '' },
      cover: { default: null },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div.yinyu-audio',
        getAttrs: (el) => ({
          src: el.getAttribute('data-src') || null,
          title: el.getAttribute('data-title') || '',
          artist: el.getAttribute('data-artist') || '',
          cover: el.getAttribute('data-cover') || null,
        }),
      },
      // 兼容旧版裸 <audio>(无封面/名称/歌手)
      {
        tag: 'audio[src]',
        getAttrs: (el) => ({
          src: el.getAttribute('src') || null,
          title: '',
          artist: '',
          cover: null,
        }),
      },
    ]
  },

  renderHTML({ node }) {
    const { src, title, artist, cover } = node.attrs

    const body = []
    if (title) body.push(['span', { style: TITLE_STYLE }, title])
    if (artist) body.push(['span', { style: ARTIST_STYLE }, artist])
    if (src) body.push(['audio', { src, controls: 'controls', style: EL_STYLE }])

    const children = []
    if (cover) {
      children.push(['img', { src: cover, alt: title || '', style: COVER_STYLE }])
    } else {
      children.push(['span', { style: PLACEHOLDER_STYLE }, '🎵'])
    }
    children.push(['span', { style: BODY_STYLE }, body])

    return [
      'div',
      {
        class: 'yinyu-audio',
        'data-src': src || '',
        'data-title': title || '',
        'data-artist': artist || '',
        'data-cover': cover || '',
        style: WRAP_STYLE,
      },
      children,
    ]
  },

  addCommands() {
    return {
      setAudio:
        (options) =>
        ({ commands }) =>
          commands.insertContent([
            {
              type: 'audio',
              attrs: {
                src: options.src,
                title: options.title || '',
                artist: options.artist || '',
                cover: options.cover || null,
              },
            },
            { type: 'paragraph' },
          ]),
    }
  },
})

export default Audio
