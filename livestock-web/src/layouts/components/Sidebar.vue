<template>
  <div class="sidebar-container">
    <div class="logo">
      <span v-if="!isCollapse">🐄 智能养殖</span>
      <span v-else>🐄</span>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      background-color="#001529"
      text-color="#ffffffa6"
      active-text-color="#fff"
      router
      class="side-menu"
    >
      <template v-for="item in menuItems" :key="item.path">
        <el-sub-menu v-if="item.children" :index="item.path">
          <template #title>
            <el-icon v-if="item.meta?.icon"><component :is="item.meta.icon" /></el-icon>
            <span>{{ item.meta?.title }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.path"
            :index="item.path + '/' + child.path"
          >
            {{ child.meta?.title }}
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-else :index="item.path">
          <el-icon v-if="item.meta?.icon"><component :is="item.meta.icon" /></el-icon>
          <template #title>{{ item.meta?.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps<{ isCollapse: boolean }>()

const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

interface MenuItem {
  path: string
  meta?: {
    title?: string
    icon?: string
    roles?: number[]
    hidden?: boolean
  }
  children?: { path: string; meta?: { title?: string; roles?: number[] } }[]
}

const allMenus: MenuItem[] = [
  {
    path: '/dashboard',
    meta: { title: '数据大屏', icon: 'DataAnalysis', roles: [1, 2, 3] },
  },
  {
    path: '/farm',
    meta: { title: '养殖场管理', icon: 'OfficeBuilding', roles: [1, 2] },
    children: [
      { path: 'info', meta: { title: '养殖场信息' } },
      { path: 'employees', meta: { title: '员工管理' } },
      { path: 'salary', meta: { title: '薪资配置' } },
    ],
  },
  {
    path: '/pen',
    meta: { title: '圈舍管理', icon: 'Grid', roles: [1, 2, 3] },
    children: [
      { path: 'list', meta: { title: '圈舍列表' } },
    ],
  },
  {
    path: '/animal',
    meta: { title: '档案管理', icon: 'Notebook', roles: [1, 2, 3] },
    children: [
      { path: 'list', meta: { title: '畜禽档案' } },
      { path: 'individual-entry', meta: { title: '个体入栏' } },
      { path: 'batch-entry', meta: { title: '批量入栏' } },
      { path: 'history', meta: { title: '历史记录' } },
    ],
  },
  {
    path: '/feeding',
    meta: { title: '饲喂管理', icon: 'Food', roles: [1, 2, 3] },
    children: [
      { path: 'plan', meta: { title: '饲喂方案' } },
      { path: 'record', meta: { title: '饲喂记录' } },
    ],
  },
  {
    path: '/inventory',
    meta: { title: '物资库存', icon: 'Box', roles: [1, 2, 3] },
    children: [
      { path: 'stock', meta: { title: '物资库存' } },
      { path: 'purchase', meta: { title: '进货记录' } },
      { path: 'consume', meta: { title: '领用记录' } },
    ],
  },
  {
    path: '/health',
    meta: { title: '防疫诊疗', icon: 'FirstAidKit', roles: [1, 2, 3] },
    children: [
      { path: 'vaccine', meta: { title: '防疫记录' } },
      { path: 'medical', meta: { title: '诊疗记录' } },
    ],
  },
  {
    path: '/breeding',
    meta: { title: '繁育管理', icon: 'Connection', roles: [1, 2, 3] },
    children: [
      { path: 'females', meta: { title: '母畜档案' } },
      { path: 'males', meta: { title: '公畜档案' } },
      { path: 'mating', meta: { title: '配种记录' } },
      { path: 'birth', meta: { title: '产犊记录' } },
      { path: 'alert', meta: { title: '繁育预警' } },
    ],
  },
  {
    path: '/review',
    meta: { title: '审核中心', icon: 'Stamp', roles: [1, 2] },
    children: [
      { path: 'list', meta: { title: '待审核列表' } },
    ],
  },
  {
    path: '/finance',
    meta: { title: '销售财务', icon: 'Money', roles: [1, 2] },
    children: [
      { path: 'sale', meta: { title: '销售订单' } },
      { path: 'cost', meta: { title: '成本支出' } },
      { path: 'profit', meta: { title: '利润核算' } },
      { path: 'salary', meta: { title: '薪资记录' } },
    ],
  },
  {
    path: '/system',
    meta: { title: '系统管理', icon: 'Setting', roles: [1] },
    children: [
      { path: 'dict', meta: { title: '字典管理' } },
    ],
  },
  {
    path: '/statistics',
    meta: { title: '统计分析', icon: 'TrendCharts', roles: [1, 2, 3] },
    children: [
      { path: 'dashboard', meta: { title: '综合统计' } },
      { path: 'breeding', meta: { title: '存栏繁育统计' } },
      { path: 'health', meta: { title: '防疫诊疗统计' } },
      { path: 'material', meta: { title: '物资消耗统计' } },
      { path: 'finance', meta: { title: '财务统计' } },
    ],
  },
]

const menuItems = computed(() => {
  const userType = authStore.userType
  return allMenus.filter(menu => {
    const roles = menu.meta?.roles || []
    return roles.includes(userType)
  })
})
</script>

<style scoped lang="scss">
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.side-menu {
  border-right: none;
  flex: 1;
}
</style>
