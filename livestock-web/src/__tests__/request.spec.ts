import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ElMessage 拉起整个 element-plus 太重，mock 掉（断言只关心调用）
vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn(), warning: vi.fn() },
}))

import { ElMessage } from 'element-plus'
import http from '@/api/request'

/** 构造 axios adapter 需要的最小响应对象 */
function ok(config: unknown, body: Record<string, unknown>) {
  return { data: body, status: 200, statusText: 'OK', headers: {}, config } as never
}

/** 手工控制 resolve 时机，模拟「慢请求后到」 */
function deferred<T>() {
  let resolve!: (v: T) => void
  const promise = new Promise<T>((r) => (resolve = r))
  return { promise, resolve }
}

beforeEach(() => {
  localStorage.clear()
  window.history.replaceState(null, '', '/')
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('GET 竞态防护', () => {
  it('同接口重复发起时，先发出的慢响应被丢弃（只认最后一次）', async () => {
    let calls = 0
    let slowConfig: unknown
    const d = deferred<never>()
    http.defaults.adapter = vi.fn(async (config) => {
      calls += 1
      if (calls === 1) {
        slowConfig = config
        return d.promise as never
      }
      return ok(config, { code: 200, msg: 'ok', data: { seq: calls } })
    })

    const p1 = http.get('/animals', { params: { pageNum: 1 } })
    // 等一个宏任务，确保 p1 已真正进入 adapter（axios 派发在微任务里）
    await new Promise((r) => setTimeout(r, 0))
    const p2 = http.get('/animals', { params: { pageNum: 1 } })
    await new Promise((r) => setTimeout(r, 0))
    // 必须携带 p1 的真实 config（含 _dedup 标记），否则拦截器无法识别竞态
    d.resolve(ok(slowConfig, { code: 200, msg: 'ok', data: { seq: 1 } }) as never)

    await expect(p1).rejects.toMatchObject({ __stale: true })
    const res2 = await p2
    expect((res2 as unknown as { data: { seq: number } }).data.seq).toBe(2)
  })

  it('不同接口互不影响', async () => {
    let slowConfig: unknown
    const d = deferred<never>()
    http.defaults.adapter = vi.fn(async (config) => {
      if (String(config.url) === '/slow') {
        slowConfig = config
        return d.promise as never
      }
      return ok(config, { code: 200, msg: 'ok', data: {} })
    })

    const slow = http.get('/slow')
    await new Promise((r) => setTimeout(r, 0))
    const fast = http.get('/fast')
    await new Promise((r) => setTimeout(r, 0))
    d.resolve(ok(slowConfig, { code: 200, msg: 'ok', data: { late: true } }) as never)

    const res = await slow
    await fast
    expect((res as unknown as { data: { late: boolean } }).data.late).toBe(true)
  })

  it('POST 不做竞态丢弃（用户主动提交不能丢）', async () => {
    let calls = 0
    const d = deferred<never>()
    http.defaults.adapter = vi.fn(async (config) => {
      calls += 1
      if (calls === 1) return d.promise as never
      return ok(config, { code: 200, msg: 'ok', data: { seq: calls } })
    })

    const p1 = http.post('/animals', { name: 'a' })
    const p2 = http.post('/animals', { name: 'a' })
    d.resolve(ok({}, { code: 200, msg: 'ok', data: { seq: 1 } }) as never)

    const res1 = await p1
    await p2
    expect((res1 as unknown as { data: { seq: number } }).data.seq).toBe(1)
  })
})

describe('响应拦截器', () => {
  it('业务成功直接返回 body（含 code/msg/data）', async () => {
    http.defaults.adapter = vi.fn(async (config) =>
      ok(config, { code: 200, msg: 'ok', data: { value: 42 } }),
    )
    const res = await http.get('/thing')
    expect((res as unknown as { data: { value: number } }).data.value).toBe(42)
  })

  it('业务失败弹错误提示并 reject', async () => {
    http.defaults.adapter = vi.fn(async (config) =>
      ok(config, { code: 500, msg: 'boom', data: null }),
    )
    await expect(http.get('/thing')).rejects.toThrow('boom')
    expect(ElMessage.error).toHaveBeenCalledWith('boom')
  })

  it('401 清除 token 并跳登录页（带回跳地址）', async () => {
    localStorage.setItem('livestock_token', 'h.p.s')
    http.defaults.adapter = vi.fn(async (config) =>
      ok(config, { code: 401, msg: '未登录', data: null }),
    )
    await expect(http.get('/thing')).rejects.toThrow('未登录')
    expect(localStorage.getItem('livestock_token')).toBeNull()
    expect(String(window.location.href)).toContain('/login?redirect=')
  })

  it('已在登录页时 401 不再重复跳转（防循环）', async () => {
    window.history.replaceState(null, '', '/login')
    http.defaults.adapter = vi.fn(async (config) =>
      ok(config, { code: 401, msg: '未登录', data: null }),
    )
    await expect(http.get('/thing')).rejects.toThrow('未登录')
    expect(String(window.location.href)).not.toContain('redirect=')
  })

  it('网络级错误兜底提示', async () => {
    http.defaults.adapter = vi.fn(async () => {
      throw Object.assign(new Error('Network Error'), { response: undefined })
    })
    await expect(http.get('/thing')).rejects.toThrow()
    expect(ElMessage.error).toHaveBeenCalledWith('网络错误，请检查连接')
  })
})
