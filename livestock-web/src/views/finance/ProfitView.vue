<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">利润核算</h2>
      <div>
        <el-date-picker
          v-model="range" type="daterange" value-format="YYYY-MM-DD"
          range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
          style="margin-right: 10px"
        />
        <el-button type="primary" @click="loadSummary">查询</el-button>
      </div>
    </div>

    <!-- 销售端 -->
    <div class="section-title">销售情况</div>
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售订单数</div><div class="stat-value">{{ summary.order_count }} 单</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售数量</div><div class="stat-value">{{ summary.animal_count }} 只</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售金额</div><div class="stat-value money">{{ fmt(summary.total_amount) }} 元</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">利润率</div><div class="stat-value" :class="rateClass">{{ summary.profit_rate }}%</div></el-card></el-col>
    </el-row>

    <!-- 成本构成 -->
    <div class="section-title">成本构成</div>
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">进货支出总成本</div>
          <div class="stat-value red">{{ fmt(summary.purchase_cost) }} 元</div>
          <div class="stat-tip">关联物资库存「进货记录」（饲料/兽药/疫苗等，仅统计审核通过）</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">物资消耗总成本</div>
          <div class="stat-value red">{{ fmt(summary.consume_cost) }} 元</div>
          <div class="stat-tip">关联「领用记录」实际使用量（数量 × 领用单价）</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">人工薪资总成本</div>
          <div class="stat-value red">{{ fmt(summary.labor_cost) }} 元</div>
          <div class="stat-tip">
            来自「薪资记录」<b>已发放</b>合计；待发放不计入成本
            <template v-if="summary.labor_pending > 0">
              <br />另有待发放 {{ fmt(summary.labor_pending) }} 元（发放后才计入）
            </template>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">其他成本</div>
          <div class="stat-value red">{{ fmt(summary.other_cost) }} 元</div>
          <div class="stat-tip">
            自主录入的水电/其他支出
            <el-button link type="primary" size="small" @click="goCost">去录入</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 结果 -->
    <div class="section-title">核算结果</div>
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card class="stat-card">
          <div class="stat-label">饲养总成本</div>
          <div class="stat-value red">{{ fmt(summary.breeding_cost) }} 元</div>
          <div class="stat-tip">进货支出 + 物资消耗 + 人工薪资 + 其他成本</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="stat-card highlight">
          <div class="stat-label">盈利金额</div>
          <div class="stat-value" :class="profitClass">{{ fmt(summary.profit) }} 元</div>
          <div class="stat-tip">销售金额 - 饲养总成本</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mt-16">
      <el-alert type="info" :closable="false" :title="formulaText" />
      <el-alert
        class="mt-8"
        type="warning"
        :closable="false"
        title="说明：进货支出按「买了多少」统计、物资消耗按「用了多少」统计，两者口径不同；按需求口径饲养总成本同时计入这两项，若只想看实际耗用成本，可只参考物资消耗一项。"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProfitSummaryApi, type ProfitSummary } from '@/api/finance'
import { useSpecies } from '@/composables/useSpecies'

const router = useRouter()
const { species } = useSpecies()

const range = ref<string[]>([])
const summary = reactive<ProfitSummary>({
  order_count: 0, animal_count: 0, total_amount: 0,
  purchase_cost: 0, consume_cost: 0, labor_cost: 0, labor_pending: 0, other_cost: 0,
  breeding_cost: 0, total_cost: 0, profit: 0, total_profit: 0,
  profit_rate: 0, expense_amount: 0, net_profit: 0,
})

const fmt = (v?: number) => Number(v || 0).toFixed(2)
const profitClass = computed(() => (summary.profit >= 0 ? 'green' : 'red'))
const rateClass = computed(() => (summary.profit_rate >= 0 ? 'green' : 'red'))
const formulaText = computed(
  () => `饲养总成本 ${fmt(summary.breeding_cost)} 元 = 进货支出 ${fmt(summary.purchase_cost)} 元`
    + ` + 物资消耗 ${fmt(summary.consume_cost)} 元`
    + ` + 人工薪资 ${fmt(summary.labor_cost)} 元`
    + ` + 其他成本 ${fmt(summary.other_cost)} 元；`
    + `盈利金额 ${fmt(summary.profit)} 元 = 销售金额 ${fmt(summary.total_amount)} 元 - 饲养总成本 ${fmt(summary.breeding_cost)} 元`,
)

function goCost() {
  router.push(`/${species.value}/finance/cost`)
}

async function loadSummary() {
  try {
    const res = await getProfitSummaryApi({
      start_date: range.value?.[0] || undefined,
      end_date: range.value?.[1] || undefined,
    })
    Object.assign(summary, res.data)
  } catch {
    // interceptor
  }
}

onMounted(loadSummary)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.mt-8 { margin-top: 8px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: #0b7f9c; margin: 4px 0 10px; }
.stat-card { text-align: center; }
.stat-label { font-size: 13px; color: #6b8ba4; margin-bottom: 8px; }
.stat-value { font-size: 22px; font-weight: 700; color: #0e2f47; }
.stat-tip { font-size: 12px; color: #8aa7bc; margin-top: 8px; line-height: 1.6; }
.money { color: #e6a23c; }
.green { color: #67c23a; }
.red { color: #f56c6c; }
.highlight { border-color: #67c23a; background: #f0f9eb; }
</style>
