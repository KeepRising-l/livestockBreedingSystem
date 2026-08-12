import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getToken, setToken, removeToken, setSelectedFarmId, removeSelectedFarmId, getSelectedFarmId } from '@/utils/token'
import { loginApi, getPermissionsApi, type LoginParams } from '@/api/auth'
import { getFarmInfoApi, getFarmListApi, type FarmInfo, type FarmListItem } from '@/api/farm'
import { SPECIES_ROUTE_MAP } from '@/utils/constants'

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
  // 多畜种（P3-6 A）：当前选中的畜种（路由值 cattle/sheep/pig）
  const currentSpecies = ref<string>('cattle')

  /** 养殖场可选畜种中文数组（来自 farm.livestock_types，逗号分隔） */
  const livestockTypes = computed<string[]>(() =>
    (farmInfo.value?.livestock_types || '').split(',').filter(Boolean),
  )
  /** 养殖场可选畜种路由值数组（cattle/sheep/pig） */
  const speciesRouteList = computed<string[]>(() =>
    livestockTypes.value.map(t => SPECIES_ROUTE_MAP[t]).filter(Boolean),
  )

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
      // 多畜种：若当前畜种不在养殖场可选范围内，默认切到第一个
      if (speciesRouteList.value.length > 0 && !speciesRouteList.value.includes(currentSpecies.value)) {
        currentSpecies.value = speciesRouteList.value[0]
      }
    } catch {
      // 忽略获取养殖场信息失败
    }
  }

  /** 切换当前畜种（仅允许养殖场可选畜种） */
  function setSpecies(s: string) {
    if (speciesRouteList.value.includes(s)) currentSpecies.value = s
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
    currentSpecies.value = 'cattle'
    removeToken()
    removeSelectedFarmId()
  }

  // 初始化时解析已有 token
  parseToken()
  // 拉取当前用户 RBAC 权限（角色/权限模块）
  if (token.value) {
    loadPermissions()
  }
  // 超管初始化：恢复 selectedFarmId + 加载农场列表
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
  }
  // 所有登录用户都加载农场信息（校正可选畜种，Sidebar 按 livestock_types 收窄）
  if (token.value) {
    loadFarmInfo()
  }

  return {
    token, userType, farmId, post, farmInfo,
    selectedFarmId, farmList, roleKeys, perms,
    currentSpecies, livestockTypes, speciesRouteList,
    login, logout, loadFarmInfo, loadFarmList, switchFarm, parseToken,
    loadPermissions, hasPerm, setSpecies,
  }
})
