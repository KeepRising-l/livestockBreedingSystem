<template>
  <div>
    <h2 class="page-title">财务统计</h2>

    <!-- KPI 卡片 -->
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

    <!-- 销售/利润趋势 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="16">
        <el-card>
          <template #header>近 12 月销售额 / 利润趋势</template>
          <v-chart v-if="profitTrendOption" :option="profitTrendOption" style="height: 320px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>成本支出分布</template>
          <v-chart v-if="expenseOption" :option="expenseOption" style="height: 320px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 本月利润明细 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card>
          <template #header>本月利润核算</template>
          <el-descriptions :column="4" border v-if="monthSummary">
            <el-descriptions-item label="销售额(元)">{{ monthSummary.total_amount.toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="总成本(元)">{{ monthSummary.total_cost.toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="销售利润(元)">{{ monthSummary.total_profit.toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="利润率(%)">{{ monthSummary.profit_rate }}%</el-descriptions-item>
            <el-descriptions-item label="成本支出(元)">{{ monthSummary.expense_amount.toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="净利润(元)">
              <span :style="{ color: (monthSummary.net_profit ?? 0) >= 0 ? '#16a34a' : '#ef4444', fontWeight: 700 }">
                {{ (monthSummary.net_profit ?? 0).toLocaleString() }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="本月暂无销售数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from '@/components/TechChart.vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getFinanceStatsApi, type FinanceStats } from '@/api/statistics'

use([CanvasRenderer, BarChart, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref<FinanceStats | null>(null)

const kpiCards = computed(() => {
  const s = stats.value
  if (!s) return []
  const t = s.total
  return [
    { label: '累计销售额', value: t.total_amount, unit: '元', color: '#0ea5e9', icon: 'Sell' },
    { label: '累计销售成本', value: t.total_cost, unit: '元', color: '#8b4513', icon: 'Money' },
    { label: '累计销售利润', value: t.total_profit, unit: '元', color: '#17954d', icon: 'TrendCharts' },
    { label: '累计净利润', value: (t.net_profit ?? 0), unit: '元', color: (t.net_profit ?? 0) >= 0 ? '#17954d' : '#dc2626', icon: 'Money' },
    { label: '累计订单数', value: t.order_count, unit: '单', color: '#475569', icon: 'Notebook' },
    { label: '累计出栏数', value: t.animal_count, unit: '头', color: '#a16207', icon: 'Grid' },
    { label: '本月净利润', value: (s.month.net_profit ?? 0), unit: '元', color: (s.month.net_profit ?? 0) >= 0 ? '#17954d' : '#dc2626', icon: 'TrendCharts' },
    { label: '成本支出', value: t.expense_amount, unit: '元', color: '#a16207', icon: 'Money' },
  ]
})

const monthSummary = computed(() => stats.value?.month || null)

const profitTrendOption = computed(() => {
  const t = stats.value?.profit_trend
  if (!t || !t.months.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['销售额', '利润'] },
    xAxis: { type: 'category', data: t.months },
    yAxis: { type: 'value' },
    series: [
      { name: '销售额', type: 'bar', data: t.sale_values, itemStyle: { color: '#0ea5e9' }, barMaxWidth: 24 },
      { name: '利润', type: 'line', smooth: true, data: t.profit_values, itemStyle: { color: '#16a34a' } },
    ],
  }
})

const expenseOption = computed(() => {
  const d = stats.value?.expense_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: d, itemStyle: { borderRadius: 4 } }],
  }
})

onMounted(async () => {
  try {
    const res = await getFinanceStatsApi()
    stats.value = res.data
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
</style>
