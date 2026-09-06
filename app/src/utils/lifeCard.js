/**
 * 人生进度分享卡:canvas 绘制暖色卡片(品牌 / 大百分比 / 已过天数 / 签名),导出图片。
 *
 * 与摘抄卡片(utils/quoteCard.js)同一套老 canvas API 管线:
 * 页面需自带一块离屏 <canvas canvas-id="lifeCard">(fixed 在视口外,不能 v-if)。
 */

export const CARD_W = 600
export const CARD_H = 760

// 导出前等待:同 quoteCard 的端差异处理
let EXPORT_WAIT_MS = 120
// #ifdef H5
EXPORT_WAIT_MS = 0
// #endif
// #ifdef APP-PLUS
EXPORT_WAIT_MS = 60
// #endif

/**
 * 绘制并导出卡片。progress=0~100,.daysLived=已过天数, .bornText='生于 1996-06'。
 */
export function makeLifeCard({ canvasId, proxy, progress, daysLived, bornText, leftText }) {
  return new Promise((resolve, reject) => {
    const ctx = uni.createCanvasContext(canvasId, proxy)

    // 暖色纸底 + 内框
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
    ctx.fillText('隐 语', CARD_W / 2, 96)
    ctx.setFontSize(16)
    ctx.font = '16px sans-serif'
    ctx.fillText('✦', CARD_W / 2, 126)

    // 大百分比
    ctx.setFillStyle('#4A4A4A')
    ctx.setFontSize(150)
    ctx.font = '150px serif'
    ctx.fillText(progress.toFixed(1) + '%', CARD_W / 2, 320)

    ctx.setFillStyle('#C4A882')
    ctx.setFontSize(26)
    ctx.font = '26px serif'
    ctx.fillText('的人生已经走过', CARD_W / 2, 372)

    // 已过天数
    ctx.setFillStyle('#8D8D8D')
    ctx.setFontSize(24)
    ctx.font = '24px serif'
    ctx.fillText('已走过 ' + daysLived.toLocaleString() + ' 天 · ' + bornText, CARD_W / 2, 448)

    // 一句轻的话
    ctx.setFillStyle('#B0B0B0')
    ctx.setFontSize(22)
    ctx.font = '22px serif'
    ctx.fillText(leftText, CARD_W / 2, 508)

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
    ctx.fillText('yinyu · 珍惜当下的美好生活', CARD_W / 2, CARD_H - 60)

    ctx.draw(false, () => {
      setTimeout(exportCanvas, EXPORT_WAIT_MS)
      function exportCanvas() {
        uni.canvasToTempFilePath(
          {
            canvasId,
            width: CARD_W,
            height: CARD_H,
            destWidth: CARD_W * 2,
            destHeight: CARD_H * 2,
            fileType: 'jpg',
            quality: 0.92,
            success: (r) => resolve(r.tempFilePath),
            fail: reject
          },
          proxy
        )
      }
    })
  })
}
