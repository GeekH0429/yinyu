import http from '../utils/request'

export function isLoggedIn() {
  return !!uni.getStorageSync('token')
}

export function getUser() {
  return uni.getStorageSync('userInfo') || null
}

/** 登录:换 token 后立即拉取用户信息。 */
export async function login(username, password) {
  const data = await http.post('/auth/login', { username, password })
  uni.setStorageSync('token', data.access_token)
  uni.setStorageSync('refresh_token', data.refresh_token)
  const me = await http.get('/me')
  uni.setStorageSync('userInfo', me)
  return me
}

/** 刷新本地用户信息(token 失效会自动登出)。 */
export async function refreshUser() {
  if (!isLoggedIn()) return null
  try {
    const me = await http.get('/me')
    uni.setStorageSync('userInfo', me)
    return me
  } catch {
    logout()
    return null
  }
}

export function logout() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refresh_token')
  uni.removeStorageSync('userInfo')
}
