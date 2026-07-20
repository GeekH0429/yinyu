/**
 * 跨端录音(H5 / App,不考虑小程序)。
 * - H5:MediaRecorder → Blob → File(webm/opus,部分浏览器 mp4/ogg)
 * - App:uni.getRecorderManager → 临时文件(mp3)
 *
 * 用法:
 *   await startRecord({ onTick: (sec) => ... })
 *   const r = await stopRecord()   // { file?, path?, filename, mimeType, duration }
 *   await cancelRecord()           // 放弃
 */
let mode = null
let tickFn = null
let timer = null
let startedAt = 0

let h5rec = null
let h5stream = null
let h5chunks = null
let appMgr = null

function clearTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function h5Supported() {
  return (
    typeof navigator !== 'undefined' &&
    navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia &&
    typeof MediaRecorder !== 'undefined'
  )
}

export function isRecordingSupported() {
  return h5Supported() || typeof uni.getRecorderManager === 'function'
}

function mimeExt(mime) {
  if (!mime) return 'audio'
  if (mime.includes('webm')) return 'webm'
  if (mime.includes('ogg')) return 'ogg'
  if (mime.includes('mp4') || mime.includes('m4a')) return 'm4a'
  if (mime.includes('mpeg') || mime.includes('mp3')) return 'mp3'
  return 'audio'
}

export function startRecord({ onTick } = {}) {
  tickFn = onTick || (() => {})
  startedAt = Date.now()

  if (h5Supported()) {
    mode = 'h5'
    h5chunks = []
    return navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        h5stream = stream
        h5rec = new MediaRecorder(stream)
        h5rec.ondataavailable = (e) => {
          if (e.data && e.data.size) h5chunks.push(e.data)
        }
        timer = setInterval(() => tickFn(Math.floor((Date.now() - startedAt) / 1000)), 250)
        h5rec.start()
      })
      .catch((e) => {
        mode = null
        throw e
      })
  }

  if (typeof uni.getRecorderManager === 'function') {
    mode = 'app'
    appMgr = uni.getRecorderManager()
    timer = setInterval(() => tickFn(Math.floor((Date.now() - startedAt) / 1000)), 250)
    appMgr.start({ duration: 60000, format: 'mp3', sampleRate: 44100, numberOfChannels: 1 })
    return Promise.resolve()
  }

  return Promise.reject(new Error('当前环境不支持录音'))
}

export function stopRecord() {
  clearTimer()
  return new Promise((resolve, reject) => {
    if (mode === 'h5') {
      const finish = () => {
        const mime =
          h5rec && h5rec.mimeType && h5rec.mimeType.startsWith('audio')
            ? h5rec.mimeType
            : 'audio/webm'
        const blob = new Blob(h5chunks || [], { type: mime })
        const ext = mimeExt(mime)
        const file = new File([blob], `record_${Date.now()}.${ext}`, { type: mime })
        if (h5stream) {
          h5stream.getTracks().forEach((t) => t.stop())
          h5stream = null
        }
        h5rec = null
        h5chunks = null
        mode = null
        resolve({
          file,
          filename: file.name,
          mimeType: mime,
          duration: Math.floor((Date.now() - startedAt) / 1000)
        })
      }
      if (h5rec && h5rec.state !== 'inactive') {
        h5rec.onstop = finish
        h5rec.stop()
      } else {
        finish()
      }
    } else if (mode === 'app' && appMgr) {
      appMgr.onStop = (res) => {
        mode = null
        resolve({
          path: res.tempFilePath,
          filename: 'record.mp3',
          mimeType: 'audio/mpeg',
          duration: Math.floor((res.duration || Date.now() - startedAt) / 1000)
        })
      }
      appMgr.stop()
    } else {
      reject(new Error('未在录音'))
    }
  })
}

export function cancelRecord() {
  clearTimer()
  if (mode === 'h5') {
    if (h5rec && h5rec.state !== 'inactive') {
      try {
        h5rec.stop()
      } catch {
        /* ignore */
      }
    }
    if (h5stream) {
      h5stream.getTracks().forEach((t) => t.stop())
      h5stream = null
    }
    h5rec = null
    h5chunks = null
  } else if (mode === 'app' && appMgr) {
    try {
      appMgr.stop()
    } catch {
      /* ignore */
    }
  }
  mode = null
}
