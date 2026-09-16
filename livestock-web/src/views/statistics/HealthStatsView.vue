<template>
  <div>
    <h2 class="page-title">防疫诊疗统计</h2>

    <!-- KPI 卡片 -->
    <el-alert type="info" :closable="false" show-icon class="mb-16"
      title="统计口径：分母=当前存栏；已免疫=本月审核通过防疫记录去重耳标；发病=本月审核通过诊疗记录数；死亡=本月审核通过诊疗记录中治疗状态为死亡的去重耳标" />
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}{{ card.suffix || '' }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分布 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <el-card>
          <template #header>疫苗类型分布（已审核）</template>
          <v-chart v-if="vaccineOption" :option="vaccineOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>病情类型分布（已审核）</template>
          <v-chart v-if="diseaseOption" :option="diseaseOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 诊疗状态 + 趋势 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>诊疗状态分布</template>
          <v-chart v-if="treatmentOption" :option="treatmentOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>近 12 月防疫 / 诊疗趋势</template>
          <v-chart v-if="healthTrendOption" :option="healthTrendOption" style="height: 300px" autoresize />
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
import { getHealthStatsApi, type HealthStats } from '@/api/statistics'

use([CanvasRenderer, BarChart, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref<HealthStats | null>(null)

const kpiCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '本月防疫记录', value: s.month_vaccine, color: '#4a95ff' },
    { label: '本月已免疫牛只', value: s.month_immunized_animals, color: '#00e6a8' },
    { label: '免疫覆盖率', value: s.immunization_coverage, suffix: '%', color: '#a78bfa' },
    { label: '本月诊疗记录', value: s.month_medical, color: '#ffb020' },
    { label: '发病率', value: s.morbidity_rate, suffix: '%', color: '#ffd166' },
    { label: '死亡率', value: s.mortality_rate, suffix: '%', color: '#ff6b85' },
    { label: '死亡数量', value: s.death_count, color: '#B71C1C' },
    { label: '治疗中', value: (s.treatment_dist.find(i => i.name === '治疗中')?.value ?? 0), color: '#7fa8c9' },
  ]
})

function barOption(data: { name: string; value: number }[] | undefined, color: string) {
  if (!data || !data.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(i => i.name), axisLabel: { interval: 0, rotate: 20 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: data.map(i => i.value), itemStyle: { color }, barMaxWidth: 40 }],
  }
}

const vaccineOption = computed(() => barOption(stats.value?.vaccine_dist, '#4a95ff'))
const diseaseOption = computed(() => barOption(stats.value?.disease_dist, '#ffb020'))

const treatmentOption = computed(() => {
  const d = stats.value?.treatment_dist
  if (!d || !d.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: d, itemStyle: { borderRadius: 4 } }],
  }
})

const healthTrendOption = computed(() => {
  const t = stats.value?.health_trend
  if (!t || !t.months.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['防疫', '诊疗'] },
    xAxis: { type: 'category', data: t.months },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '防疫', type: 'line', smooth: true, data: t.vaccine_values, itemStyle: { color: '#4a95ff' } },
      { name: '诊疗', type: 'line', smooth: true, data: t.medical_values, itemStyle: { color: '#ffb020' } },
    ],
  }
})

onMounted(async () => {
  try {
    const res = await getHealthStatsApi()
    stats.value = res.data
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px; }
.stat-value { font-size: 26px; font-weight: 700; }
.stat-label { font-size: 13px; color: #8fa9bf; margin-top: 4px; }
</style>
