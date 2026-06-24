import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

/**
 * 统一解包后端 ApiResponse 信封：{ ok, data, error }。
 * 成功时把 response.data 替换为业务负载（data 字段内容），调用方仍用 res.data 读取。
 * 失败时 reject，附带 error: { code, message }。
 *
 * 422 校验失败：FastAPI 返回 { detail: [...] }，不走业务信封，保持 axios 默认结构。
 * 页面 catch：422 读 e.response.data.detail；业务错误读 e.error?.code。
 *
 * 网络/超时错误会被翻成中文友好提示（带可能原因），方便值班快速定位。
 */
const NETWORK_ERROR_HINT =
  '请确认后端服务（默认 8000 端口）、Kafka、Elasticsearch、Docker 是否都处于运行状态。'

function describeNetworkError(error) {
  if (!error) return '请求失败'
  if (error.code === 'ECONNABORTED') {
    return `请求超时（${error.message}）。${NETWORK_ERROR_HINT}`
  }
  if (error.message === 'Network Error') {
    return `无法连接后端服务。${NETWORK_ERROR_HINT}`
  }
  if (error.response) {
    const status = error.response.status
    if (status === 404) return '接口不存在（404），请确认后端路由版本是否一致。'
    if (status === 502 || status === 503 || status === 504) {
      return `后端网关不可用（${status}）。${NETWORK_ERROR_HINT}`
    }
    return `请求失败（HTTP ${status}）`
  }
  return error.message || '请求失败'
}

request.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.ok === 'boolean') {
      if (body.ok) {
        response.data = body.data
        return response
      }
      const errInfo = body.error ?? { code: 'unknown', message: 'request failed' }
      const error = new Error(errInfo.message || errInfo.code || 'request failed')
      error.error = errInfo
      error.response = response
      return Promise.reject(error)
    }
    return response
  },
  (error) => {
    const wrapped = new Error(describeNetworkError(error))
    wrapped.cause = error
    wrapped.code = error?.code
    wrapped.response = error?.response
    return Promise.reject(wrapped)
  }
)

export default request
