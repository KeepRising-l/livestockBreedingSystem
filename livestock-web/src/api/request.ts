import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getToken, getSelectedFarmId, removeToken } from '@/utils/token'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 15000,
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    // 超管农场切换：从 JWT 判断是否超管，是则附加 X-Farm-Id
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.user_type === 1) {
        const farmId = getSelectedFarmId()
        if (farmId) {
          config.headers['X-Farm-Id'] = String(farmId)
        }
      }
    } catch {
      // token 解析失败，忽略
    }
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code !== 200) {
      if (data.code === 401) {
        removeToken()
        window.location.href = '/login'
        return Promise.reject(new Error('未登录或 token 已过期'))
      }
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg))
    }
    return data
  },
  (error: AxiosError) => {
    const data = error.response?.data as any
    ElMessage.error(data?.detail || data?.msg || '网络错误，请检查连接')
    return Promise.reject(error)
  }
)

export default http
