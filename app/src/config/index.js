/**
 * 后端地址配置。
 * - H5 调试:127.0.0.1:8010(浏览器与本机后端直连)
 * - 真机 / 小程序:电脑局域网 IP(如 192.168.x.x:8010),且手机与电脑同网段
 * - 生产:改成线上域名(https)
 *
 * 按平台条件编译:H5 默认走 localhost;App/小程序走局域网 IP。
 * 换机器改 IP 时只改 NON_H5_SERVER_ORIGIN 一处即可。
 *
 * 注意:本机 dev 端口用 8010——8000 会被 HBuilderX 内置 httpServer 抢占
 * (还独占 IPv6 [::]:8000),localhost 解析到 ::1 的请求会被它劫走。
 */
// #ifdef H5
const SERVER_ORIGIN = 'http://127.0.0.1:8010'
// #endif
// #ifndef H5
const NON_H5_SERVER_ORIGIN = 'http://192.168.1.5:8010'
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

/**
 * 列表缩略图 URL:上传管线为最大边 >800 的图生成缩略档,文件名约定为
 * 扩展名前插 `_s`(abc.webp → abc_s.webp)。只做纯字符串变换,不看格式大小。
 * 仅对指向本服务的相对路径(/uploads/...)生效;外部图与本地路径原样返回。
 * 历史图可能没有缩略档(404)→ 给 CachedImage 传 fallback 回原图兜底;
 * 存量文件可用 backend/scripts/backfill_thumbs.py 一次性补齐。
 */
export function thumbUrl(p) {
  if (!p) return ''
  if (isRemoteUrl(p)) return p
  if (/^(blob:|wxfile:|file:|_doc|_www)/.test(p)) return p
  const i = String(p).lastIndexOf('.')
  return i > String(p).lastIndexOf('/') ? p.slice(0, i) + '_s' + p.slice(i) : p
}
