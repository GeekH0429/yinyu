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
    // #ifdef H5
    // H5 环境使用原生 input
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'audio/*'
    input.style.position = 'fixed'
    input.style.opacity = '0'
    input.style.pointerEvents = 'none'
    document.body.appendChild(input)

    const cleanup = () => {
      document.body.removeChild(input)
    }

    input.onchange = (e) => {
      cleanup()
      const file = e.target.files[0]
      if (file) {
        // 对于 H5，直接返回 File 对象
        resolve(file)
      } else {
        reject(new Error('no file selected'))
      }
    }

    input.oncancel = () => {
      cleanup()
      reject(new Error('user cancel'))
    }

    input.click()
    // #endif

    // #ifdef APP-PLUS
    // APP 环境：需要原生权限和文件选择
    const requestStoragePermission = () => {
      return new Promise((resolveReq, rejectReq) => {
        const systemInfo = uni.getSystemInfoSync()
        const isAndroid = systemInfo.platform === 'android'

        if (!isAndroid) {
          // iOS不需要权限请求
          resolveReq()
          return
        }

        // Android 13+ 使用新权限
        if (systemInfo.system && parseInt(systemInfo.system) >= 13) {
          // Android 13+ 使用 READ_MEDIA_AUDIO 权限
          plus.android.requestPermissions(
            ['android.permission.READ_MEDIA_AUDIO'],
            (e) => {
              if (e.granted && e.granted.length > 0) {
                resolveReq()
              } else {
                rejectReq(new Error('存储权限被拒绝'))
              }
            },
            (e) => {
              rejectReq(new Error('权限请求失败: ' + e.message))
            }
          )
        } else {
          // Android 12 及以下使用旧权限
          plus.android.requestPermissions(
            ['android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE'],
            (e) => {
              if (e.granted && e.granted.length > 0) {
                resolveReq()
              } else {
                rejectReq(new Error('存储权限被拒绝'))
              }
            },
            (e) => {
              rejectReq(new Error('权限请求失败: ' + e.message))
            }
          )
        }
      })
    }

    requestStoragePermission()
      .then(() => {
        // 权限获取成功，使用原生文件选择器
        try {
          const main = plus.android.runtimeMainActivity()
          const Intent = plus.android.importClass('android.content.Intent')

          // 创建Intent，选择音频文件
          const intent = new Intent(Intent.ACTION_GET_CONTENT)
          intent.setType('audio/*')
          intent.addCategory(Intent.CATEGORY_OPENABLE)

          // 启动文件选择器
          main.startActivityForResult(intent, 10001)

          // 监听结果
          main.onActivityResult = (requestCode, resultCode, data) => {
            if (requestCode === 10001 && resultCode === -1) {  // -1 = RESULT_OK
              try {
                const uri = data.getData()
                const uriString = uri.toString()

                // 获取文件名
                let fileName = 'audio.mp3'
                try {
                  const Cursor = plus.android.importClass('android.database.Cursor')
                  const ContentResolver = plus.android.importClass('android.content.ContentResolver')
                  const OpenableColumns = plus.android.importClass('android.provider.OpenableColumns')

                  const resolver = main.getContentResolver()
                  const projection = [OpenableColumns.DISPLAY_NAME]

                  const cursor = resolver.query(uri, projection, null, null, null)
                  if (cursor) {
                    const columnIndex = plus.android.invoke(cursor, 'getColumnIndex', OpenableColumns.DISPLAY_NAME)
                    if (cursor.moveToFirst()) {
                      fileName = plus.android.invoke(cursor, 'getString', columnIndex)
                    }
                    cursor.close()
                  }
                } catch (e) {
                  console.warn('获取文件名失败，使用默认名称:', e)
                }

                // 直接使用 content URI（uni.uploadFile 支持）
                resolve(uriString)
              } catch (err) {
                console.error('处理文件失败:', err)
                reject(new Error('处理文件失败'))
              }
            } else if (requestCode === 10001 && resultCode === 0) {
              reject(new Error('user cancel'))
            }
          }
        } catch (err) {
          console.error('启动文件选择器失败:', err)
          reject(new Error('文件选择器启动失败'))
        }
      })
      .catch((err) => {
        console.error('权限请求失败:', err)
        uni.showModal({
          title: '权限请求',
          content: '需要存储权限才能选择音频文件，请在设置中开启权限',
          showCancel: false,
        })
        reject(err)
      })
    // #endif

    // #ifdef MP-WEIXIN
    // 微信小程序环境
    uni.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: AUDIO_EXT,
      success: (res) => {
        const file = res.tempFiles[0]
        resolve(file.path)
      },
      fail: reject
    })
    // #endif
  })
}
