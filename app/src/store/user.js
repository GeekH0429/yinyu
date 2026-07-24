import http from '../utils/request'
import { SNAP, clearSnap } from '../utils/snap'
import { clearArticleSnaps } from '../utils/articleCache'
import { resetFeed } from './feed'
import { resetMe } from './me'

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

/**
 * 刷新本地用户信息。
 * 注意:非鉴权错误(5xx / 网络抖动)不应触发 logout —— request.js 拦截器已
 * 在 refresh token 失败时统一跳登录,这里再 logout 会把暂时性故障误判为登出。
 */
export async function refreshUser() {
  if (!isLoggedIn()) return null
  try {
    const me = await http.get('/me')
    uni.setStorageSync('userInfo', me)
    return me
  } catch {
    return null
  }
}

export function logout() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refresh_token')
  uni.removeStorageSync('userInfo')
  // 清缓存:换号登录时不会看到上一账号的图文/树洞(treehole 含 code,属隐私)
  clearSnap(SNAP.FEED)
  clearSnap(SNAP.ME)
  clearArticleSnaps()
  resetFeed()
  resetMe()
}
