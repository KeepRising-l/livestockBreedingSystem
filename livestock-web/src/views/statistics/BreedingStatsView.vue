<template>
  <div>
    <h2 class="page-title">存栏繁育统计</h2>

    <!-- KPI 卡片 -->
    <el-alert type="info" :closable="false" show-icon class="mb-16"
      title="统计口径：受孕率=累计已孕检定论配种中成功怀孕占比（待孕检不计入）；生产率=本月产犊数÷本月配种数；平均成活率=产犊记录成活率均值" />
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

    <!-- 分布 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="8">
        <el-card>
          <template #header>畜种分布</template>
          <v-chart v-if="speciesOption" :option="speciesOption" style="height: 280px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>性别分布</template>
          <v-chart v-if="genderOption" :option="genderOption" style="height: 280px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>生长阶段分布</template>
          <v-chart v-if="stageOption" :option="stageOption" style="height: 280px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 圈舍存栏 + 预警 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <el-card>
          <template #header>圈舍存栏分布</template>
          <v-chart v-if="penOption" :option="penOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>待处理预警分布</template>
          <v-chart v-if="alertOption" :option="alertOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 产犊趋势 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card>
          <template #header>近 12 月产犊趋势</template>
          <v-chart v-if="birthTrendOption" :option="birthTrendOption" style="height: 300px" autoresize />
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
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getBreedingStatsApi, type BreedingStats } from '@/api/statistics'

use([CanvasRenderer, BarChart, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref<BreedingStats | null>(null)

const kpiCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '当前存栏', value: s.current_stock, unit: '头', color: '#0b9a78', icon: 'Grid' },
    { label: '本月配种', value: s.month_mating, unit: '次', color: '#2b7fff', icon: 'Connection' },
    { label: '本月产犊', value: s.month_birth, unit: '头', color: '#d98d1c', icon: 'Plus' },
    { label: '妊娠母畜', value: s.pregnant_count, unit: '头', color: '#6b46e0', icon: 'Notebook' },
    { label: '受孕率', value: s.pregnancy_rate, unit: '%', color: '#0b9a78', icon: 'DataAnalysis' },
    { label: '生产率', value: s.reproduction_rate, unit: '%', color: '#d98d1c', icon: 'TrendCharts' },
    { label: '平均成活率', value: s.avg_survival_rate, unit: '%', color: '#0b9a78', icon: 'FirstAidKit' },
    { label: '待处理预警', value: s.pending_alert_count, unit: '条', color: '#e8455f', icon: 'Bell' },
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

const speciesOption = computed(() => pieOption(stats.value?.species_dist))
const genderOption = computed(() => pieOption(stats.value?.gender_dist))
const stageOption = computed(() => pieOption(stats.value?.stage_dist))
const alertOption = computed(() => pieOption(stats.value?.alert_dist))

const penOption = computed(() => {
  const d = stats.value?.pen_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.map(i => i.name) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: d.map(i => i.value), itemStyle: { color: '#2b7fff' }, barMaxWidth: 36 }],
  }
})

const birthTrendOption = computed(() => {
  const t = stats.value?.birth_trend
  if (!t || !t.months.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: t.months },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '产犊数', type: 'line', smooth: true, data: t.values, areaStyle: { opacity: 0.15 }, itemStyle: { color: '#d98d1c' } }],
  }
})

onMounted(async () => {
  try {
    const res = await getBreedingStatsApi()
    stats.value = res.data
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
</style>
