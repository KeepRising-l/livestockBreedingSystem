<template>
  <div class="sidebar-container">
    <div class="logo">
      <span class="logo-mark">🐄</span>
      <span v-if="!isCollapse" class="logo-text">智能养殖</span>
    </div>
    <el-scrollbar class="menu-scrollbar">
      <el-menu
        ref="menuRef"
        unique-opened
        :default-active="activeMenu"
        :default-openeds="defaultOpeneds"
        :collapse="isCollapse"
        router
        class="side-menu"
      >
      <!-- 顶层：数据大屏（跨畜种） -->
      <el-menu-item v-if="showDashboard" index="/dashboard">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>数据大屏</template>
      </el-menu-item>
      <!-- 顶层：我的工作台（员工登录默认落地，C） -->
      <el-menu-item v-if="userType === 3" :index="`/${authStore.currentSpecies}/workbench`">
        <el-icon><Suitcase /></el-icon>
        <template #title>我的工作台</template>
      </el-menu-item>
      <!-- 顶层：养殖场管理（跨畜种，场主/超管） -->
      <el-sub-menu v-if="showFarm" index="/farm">
        <template #title>
          <el-icon><OfficeBuilding /></el-icon>
          <span>养殖场管理</span>
        </template>
        <el-menu-item index="/farm/info">养殖场信息</el-menu-item>
        <el-menu-item index="/farm/employees">员工管理</el-menu-item>
        <el-menu-item index="/farm/salary">薪资配置</el-menu-item>
      </el-sub-menu>

      <!-- 我的养殖场 → 畜种 → 模块 -->
      <el-sub-menu index="livestock">
        <template #title>
          <el-icon><House /></el-icon>
          <span>我的养殖场</span>
        </template>
        <el-sub-menu v-for="sp in speciesList" :key="sp" :index="'/' + sp">
          <template #title>
            <span>{{ SPECIES_CODE_MAP[sp] || sp }}场</span>
          </template>
          <el-sub-menu v-for="mod in modulesOf(sp)" :key="mod.key" :index="`/${sp}/${mod.key}`">
            <template #title>
              <el-icon><component :is="mod.icon" /></el-icon>
              <span>{{ mod.title }}</span>
            </template>
            <el-menu-item
              v-for="pg in mod.pages"
              :key="pg.path"
              :index="`/${sp}/${mod.key}/${pg.path}`"
            >
              {{ pg.title }}
            </el-menu-item>
          </el-sub-menu>
        </el-sub-menu>
      </el-sub-menu>

      <!-- 顶层：系统管理（仅超管） -->
      <el-sub-menu v-if="showSystem" index="/system">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/system/user">用户管理</el-menu-item>
        <el-menu-item index="/system/role">角色管理</el-menu-item>
        <el-menu-item index="/system/menu">菜单管理</el-menu-item>
        <el-menu-item index="/system/dict">字典管理</el-menu-item>
        <el-menu-item index="/system/log">日志管理</el-menu-item>
        <el-menu-item index="/system/notice">通知公告</el-menu-item>
      </el-sub-menu>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import type { MenuInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { SPECIES_CODE_MAP } from '@/utils/constants'

defineProps<{ isCollapse: boolean }>()

const route = useRoute()
const authStore = useAuthStore()
const menuRef = ref<MenuInstance>()

const activeMenu = computed(() => route.path)

/** 首次渲染默认展开：「我的养殖场」+ 当前畜种 + 当前模块（配合 unique-opened 手风琴） */
const defaultOpeneds = computed(() => buildOpeneds())

/** 从当前路由推导要展开的目录链：我的养殖场 → 畜种 → 模块
 *  仅畜种业务路由（/cattle|sheep|pig/...）联动展开；
 *  /farm、/system、/dashboard 等顶层页面不自动展开畜种目录，
 *  避免 unique-opened 手风琴把用户正在浏览的顶层目录（如养殖场管理）收起 */
function buildOpeneds(): string[] {
  const segs = route.path.replace(/^\//, '').split('/')
  if (!['cattle', 'sheep', 'pig'].includes(segs[0])) return []
  const sp = segs[0]
  const mod = segs[1]
  const opened = ['livestock', `/${sp}`]
  if (mod && mod !== 'workbench') opened.push(`/${sp}/${mod}`)
  return opened
}

// 路由切换（含跨畜种）时，侧边栏动态展开对应目录，其它自动收起
// 修改：只 open 真实存在的子菜单索引 + try/catch 兜底，防止 Vue 调度器死锁
watch(
  () => route.path,
  () => {
    const opened = buildOpeneds().filter((idx) => {
      if (idx === 'livestock') return true
      const segs = idx.split('/').filter(Boolean) // 如 ['cattle', 'feeding']
      if (segs.length === 1) return true // '/cattle' 畜种子菜单必定存在
      return MODULES.some((mod) => mod.key === segs[1])
    })
    opened.forEach((idx) => {
      try {
        menuRef.value?.open(idx)
      } catch {
        // 子菜单因 v-if/时序尚未注册时忽略，避免异常毒化调度器
      }
    })
  },
  { flush: 'post' },
)

const userType = computed(() => authStore.userType)

/** 可选畜种（路由值 cattle/sheep/pig），farmInfo 未加载时兜底全量 */
const speciesList = computed<string[]>(() =>
  authStore.speciesRouteList.length ? authStore.speciesRouteList : ['cattle', 'sheep', 'pig'],
)

const showDashboard = computed(() => [1, 2, 3].includes(userType.value))
const showFarm = computed(() => [1, 2].includes(userType.value))
const showSystem = computed(() => userType.value === 1)

interface PageDef {
  path: string
  title: string
}
interface ModuleDef {
  key: string
  title: string
  icon: string
  roles: number[]
  pages: PageDef[]
}

/** 业务模块模板（畜种维度内） */
const MODULES: ModuleDef[] = [
  {
    key: 'pen', title: '圈舍管理', icon: 'Grid', roles: [1, 2, 3],
    pages: [{ path: 'list', title: '圈舍列表' }],
  },
  {
    key: 'animal', title: '档案管理', icon: 'Notebook', roles: [1, 2, 3],
    pages: [
      { path: 'list', title: '畜禽档案' },
      { path: 'individual-entry', title: '个体入栏' },
      { path: 'batch-entry', title: '批量入栏' },
      { path: 'history', title: '历史记录' },
    ],
  },
  {
    key: 'feeding', title: '饲喂管理', icon: 'Food', roles: [1, 2, 3],
    pages: [
      { path: 'plan', title: '饲喂方案' },
      { path: 'record', title: '饲喂记录' },
    ],
  },
  {
    key: 'inventory', title: '物资库存', icon: 'Box', roles: [1, 2, 3],
    pages: [
      { path: 'stock', title: '物资库存' },
      { path: 'purchase', title: '进货记录' },
      { path: 'consume', title: '领用记录' },
    ],
  },
  {
    key: 'health', title: '防疫诊疗', icon: 'FirstAidKit', roles: [1, 2, 3],
    pages: [
      { path: 'vaccine', title: '防疫记录' },
      { path: 'medical', title: '诊疗记录' },
    ],
  },
  {
    key: 'breeding', title: '繁育管理', icon: 'Connection', roles: [1, 2, 3],
    pages: [
      { path: 'females', title: '母畜档案' },
      { path: 'males', title: '公畜档案' },
      { path: 'mating', title: '配种记录' },
      { path: 'birth', title: '产犊记录' },
      { path: 'alert', title: '繁育预警' },
    ],
  },
  {
    key: 'review', title: '审核中心', icon: 'Stamp', roles: [1, 2],
    pages: [{ path: 'list', title: '待审核列表' }],
  },
  {
    key: 'finance', title: '销售财务', icon: 'Money', roles: [1, 2],
    pages: [
      { path: 'sale', title: '销售订单' },
      { path: 'cost', title: '成本支出' },
      { path: 'profit', title: '利润核算' },
      { path: 'salary', title: '薪资记录' },
    ],
  },
  {
    key: 'statistics', title: '统计分析', icon: 'TrendCharts', roles: [1, 2, 3],
    pages: [
      { path: 'dashboard', title: '综合统计' },
      { path: 'breeding', title: '存栏繁育统计' },
      { path: 'health', title: '防疫诊疗统计' },
      { path: 'material', title: '物资消耗统计' },
      { path: 'finance', title: '财务统计' },
    ],
  },
]

/** 当前用户可见的模块（roles + 员工 perms 过滤） */
function modulesOf(sp: string): ModuleDef[] {
  return MODULES.filter(mod => {
    if (!mod.roles.includes(userType.value)) return false
    if (userType.value === 3 && !authStore.hasPerm(mod.key)) return false
    return true
  })
}
</script>

<style scoped lang="scss">
.sidebar-container {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 品牌区：HUD 徽标 + 全息渐变文字 */
.logo {
  height: 58px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(15, 168, 201, 0.16);
  background: linear-gradient(90deg, rgba(15, 168, 201, 0.1), transparent 70%);
  overflow: hidden;
}

.logo-mark {
  font-size: 19px;
  line-height: 1;
  filter: drop-shadow(0 0 10px rgba(15, 168, 201, 0.7));
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 2px;
  white-space: nowrap;
  background: linear-gradient(92deg, #0e2f47 10%, #37bcd8 55%, #2b7fff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.menu-scrollbar {
  flex: 1;
  min-height: 0;
}

.side-menu {
  border-right: none;
}

/* 菜单内图标在激活态下发光 */
.side-menu :deep(.el-menu-item.is-active .el-icon),
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title .el-icon) {
  color: #37bcd8;
  filter: drop-shadow(0 0 8px rgba(15, 168, 201, 0.85));
}

.side-menu :deep(.el-sub-menu .el-menu-item) {
  min-width: auto;
}

/* 三级菜单文字略小，层级更清爽 */
.side-menu :deep(.el-menu--inline .el-menu-item) {
  font-size: 13px;
  height: 38px;
  line-height: 38px;
}
</style>
