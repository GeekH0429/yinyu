import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 20000
})

let refreshing = false
let waitingQueue = []

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function redirectToLogin() {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh')
  localStorage.removeItem('user')
  if (location.pathname !== '/login') {
    location.href = '/login'
  }
}

request.interceptors.response.use(
  (resp) => resp.data, // 直接返回业务 data
  async (error) => {
    const { response, config } = error
    const isAuthCall = config?.url?.includes('/auth/login') || config?.url?.includes('/auth/refresh')

    // 401 且非登录/刷新接口:尝试用 refresh token 续期
    if (response?.status === 401 && !config?.__retried && !isAuthCall) {
      const refreshToken = localStorage.getItem('refresh')
      if (refreshToken && !refreshing) {
        refreshing = true
        try {
          const r = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('token', r.data.access_token)
          localStorage.setItem('refresh', r.data.refresh_token)
          const queue = waitingQueue
          waitingQueue = []
          refreshing = false
          // 重放所有排队请求(新 token 由请求拦截器从 localStorage 注入)
          queue.forEach(({ resolve, config: cfg }) => resolve(request(cfg)))
          config.headers.Authorization = `Bearer ${r.data.access_token}`
          config.__retried = true
          return request(config)
        } catch (e) {
          const queue = waitingQueue
          waitingQueue = []
          refreshing = false
          // 必须显式 reject 排队的 Promise,否则它们会永久挂死
          queue.forEach(({ reject }) => reject(e))
          redirectToLogin()
          return Promise.reject(e)
        }
      } else if (refreshing) {
        // 排队:同时保留 resolve 与 reject,确保 refresh 失败时也能正确 reject
        return new Promise((resolve, reject) => {
          waitingQueue.push({ resolve, reject, config })
        })
      } else {
        redirectToLogin()
      }
    }

    const detail =
      response?.data?.detail || error.message || '请求失败,请稍后重试'
    if (!config?.__silent) {
      ElMessage.error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }
    return Promise.reject(error)
  }
)

export default request
