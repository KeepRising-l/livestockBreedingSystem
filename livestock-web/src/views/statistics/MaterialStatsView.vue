<template>
  <div>
    <h2 class="page-title">物资消耗统计</h2>

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

    <!-- 类型/状态分布 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <el-card>
          <template #header>物资类型分布（种类数）</template>
          <v-chart v-if="typeOption" :option="typeOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>库存状态分布</template>
          <v-chart v-if="statusOption" :option="statusOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 领用趋势 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card>
          <template #header>近 12 月领用数量趋势</template>
          <v-chart v-if="consumeTrendOption" :option="consumeTrendOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
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
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getMaterialStatsApi, type MaterialStats } from '@/api/statistics'

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref<MaterialStats | null>(null)

const kpiCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '库存种类', value: s.stock_count, unit: '种', color: '#0ea5e9', icon: 'Grid' },
    { label: '缺货物资', value: s.shortage_count, unit: '项', color: '#dc2626', icon: 'Box' },
    { label: '已过期', value: s.expired_count, unit: '项', color: '#b91c1c', icon: 'Delete' },
    { label: '即将过期', value: s.expiring_count, unit: '项', color: '#a16207', icon: 'AlarmClock' },
    { label: '本月进货金额', value: s.month_purchase_amount, unit: '元', color: '#17954d', icon: 'Money' },
    { label: '本月领用量', value: s.month_consume, unit: '', color: '#8b4513', icon: 'Sell' },
  ]
})

function pieOption(data: { name: string; value: number }[] | undefined) {
  if (!data || !data.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '70%'], data, itemStyle: { borderRadius: 4 } }],
  }
}

const typeOption = computed(() => pieOption(stats.value?.type_dist))
const statusOption = computed(() => pieOption(stats.value?.status_dist))

const consumeTrendOption = computed(() => {
  const t = stats.value?.consume_trend
  if (!t || !t.months.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: t.months },
    yAxis: { type: 'value' },
    series: [{ name: '领用量', type: 'bar', data: t.values, itemStyle: { color: '#b45309' }, barMaxWidth: 36 }],
  }
})

onMounted(async () => {
  try {
    const res = await getMaterialStatsApi()
    stats.value = res.data
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
</style>
