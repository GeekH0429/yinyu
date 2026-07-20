/** 选图 / 选音频的跨端封装(写作页、树洞页共用)。 */

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
    if (typeof uni.chooseMessageFile === 'function') {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        success: (res) => resolve(res.tempFiles[0].path || res.tempFiles[0]),
        fail: reject
      })
    } else if (typeof uni.chooseFile === 'function') {
      uni.chooseFile({
        count: 1,
        success: (res) => {
          if (res.tempFilePaths) resolve(res.tempFilePaths[0])
          else resolve(res.tempFiles[0].path || res.tempFiles[0])
        },
        fail: reject
      })
    } else {
      uni.showToast({ title: '当前环境暂不支持选择音频', icon: 'none' })
      reject(new Error('no audio picker'))
    }
  })
}
