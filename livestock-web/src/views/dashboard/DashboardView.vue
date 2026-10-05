<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">数据大屏</h2>
      <el-button type="primary" plain @click="handleExport">
        <el-icon><Download /></el-icon> 导出 Excel
      </el-button>
    </div>

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
          <MetricCard
            :label="card.label"
            :value="card.value"
            :unit="card.unit"
            :color="card.color"
            :icon="card.icon"
            :clickable="!!card.path"
            @click="card.path && goTo(card.path, card.perm)"
          />
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
      <el-col :span="6" v-for="card in kpiCards" :key="card.label" class="mb-16">
        <MetricCard
          :label="card.label"
          :value="card.value"
          :unit="card.unit"
          :color="card.color"
          :icon="card.icon"
        />
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
import { ElMessage } from 'element-plus'
import VChart from '@/components/TechChart.vue'
import MetricCard from '@/components/MetricCard.vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getDashboardStatsApi, type DashboardStats } from '@/api/statistics'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { getFarmInfoApi, type FarmInfo } from '@/api/farm'
import { useAuthStore } from '@/stores/auth'
import { exportToExcelAsync, type ExportSheet } from '@/utils/excel'

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
    { label: '今日存栏', value: k.today_stock, unit: '头', color: '#0b9a78', icon: 'Grid' },
    { label: '本月入栏', value: k.month_in, unit: '头', color: '#2b7fff', icon: 'Plus' },
    { label: '本月出栏', value: k.month_out, unit: '头', color: '#d98d1c', icon: 'Sell' },
    { label: '当前养殖场', value: farmInfo.value?.farm_name || '-', unit: '', color: '#5b7d95', icon: 'OfficeBuilding' },
    { label: '累计销售额', value: k.total_sale, unit: '元', color: '#6b46e0', icon: 'Money' },
    { label: '累计利润', value: k.total_profit, unit: '元', color: '#e8455f', icon: 'TrendCharts' },
    { label: '待审核记录', value: k.pending_audit, unit: '条', color: '#d98d1c', icon: 'Stamp' },
    { label: '待处理预警', value: k.pending_alert, unit: '条', color: '#e8455f', icon: 'Bell' },
  ]
})

const todoCards = computed(() => {
  const k = stats.value?.kpi
  const t = stats.value?.todos
  if (!k || !t) return []
  const alertMap: Record<string, number> = {}
  t.alert_by_type.forEach(a => { alertMap[a.name] = a.value })
  return [
    { label: '存栏总数', value: k.today_stock, unit: '头', color: '#0b9a78', icon: 'Grid', path: '', perm: '' },
    { label: '圈舍总数', value: t.pen_count, unit: '个', color: '#2b7fff', icon: 'House', path: '', perm: '' },
    { label: '待审核记录', value: k.pending_audit, unit: '条', color: '#d98d1c', icon: 'Stamp', path: 'review/list', perm: 'review' },
    { label: '待处理预警', value: k.pending_alert, unit: '条', color: '#e8455f', icon: 'Bell', path: 'breeding/alert', perm: 'breeding' },
    { label: '临产提醒', value: alertMap['临产'] || 0, unit: '条', color: '#d98d1c', icon: 'AlarmClock', path: 'breeding/alert', perm: 'breeding' },
    { label: '库存不足', value: t.shortage_count, unit: '项', color: '#e8455f', icon: 'Box', path: 'inventory/stock', perm: 'inventory' },
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
      { name: '入栏', type: 'bar', data: t.in_values, itemStyle: { color: '#2b7fff' }, barMaxWidth: 24 },
      { name: '出栏', type: 'bar', data: t.out_values, itemStyle: { color: '#d98d1c' }, barMaxWidth: 24 },
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
    // 圈舍编号只在畜种内唯一（牛/羊/猪 都可能叫 A01），坐标轴上要带畜种前缀才不至于混淆
    xAxis: { type: 'category', data: pens.value.map(p => `${p.species || '待归属'}-${p.pen_code}`) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '容量', type: 'bar', data: pens.value.map(p => p.capacity), itemStyle: { color: '#5b7f9e' }, barMaxWidth: 20 },
      { name: '存栏', type: 'bar', data: pens.value.map(p => p.current_count), itemStyle: { color: '#0ea47a' }, barMaxWidth: 20 },
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
    series: [{ type: 'bar', data: d.map(i => i.value), itemStyle: { color: '#a78bfa' }, barMaxWidth: 40 }],
  }
})

function handleExport() {
  const sheets: ExportSheet[] = []
  if (kpiCards.value.length) {
    sheets.push({ name: 'KPI概览', headers: ['指标', '数值'], rows: kpiCards.value.map((c) => [c.label, c.value]) })
  }
  if (todoCards.value.length) {
    sheets.push({ name: '今日待办', headers: ['指标', '数值'], rows: todoCards.value.map((c) => [c.label, c.value]) })
  }
  if (todoItems.value.length) {
    sheets.push({
      name: '待办明细',
      headers: ['类型', '内容', '关联'],
      rows: todoItems.value.map((i) => [i.type, i.text, i.meta || '']),
    })
  }
  const t = stats.value?.stock_trend
  if (t?.months?.length) {
    sheets.push({
      name: '入栏出栏趋势',
      headers: ['月份', '入栏', '出栏'],
      rows: t.months.map((m, i) => [m, t.in_values[i] ?? 0, t.out_values[i] ?? 0]),
    })
  }
  if (stats.value?.species_dist?.length) {
    sheets.push({
      name: '畜种分布',
      headers: ['畜种', '数量'],
      rows: stats.value.species_dist.map((d) => [d.name, d.value]),
    })
  }
  if (stats.value?.stage_dist?.length) {
    sheets.push({
      name: '生长阶段分布',
      headers: ['生长阶段', '数量'],
      rows: stats.value.stage_dist.map((d) => [d.name, d.value]),
    })
  }
  if (pens.value.length) {
    sheets.push({
      name: '圈舍存栏',
      headers: ['畜种', '圈舍编号', '容量', '存栏'],
      rows: pens.value.map((p) => [p.species || '待归属', p.pen_code, p.capacity, p.current_count]),
    })
  }
  if (!sheets.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const today = new Date().toISOString().split('T')[0]
  exportToExcelAsync(`数据大屏报表_${today}.xlsx`, sheets, '正在生成大屏报表...')
}

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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }


/* 快捷入口：霓虹描边 + 悬停浮起发光 */
.quick-btn {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid rgba(15, 168, 201, 0.2);
  transition: border-color .25s ease, color .25s ease, box-shadow .25s ease, transform .25s ease;
}
.quick-btn:hover {
  border-color: #0fa8c9;
  color: #37bcd8;
  box-shadow: 0 0 20px rgba(15, 168, 201, 0.24);
  transform: translateY(-2px);
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; }

/* 今日待办列表（轻量条目：左侧色条 + 悬停高亮） */
.todo-list { display: flex; flex-direction: column; gap: 8px; }
.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border-left: 2px solid rgba(15, 168, 201, 0.45);
  background: rgba(15, 168, 201, 0.05);
  cursor: pointer;
  transition: background-color .2s ease, border-color .2s ease;
}
.todo-item:hover {
  background: rgba(15, 168, 201, 0.12);
  border-left-color: #0fa8c9;
}
.todo-text {
  flex: 1;
  font-size: 13px;
  color: #2b4b63;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.todo-meta { font-size: 12px; color: #8ba7bb; white-space: nowrap; }

</style>
