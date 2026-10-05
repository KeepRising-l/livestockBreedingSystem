<template>
  <div class="workbench">
    <div class="flex-between mb-16">
      <h2 class="page-title">员工工作台<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-tag size="large" type="success">{{ post || '未设置岗位' }}</el-tag>
    </div>

    <!-- 通用 KPI（所有岗位） -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6" v-for="card in kpiCards" :key="card.label">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="kpi-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 饲喂员工作台 -->
    <template v-if="post === '饲喂员'">
      <el-row :gutter="16" class="mb-16">
        <el-col :span="12">
          <el-card>
            <template #header>启用中的饲喂方案</template>
            <el-table :data="plans" size="small" v-loading="loading">
              <el-table-column prop="plan_name" label="方案名称" min-width="140" />
              <el-table-column prop="applicable_stage" label="适用阶段" width="120" />
              <el-table-column prop="feed_times_per_day" label="日喂次数" width="80" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>圈舍存栏</template>
            <el-table :data="pens" size="small" v-loading="loading">
              <el-table-column prop="pen_code" label="编号" width="90" />
              <el-table-column prop="pen_type" label="类型" width="70" />
              <el-table-column prop="current_count" label="存栏" width="70" />
              <el-table-column prop="capacity" label="容量" width="70" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
      <el-card>
        <template #header>最近饲喂记录</template>
        <el-table :data="feedRecords" size="small" v-loading="loading">
          <el-table-column prop="feed_date" label="日期" width="110" />
          <el-table-column prop="time_period" label="时段" width="90" />
          <el-table-column prop="pen_type" label="圈舍类型" width="90" />
          <el-table-column prop="animal_count" label="数量" width="70" />
          <el-table-column prop="feed_cost" label="成本(元)" width="90" />
          <el-table-column prop="audit_status" label="审核" width="90" />
        </el-table>
      </el-card>
    </template>

    <!-- 兽医工作台 -->
    <template v-else-if="post === '兽医'">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>最近防疫记录</template>
            <el-table :data="vaccines" size="small" v-loading="loading">
              <el-table-column prop="vaccine_date" label="日期" width="110" />
              <el-table-column prop="ear_tag" label="耳标" width="110" />
              <el-table-column prop="vaccine_type" label="疫苗类型" min-width="120" />
              <el-table-column prop="next_vaccine_date" label="下次日期" width="110" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>最近诊疗记录</template>
            <el-table :data="medicals" size="small" v-loading="loading">
              <el-table-column prop="medical_date" label="日期" width="110" />
              <el-table-column prop="ear_tag" label="耳标" width="110" />
              <el-table-column prop="disease_type" label="病症" min-width="120" />
              <el-table-column prop="treatment_status" label="状态" width="90" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 繁育员工作台 -->
    <template v-else-if="post === '繁育员'">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>繁育预警</template>
            <el-table :data="alerts" size="small" v-loading="loading">
              <el-table-column prop="alert_type" label="类型" width="90" />
              <el-table-column prop="animal_tag" label="耳标" width="110" />
              <el-table-column prop="alert_content" label="内容" min-width="140" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>最近配种记录</template>
            <el-table :data="matings" size="small" v-loading="loading">
              <el-table-column prop="mating_date" label="日期" width="110" />
              <el-table-column prop="female_tag" label="母畜" width="100" />
              <el-table-column prop="male_tag" label="公畜" width="100" />
              <el-table-column prop="status" label="状态" min-width="100" />
              <el-table-column prop="remain_days" label="距预产(天)" width="100" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 库管员工作台 -->
    <template v-else-if="post === '库管员'">
      <el-card class="mb-16">
        <template #header>库存不足预警</template>
        <el-table :data="stocks" size="small" v-loading="loading">
          <el-table-column prop="material_name" label="物资名称" min-width="140" />
          <el-table-column prop="specification" label="规格" min-width="100" />
          <el-table-column prop="quantity" label="现有量" width="80" />
          <el-table-column prop="unit" label="单位" width="70" />
          <el-table-column prop="warning_threshold" label="警戒线" width="80" />
        </el-table>
      </el-card>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>最近领用</template>
            <el-table :data="consumes" size="small" v-loading="loading">
              <el-table-column prop="consume_date" label="日期" width="110" />
              <el-table-column prop="material_name" label="物资" min-width="120" />
              <el-table-column prop="quantity" label="数量" width="70" />
              <el-table-column prop="unit" label="单位" width="70" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>最近进货</template>
            <el-table :data="purchases" size="small" v-loading="loading">
              <el-table-column prop="purchase_date" label="日期" width="110" />
              <el-table-column prop="material_name" label="物资" min-width="120" />
              <el-table-column prop="quantity" label="数量" width="70" />
              <el-table-column prop="total_cost" label="金额(元)" width="90" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="未配置岗位工作台" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSpecies } from '@/composables/useSpecies'
