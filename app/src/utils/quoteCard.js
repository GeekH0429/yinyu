/**
 * 摘抄分享卡片:canvas 绘制暖色信纸(品牌 / 引号 / 句子 / 出处 / 签名),导出图片。
 *
 * 用老 canvas API(uni.createCanvasContext),H5 / App 双端可用;页面需自带一块
 * 离屏 <canvas canvas-id="...">(fixed 在视口外,不能 v-if,否则取不到上下文)。
 * 摘抄本页与阅读页选中菜单共用这一份绘制逻辑。
 */

export const CARD_W = 600 // 逻辑宽高;导出 destWidth×2 保证清晰度
export const CARD_H = 840

/** 绘制并导出卡片,resolve 临时文件路径。text=句子,source=出处文章标题(可空)。 */
export function makeQuoteCard({ canvasId, proxy, text, source = '' }) {
  return new Promise((resolve, reject) => {
    const ctx = uni.createCanvasContext(canvasId, proxy)

    // 暖色信纸底 + 内框
    ctx.setFillStyle('#FDFBF7')
    ctx.fillRect(0, 0, CARD_W, CARD_H)
    ctx.setStrokeStyle('rgba(196,168,130,0.4)')
    ctx.setLineWidth(2)
    ctx.strokeRect(18, 18, CARD_W - 36, CARD_H - 36)

    // 顶部品牌
    ctx.setFillStyle('#C4A882')
    ctx.setTextAlign('center')
    ctx.setFontSize(30)
    ctx.font = '30px serif'
    ctx.fillText('隐 语', CARD_W / 2, 100)
    ctx.setFontSize(16)
    ctx.font = '16px sans-serif'
    ctx.fillText('✦', CARD_W / 2, 130)

    // 引号
    ctx.setFillStyle('#E8D9BE')
    ctx.setFontSize(72)
    ctx.font = '72px serif'
    ctx.setTextAlign('left')
    ctx.fillText('❝', 56, 226)

    // 句子(按字换行,超长截断)
    ctx.setFillStyle('#4A4A4A')
    ctx.setFontSize(30)
    ctx.font = '30px serif'
    const maxLines = 12
    let lines = wrapText(ctx, text, CARD_W - 130)
    if (lines.length > maxLines) lines = [...lines.slice(0, maxLines - 1), '……']
    let y = 286
    for (const ln of lines) {
      ctx.fillText(ln, 64, y)
      y += 52
    }

    // 出处(右对齐,固定压在句子区下方)
    if (source) {
      ctx.setFillStyle('#B0B0B0')
      ctx.setFontSize(24)
      ctx.font = '24px serif'
      ctx.setTextAlign('right')
      ctx.fillText('——《' + String(source).slice(0, 18) + '》', CARD_W - 60, CARD_H - 150)
    }

    // 底部签名
    ctx.setStrokeStyle('rgba(196,168,130,0.3)')
    ctx.setLineWidth(1)
    ctx.beginPath()
    ctx.moveTo(CARD_W / 2 - 40, CARD_H - 96)
    ctx.lineTo(CARD_W / 2 + 40, CARD_H - 96)
    ctx.stroke()
    ctx.setFillStyle('#C4A882')
    ctx.setFontSize(20)
    ctx.font = '20px sans-serif'
    ctx.setTextAlign('center')
    ctx.fillText('yinyu · 慢慢读,慢慢治愈', CARD_W / 2, CARD_H - 60)

    ctx.draw(false, () => {
      setTimeout(() => {
        // 等 draw 完成帧再导出
        uni.canvasToTempFilePath(
          {
            canvasId,
            width: CARD_W,
            height: CARD_H,
            destWidth: CARD_W * 2,
            destHeight: CARD_H * 2,
            success: (r) => resolve(r.tempFilePath),
            fail: reject
          },
          proxy
        )
      }, 300)
    })
  })
}

/** 保存卡片:H5 触发下载,App 存相册。自带 hideLoading 与结果 toast。 */
export function saveQuoteCard(tempPath) {
  uni.hideLoading()
  // #ifdef H5
  const a = document.createElement('a')
  a.href = tempPath
  a.download = 'yinyu-quote.png'
  document.body.appendChild(a)
  a.click()
  a.remove()
  uni.showToast({ title: '卡片已生成,正在下载 ✦', icon: 'none' })
  // #endif
  // #ifndef H5
  uni.saveImageToPhotosAlbum({
    filePath: tempPath,
    success: () => uni.showToast({ title: '已保存到相册 ✦', icon: 'none' }),
    fail: () => uni.showToast({ title: '保存失败,请检查相册权限', icon: 'none' })
  })
  // #endif
}

/** 中文友好按字符换行(measureText 逐字累积) */
function wrapText(ctx, text, maxWidth) {
  const lines = []
  let line = ''
  for (const ch of String(text || '')) {
    if (ch === '\n') {
      lines.push(line)
      line = ''
      continue
    }
    if (ctx.measureText(line + ch).width > maxWidth) {
      lines.push(line)
      line = ch
    } else {
      line += ch
    }
  }
  if (line) lines.push(line)
  return lines
}
