<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">薪资记录</h2>
      <div>
        <el-date-picker
          v-model="payMonth" type="month" value-format="YYYY-MM" placeholder="选择月份"
          style="width: 140px; margin-right: 10px"
        />
        <el-button type="primary" @click="handleGenerate" :loading="generating">生成薪资</el-button>
      </div>
    </div>

    <el-card class="mb-16">
      <el-form inline>
        <el-form-item label="岗位">
          <el-select v-model="query.post" clearable placeholder="全部" style="width: 130px" @change="loadSalaries">
            <el-option v-for="(_, key) in POST_MAP" :key="key" :label="key" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width: 120px" @change="loadSalaries">
            <el-option label="待发放" value="待发放" />
            <el-option label="已发放" value="已发放" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadSalaries">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="salaries" v-loading="loading" stripe>
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="username" label="账号" width="110" />
        <el-table-column prop="post" label="岗位" width="90">
          <template #default="{ row }"><el-tag type="info">{{ row.post }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="pay_month" label="月份" width="90" />
        <el-table-column prop="base_salary" label="基础薪资" width="100" />
        <el-table-column prop="bonus" label="奖金" width="80" />
        <el-table-column prop="deduct" label="扣款" width="80" />
        <el-table-column prop="actual_pay" label="实发" width="110">
          <template #default="{ row }"><span class="amount">{{ Number(row.actual_pay).toFixed(2) }}</span></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '已发放' ? 'success' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pay_time" label="发放时间" min-width="160">
          <template #default="{ row }"><span v-if="row.pay_time">{{ row.pay_time }}</span><span v-else class="muted">-</span></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待发放'" link type="success" size="small" @click="handlePay(row)">
              发放
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="text-right mt-16">
        <el-pagination
          v-model:current-page="pageNum" v-model:page-size="pageSize" :total="total"
          :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @size-change="loadSalaries" @current-change="loadSalaries"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getSalaryListApi, generateSalaryApi, paySalaryApi, type SalaryRecord,
} from '@/api/finance'
import { POST_MAP } from '@/utils/constants'
import { ElMessage, ElMessageBox } from 'element-plus'

const salaries = ref<SalaryRecord[]>([])
const loading = ref(false)
const generating = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const payMonth = ref('')
const query = reactive({ post: '', status: '' })

async function loadSalaries() {
  loading.value = true
  try {
    const res = await getSalaryListApi({
      pay_month: payMonth.value || undefined,
      post: query.post || undefined,
      status: query.status || undefined,
      pageNum: pageNum.value, pageSize: pageSize.value,
    })
    const data = res.data as any
    salaries.value = data.list || []
    total.value = data.total || 0
  } catch {
    // interceptor
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (!payMonth.value) {
    ElMessage.warning('请先选择月份')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将为 ${payMonth.value} 月份的在职员工生成薪资记录，确定继续？`,
      '生成薪资', { confirmButtonText: '生成', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  generating.value = true
  try {
    const res = await generateSalaryApi(payMonth.value)
    ElMessage.success((res as any).msg || '生成成功')
    loadSalaries()
  } catch {
    // interceptor
  } finally {
    generating.value = false
  }
}

async function handlePay(row: SalaryRecord) {
  try {
    await paySalaryApi(row.id)
    ElMessage.success('发放成功')
    loadSalaries()
  } catch {
    // interceptor
  }
}

onMounted(loadSalaries)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.amount { font-weight: 600; color: #e6a23c; }
.muted { color: #999; }
</style>
