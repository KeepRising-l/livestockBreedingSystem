<template>
  <div>
    <h2 class="page-title">物资消耗统计</h2>

    <!-- KPI 卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
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
import VChart from 'vue-echarts'
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
    { label: '库存种类', value: s.stock_count, color: '#1976D2' },
    { label: '缺货物资', value: s.shortage_count, color: '#D32F2F' },
    { label: '已过期', value: s.expired_count, color: '#C62828' },
    { label: '即将过期', value: s.expiring_count, color: '#F57F17' },
    { label: '本月进货金额(元)', value: s.month_purchase_amount.toLocaleString(), color: '#2E7D32' },
    { label: '本月领用量', value: s.month_consume.toLocaleString(), color: '#6A1B9A' },
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
    series: [{ name: '领用量', type: 'bar', data: t.values, itemStyle: { color: '#6A1B9A' }, barMaxWidth: 36 }],
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
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #333; }
.mb-16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px; }
.stat-value { font-size: 26px; font-weight: 700; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
</style>
