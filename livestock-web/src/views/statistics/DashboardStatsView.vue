<template>
  <div>
    <h2 class="page-title">综合统计</h2>

    <!-- KPI 卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 入栏/出栏趋势 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="16">
        <el-card>
          <template #header>近 12 月入栏 / 出栏趋势</template>
          <el-skeleton v-if="loading" :rows="6" animated />
          <v-chart v-else-if="trendOption" :option="trendOption" style="height: 320px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>畜种分布</template>
          <el-skeleton v-if="loading" :rows="6" animated />
          <v-chart v-else-if="speciesOption" :option="speciesOption" style="height: 320px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 生长阶段分布 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>生长阶段分布</template>
          <el-skeleton v-if="loading" :rows="6" animated />
          <v-chart v-else-if="stageOption" :option="stageOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>经营概况</template>
          <el-row :gutter="12" class="summary-row">
            <el-col :span="8" v-for="item in summaryItems" :key="item.label">
              <div class="summary-item">
                <div class="summary-value">{{ item.value }}</div>
                <div class="summary-label">{{ item.label }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getDashboardStatsApi, type DashboardStats } from '@/api/statistics'

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref<DashboardStats | null>(null)
const loading = ref(false)

const kpiCards = computed(() => {
  const k = stats.value?.kpi
  if (!k) return []
  return [
    { label: '今日存栏', value: k.today_stock, color: '#2E7D32' },
    { label: '本月入栏', value: k.month_in, color: '#1976D2' },
    { label: '本月出栏', value: k.month_out, color: '#E65100' },
    { label: '累计销售额(元)', value: k.total_sale.toLocaleString(), color: '#6A1B9A' },
    { label: '累计利润(元)', value: k.total_profit.toLocaleString(), color: '#C62828' },
    { label: '待审核记录', value: k.pending_audit, color: '#F57F17' },
    { label: '待处理预警', value: k.pending_alert, color: '#D32F2F' },
    { label: '员工数', value: k.staff_count, color: '#455A64' },
  ]
})

const summaryItems = computed(() => {
  const k = stats.value?.kpi
  if (!k) return []
  return [
    { label: '净利润(元)', value: (k.total_profit).toLocaleString() },
    { label: '待审核', value: k.pending_audit },
    { label: '待处理预警', value: k.pending_alert },
  ]
})

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

const stageOption = computed(() => {
  const d = stats.value?.stage_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.map(i => i.name) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: d.map(i => i.value), itemStyle: { color: '#2E7D32' }, barMaxWidth: 40 }],
  }
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await getDashboardStatsApi()
    stats.value = res.data
  } catch { /* */ } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #333; }
.mb-16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px; }
.stat-value { font-size: 26px; font-weight: 700; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.summary-row { margin-top: 8px; }
.summary-item { text-align: center; padding: 20px 0; border: 1px solid #eef2f6; border-radius: 8px; background: #fafbfc; }
.summary-value { font-size: 24px; font-weight: 700; color: #2E7D32; }
.summary-label { font-size: 13px; color: #999; margin-top: 6px; }
</style>
