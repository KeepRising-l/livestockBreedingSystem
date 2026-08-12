<template>
  <div>
    <h2 class="page-title">数据大屏</h2>

    <!-- 今日待办 -->
    <el-card class="mb-16">
      <template #header>
        <div class="card-header">
          <span class="card-title">今日待办</span>
          <el-button v-if="canAccess('breeding')" link type="primary" @click="goTo('breeding/alert', 'breeding')">查看全部预警 →</el-button>
        </div>
      </template>
      <el-row :gutter="12">
        <el-col :span="4" v-for="card in todoCards" :key="card.label">
          <div class="todo-card" :class="{ clickable: !!card.path }" @click="card.path && goTo(card.path, card.perm)">
            <div class="todo-value" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="todo-label">{{ card.label }}</div>
          </div>
        </el-col>
      </el-row>
      <el-divider v-if="todoItems.length" />
      <div v-if="todoItems.length" class="todo-list">
        <div v-for="item in todoItems" :key="item.key" class="todo-item" @click="goTo(item.path, item.perm)">
          <el-tag :type="item.tagType" size="small">{{ item.type }}</el-tag>
          <span class="todo-text">{{ item.text }}</span>
          <span v-if="item.meta" class="todo-meta">{{ item.meta }}</span>
        </div>
      </div>
      <el-empty v-else description="今日暂无待办事项" :image-size="60" />
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="24">
        <el-card>
          <template #header>快捷入口</template>
          <el-row :gutter="12">
            <el-col :span="4" v-for="item in quickLinks" :key="item.path">
              <el-button class="quick-btn" @click="router.push(item.path)">
                <el-icon :size="24"><component :is="item.icon" /></el-icon>
                <span>{{ item.label }}</span>
              </el-button>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 入栏/出栏趋势 + 畜种分布 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="16">
        <el-card>
          <template #header>近 12 月入栏 / 出栏趋势</template>
          <v-chart v-if="trendOption" :option="trendOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>畜种分布</template>
          <v-chart v-if="speciesOption" :option="speciesOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 圈舍存栏 + 生长阶段 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>圈舍存栏分布</template>
          <v-chart v-if="penOption" :option="penOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>生长阶段分布</template>
          <v-chart v-if="stageOption" :option="stageOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getDashboardStatsApi, type DashboardStats } from '@/api/statistics'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { getFarmInfoApi, type FarmInfo } from '@/api/farm'
import { useAuthStore } from '@/stores/auth'

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const authStore = useAuthStore()
const farmInfo = ref<FarmInfo | null>(null)
const pens = ref<PenInfo[]>([])
const stats = ref<DashboardStats | null>(null)

const quickLinks = computed(() => {
  const sp = authStore.currentSpecies
  return [
    { path: `/${sp}/animal/list`, icon: 'Notebook', label: '畜禽档案' },
    { path: `/${sp}/pen/list`, icon: 'Grid', label: '圈舍管理' },
    { path: `/${sp}/animal/individual-entry`, icon: 'Plus', label: '个体入栏' },
    { path: `/${sp}/animal/batch-entry`, icon: 'Upload', label: '批量入栏' },
    { path: '/farm/info', icon: 'OfficeBuilding', label: '养殖场信息' },
    { path: '/farm/employees', icon: 'UserFilled', label: '员工管理' },
  ]
})

const kpiCards = computed(() => {
  const k = stats.value?.kpi
  if (!k) return []
  return [
    { label: '今日存栏', value: k.today_stock, color: '#2E7D32' },
    { label: '本月入栏', value: k.month_in, color: '#1976D2' },
    { label: '本月出栏', value: k.month_out, color: '#E65100' },
    { label: '当前养殖场', value: farmInfo.value?.farm_name || '-', color: '#455A64' },
    { label: '累计销售额(元)', value: k.total_sale.toLocaleString(), color: '#6A1B9A' },
    { label: '累计利润(元)', value: k.total_profit.toLocaleString(), color: '#C62828' },
    { label: '待审核记录', value: k.pending_audit, color: '#F57F17' },
    { label: '待处理预警', value: k.pending_alert, color: '#D32F2F' },
  ]
})

