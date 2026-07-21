/**
 * HTTP 请求封装(适配 yinyu FastAPI 后端)。
 *
 * 与 pig-blog 的差异:yinyu 后端 2xx 直接返回业务对象(无 {code,data} 信封),
 * 错误为 {code, detail} + HTTP 状态码。401 时用 refresh_token 自动续期并重放一次。
 */
import { API_BASE } from '../config'

function getToken() {
  return uni.getStorageSync('token') || ''
}
function getRefresh() {
  return uni.getStorageSync('refresh_token') || ''
}

function clearAuth() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refresh_token')
  uni.removeStorageSync('userInfo')
}

function toast(detail) {
  const msg = typeof detail === 'string' ? detail : detail?.message || detail?.detail || '请求失败'
  uni.showToast({ title: msg, icon: 'none' })
}

/** 用 refresh_token 换一对新 token。成功返回 true。 */
function tryRefresh() {
  const refresh = getRefresh()
  if (!refresh) return Promise.resolve(false)
  return new Promise((resolve) => {
    uni.request({
      url: API_BASE + '/auth/refresh',
      method: 'POST',
      data: { refresh_token: refresh },
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.access_token) {
          uni.setStorageSync('token', res.data.access_token)
          uni.setStorageSync('refresh_token', res.data.refresh_token)
          resolve(true)
        } else {
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
  })
}

function request(options) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json', ...(options.header || {}) }
    const token = getToken()
    if (token) header.Authorization = `Bearer ${token}`

    uni.request({
      url: API_BASE + options.url,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: async (res) => {
        // 2xx:直接返回业务对象
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        // 401:尝试续期后重放一次(登录/刷新接口自身 401 不重放)
        const isAuthCall =
          options.url.startsWith('/auth/login') || options.url.startsWith('/auth/refresh')
        if (res.statusCode === 401 && !options.__retried && !isAuthCall) {
          const ok = await tryRefresh()
          if (ok) {
            request({ ...options, __retried: true }).then(resolve).catch(reject)
            return
          }
          clearAuth()
          uni.reLaunch({ url: '/pages/login/index' })
          reject(res.data)
          return
        }
        if (!options.__silent) toast(res.data)
        reject(res.data)
      },
      fail: (err) => {
        const msg =
          err.errMsg && err.errMsg.includes('timeout')
            ? '请求超时'
            : '网络异常,请检查网络或服务器地址'
        if (!options.__silent) uni.showToast({ title: msg, icon: 'none' })
        reject(err)
      }
    })
  })
}

/** 上传文件(filePath 为 uni.chooseImage/chooseMessageFile 返回的临时路径或 H5 的 File 对象)。 */
function upload(filePath, url = '/upload') {
  return new Promise((resolve, reject) => {
    // #ifdef H5
    // H5 环境下如果是 File 对象，使用 uploadBlob
    if (filePath instanceof File) {
      uploadBlob(filePath, filePath.name, url).then(resolve).catch(reject)
      return
    }
    // #endif

    const token = getToken()
    uni.uploadFile({
      url: API_BASE + url,
      filePath,
      name: 'file',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data))
          } catch (e) {
            reject(e)
          }
        } else {
          try {
            reject(JSON.parse(res.data))
          } catch {
            reject(res.data)
          }
        }
      },
      fail: reject
    })
  })
}

/** H5 录音等已拿到 File/Blob 的场景:fetch + FormData 上传(不设 Content-Type,让浏览器带 boundary)。 */
function uploadBlob(file, filename, url = '/upload') {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const form = new FormData()
    form.append('file', file, filename || file.name || 'file')
    fetch(API_BASE + url, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
      .then((r) => r.json().then((data) => (r.ok ? resolve(data) : reject(data))))
      .catch(reject)
  })
}

export default {
  get: (url, data, opts = {}) => request({ url, method: 'GET', data, ...opts }),
  post: (url, data, opts = {}) => request({ url, method: 'POST', data, ...opts }),
  put: (url, data, opts = {}) => request({ url, method: 'PUT', data, ...opts }),
  delete: (url, data, opts = {}) => request({ url, method: 'DELETE', data, ...opts }),
  upload,
  uploadBlob
}
