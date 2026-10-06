import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getToken, getSelectedFarmId, removeToken } from '@/utils/token'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 15000,
})

// ---- 请求竞态防护（防页面卡顿/数据闪回） ----
// 同一个 GET 接口连续发起时，只认最后一次：过早返回的旧响应直接丢弃（静默，不覆盖新数据、不弹错误）。
// 解决快速切换畜种 / 连续点查询 / 翻页时"旧慢请求晚到覆盖新结果"的抖动。
interface PendingEntry { seq: number; ts: number }
const pendingGetSeq = new Map<string, PendingEntry>()
let globalSeq = 0

/** 稳定序列化 params，保证同一接口不同查询参数按 key 区分 */
function dedupKey(config: InternalAxiosRequestConfig): string {
  const p: any = config.params || {}
  const sorted = Object.keys(p)
    .filter((k) => p[k] !== undefined && p[k] !== '' && p[k] !== null)
    .sort()
    .map((k) => `${k}=${p[k]}`)
    .join('&')
  return `${config.method?.toUpperCase() ?? ''}|${config.url ?? ''}|${sorted}`
}

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

  // 只对 GET 做竞态保护（POST/PUT/DELETE 是用户主动提交，不能丢弃）
  if ((config.method || '').toUpperCase() === 'GET') {
    const key = dedupKey(config)
    const now = Date.now()
    const seq = ++globalSeq
    ;(config as any)._dedup = { key, seq }
    pendingGetSeq.set(key, { seq, ts: now })
    // 顺手清理 60s 前无更新的记录，防止 Map 无限增长
    for (const [k, v] of pendingGetSeq) {
      if (now - v.ts > 60000) pendingGetSeq.delete(k)
    }
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const cfg = response.config as InternalAxiosRequestConfig & { _dedup?: { key: string; seq: number } }
    // 过期 GET 响应：丢弃，不进入页面 data
    if (cfg._dedup) {
      const cur = pendingGetSeq.get(cfg._dedup.key)
      if (cur && cur.seq !== cfg._dedup.seq) {
        return Promise.reject(Object.assign(new Error('STALE_RESPONSE'), { __stale: true }))
      }
    }
    const { data } = response
    if (data.code !== 200) {
    if (data.code === 401) {
      removeToken()
      // 未在登录页才跳转（避免登录接口自身 401 时循环刷新）；带上回跳地址，登录后回到原页面
      if (!window.location.pathname.startsWith('/login')) {
        const current = window.location.pathname + window.location.search
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      }
      return Promise.reject(new Error('未登录或 token 已过期'))
    }
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg))
    }
    return data
  },
  (error: AxiosError) => {
    // 已标记为过期的竞态响应：静默，不弹错误
    if ((error as any)?.__stale) return Promise.reject(error)
    const data = error.response?.data as any
    ElMessage.error(data?.detail || data?.msg || '网络错误，请检查连接')
    return Promise.reject(error)
  }
)

export default http
