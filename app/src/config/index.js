/**
 * 后端地址配置。
 * - H5 调试:127.0.0.1:8000 即可
 * - 真机 / 小程序:改成电脑局域网 IP(如 192.168.x.x:8000),且手机与电脑同网段
 * - 生产:改成线上域名(https)
 */
// export const SERVER_ORIGIN = 'http://127.0.0.1:8000'
export const SERVER_ORIGIN = 'http://192.168.137.1:8000'
export const API_BASE = SERVER_ORIGIN + '/api/v1'

/**
 * 把后端返回的资源路径(/uploads/xxx)补成完整 URL。
 */
export function resourceUrl(p) {
  if (!p) return ''
  if (/^https?:\/\//.test(p)) return p
  if (/^(blob:|wxfile:|file:|_doc|_www)/.test(p)) return p
  return SERVER_ORIGIN + (p.startsWith('/') ? p : '/' + p)
}

/** 是否为远程 URL(http/https 或协议相对 //)。供缓存层/CachedImage 判断是否需要走缓存。 */
export function isRemoteUrl(p) {
  return /^(https?:)?\/\//.test(p || '')
}
