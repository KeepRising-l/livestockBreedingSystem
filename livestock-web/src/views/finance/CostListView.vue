<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">成本支出</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增支出
      </el-button>
    </div>

    <el-card class="mb-16">
      <el-form inline>
        <el-form-item label="支出类型">
          <el-select v-model="query.expense_type" clearable placeholder="全部" style="width: 130px" @change="loadExpenses">
            <el-option v-for="t in EXPENSE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadExpenses">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="expenses" v-loading="loading" stripe>
        <el-table-column prop="expense_date" label="日期" width="120" />
        <el-table-column prop="expense_type" label="类型" width="100">
          <template #default="{ row }"><el-tag type="info">{{ row.expense_type }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="130">
          <template #default="{ row }"><span class="amount">{{ Number(row.amount).toFixed(2) }} 元</span></template>
        </el-table-column>
        <el-table-column prop="voucher_no" label="凭证号" width="120">
          <template #default="{ row }"><span v-if="row.voucher_no">{{ row.voucher_no }}</span><span v-else class="muted">-</span></template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="180" />
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row as CostExpense)">编辑</el-button>
            <el-popconfirm title="确定删除该支出？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="text-right mt-16">
        <el-pagination
          v-model:current-page="pageNum" v-model:page-size="pageSize" :total="total"
          :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @size-change="loadExpenses" @current-change="loadExpenses"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑支出' : '新增支出'" width="460px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="支出类型" prop="expense_type">
          <el-select v-model="form.expense_type" placeholder="请选择类型" style="width: 100%">
            <el-option v-for="t in EXPENSE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" style="width: 100%" placeholder="元" />
        </el-form-item>
        <el-form-item label="支出日期" prop="expense_date">
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="凭证号" prop="voucher_no">
          <el-input v-model="form.voucher_no" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { ref, reactive, onMounted } from 'vue'
import {
  getExpenseListApi, addExpenseApi, updateExpenseApi, deleteExpenseApi, type CostExpense,
} from '@/api/finance'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const EXPENSE_TYPES = ['饲料', '兽药', '疫苗', '人工', '水电', '其他']

const expenses = ref<CostExpense[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const query = reactive({ expense_type: '' })

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  expense_type: '饲料',
  amount: 100,
  expense_date: '',
  voucher_no: '',
  remark: '',
})

const formRules: FormRules = {
  expense_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  expense_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
}

async function loadExpenses() {
  loading.value = true
  try {
    const res = await getExpenseListApi({
      expense_type: query.expense_type || undefined,
      pageNum: pageNum.value, pageSize: pageSize.value,
    })
    const data = res.data as any
    expenses.value = data.list || []
    total.value = data.total || 0
  } catch {
    // interceptor
  } finally {
    loading.value = false
  }
}

function today() {
  return dayjs().format('YYYY-MM-DD')
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  form.expense_type = '饲料'
  form.amount = 100
  form.expense_date = today()
  form.voucher_no = ''
  form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row: CostExpense) {
  isEdit.value = true
  editId.value = row.id
  form.expense_type = row.expense_type
  form.amount = Number(row.amount)
  form.expense_date = row.expense_date
  form.voucher_no = row.voucher_no || ''
  form.remark = row.remark || ''
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = {
      expense_type: form.expense_type,
      amount: form.amount,
      expense_date: form.expense_date,
      voucher_no: form.voucher_no || undefined,
      remark: form.remark || undefined,
    }
    if (isEdit.value) {
      await updateExpenseApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addExpenseApi(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadExpenses()
  } catch {
    // interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteExpenseApi(id)
    ElMessage.success('已删除')
    loadExpenses()
  } catch {
    // interceptor
  }
}

onMounted(loadExpenses)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.amount { font-weight: 600; color: #e6a23c; }
.muted { color: #6b8ba4; }
</style>
