import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/token'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/register/owner',
    name: 'RegisterOwner',
    component: () => import('@/views/login/RegisterOwnerView.vue'),
    meta: { title: '养殖场主注册', noAuth: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/DashboardView.vue'), meta: { title: '数据大屏' } },
      // 个人中心（跨畜种，所有角色可访问，auth:false 跳过员工权限模块校验）
      { path: 'profile', name: 'Profile', component: () => import('@/views/profile/ProfileView.vue'), meta: { title: '个人中心', auth: false } },
      // 我的消息（缺口6：审核结果通知，所有角色可访问）
      { path: 'messages', name: 'Messages', component: () => import('@/views/system/MessageListView.vue'), meta: { title: '我的消息', auth: false } },
      // 养殖场（跨畜种）
      { path: 'farm/info', name: 'FarmInfo', component: () => import('@/views/farm/FarmInfoView.vue'), meta: { title: '养殖场信息' } },
      { path: 'farm/employees', name: 'FarmEmployees', component: () => import('@/views/farm/EmployeeListView.vue'), meta: { title: '员工管理' } },
      { path: 'farm/salary', name: 'SalaryConfig', component: () => import('@/views/farm/SalaryConfigView.vue'), meta: { title: '薪资配置' } },
      // 圈舍（多畜种独立子模块，:species = cattle/sheep/pig）
      { path: ':species/pen/list', name: 'PenList', component: () => import('@/views/pen/PenListView.vue'), meta: { title: '圈舍管理' } },
      { path: ':species/pen/:id', name: 'PenDetail', component: () => import('@/views/pen/PenDetailView.vue'), meta: { title: '圈舍详情' } },
      // 档案
      { path: ':species/animal/list', name: 'AnimalList', component: () => import('@/views/animal/AnimalListView.vue'), meta: { title: '畜禽档案' } },
      { path: ':species/animal/:id', name: 'AnimalDetail', component: () => import('@/views/animal/AnimalDetailView.vue'), meta: { title: '档案详情' } },
      { path: ':species/animal/individual-entry', name: 'AnimalIndividual', component: () => import('@/views/animal/AnimalIndividualView.vue'), meta: { title: '个体入栏' } },
      { path: ':species/animal/batch-entry', name: 'AnimalBatch', component: () => import('@/views/animal/AnimalBatchView.vue'), meta: { title: '批量入栏' } },
      { path: ':species/animal/history', name: 'AnimalHistory', component: () => import('@/views/animal/AnimalHistoryView.vue'), meta: { title: '历史记录' } },
      // 饲喂
      { path: ':species/feeding/plan', name: 'FeedingPlan', component: () => import('@/views/feeding/FeedingPlanView.vue'), meta: { title: '饲喂方案' } },
      { path: ':species/feeding/record', name: 'FeedingRecord', component: () => import('@/views/feeding/FeedingRecordView.vue'), meta: { title: '饲喂记录' } },
      // 物资库存
      { path: ':species/inventory/stock', name: 'InventoryStock', component: () => import('@/views/inventory/StockListView.vue'), meta: { title: '物资库存' } },
      { path: ':species/inventory/purchase', name: 'InventoryPurchase', component: () => import('@/views/inventory/PurchaseListView.vue'), meta: { title: '进货记录' } },
      { path: ':species/inventory/consume', name: 'InventoryConsume', component: () => import('@/views/inventory/ConsumeListView.vue'), meta: { title: '领用记录' } },
      // 防疫诊疗
      { path: ':species/health/vaccine', name: 'HealthVaccine', component: () => import('@/views/health/VaccineListView.vue'), meta: { title: '防疫记录' } },
      { path: ':species/health/medical', name: 'HealthMedical', component: () => import('@/views/health/MedicalListView.vue'), meta: { title: '诊疗记录' } },
      // 繁育
      { path: ':species/breeding/females', name: 'BreedingFemale', component: () => import('@/views/breeding/BreedingFemaleView.vue'), meta: { title: '母畜档案' } },
      { path: ':species/breeding/males', name: 'BreedingMale', component: () => import('@/views/breeding/BreedingMaleView.vue'), meta: { title: '公畜档案' } },
      { path: ':species/breeding/mating', name: 'BreedingMating', component: () => import('@/views/breeding/BreedingMatingView.vue'), meta: { title: '配种记录' } },
      { path: ':species/breeding/birth', name: 'BreedingBirth', component: () => import('@/views/breeding/BreedingBirthView.vue'), meta: { title: '产犊记录' } },
      { path: ':species/breeding/alert', name: 'BreedingAlert', component: () => import('@/views/breeding/BreedingAlertView.vue'), meta: { title: '繁育预警' } },
      // 员工工作台（C，仅员工登录默认落地；auth:false 跳过员工模块权限校验，工作台按岗位分流不受模块限制）
      { path: ':species/workbench', name: 'Workbench', component: () => import('@/views/workbench/WorkbenchView.vue'), meta: { title: '员工工作台', auth: false } },
      // 审核
      { path: ':species/review/list', name: 'ReviewList', component: () => import('@/views/review/ReviewListView.vue'), meta: { title: '审核中心' } },
      // 销售财务
      { path: ':species/finance/sale', name: 'FinanceSale', component: () => import('@/views/finance/SaleListView.vue'), meta: { title: '销售订单' } },
      { path: ':species/finance/cost', name: 'FinanceCost', component: () => import('@/views/finance/CostListView.vue'), meta: { title: '成本支出' } },
      { path: ':species/finance/profit', name: 'FinanceProfit', component: () => import('@/views/finance/ProfitView.vue'), meta: { title: '利润核算' } },
      { path: ':species/finance/salary', name: 'FinanceSalary', component: () => import('@/views/finance/SalaryListView.vue'), meta: { title: '薪资记录' } },
      // 统计分析
      { path: ':species/statistics/dashboard', name: 'StatisticsDashboard', component: () => import('@/views/statistics/DashboardStatsView.vue'), meta: { title: '综合统计' } },
      { path: ':species/statistics/breeding', name: 'StatisticsBreeding', component: () => import('@/views/statistics/BreedingStatsView.vue'), meta: { title: '存栏繁育统计' } },
      { path: ':species/statistics/health', name: 'StatisticsHealth', component: () => import('@/views/statistics/HealthStatsView.vue'), meta: { title: '防疫诊疗统计' } },
      { path: ':species/statistics/material', name: 'StatisticsMaterial', component: () => import('@/views/statistics/MaterialStatsView.vue'), meta: { title: '物资消耗统计' } },
      { path: ':species/statistics/finance', name: 'StatisticsFinance', component: () => import('@/views/statistics/FinanceStatsView.vue'), meta: { title: '财务统计' } },
      // 系统管理（跨畜种，仅超管）
      { path: 'system/dict', name: 'SystemDict', component: () => import('@/views/system/DictListView.vue'), meta: { title: '字典管理' } },
      { path: 'system/user', name: 'SystemUser', component: () => import('@/views/system/UserListView.vue'), meta: { title: '用户管理' } },
      { path: 'system/role', name: 'SystemRole', component: () => import('@/views/system/RoleListView.vue'), meta: { title: '角色管理' } },
      { path: 'system/menu', name: 'SystemMenu', component: () => import('@/views/system/MenuListView.vue'), meta: { title: '菜单管理' } },
      { path: 'system/log', name: 'SystemLog', component: () => import('@/views/system/LogListView.vue'), meta: { title: '日志管理' } },
      { path: 'system/notice', name: 'SystemNotice', component: () => import('@/views/system/NoticeListView.vue'), meta: { title: '通知公告' } },
    ],
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404View.vue'),
    meta: { title: '404', noAuth: true },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403View.vue'),
    meta: { title: '403', noAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由懒加载组件失败（dev server 重启/代码更新后，旧标签页点菜单会静默无反应）：
// 给出可见提示并自动刷新一次，避免"点击没反应"的困惑；加时间戳防止刷新循环
router.onError((error, to) => {
  const msg = String((error as Error)?.message || error)
  if (/import|fetch|chunk|dynamically|network/i.test(msg)) {
    const KEY = 'route_reload_at'
    const last = Number(sessionStorage.getItem(KEY) || 0)
    if (Date.now() - last > 5000) {
      sessionStorage.setItem(KEY, String(Date.now()))
      ElMessage.error('页面资源已更新，正在刷新…')
      setTimeout(() => window.location.assign(to?.fullPath || '/'), 600)
    } else {
      ElMessage.error('页面加载失败，请手动刷新（F5）；仍无效请重启 dev server')
    }
  }
})

router.beforeEach(async (to, _from, next) => {
  document.title = (to.meta.title as string) || '智能养殖信息管理系统'
  const token = getToken()

  if (to.meta.noAuth) {
    // 如果已登录且访问登录页，重定向到首页
    if (token && to.name === 'Login') {
      next('/dashboard')
      return
    }
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  const auth = useAuthStore()
  // RBAC + 多畜种（P3-6 A）：畜种校验 + 员工按权限模块校验
  try {
    // 1) 畜种校验：业务页面 /:species/... 的畜种必须属于当前养殖场可选畜种
    const sp = to.params.species as string | undefined
    if (sp) {
      if (auth.livestockTypes.length === 0) {
        await auth.loadFarmInfo()
      }
      if (auth.livestockTypes.length > 0 && !auth.speciesRouteList.includes(sp)) {
        next('/404')
        return
      }
    }
    // 2) 员工权限：模块 = 路径第二段（:species/模块/...），根路径取第一段；auth:false 的基础页面（个人中心等）不校验
    if (auth.userType === 3 && to.meta.auth !== false && to.path !== '/dashboard') {
      if (auth.perms.length === 0) {
        await auth.loadPermissions()
      }
      const segments = to.path.replace(/^\//, '').split('/')
      const perm = segments.length >= 3 ? segments[1] : segments[0]
      if (perm && !auth.perms.includes(perm)) {
        next('/403')
        return
      }
    }
  } catch {
    // 权限校验异常时放行，由页面接口自行拦截
  }

  next()
})

export default router
