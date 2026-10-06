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
import { loginApi, getPermissionsApi } from '@/api/auth'
import { getFarmInfoApi, getFarmListApi } from '@/api/farm'
import { getUnreadMessageCountApi } from '@/api/system'

/** 生成测试用 JWT（payload 仅 ASCII，避开 atob 的非拉丁字符问题） */
function makeJwt(payload: Record<string, unknown>) {
  const body = btoa(JSON.stringify(payload)).replace(/=+$/, '')
  return `h.${body}.s`
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('auth store：登录', () => {
  it('员工登录：token 落地、解析身份、拉权限与养殖场信息', async () => {
    vi.mocked(loginApi).mockResolvedValue({
      code: 200,
      data: { access_token: makeJwt({ sub: '7', user_type: 3, farm_id: 5, post: 'feeder' }) },
    } as never)
    vi.mocked(getPermissionsApi).mockResolvedValue({
      code: 200,
      data: { roles: ['r1'], perms: ['animal', 'feeding'], post: 'feeder' },
    } as never)
    vi.mocked(getFarmInfoApi).mockResolvedValue({
      code: 200,
      data: { livestock_types: '牛,羊' },
    } as never)
    vi.mocked(getUnreadMessageCountApi).mockResolvedValue({
      code: 200,
      data: { count: 2 },
    } as never)

    const store = useAuthStore()
    await store.login({ username: 'e', password: 'p' })

    expect(localStorage.getItem('livestock_token')).toBeTruthy()
    expect(store.userType).toBe(3)
    expect(store.farmId).toBe(5)
    expect(store.perms).toEqual(['animal', 'feeding'])
    expect(store.selectedFarmId).toBe(5) // 非超管：绑定自身 farm_id
    expect(store.speciesRouteList).toEqual(['cattle', 'sheep'])
    expect(store.unreadCount).toBe(2)
  })

  it('超管登录：初始化选中第一个农场并持久化', async () => {
    vi.mocked(loginApi).mockResolvedValue({
      code: 200,
      data: { access_token: makeJwt({ sub: '1', user_type: 1, farm_id: 0 }) },
    } as never)
    vi.mocked(getPermissionsApi).mockResolvedValue({
      code: 200,
      data: { roles: ['admin'], perms: ['all'], post: '' },
    } as never)
    vi.mocked(getFarmListApi).mockResolvedValue({
      code: 200,
      data: [{ id: 3, farm_name: 'A场' }, { id: 4, farm_name: 'B场' }],
    } as never)
    vi.mocked(getFarmInfoApi).mockResolvedValue({
      code: 200,
      data: { livestock_types: '猪' },
    } as never)
    vi.mocked(getUnreadMessageCountApi).mockResolvedValue({
      code: 200,
      data: { count: 0 },
    } as never)

    const store = useAuthStore()
    await store.login({ username: 'a', password: 'p' })

    expect(store.userType).toBe(1)
    expect(store.selectedFarmId).toBe(3)
    expect(localStorage.getItem('livestock_selected_farm_id')).toBe('3')
    expect(store.speciesRouteList).toEqual(['pig'])
  })

  it('登录失败：不落 token，异常向上抛（由拦截器提示）', async () => {
    vi.mocked(loginApi).mockRejectedValue(new Error('账号或密码错误'))
    const store = useAuthStore()
    await expect(store.login({ username: 'x', password: 'y' })).rejects.toThrow()
    expect(store.token).toBeNull()
    expect(localStorage.getItem('livestock_token')).toBeNull()
  })
})

describe('auth store：权限与身份', () => {
  it('hasPerm：超管/场主全通过，员工按 perms 判定', () => {
    const store = useAuthStore()

    store.userType = 1
    expect(store.hasPerm('system')).toBe(true)
    store.userType = 2
    expect(store.hasPerm('anything')).toBe(true)

    store.userType = 3
    store.perms = ['animal']
    expect(store.hasPerm('animal')).toBe(true)
    expect(store.hasPerm('finance')).toBe(false)
  })

  it('setSpecies：仅允许养殖场可选畜种', () => {
    const store = useAuthStore()
    store.farmInfo = { livestock_types: '牛,羊' } as never
    store.setSpecies('pig')
    expect(store.currentSpecies).not.toBe('pig')
    store.setSpecies('sheep')
    expect(store.currentSpecies).toBe('sheep')
  })

  it('损坏的 token：解析失败不崩溃，身份回退 0', () => {
    localStorage.setItem('livestock_token', 'not-a-jwt')
    const store = useAuthStore()
    expect(store.userType).toBe(0)
  })
})

describe('auth store：登出', () => {
  it('清空全部身份状态与本地存储', async () => {
    vi.mocked(loginApi).mockResolvedValue({
      code: 200,
      data: { access_token: makeJwt({ sub: '7', user_type: 3, farm_id: 5 }) },
    } as never)
    vi.mocked(getPermissionsApi).mockResolvedValue({
      code: 200,
      data: { roles: [], perms: ['animal'], post: '' },
    } as never)
    vi.mocked(getFarmInfoApi).mockResolvedValue({
      code: 200,
      data: { livestock_types: '牛' },
    } as never)
    vi.mocked(getUnreadMessageCountApi).mockResolvedValue({
      code: 200,
      data: { count: 1 },
    } as never)

    const store = useAuthStore()
    await store.login({ username: 'e', password: 'p' })
    expect(store.token).toBeTruthy()

    store.logout()
    expect(store.token).toBeNull()
    expect(store.userType).toBe(0)
    expect(store.perms).toEqual([])
    expect(store.farmInfo).toBeNull()
    expect(localStorage.getItem('livestock_token')).toBeNull()
    expect(localStorage.getItem('livestock_selected_farm_id')).toBeNull()
  })
})
