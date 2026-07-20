/** 选图 / 选音频的跨端封装(写作页、树洞页共用)。 */

// 与后端 ALLOWED_MIMES 对齐:录音文件常为 m4a/aac/flac,这里一并放行。
const AUDIO_EXT = ['mp3', 'wav', 'm4a', 'aac', 'flac']

export function chooseImage(count = 1) {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count,
      success: (res) => resolve(count === 1 ? res.tempFilePaths[0] : res.tempFilePaths),
      fail: reject
    })
  })
}

export function pickAudio() {
  return new Promise((resolve, reject) => {
    const done = (res) => {
      if (res.tempFilePaths) resolve(res.tempFilePaths[0])
      else resolve(res.tempFiles[0].path || res.tempFiles[0])
    }
    if (typeof uni.chooseMessageFile === 'function') {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: AUDIO_EXT,
        success: done,
        fail: reject
      })
    } else if (typeof uni.chooseFile === 'function') {
      uni.chooseFile({
        count: 1,
        extension: AUDIO_EXT,
        success: done,
        fail: reject
      })
    } else {
      uni.showToast({ title: '当前环境暂不支持选择音频', icon: 'none' })
      reject(new Error('no audio picker'))
    }
  })
}
