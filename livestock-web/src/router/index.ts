import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { getToken } from '@/utils/token'

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
      // 养殖场
      { path: 'farm/info', name: 'FarmInfo', component: () => import('@/views/farm/FarmInfoView.vue'), meta: { title: '养殖场信息' } },
      { path: 'farm/employees', name: 'FarmEmployees', component: () => import('@/views/farm/EmployeeListView.vue'), meta: { title: '员工管理' } },
      { path: 'farm/salary', name: 'SalaryConfig', component: () => import('@/views/farm/SalaryConfigView.vue'), meta: { title: '薪资配置' } },
      // 圈舍
      { path: 'pen/list', name: 'PenList', component: () => import('@/views/pen/PenListView.vue'), meta: { title: '圈舍管理' } },
      { path: 'pen/:id', name: 'PenDetail', component: () => import('@/views/pen/PenDetailView.vue'), meta: { title: '圈舍详情' } },
      // 档案
      { path: 'animal/list', name: 'AnimalList', component: () => import('@/views/animal/AnimalListView.vue'), meta: { title: '畜禽档案' } },
      { path: 'animal/:id', name: 'AnimalDetail', component: () => import('@/views/animal/AnimalDetailView.vue'), meta: { title: '档案详情' } },
      { path: 'animal/individual-entry', name: 'AnimalIndividual', component: () => import('@/views/animal/AnimalIndividualView.vue'), meta: { title: '个体入栏' } },
      { path: 'animal/batch-entry', name: 'AnimalBatch', component: () => import('@/views/animal/AnimalBatchView.vue'), meta: { title: '批量入栏' } },
      { path: 'animal/history', name: 'AnimalHistory', component: () => import('@/views/animal/AnimalHistoryView.vue'), meta: { title: '历史记录' } },
      // 饲喂
      { path: 'feeding/plan', name: 'FeedingPlan', component: () => import('@/views/feeding/FeedingPlanView.vue'), meta: { title: '饲喂方案' } },
      { path: 'feeding/record', name: 'FeedingRecord', component: () => import('@/views/feeding/FeedingRecordView.vue'), meta: { title: '饲喂记录' } },
      // 物资库存
      { path: 'inventory/stock', name: 'InventoryStock', component: () => import('@/views/inventory/StockListView.vue'), meta: { title: '物资库存' } },
      { path: 'inventory/purchase', name: 'InventoryPurchase', component: () => import('@/views/inventory/PurchaseListView.vue'), meta: { title: '进货记录' } },
      { path: 'inventory/consume', name: 'InventoryConsume', component: () => import('@/views/inventory/ConsumeListView.vue'), meta: { title: '领用记录' } },
      // 防疫诊疗
      { path: 'health/vaccine', name: 'HealthVaccine', component: () => import('@/views/health/VaccineListView.vue'), meta: { title: '防疫记录' } },
      { path: 'health/medical', name: 'HealthMedical', component: () => import('@/views/health/MedicalListView.vue'), meta: { title: '诊疗记录' } },
      // 繁育
      { path: 'breeding/females', name: 'BreedingFemale', component: () => import('@/views/breeding/BreedingFemaleView.vue'), meta: { title: '母畜档案' } },
      { path: 'breeding/males', name: 'BreedingMale', component: () => import('@/views/breeding/BreedingMaleView.vue'), meta: { title: '公畜档案' } },
      { path: 'breeding/mating', name: 'BreedingMating', component: () => import('@/views/breeding/BreedingMatingView.vue'), meta: { title: '配种记录' } },
      { path: 'breeding/birth', name: 'BreedingBirth', component: () => import('@/views/breeding/BreedingBirthView.vue'), meta: { title: '产犊记录' } },
      { path: 'breeding/alert', name: 'BreedingAlert', component: () => import('@/views/breeding/BreedingAlertView.vue'), meta: { title: '繁育预警' } },
      // 审核
      { path: 'review/list', name: 'ReviewList', component: () => import('@/views/review/ReviewListView.vue'), meta: { title: '审核中心' } },
      // 销售财务
      { path: 'finance/sale', name: 'FinanceSale', component: () => import('@/views/finance/SaleListView.vue'), meta: { title: '销售订单' } },
      { path: 'finance/cost', name: 'FinanceCost', component: () => import('@/views/finance/CostListView.vue'), meta: { title: '成本支出' } },
      { path: 'finance/profit', name: 'FinanceProfit', component: () => import('@/views/finance/ProfitView.vue'), meta: { title: '利润核算' } },
      { path: 'finance/salary', name: 'FinanceSalary', component: () => import('@/views/finance/SalaryListView.vue'), meta: { title: '薪资记录' } },
      // 统计分析
      { path: 'statistics/dashboard', name: 'StatisticsDashboard', component: () => import('@/views/statistics/DashboardStatsView.vue'), meta: { title: '综合统计' } },
      { path: 'statistics/breeding', name: 'StatisticsBreeding', component: () => import('@/views/statistics/BreedingStatsView.vue'), meta: { title: '存栏繁育统计' } },
      { path: 'statistics/health', name: 'StatisticsHealth', component: () => import('@/views/statistics/HealthStatsView.vue'), meta: { title: '防疫诊疗统计' } },
      { path: 'statistics/material', name: 'StatisticsMaterial', component: () => import('@/views/statistics/MaterialStatsView.vue'), meta: { title: '物资消耗统计' } },
      { path: 'statistics/finance', name: 'StatisticsFinance', component: () => import('@/views/statistics/FinanceStatsView.vue'), meta: { title: '财务统计' } },
      // 系统管理
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

router.beforeEach((to, _from, next) => {
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

  next()
})

export default router
