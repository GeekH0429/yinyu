/**
 * 把 App 端 textarea 写出的内容整理成结构化 HTML。
 *
 * 背景:App 写作用原生 <textarea v-model="content_html">,用户敲回车产生的是 \n。
 * 但 content_html 按 HTML 渲染(mp-html),\n 会被当成普通空白折叠 →
 * 「写了好几行,读出来全挤在一行」。这里在提交前把纯文本转成 <p> 段落。
 *
 * 内容里同时混着「单行媒体 HTML」(图片 <p><img/></p>、音频卡片
 * <div class="yinyu-audio">…</div>),它们本身没有 \n,且必须原样保留。
 * 所以用正则先把块级 HTML 切出来,只对中间的纯文本段做段落化。
 */

// 文本内容转义(属性串已在别处处理;这里只管文本节点)
function escText(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// 一段纯文本 → 若干 <p>:空行分段,段内单换行用 <br/>
function textToHtml(seg) {
  if (!seg || !seg.trim()) return ''
  return seg
    .split(/\n{2,}/) // 连续空行 = 段落分隔
    .map((para) => {
      const lines = para
        .split('\n')
        .map((l) => escText(l.trim()))
        .filter(Boolean)
      return lines.length ? `<p>${lines.join('<br/>')}</p>` : ''
    })
    .filter(Boolean)
    .join('')
}

/**
 * 块级 HTML 切分:图片 <p><img/></p>、裸 <img>、音频卡片 <div class="yinyu-audio">。
 * 音频卡片内部不嵌套 <div>,故 [\s\S]*? 到首个 </div> 即整张卡片。
 */
const BLOCK_RE = /(<div\b[^>]*>[\s\S]*?<\/div>|<p\b[^>]*>[\s\S]*?<\/p>|<img\b[^>]*\/?>)/gi

export function normalizeContentHtml(raw) {
  if (!raw) return ''
  const s = String(raw).replace(/\r\n/g, '\n').replace(/\r/g, '\n')

  // split 带捕获组 → [文本, 块, 文本, 块, …];块在奇数下标
  const parts = s.split(BLOCK_RE)
  const out = []
  parts.forEach((part, i) => {
    if (!part) return
    if (i % 2 === 1) out.push(part) // 块级 HTML,原样保留
    else out.push(textToHtml(part)) // 纯文本段 → 段落
  })
  return out.filter(Boolean).join('')
}
