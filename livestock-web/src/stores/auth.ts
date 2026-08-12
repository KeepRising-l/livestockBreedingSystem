import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getToken, setToken, removeToken, setSelectedFarmId, removeSelectedFarmId, getSelectedFarmId } from '@/utils/token'
import { loginApi, getPermissionsApi, type LoginParams } from '@/api/auth'
import { getFarmInfoApi, getFarmListApi, type FarmInfo, type FarmListItem } from '@/api/farm'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const userType = ref<number>(0)
  const farmId = ref<number>(0)
  const post = ref<string>('')
  const farmInfo = ref<FarmInfo | null>(null)
  // 超管农场切换相关
  const selectedFarmId = ref<number>(0)
  const farmList = ref<FarmListItem[]>([])
  // RBAC（P3-4）：当前用户拥有的角色与权限模块
  const roleKeys = ref<string[]>([])
  const perms = ref<string[]>([])

  function parseToken() {
    if (!token.value) return
    try {
      const payload = JSON.parse(atob(token.value.split('.')[1]))
      userType.value = payload.user_type || 0
      farmId.value = payload.farm_id || 0
      post.value = payload.post || ''
    } catch {
      // token 解析失败，忽略
    }
  }

  function hasPerm(perm: string) {
    // 超管/场主默认拥有全部模块权限，员工按角色 perms 校验
    if (userType.value === 1 || userType.value === 2) return true
    return perms.value.includes(perm)
  }

  async function loadPermissions() {
    try {
      const res = await getPermissionsApi()
      roleKeys.value = res.data.roles || []
      perms.value = res.data.perms || []
      if (res.data.post) post.value = res.data.post
    } catch {
      // 权限拉取失败忽略，Sidebar 按 userType 兜底
    }
  }

  async function login(params: LoginParams) {
    const res = await loginApi(params)
    token.value = res.data.access_token
    setToken(res.data.access_token)
    parseToken()
    await loadPermissions()
    await loadFarmList()
    // 初始化 selectedFarmId
    if (userType.value === 1 && farmList.value.length > 0) {
      selectedFarmId.value = farmList.value[0].id
      setSelectedFarmId(farmList.value[0].id)
    } else {
      selectedFarmId.value = farmId.value
    }
    await loadFarmInfo()
  }

  async function loadFarmInfo() {
    try {
      const res = await getFarmInfoApi()
      farmInfo.value = res.data
    } catch {
      // 忽略获取养殖场信息失败
    }
  }

  async function loadFarmList() {
    if (userType.value !== 1) return
    try {
      const res = await getFarmListApi()
      farmList.value = res.data || []
    } catch {
      // 忽略
    }
  }

  function switchFarm(fid: number) {
    selectedFarmId.value = fid
    setSelectedFarmId(fid)
    // 立即加载新农场信息
    loadFarmInfo()
  }

  function logout() {
    token.value = null
    userType.value = 0
    farmId.value = 0
    post.value = ''
    farmInfo.value = null
    selectedFarmId.value = 0
    farmList.value = []
    roleKeys.value = []
    perms.value = []
    removeToken()
    removeSelectedFarmId()
  }

  // 初始化时解析已有 token
  parseToken()
  // 拉取当前用户 RBAC 权限（角色/权限模块）
  if (token.value) {
    loadPermissions()
  }
  // 超管初始化：加载农场列表和农场信息
  if (userType.value === 1) {
    // 先同步从 localStorage 恢复 selectedFarmId（如果有的话）
    const savedFarmId = getSelectedFarmId()
    if (savedFarmId) {
      selectedFarmId.value = savedFarmId
    }
    // 异步加载农场列表
    loadFarmList().then(() => {
      // 只在没有缓存值时才设为首个农场
      if (farmList.value.length > 0 && !selectedFarmId.value) {
        selectedFarmId.value = farmList.value[0].id
        setSelectedFarmId(farmList.value[0].id)
      }
    })
    // 超管也需要加载农场信息
    loadFarmInfo()
  }

  return {
    token, userType, farmId, post, farmInfo,
    selectedFarmId, farmList, roleKeys, perms,
    login, logout, loadFarmInfo, loadFarmList, switchFarm, parseToken,
    loadPermissions, hasPerm,
  }
})
