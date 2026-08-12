<template>
  <div>
    <h2 class="page-title">数据大屏</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ penTotal }}</div>
          <div class="stat-label">圈舍总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ animalTotal }}</div>
          <div class="stat-label">畜禽总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ penUsed }}</div>
          <div class="stat-label">在用圈舍</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ farmInfo?.farm_name || '-' }}</div>
          <div class="stat-label">当前养殖场</div>
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

    <!-- 圈舍利用情况 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card class="mb-16">
          <template #header>圈舍存栏分布</template>
          <v-chart v-if="penChartOption" :option="penChartOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="mb-16">
          <template #header>品种分布</template>
          <v-chart v-if="breedChartOption" :option="breedChartOption" style="height: 300px" autoresize />
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
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { getAnimalListApi, type AnimalInfo } from '@/api/animal'
import { getFarmInfoApi, type FarmInfo } from '@/api/farm'
import { useAuthStore } from '@/stores/auth'

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const router = useRouter()
const authStore = useAuthStore()
const farmInfo = ref<FarmInfo | null>(null)
const pens = ref<PenInfo[]>([])
const animals = ref<AnimalInfo[]>([])
const penTotal = ref(0)
const animalTotal = ref(0)

const penUsed = computed(() => pens.value.filter(p => p.current_count > 0).length)

const quickLinks = [
  { path: '/animal/list', icon: 'Notebook', label: '畜禽档案' },
  { path: '/pen/list', icon: 'Grid', label: '圈舍管理' },
  { path: '/animal/individual-entry', icon: 'Plus', label: '个体入栏' },
  { path: '/animal/batch-entry', icon: 'Upload', label: '批量入栏' },
  { path: '/farm/info', icon: 'OfficeBuilding', label: '养殖场信息' },
  { path: '/farm/employees', icon: 'UserFilled', label: '员工管理' },
]

const penChartOption = computed(() => {
  if (!pens.value.length) return null
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: pens.value.map(p => p.pen_code) },
    yAxis: { type: 'value' },
    series: [
      { name: '容量', type: 'bar', data: pens.value.map(p => p.capacity), itemStyle: { color: '#b0bec5' } },
      { name: '存栏', type: 'bar', data: pens.value.map(p => p.current_count), itemStyle: { color: '#2E7D32' } },
    ],
  }
})

const breedChartOption = computed(() => {
  const breedMap: Record<string, number> = {}
  animals.value.forEach(a => {
    breedMap[a.breed] = (breedMap[a.breed] || 0) + 1
  })
  const data = Object.entries(breedMap).map(([name, value]) => ({ name, value }))
  if (!data.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '70%'], data, itemStyle: { borderRadius: 4 } }],
  }
})

onMounted(async () => {
  try {
    const fRes = await getFarmInfoApi()
    farmInfo.value = fRes.data
  } catch { /* */ }

  try {
    const pRes = await getPenListApi({ pageNum: 1, pageSize: 100 })
    const pData = pRes.data as any
    pens.value = pData.list || []
    penTotal.value = pData.total || 0
  } catch { /* */ }

  try {
    const aRes = await getAnimalListApi({ pageNum: 1, pageSize: 1 })
    animalTotal.value = (aRes.data as any)?.total || 0
    // Get breed data - load up to 500 records for chart
    const fullRes = await getAnimalListApi({ pageNum: 1, pageSize: 100 })
    animals.value = (fullRes.data as any)?.list || []
  } finally { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #333; }
.mb-16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #2E7D32; }
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
</style>
