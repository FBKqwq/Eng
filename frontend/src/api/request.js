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
 */
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
  (error) => Promise.reject(error)
)

export default request
