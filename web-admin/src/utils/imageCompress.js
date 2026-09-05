/**
 * 图片上传前的客户端压缩:最大边 >2000 先缩到 2000,统一重编码 webp(质量 0.85)。
 *
 * 为什么:手机照片常见 5-10MB,原样走网络、落地后才由服务端压成 1280 webp ——
 * 传输大头的原始字节全浪费了。客户端先压一道,上传字节通常砍 80%+;服务端
 * 再压到 1280 基本无二次损失(2000 给封面裁切留了少量余量)。
 *
 * 跳过:非图片、gif(canvas 会丢动画)、svg(矢量不栅格化)、<300KB 小图、
 *      压完反而更大的(已高度优化的图)。
 * 兜底:浏览器不支持 / 解码或编码失败,一律返回原文件,绝不阻塞上传。
 */

const MAX_SIDE = 2000
const QUALITY = 0.85
const MIN_BYTES = 300 * 1024

async function decode(file) {
  // 显式 from-image:按 EXIF 方向摆正;老浏览器不认该选项时降级为默认解码
  try {
    return await createImageBitmap(file, { imageOrientation: 'from-image' })
  } catch {
    return createImageBitmap(file)
  }
}

function encode(canvas, type) {
  return new Promise((resolve) => canvas.toBlob(resolve, type, QUALITY))
}

export async function compressImage(file) {
  if (!(file instanceof File || file instanceof Blob)) return file
  const type = file.type || ''
  if (!type.startsWith('image/')) return file
  if (type === 'image/gif' || type === 'image/svg+xml') return file
  if (file.size < MIN_BYTES) return file
  try {
    const bitmap = await decode(file)
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
    const w = Math.max(1, Math.round(bitmap.width * scale))
    const h = Math.max(1, Math.round(bitmap.height * scale))
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    canvas.getContext('2d').drawImage(bitmap, 0, 0, w, h)
    bitmap.close()

    let blob = await encode(canvas, 'image/webp')
    let ext = '.webp'
    // 不支持 webp 编码的浏览器(旧 Safari)toBlob 会静默回退成 png(体积可能反超)→ 改走 jpeg
    if (!blob || blob.type === 'image/png') {
      const jpg = document.createElement('canvas')
      jpg.width = w
      jpg.height = h
      const ctx = jpg.getContext('2d')
      ctx.fillStyle = '#fff' // jpeg 无 alpha:白底垫底,避免透明区域变黑
      ctx.fillRect(0, 0, w, h)
      ctx.drawImage(canvas, 0, 0)
      blob = await encode(jpg, 'image/jpeg')
      ext = '.jpg'
    }
    if (!blob || blob.size >= file.size) return file

    const base = (file.name || 'image').replace(/\.[^.]+$/, '')
    return new File([blob], base + ext, { type: blob.type, lastModified: Date.now() })
  } catch {
    return file
  }
}