const todoCards = computed(() => {
  const k = stats.value?.kpi
  const t = stats.value?.todos
  if (!k || !t) return []
  const alertMap: Record<string, number> = {}
  t.alert_by_type.forEach(a => { alertMap[a.name] = a.value })
  return [
    { label: '存栏总数', value: k.today_stock, color: '#2E7D32', path: '', perm: '' },
    { label: '圈舍总数', value: t.pen_count, color: '#1976D2', path: '', perm: '' },
    { label: '待审核记录', value: k.pending_audit, color: '#F57F17', path: 'review/list', perm: 'review' },
    { label: '待处理预警', value: k.pending_alert, color: '#D32F2F', path: 'breeding/alert', perm: 'breeding' },
    { label: '临产提醒', value: alertMap['临产'] || 0, color: '#E65100', path: 'breeding/alert', perm: 'breeding' },
    { label: '库存不足', value: t.shortage_count, color: '#C62828', path: 'inventory/stock', perm: 'inventory' },
  ]
})

const tagTypeMap: Record<string, any> = { 临产: 'danger', 孕检: 'primary', 未发情: 'warning' }
const todoItems = computed(() => {
  const t = stats.value?.todos
  if (!t) return []
  const items: any[] = []
  t.recent_alerts.forEach(a => {
    items.push({
      key: `alert-${a.id}`,
      type: a.alert_type,
      tagType: tagTypeMap[a.alert_type] || 'info',
      text: a.alert_content,
      meta: a.animal_tag,
      path: 'breeding/alert',
      perm: 'breeding',
    })
  })
  t.shortage_items.forEach(s => {
    items.push({
      key: `shortage-${s.id}`,
      type: '缺货',
      tagType: 'danger',
      text: `${s.material_name}（${s.material_type}）`,
      meta: `库存 ${s.quantity}`,
      path: 'inventory/stock',
      perm: 'inventory',
    })
  })
  return items
})

function canAccess(perm: string) {
  return authStore.hasPerm(perm)
}

function goTo(path: string, perm: string) {
  if (perm && !authStore.hasPerm(perm)) return
  const sp = authStore.currentSpecies
  router.push(`/${sp}/${path}`)
}

const trendOption = computed(() => {
  const t = stats.value?.stock_trend
  if (!t || !t.months.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['入栏', '出栏'] },
    xAxis: { type: 'category', data: t.months },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '入栏', type: 'bar', data: t.in_values, itemStyle: { color: '#1976D2' }, barMaxWidth: 24 },
      { name: '出栏', type: 'bar', data: t.out_values, itemStyle: { color: '#E65100' }, barMaxWidth: 24 },
    ],
  }
})

const speciesOption = computed(() => {
  const d = stats.value?.species_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: d, itemStyle: { borderRadius: 4 } }],
  }
})

const penOption = computed(() => {
  if (!pens.value.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: pens.value.map(p => p.pen_code) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '容量', type: 'bar', data: pens.value.map(p => p.capacity), itemStyle: { color: '#b0bec5' }, barMaxWidth: 20 },
      { name: '存栏', type: 'bar', data: pens.value.map(p => p.current_count), itemStyle: { color: '#2E7D32' }, barMaxWidth: 20 },
    ],
  }
})

const stageOption = computed(() => {
  const d = stats.value?.stage_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.map(i => i.name) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: d.map(i => i.value), itemStyle: { color: '#6A1B9A' }, barMaxWidth: 40 }],
  }
})

onMounted(async () => {
  try {
    const fRes = await getFarmInfoApi()
    farmInfo.value = fRes.data
  } catch { /* */ }

  try {
    const pRes = await getPenListApi({ pageNum: 1, pageSize: 100 })
    pens.value = (pRes.data as any)?.list || []
  } catch { /* */ }

  try {
    const sRes = await getDashboardStatsApi()
    stats.value = sRes.data
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #333; }
.mb-16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px; }
.stat-value { font-size: 26px; font-weight: 700; color: #2E7D32; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.quick-btn {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid #e8ecf1;
}
.quick-btn:hover { border-color: #2E7D32; color: #2E7D32; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; }
.todo-card {
  text-align: center;
  padding: 10px 4px;
  border: 1px solid #e8ecf1;
  border-radius: 6px;
  transition: border-color .2s;
}
.todo-card.clickable { cursor: pointer; }
.todo-card.clickable:hover { border-color: #2E7D32; }
.todo-value { font-size: 22px; font-weight: 700; }
.todo-label { font-size: 12px; color: #999; margin-top: 4px; }
.todo-list { display: flex; flex-direction: column; gap: 8px; }
.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  background: #f8fafc;
  cursor: pointer;
}
.todo-item:hover { background: #eef4f0; }
.todo-text {
  flex: 1;
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.todo-meta { font-size: 12px; color: #999; white-space: nowrap; }
</style>
