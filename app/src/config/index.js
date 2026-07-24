/**
 * 后端地址配置。
 * - H5 调试:127.0.0.1:8000(浏览器与本机后端直连)
 * - 真机 / 小程序:电脑局域网 IP(如 192.168.x.x:8000),且手机与电脑同网段
 * - 生产:改成线上域名(https)
 *
 * 按平台条件编译:H5 默认走 localhost;App/小程序走局域网 IP。
 * 换机器改 IP 时只改 NON_H5_SERVER_ORIGIN 一处即可。
 */
// #ifdef H5
const SERVER_ORIGIN = 'http://127.0.0.1:8000'
// #endif
// #ifndef H5
const NON_H5_SERVER_ORIGIN = 'http://192.168.1.5:8000'
const SERVER_ORIGIN = NON_H5_SERVER_ORIGIN
// #endif
export { SERVER_ORIGIN }
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
