<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">进货记录</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 提交进货
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="物资类型">
          <el-select v-model="query.material_type" placeholder="全部" clearable style="width: 140px" @change="search">
            <el-option v-for="o in MATERIAL_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="query.material_name" placeholder="物资名称" clearable style="width: 180px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="进货日期">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD"
            style="width: 260px" @change="onDateChange" />
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="query.audit_status" placeholder="全部" clearable style="width: 120px" @change="search">
            <el-option v-for="(label, key) in AUDIT_STATUS_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="purchase_date" label="进货日期" width="110" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.material_type)" size="small">{{ row.material_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="物资名称" min-width="140" />
        <el-table-column prop="batch_no" label="批次号" width="120">
          <template #default="{ row }">{{ row.batch_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="单价" width="90">
          <template #default="{ row }">{{ row.cost_price }} 元</template>
        </el-table-column>
        <el-table-column label="总金额" width="110">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: 600;">{{ row.total_cost }} 元</span>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="110">
          <template #default="{ row }">{{ row.expiry_date || '-' }}</template>
        </el-table-column>
        <el-table-column prop="supplier" label="供应商" width="120" show-overflow-tooltip />
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click.stop="handleEdit(row)" v-if="row.audit_status === '待审核'">编辑</el-button>
            <el-button link type="success" size="small" @click.stop="handleAudit(row, '通过')" v-if="canAudit && row.audit_status === '待审核'">通过</el-button>
            <el-button link type="danger" size="small" @click.stop="handleAudit(row, '驳回')" v-if="canAudit && row.audit_status === '待审核'">驳回</el-button>
            <el-popconfirm title="确定删除该记录？" @confirm="handleDelete(row.id)" v-if="row.audit_status !== '通过'">
              <template #reference>
                <el-button link type="danger" size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="text-right mt-16">
        <el-pagination v-model:current-page="pageNum" v-model:page-size="pageSize" :total="total"
          :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @size-change="loadData" @current-change="loadData" />
      </div>
    </el-card>

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑进货记录' : '提交进货记录'" width="600px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="物资类型" prop="material_type">
          <el-select v-model="form.material_type" placeholder="请选择" style="width: 100%" :disabled="isEdit">
            <el-option v-for="o in MATERIAL_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
          <div style="color:#999;font-size:12px;">若库存里没有此物资，审核通过时会自动创建</div>
        </el-form-item>
        <el-form-item label="物资名称" prop="material_name">
          <el-input v-model="form.material_name" placeholder="如：玉米精料" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="批次号">
          <el-input v-model="form.batch_no" placeholder="如：YL20260810" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="数量" prop="quantity">
              <el-input-number v-model="form.quantity" :min="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位" prop="unit">
              <el-select v-model="form.unit" filterable allow-create style="width: 100%">
                <el-option v-for="u in MATERIAL_UNIT_OPTIONS" :key="u" :label="u" :value="u" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="单价(元)" prop="cost_price">
              <el-input-number v-model="form.cost_price" :min="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总金额">
              <span style="color:#e6a23c;font-weight:600;font-size:16px;">{{ totalCost }} 元</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="生产日期">
              <el-date-picker v-model="form.production_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有效期">
              <el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="供应商">
          <el-input v-model="form.supplier" placeholder="如：本地饲料厂" />
        </el-form-item>
        <el-form-item label="进货日期" prop="purchase_date">
          <el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审核弹窗 -->
    <el-dialog v-model="auditDialogVisible" :title="`审核 - ${auditAction}`" width="420px">
      <el-form :model="auditForm" label-width="80px">
        <el-form-item label="备注">
          <el-input v-model="auditForm.remark" type="textarea" :rows="3" placeholder="审核备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button :type="auditAction === '通过' ? 'success' : 'danger'" :loading="auditSaving" @click="confirmAudit">确认{{ auditAction }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  getPurchaseListApi, addPurchaseApi, updatePurchaseApi,
  deletePurchaseApi, auditPurchaseApi, type MaterialPurchase,
} from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'
import { MATERIAL_TYPE_OPTIONS, MATERIAL_UNIT_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canAudit = computed(() => authStore.userType !== 3)

const list = ref<MaterialPurchase[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dateRange = ref<string[]>([])
const query = reactive({
  material_type: '', material_name: '',
  purchase_date_start: '', purchase_date_end: '',
  audit_status: '',
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  material_type: '饲料',
  material_name: '',
  batch_no: '',
  quantity: undefined as number | undefined,
  unit: 'kg',
  cost_price: undefined as number | undefined,
  production_date: '',
  expiry_date: '',
  supplier: '',
  purchase_date: new Date().toISOString().slice(0, 10),
  remark: '',
})
const totalCost = computed(() => {
  const q = form.quantity || 0
  const p = form.cost_price || 0
  return (q * p).toFixed(2)
})

const formRules: FormRules = {
  material_type: [{ required: true, message: '请选择物资类型', trigger: 'change' }],
  material_name: [{ required: true, message: '请输入物资名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  cost_price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
  purchase_date: [{ required: true, message: '请选择进货日期', trigger: 'change' }],
}

const auditDialogVisible = ref(false)
const auditAction = ref('通过')
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditForm = reactive({ remark: '' })

function typeColor(t: string) {
  return { '饲料': 'success', '疫苗': 'warning', '兽药': 'danger' }[t] || 'info'
}
function auditColor(s: string) {
  return { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }[s] || 'info'
}

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.purchase_date_start = val[0]
    query.purchase_date_end = val[1]
  } else {
    query.purchase_date_start = ''
    query.purchase_date_end = ''
  }
  search()
}

function search() { pageNum.value = 1; loadData() }
function resetSearch() {
  dateRange.value = []
  query.material_type = ''; query.material_name = ''
  query.purchase_date_start = ''; query.purchase_date_end = ''
  query.audit_status = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.material_type) params.material_type = query.material_type
    if (query.material_name) params.material_name = query.material_name
    if (query.purchase_date_start) params.purchase_date_start = query.purchase_date_start
    if (query.purchase_date_end) params.purchase_date_end = query.purchase_date_end
    if (query.audit_status) params.audit_status = query.audit_status
    const res = await getPurchaseListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {} finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    material_type: '饲料', material_name: '', batch_no: '',
    quantity: undefined, unit: 'kg', cost_price: undefined,
    production_date: '', expiry_date: '', supplier: '',
    purchase_date: new Date().toISOString().slice(0, 10), remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: MaterialPurchase) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    material_type: row.material_type,
    material_name: row.material_name,
    batch_no: row.batch_no || '',
    quantity: row.quantity ?? undefined,
    unit: row.unit || 'kg',
    cost_price: row.cost_price ?? undefined,
    production_date: row.production_date || '',
    expiry_date: row.expiry_date || '',
    supplier: row.supplier || '',
    purchase_date: row.purchase_date,
    remark: row.remark || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload: any = { ...form }
    if (payload.production_date === '') delete payload.production_date
    if (payload.expiry_date === '') delete payload.expiry_date
    if (payload.batch_no === '') delete payload.batch_no
    if (payload.supplier === '') delete payload.supplier
    if (isEdit.value) {
      await updatePurchaseApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addPurchaseApi(payload)
      ElMessage.success('提交成功，等待审核')
    }
    dialogVisible.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleDelete(id: number) {
  try {
    await deletePurchaseApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {}
}

function handleAudit(row: MaterialPurchase, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditPurchaseApi(auditRecordId.value, {
      audit_status: auditAction.value, remark: auditForm.remark,
    })
    ElMessage.success(`已${auditAction.value}`)
    auditDialogVisible.value = false
    loadData()
  } catch {} finally { auditSaving.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
