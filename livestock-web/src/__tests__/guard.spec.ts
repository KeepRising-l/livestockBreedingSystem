import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn(), warning: vi.fn() },
}))
vi.mock('@/api/auth', () => ({
  loginApi: vi.fn(),
  getPermissionsApi: vi.fn(),
}))
vi.mock('@/api/farm', () => ({
  getFarmListApi: vi.fn(),
  getFarmInfoApi: vi.fn(),
}))
vi.mock('@/api/system', () => ({
  getUnreadMessageCountApi: vi.fn(),
}))

import { useAuthStore } from '@/stores/auth'
import { authGuard } from '@/router'
import { setToken } from '@/utils/token'
import { getFarmInfoApi, getFarmListApi } from '@/api/farm'
import { getPermissionsApi } from '@/api/auth'

/** 构造守卫需要的最小路由对象 */
function route(partial: Record<string, unknown>) {
  return partial as unknown as Parameters<typeof authGuard>[0]
}

/** 创建 store 并冲刷其初始化异步请求，避免初始化响应在守卫 await 期间覆盖手动状态 */
async function freshStore() {
  const store = useAuthStore()
  await new Promise((r) => setTimeout(r, 0))
  return store
}

function makeJwt(payload: Record<string, unknown>) {
  const body = btoa(JSON.stringify(payload)).replace(/=+$/, '')
  return `h.${body}.s`
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  vi.clearAllMocks()
  // store 创建即触发初始化请求，全部 mock 成空实现避免未捕获拒绝
  vi.mocked(getPermissionsApi).mockResolvedValue({ code: 200, data: { roles: [], perms: [], post: '' } } as never)
  vi.mocked(getFarmInfoApi).mockResolvedValue({ code: 200, data: { livestock_types: '牛' } } as never)
  vi.mocked(getFarmListApi).mockResolvedValue({ code: 200, data: [] } as never)
})

describe('路由守卫：登录态', () => {
  it('设置页面标题', async () => {
    await authGuard(route({ meta: { title: '畜禽档案' }, path: '/', params: {} }))
    expect(document.title).toBe('畜禽档案')
  })

  it('noAuth 页面无 token 可直接访问', async () => {
    const res = await authGuard(route({ meta: { noAuth: true }, name: 'RegisterOwner', path: '/register/owner', params: {} }))
    expect(res).toBeUndefined()
  })

  it('已登录访问登录页重定向到大屏', async () => {
    setToken(makeJwt({ sub: '1', user_type: 1 }))
    const res = await authGuard(route({ meta: { noAuth: true }, name: 'Login', path: '/login', params: {} }))
    expect(res).toBe('/dashboard')
  })

  it('受保护页面无 token 重定向登录页', async () => {
    const res = await authGuard(route({ meta: {}, path: '/dashboard', params: {} }))
    expect(res).toBe('/login')
  })
})

describe('路由守卫：畜种校验', () => {
  it('不属于养殖场可选畜种 → 404', async () => {
    setToken(makeJwt({ sub: '2', user_type: 2, farm_id: 1 }))
    const store = await freshStore()
    store.farmInfo = { livestock_types: '牛' } as never

    const res = await authGuard(route({ meta: {}, path: '/pig/animal/list', params: { species: 'pig' } }))
    expect(res).toBe('/404')
  })

  it('可选畜种放行', async () => {
    setToken(makeJwt({ sub: '2', user_type: 2, farm_id: 1 }))
    const store = await freshStore()
    store.farmInfo = { livestock_types: '牛,羊' } as never

    const res = await authGuard(route({ meta: {}, path: '/sheep/animal/list', params: { species: 'sheep' } }))
    expect(res).toBeUndefined()
  })

  it('farm 信息为空时先拉取再判定', async () => {
    setToken(makeJwt({ sub: '2', user_type: 2, farm_id: 1 }))
    const store = await freshStore()
    store.farmInfo = null

    const res = await authGuard(route({ meta: {}, path: '/pig/animal/list', params: { species: 'pig' } }))
    expect(getFarmInfoApi).toHaveBeenCalled()
    expect(res).toBe('/404')
  })

  it('拉取 farm 信息失败时放行（fail-open，由页面接口与后端兜底）', async () => {
    setToken(makeJwt({ sub: '2', user_type: 2, farm_id: 1 }))
    vi.mocked(getFarmInfoApi).mockRejectedValue(new Error('network down'))
    const store = await freshStore()
    store.farmInfo = null

    const res = await authGuard(route({ meta: {}, path: '/pig/animal/list', params: { species: 'pig' } }))
    expect(res).toBeUndefined()
  })
})

describe('路由守卫：员工模块权限', () => {
  it('员工访问未授权模块 → 403', async () => {
    setToken(makeJwt({ sub: '7', user_type: 3, farm_id: 1 }))
    const store = await freshStore()
    store.userType = 3
    store.perms = ['animal']

    const res = await authGuard(route({ meta: {}, path: '/cattle/inventory/stock', params: { species: 'cattle' } }))
    expect(res).toBe('/403')
  })

  it('员工访问已授权模块放行', async () => {
    setToken(makeJwt({ sub: '7', user_type: 3, farm_id: 1 }))
    const store = await freshStore()
    store.userType = 3
    store.perms = ['inventory']

    const res = await authGuard(route({ meta: {}, path: '/cattle/inventory/stock', params: { species: 'cattle' } }))
    expect(res).toBeUndefined()
  })

  it('员工访问大屏不受模块权限限制', async () => {
    setToken(makeJwt({ sub: '7', user_type: 3, farm_id: 1 }))
    const store = await freshStore()
    store.userType = 3
    store.perms = []

    const res = await authGuard(route({ meta: {}, path: '/dashboard', params: {} }))
    expect(res).toBeUndefined()
  })

  it('auth:false 的基础页面（个人中心）不做模块校验', async () => {
    setToken(makeJwt({ sub: '7', user_type: 3, farm_id: 1 }))
    const store = await freshStore()
    store.userType = 3
    store.perms = []

    const res = await authGuard(route({ meta: { auth: false }, path: '/profile', params: {} }))
    expect(res).toBeUndefined()
  })

  it('超管/场主不做员工模块校验', async () => {
    setToken(makeJwt({ sub: '1', user_type: 1, farm_id: 0 }))
    const store = await freshStore()
    store.userType = 1

    const res = await authGuard(route({ meta: {}, path: '/system/user', params: {} }))
    expect(res).toBeUndefined()
  })
})
