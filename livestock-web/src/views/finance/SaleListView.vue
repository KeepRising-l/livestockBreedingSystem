<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">销售订单<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="openSale">
        <el-icon><Sell /></el-icon> 出栏销售
      </el-button>
    </div>

    <el-card class="mb-16">
      <el-form inline>
        <el-form-item label="订单号">
          <el-input v-model="query.order_no" placeholder="如 SO20260812" clearable style="width: 180px" @change="loadOrders" />
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="query.customer" placeholder="客户名称" clearable style="width: 150px" @change="loadOrders" />
        </el-form-item>
        <el-form-item label="结算状态">
          <el-select v-model="query.settle_status" clearable placeholder="全部" style="width: 120px" @change="loadOrders">
            <el-option label="未结算" value="未结算" />
            <el-option label="已结算" value="已结算" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadOrders">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="customer" label="客户" width="140" />
        <el-table-column prop="animal_count" label="数量" width="70" />
        <el-table-column prop="total_weight" label="总重量kg" width="90" />
        <el-table-column prop="unit_price" label="单价" width="90">
          <template #default="{ row }">{{ row.unit_price }} 元/kg</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="销售额" width="110">
          <template #default="{ row }"><span class="amount">{{ Number(row.total_amount).toFixed(2) }}</span></template>
        </el-table-column>
        <el-table-column prop="order_date" label="订单日期" width="160" />
        <el-table-column prop="settle_status" label="结算" width="90">
          <template #default="{ row }">
            <el-tag :type="row.settle_status === '已结算' ? 'success' : 'warning'">{{ row.settle_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showDetail(row.id)">详情</el-button>
            <el-button v-if="row.settle_status === '未结算'" link type="success" size="small" @click="handleSettle(row)">
              结算
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="text-right mt-16">
        <el-pagination
          v-model:current-page="pageNum" v-model:page-size="pageSize" :total="total"
          :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @size-change="loadOrders" @current-change="loadOrders"
        />
      </div>
    </el-card>

    <!-- 出栏销售弹窗 -->
    <el-dialog v-model="saleVisible" title="出栏销售" width="820px">
      <el-form :model="saleForm" label-width="80px" class="mb-16">
        <el-form-item label="客户名称" required>
          <el-input v-model="saleForm.customer" placeholder="客户名称" style="width: 220px" />
        </el-form-item>
        <el-form-item label="客户电话">
          <el-input v-model="saleForm.customer_phone" placeholder="选填" style="width: 200px" />
        </el-form-item>
        <el-form-item label="单价" required>
          <el-input-number v-model="saleForm.unit_price" :min="0.1" :precision="2" style="width: 160px" /> 元/kg
        </el-form-item>
        <el-form-item label="销售日期">
          <el-date-picker v-model="saleForm.order_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" class="mb-16"
        title="勾选要出售的畜禽并填写重量，勾选后自动计算该只销售额" />
      <el-table ref="candRef" :data="candidates" v-loading="candLoading" stripe max-height="320">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="ear_tag" label="耳标" width="90" />
        <el-table-column prop="species" label="种类" width="70" />
        <el-table-column prop="breed" label="品种" width="110" />
        <el-table-column prop="growth_stage" label="生长阶段" width="110" />
        <el-table-column prop="in_date" label="入栏日期" width="110" />
        <el-table-column label="销售重量kg" width="140">
          <template #default="{ row }">
            <el-input-number v-model="row._weight" :min="1" :precision="2" :step="10" size="small" style="width: 110px" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="saleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaleOut">确认出栏</el-button>
      </template>
    </el-dialog>

    <!-- 订单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="销售订单详情" width="820px">
      <template v-if="detail">
        <el-descriptions :column="3" border class="mb-16">
          <el-descriptions-item label="订单号">{{ detail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ detail.customer }}</el-descriptions-item>
          <el-descriptions-item label="结算状态">{{ detail.settle_status }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ detail.animal_count }} 只</el-descriptions-item>
          <el-descriptions-item label="总重量">{{ detail.total_weight }} kg</el-descriptions-item>
          <el-descriptions-item label="销售额">{{ Number(detail.total_amount).toFixed(2) }} 元</el-descriptions-item>
        </el-descriptions>
        <el-table :data="detail.details" stripe>
          <el-table-column prop="ear_tag" label="耳标" width="90" />
          <el-table-column prop="species" label="种类" width="70" />
          <el-table-column prop="weight" label="重量kg" width="80" />
          <el-table-column prop="raise_days" label="饲养天数" width="80" />
          <el-table-column prop="feed_cost" label="饲料成本" width="90" />
          <el-table-column prop="labor_cost" label="人工成本" width="90" />
          <el-table-column prop="total_cost" label="总成本" width="90" />
          <el-table-column prop="sale_amount" label="销售额" width="90" />
          <el-table-column prop="profit" label="利润" width="90">
            <template #default="{ row }"><span class="profit">+{{ Number(row.profit).toFixed(2) }}</span></template>
          </el-table-column>
          <el-table-column prop="profit_rate" label="利润率" width="80">
            <template #default="{ row }">{{ row.profit_rate }}%</template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getSaleListApi, getSaleCandidatesApi, saleOutApi, getSaleDetailApi, settleSaleApi,
  type SaleOrder, type SaleOrderDetail, type SaleCandidate,
} from '@/api/finance'
import { ElMessage } from 'element-plus'
import type { TableInstance } from 'element-plus'
import { useSpecies } from '@/composables/useSpecies'