import { getDashboardStatsApi, type DashboardStats } from '@/api/statistics'
import { getFeedingPlanListApi, getFeedingRecordListApi } from '@/api/feeding'
import { getPenListApi } from '@/api/pen'
import { getVaccineListApi, getMedicalListApi } from '@/api/health'
import { getAlertListApi, getMatingListApi } from '@/api/breeding'
import { getStockListApi, getConsumeListApi, getPurchaseListApi } from '@/api/inventory'

const authStore = useAuthStore()
const { species, speciesZh } = useSpecies()
const post = computed(() => authStore.post)

const loading = ref(false)
const stats = ref<DashboardStats | null>(null)
const plans = ref<any[]>([])
const feedRecords = ref<any[]>([])
const pens = ref<any[]>([])
const vaccines = ref<any[]>([])
const medicals = ref<any[]>([])
const alerts = ref<any[]>([])
const matings = ref<any[]>([])
const stocks = ref<any[]>([])
const consumes = ref<any[]>([])
const purchases = ref<any[]>([])

const kpiCards = computed(() => {
  const k = stats.value?.kpi
  return [
    { label: '今日存栏', value: k?.today_stock ?? '-', color: '#16a34a' },
    { label: '待处理预警', value: k?.pending_alert ?? '-', color: '#dc2626' },
    { label: '待审核记录', value: k?.pending_audit ?? '-', color: '#fbbf24' },
    { label: '我的岗位', value: post.value || '-', color: '#94a3b8' },
  ]
})

async function loadKpi() {
  try {
    const res = await getDashboardStatsApi()
    stats.value = res.data
  } catch {
    // 忽略，接口异常不阻塞工作台
  }
}

async function loadAll() {
  loading.value = true
  try {
    const p = post.value
    if (p === '饲喂员') {
      const [planRes, recordRes, penRes] = await Promise.all([
        getFeedingPlanListApi({ species: species.value, status: 1, pageNum: 1, pageSize: 5 }),
        getFeedingRecordListApi({ species: speciesZh.value, pageNum: 1, pageSize: 5 }),
        getPenListApi({ species: speciesZh.value, pageNum: 1, pageSize: 20 }),
      ])
      plans.value = (planRes.data as any)?.list || []
      feedRecords.value = (recordRes.data as any)?.list || []
      pens.value = (penRes.data as any)?.list || []
    } else if (p === '兽医') {
      const [vRes, mRes] = await Promise.all([
        getVaccineListApi({ species: speciesZh.value, pageNum: 1, pageSize: 5 }),
        getMedicalListApi({ species: speciesZh.value, pageNum: 1, pageSize: 5 }),
      ])
      vaccines.value = (vRes.data as any)?.list || []
      medicals.value = (mRes.data as any)?.list || []
    } else if (p === '繁育员') {
      const [aRes, mRes] = await Promise.all([
        getAlertListApi({ species: speciesZh.value, pageNum: 1, pageSize: 5 }),
        getMatingListApi({ species: speciesZh.value, pageNum: 1, pageSize: 5 }),
      ])
      alerts.value = (aRes.data as any)?.list || []
      matings.value = (mRes.data as any)?.list || []
    } else if (p === '库管员') {
      const [sRes, cRes, puRes] = await Promise.all([
        getStockListApi({ is_shortage: 1, pageNum: 1, pageSize: 20 }),
        getConsumeListApi({ pageNum: 1, pageSize: 5 }),
        getPurchaseListApi({ pageNum: 1, pageSize: 5 }),
      ])
      stocks.value = (sRes.data as any)?.list || []
      consumes.value = (cRes.data as any)?.list || []
      purchases.value = (puRes.data as any)?.list || []
    }
  } catch {
    // 岗位数据加载失败，忽略
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadKpi()
  loadAll()
})

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  loadKpi()
  loadAll()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.kpi-card { text-align: center; padding: 8px; }
.kpi-value { font-size: 26px; font-weight: 700; }
.kpi-label { font-size: 13px; color: #64748b; margin-top: 4px; }
</style>
