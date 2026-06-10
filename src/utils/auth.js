/**
 * 简单的用户身份标识
 *
 * 后端 GEE 接口需要一个 Authorization header 来区分用户。
 * 这里生成一个持久化 UUID 作为用户 token，存 localStorage。
 * 注意：这不是安全认证，只是用户区分。
 */
const TOKEN_KEY = 'rs_urban_user_token'

let _token = null

export function getUserToken() {
  if (_token) return _token

  _token = localStorage.getItem(TOKEN_KEY)
  if (!_token) {
    _token = crypto.randomUUID()
    localStorage.setItem(TOKEN_KEY, _token)
  }
  return _token
}
