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

    <el-row :gutter="16" class="mb-16">
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售订单数</div><div class="stat-value">{{ summary.order_count }}</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售数量</div><div class="stat-value">{{ summary.animal_count }} 只</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售额</div><div class="stat-value money">{{ summary.total_amount.toFixed(2) }} 元</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">饲养总成本</div><div class="stat-value money">{{ summary.total_cost.toFixed(2) }} 元</div></el-card></el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">销售利润</div><div class="stat-value green">{{ summary.total_profit.toFixed(2) }} 元</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">利润率</div><div class="stat-value green">{{ summary.profit_rate }}%</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card"><div class="stat-label">成本支出</div><div class="stat-value red">{{ summary.expense_amount.toFixed(2) }} 元</div></el-card></el-col>
      <el-col :span="6"><el-card class="stat-card highlight"><div class="stat-label">净利润</div><div class="stat-value">{{ summary.net_profit.toFixed(2) }} 元</div></el-card></el-col>
    </el-row>

    <el-card class="mt-16">
      <el-alert type="success" :closable="false"
        :title="`净利润 = 销售利润 ${summary.total_profit.toFixed(2)} 元 - 成本支出 ${summary.expense_amount.toFixed(2)} 元`" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getProfitSummaryApi, type ProfitSummary } from '@/api/finance'

const range = ref<string[]>([])
const summary = reactive<ProfitSummary>({
  order_count: 0, animal_count: 0, total_amount: 0, total_cost: 0,
  total_profit: 0, profit_rate: 0, expense_amount: 0, net_profit: 0,
})

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
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.stat-card { text-align: center; }
.stat-label { font-size: 13px; color: #999; margin-bottom: 8px; }
.stat-value { font-size: 22px; font-weight: 700; color: #333; }
.money { color: #e6a23c; }
.green { color: #67c23a; }
.red { color: #f56c6c; }
.highlight { border-color: #67c23a; background: #f0f9eb; }
</style>
