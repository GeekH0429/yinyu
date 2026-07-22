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

// 单飞:并发请求同时 401 时,只让第一个去刷新 token,其余入队等结果
// (refresh_token 用过即轮换,并发刷新第二个必失败 → 误判登出)
let refreshing = false
let waitingQueue = []

function notifyQueue(ok) {
  const q = waitingQueue
  waitingQueue = []
  q.forEach(({ resolve, reject, options }) => {
    if (ok) request({ ...options, __retried: true }).then(resolve).catch(reject)
    else reject({ detail: '登录已过期' })
  })
}

function request(options) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json', ...(options.header || {}) }
    const token = getToken()
    if (token) header.Authorization = `Bearer ${token}`

    const method = (options.method || 'GET').toUpperCase()
    // 超时:GET 默认 12s,其它默认 20s;允许 options.timeout 覆盖
    // uni.request 的 timeout 既控制连接又控制整体,超时后 fail 回调 errMsg 含 'timeout'
    const timeout = options.timeout || (method === 'GET' ? 12000 : 20000)
    // GET 类查询接口允许一次静默重试(5xx/网络异常),写操作(POST/PUT/DELETE)不重试避免重复提交
    const allowRetry = method === 'GET' && !options.__retried

    const doRequest = (retryCount) => {
      uni.request({
        url: API_BASE + options.url,
        method,
        data: options.data,
        header,
        timeout,
        success: async (res) => {
          // 2xx:直接返回业务对象
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
            return
          }
          // 401:单飞续期后重放一次(登录/刷新接口自身 401 不重放)
          const isAuthCall =
            options.url.startsWith('/auth/login') || options.url.startsWith('/auth/refresh')
          if (res.statusCode === 401 && !options.__retried && !isAuthCall) {
            if (refreshing) {
              // 已有刷新在进行:直接把外层 resolve/reject 入队
              // 注意:不能 new 新 Promise(原代码的 bug —— 外层 Promise 永远 pending)
              waitingQueue.push({ resolve, reject, options })
              return // 仅退出 success 回调;外层 Promise 由 notifyQueue 结算
            }
            refreshing = true
            const ok = await tryRefresh()
            refreshing = false
            if (ok) {
              notifyQueue(true)
              request({ ...options, __retried: true }).then(resolve).catch(reject)
              return
            }
            notifyQueue(false)
            clearAuth()
            uni.reLaunch({ url: '/pages/login/index' })
            reject(res.data)
            return
          }
          // 5xx:GET 静默重试一次(瞬时服务器错误常见,重试能救回一部分)
          if (allowRetry && retryCount === 0 && res.statusCode >= 500) {
            setTimeout(() => doRequest(1), 500)
            return
          }
          if (!options.__silent) toast(res.data)
          reject(res.data)
        },
        fail: (err) => {
          // 网络异常/超时:GET 重试一次
          if (allowRetry && retryCount === 0) {
            setTimeout(() => doRequest(1), 500)
            return
          }
          const msg =
            err.errMsg && err.errMsg.includes('timeout')
              ? '请求超时'
              : '网络异常,请检查网络或服务器地址'
          if (!options.__silent) uni.showToast({ title: msg, icon: 'none' })
          reject(err)
        }
      })
    }
    doRequest(0)
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