const { species, speciesZh } = useSpecies()

const orders = ref<SaleOrder[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const query = reactive({ order_no: '', customer: '', settle_status: '' })

const saleVisible = ref(false)
const saving = ref(false)
const candLoading = ref(false)
const candidates = ref<SaleCandidate[]>([])
const candRef = ref<TableInstance>()
const saleForm = reactive({
  customer: '',
  customer_phone: '',
  unit_price: 30,
  order_date: '',
})

const detailVisible = ref(false)
const detail = ref<{
  order_no: string; customer: string; settle_status: string
  animal_count: number; total_weight: number; total_amount: number
  details: SaleOrderDetail[]
} | null>(null)

async function loadOrders() {
  loading.value = true
  try {
    const res = await getSaleListApi({
      order_no: query.order_no || undefined,
      customer: query.customer || undefined,
      settle_status: query.settle_status || undefined,
      pageNum: pageNum.value, pageSize: pageSize.value,
    })
    const data = res.data as any
    orders.value = data.list || []
    total.value = data.total || 0
  } catch {
    // interceptor
  } finally {
    loading.value = false
  }
}

async function loadCandidates() {
  candLoading.value = true
  try {
    const res = await getSaleCandidatesApi({ species: speciesZh.value })
    candidates.value = (res.data as SaleCandidate[]) || []
    candidates.value.forEach((c: any) => { c._weight = 100 })
  } catch {
    // interceptor
  } finally {
    candLoading.value = false
  }
}

async function openSale() {
  saleForm.customer = ''
  saleForm.customer_phone = ''
  saleForm.unit_price = 30
  saleForm.order_date = ''
  saleVisible.value = true
  await loadCandidates()
}

async function handleSaleOut() {
  if (!saleForm.customer.trim()) {
    ElMessage.warning('请填写客户名称')
    return
  }
  if (!saleForm.unit_price || saleForm.unit_price <= 0) {
    ElMessage.warning('请填写单价')
    return
  }
  const rows: any[] = (candRef.value as any)?.getSelectionRows?.() || []
  if (!rows.length) {
    ElMessage.warning('请勾选要出售的畜禽')
    return
  }
  const items = rows.map((r: any) => ({ ear_tag: r.ear_tag, weight: r._weight }))
  saving.value = true
  try {
    const res = await saleOutApi({
      customer: saleForm.customer,
      customer_phone: saleForm.customer_phone || undefined,
      unit_price: saleForm.unit_price,
      order_date: saleForm.order_date || undefined,
      items,
    })
    ElMessage.success((res as any).msg || '出栏成功')
    saleVisible.value = false
    loadOrders()
  } catch {
    // interceptor
  } finally {
    saving.value = false
  }
}

async function showDetail(id: number) {
  const res = await getSaleDetailApi(id)
  detail.value = (res.data as any) || null
  detailVisible.value = true
}

async function handleSettle(row: SaleOrder) {
  try {
    await settleSaleApi(row.id)
    ElMessage.success('结算成功')
    loadOrders()
  } catch {
    // interceptor
  }
}

onMounted(loadOrders)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.amount { font-weight: 600; color: #e6a23c; }
.profit { color: #67c23a; }
</style>
