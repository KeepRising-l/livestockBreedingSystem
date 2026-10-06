<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">物资库存</h2>
      <div>
        <el-button type="primary" @click="openIncrease" v-if="canEdit">
          <el-icon><Plus /></el-icon> 增加库存
        </el-button>
        <el-button type="primary" @click="openApply" v-else>
          <el-icon><Plus /></el-icon> 申请添加
        </el-button>
      </div>
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
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 140px" @change="search">
            <el-option v-for="(label, key) in STOCK_STATUS_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="缺货">
          <el-select v-model="query.is_shortage" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option label="是" :value="1" />
            <el-option label="否" :value="0" />
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
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.material_type)" size="small">{{ row.material_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="物资名称" min-width="140" />
        <el-table-column prop="specification" label="规格" width="120">
          <template #default="{ row }">{{ row.specification || '-' }}</template>
        </el-table-column>
        <el-table-column label="库存数量" width="120">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.is_shortage === 1 }" style="font-weight: 600;">
              {{ row.quantity }} {{ row.unit }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="当前均价" width="100">
          <template #default="{ row }">
            <span v-if="row.unit_price !== null && row.unit_price !== undefined">{{ row.unit_price }} 元/{{ row.unit }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="预警阈值" width="100">
          <template #default="{ row }">{{ row.warning_threshold ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="生产日期" width="110">
          <template #default="{ row }">{{ row.production_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="有效期" width="110">
          <template #default="{ row }">{{ row.expiry_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="缺货" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_shortage === 1" type="danger" size="small">缺</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click.stop="handleEdit(row as MaterialStock)" v-if="canEdit">编辑</el-button>
            <el-popconfirm title="确定删除该物资？库存数量需为0才能删除" @confirm="handleDelete(row.id)" v-if="canEdit">
              <template #reference>
                <el-button link type="danger" size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="text-right mt-16">
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 增加库存（管理端，免审直接入库） -->
    <el-dialog v-model="incDialogVisible" title="增加库存" width="560px">
      <el-form :model="incForm" :rules="incRules" ref="incFormRef" label-width="100px">
        <el-form-item label="物资类型" prop="material_type">
          <el-select v-model="incForm.material_type" placeholder="请选择" style="width: 100%" :disabled="!incIsNew">
            <el-option v-for="o in MATERIAL_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="物资名称" prop="material_name">
          <el-select v-model="incForm.material_name" placeholder="选择已有物资，或输入新名称" filterable allow-create style="width: 100%"
            @change="onIncNameChange">
            <el-option v-for="s in stockOptions" :key="s.id" :label="`${s.material_type} / ${s.material_name}（库存：${s.quantity} ${s.unit || ''}）`" :value="s.material_name" />
          </el-select>
        </el-form-item>
        <el-form-item label="当前库存">
          <el-input :model-value="incCurrentText" disabled />
        </el-form-item>
        <el-form-item label="进货数量" prop="quantity">
          <el-input-number v-model="incForm.quantity" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="进货单价">
          <el-input-number v-model="incForm.cost_price" :min="0.01" :precision="2" style="width: 100%" />
          <div style="color:#6b8ba4;font-size:12px;">元/单位，选填；不填则库存均价保持不变</div>
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="incForm.unit" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="u in MATERIAL_UNIT_OPTIONS" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="进货日期" prop="purchase_date">
          <el-date-picker v-model="incForm.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="批次号">
          <el-input v-model="incForm.batch_no" placeholder="如：YL20260810（可选）" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="incForm.supplier" placeholder="可选" />
        </el-form-item>
        <el-form-item label="生产日期">
          <el-date-picker v-model="incForm.production_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="incForm.expiry_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="incForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="incDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="incSaving" @click="handleIncrease">入库</el-button>
      </template>
    </el-dialog>

    <!-- 申请添加（员工端，提交后需场主审核，通过后同步库存） -->
    <el-dialog v-model="applyDialogVisible" title="申请添加物资" width="560px">
      <el-alert type="info" :closable="false" class="mb-16"
        title="提交后需场主审核通过，才会同步到物资库存；新物资会在审核通过后自动建档。" />
      <el-form :model="applyForm" :rules="applyRules" ref="applyFormRef" label-width="100px">
        <el-form-item label="物资类型" prop="material_type">
          <el-select v-model="applyForm.material_type" placeholder="请选择" style="width: 100%" :disabled="!applyIsNew">
            <el-option v-for="o in MATERIAL_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="物资名称" prop="material_name">
          <el-select v-model="applyForm.material_name" placeholder="选择已有物资，或输入新名称" filterable allow-create style="width: 100%"
            @change="onApplyNameChange">
            <el-option v-for="s in stockOptions" :key="s.id" :label="`${s.material_type} / ${s.material_name}（库存：${s.quantity} ${s.unit || ''}）`" :value="s.material_name" />
          </el-select>
        </el-form-item>
        <el-form-item label="当前库存">
          <el-input :model-value="applyCurrentText" disabled />
        </el-form-item>
        <el-form-item label="进货数量" prop="quantity">
          <el-input-number v-model="applyForm.quantity" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="进货单价" prop="cost_price">
          <el-input-number v-model="applyForm.cost_price" :min="0.01" :precision="2" style="width: 100%" />
          <div style="color:#6b8ba4;font-size:12px;">元/单位，必填；审核通过后按移动加权平均更新库存均价</div>
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="applyForm.unit" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="u in MATERIAL_UNIT_OPTIONS" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="进货日期" prop="purchase_date">
          <el-date-picker v-model="applyForm.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="批次号">
          <el-input v-model="applyForm.batch_no" placeholder="如：YL20260810（可选）" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="applyForm.supplier" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="applyForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applySaving" @click="handleApply">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- 编辑物资基本信息（数量不在此处改，走进货/领用） -->
    <el-dialog v-model="dialogVisible" title="编辑物资" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="物资类型">
          <el-input :model-value="form.material_type" disabled />
        </el-form-item>
        <el-form-item label="物资名称">
          <el-input :model-value="form.material_name" disabled />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" placeholder="如：50kg/袋" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="form.unit" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="u in MATERIAL_UNIT_OPTIONS" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
          <div style="color:#6b8ba4;font-size:12px;">元/单位；进货审核通过后按移动加权平均自动更新，用于出栏药品成本核算</div>
        </el-form-item>
        <el-form-item label="预警阈值">
          <el-input-number v-model="form.warning_threshold" :min="0" :precision="2" style="width: 100%" />
          <div style="color:#6b8ba4;font-size:12px;">库存低于此值时标记为缺货</div>
        </el-form-item>
        <el-form-item label="生产日期">
          <el-date-picker v-model="form.production_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { ref, reactive, computed, onMounted } from 'vue'
import {
  getStockListApi, updateStockApi, deleteStockApi, increaseStockApi, addPurchaseApi,
  type MaterialStock,
} from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'
import { usePagedList } from '@/composables/usePagedList'
import { MATERIAL_TYPE_OPTIONS, MATERIAL_UNIT_OPTIONS, STOCK_STATUS_MAP } from '@/utils/constants'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canEdit = computed(() => authStore.userType !== 3)

const {
  list, loading, pageNum, pageSize, total, query, loadData, search, resetSearch,
} = usePagedList<MaterialStock, {
  material_type: string; material_name: string; status: string; is_shortage: number | undefined
}>({
  fetch: getStockListApi,
  query: { material_type: '', material_name: '', status: '', is_shortage: undefined },
})

// 下拉选项：已有物资（供"增加库存 / 申请添加"选择）
const stockOptions = ref<MaterialStock[]>([])

async function loadStockOptions() {
  try {
    const res = await getStockListApi({ pageNum: 1, pageSize: 100 })
    stockOptions.value = (res.data as any).list || []
  } catch {}
}

function findStock(type: string, name: string) {
  return stockOptions.value.find(s => s.material_type === type && s.material_name === name)
}

// 名称反查（不同物资类型可能有同名物资，选中后自动带出类型/单位）
function findStockByName(name: string) {
  return stockOptions.value.find(s => s.material_name === name)
}

function typeColor(t: string): TagProps['type'] {
  return ({ '饲料': 'success', '疫苗': 'warning', '兽药': 'danger' } as Record<string, TagProps['type']>)[t] || 'info'
}
function statusColor(s: string): TagProps['type'] {
  return ({ '正常': 'success', '即将过期': 'warning', '已过期': 'danger' } as Record<string, TagProps['type']>)[s] || 'info'
}

// ============ 增加库存（管理端） ============

const incDialogVisible = ref(false)
const incSaving = ref(false)
const incFormRef = ref<FormInstance>()
const incForm = reactive({
  material_type: '饲料',
  material_name: '',
  quantity: undefined as number | undefined,
  cost_price: undefined as number | undefined,
  unit: 'kg',
  purchase_date: dayjs().format('YYYY-MM-DD'),
  batch_no: '', supplier: '',
  production_date: '', expiry_date: '', remark: '',
})

const incCurrent = computed(() => findStockByName(incForm.material_name))
const incIsNew = computed(() => !!incForm.material_name && !incCurrent.value)
const incCurrentText = computed(() =>
  incCurrent.value
    ? `${incCurrent.value.quantity} ${incCurrent.value.unit || ''}`
    : '0（新物资，入库后自动建档）'
)

const incRules: FormRules = {
  material_type: [{ required: true, message: '请选择物资类型', trigger: 'change' }],
  material_name: [{ required: true, message: '请选择或输入物资名称', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入进货数量', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择进货日期', trigger: 'change' }],
}

function onIncNameChange(name: string) {
  const s = findStockByName(name)
  if (s) {
    incForm.material_type = s.material_type
    incForm.unit = s.unit || 'kg'
  }
}

function openIncrease() {
  Object.assign(incForm, {
    material_type: '饲料', material_name: '',
    quantity: undefined, cost_price: undefined, unit: 'kg',
    purchase_date: dayjs().format('YYYY-MM-DD'),
    batch_no: '', supplier: '', production_date: '', expiry_date: '', remark: '',
  })
  loadStockOptions()
  incDialogVisible.value = true
}

async function handleIncrease() {
  const valid = await incFormRef.value?.validate().catch(() => false)
  if (!valid) return
  incSaving.value = true
  try {
    const payload: any = {
      material_type: incForm.material_type,
      material_name: incForm.material_name,
      quantity: incForm.quantity,
      unit: incForm.unit,
      purchase_date: incForm.purchase_date,
    }
    if (incForm.cost_price !== undefined) payload.cost_price = incForm.cost_price
    if (incForm.batch_no) payload.batch_no = incForm.batch_no
    if (incForm.supplier) payload.supplier = incForm.supplier
    if (incForm.production_date) payload.production_date = incForm.production_date
    if (incForm.expiry_date) payload.expiry_date = incForm.expiry_date
    if (incForm.remark) payload.remark = incForm.remark
    await increaseStockApi(payload)
    ElMessage.success('入库成功')
    incDialogVisible.value = false
    loadData()
  } catch {} finally { incSaving.value = false }
}

// ============ 申请添加（员工端） ============

const applyDialogVisible = ref(false)
const applySaving = ref(false)
const applyFormRef = ref<FormInstance>()
const applyForm = reactive({
  material_type: '饲料',
  material_name: '',
  quantity: undefined as number | undefined,
  cost_price: undefined as number | undefined,
  unit: 'kg',
  purchase_date: dayjs().format('YYYY-MM-DD'),
  batch_no: '', supplier: '', remark: '',
})

const applyCurrent = computed(() => findStockByName(applyForm.material_name))
const applyIsNew = computed(() => !!applyForm.material_name && !applyCurrent.value)
const applyCurrentText = computed(() =>
  applyCurrent.value
    ? `${applyCurrent.value.quantity} ${applyCurrent.value.unit || ''}`
    : '0（新物资，审核通过后自动建档）'
)

const applyRules: FormRules = {
  material_type: [{ required: true, message: '请选择物资类型', trigger: 'change' }],
  material_name: [{ required: true, message: '请选择或输入物资名称', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入进货数量', trigger: 'blur' }],
  cost_price: [{ required: true, message: '请输入进货单价', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择进货日期', trigger: 'change' }],
}

function onApplyNameChange(name: string) {
  const s = findStockByName(name)
  if (s) {
    applyForm.material_type = s.material_type
    applyForm.unit = s.unit || 'kg'
  }
}

function openApply() {
  Object.assign(applyForm, {
    material_type: '饲料', material_name: '',
    quantity: undefined, cost_price: undefined, unit: 'kg',
    purchase_date: dayjs().format('YYYY-MM-DD'),
    batch_no: '', supplier: '', remark: '',
  })
  loadStockOptions()
  applyDialogVisible.value = true
}

async function handleApply() {
  const valid = await applyFormRef.value?.validate().catch(() => false)
  if (!valid) return
  applySaving.value = true
  try {
    const payload: any = {
      material_type: applyForm.material_type,
      material_name: applyForm.material_name,
      quantity: applyForm.quantity,
      unit: applyForm.unit,
      cost_price: applyForm.cost_price,
      purchase_date: applyForm.purchase_date,
    }
    if (applyForm.batch_no) payload.batch_no = applyForm.batch_no
    if (applyForm.supplier) payload.supplier = applyForm.supplier
    if (applyForm.remark) payload.remark = applyForm.remark
    await addPurchaseApi(payload)
    ElMessage.success('提交成功，等待审核')
    applyDialogVisible.value = false
  } catch {} finally { applySaving.value = false }
}

// ============ 编辑 / 删除 ============

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)

const form = reactive({
  material_type: '',
  material_name: '',
  specification: '',
  unit: 'kg',
  unit_price: undefined as number | undefined,
  warning_threshold: undefined as number | undefined,
  production_date: '',
  expiry_date: '',
  remark: '',
})

const formRules: FormRules = {
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
}

function handleEdit(row: MaterialStock) {
  editId.value = row.id
  Object.assign(form, {
    material_type: row.material_type,
    material_name: row.material_name,
    specification: row.specification || '',
    unit: row.unit || 'kg',
    unit_price: row.unit_price ?? undefined,
    warning_threshold: row.warning_threshold ?? undefined,
    production_date: row.production_date || '',
    expiry_date: row.expiry_date || '',
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
    delete payload.material_type
    delete payload.material_name
    if (payload.production_date === '') delete payload.production_date
    if (payload.expiry_date === '') delete payload.expiry_date
    if (payload.warning_threshold === undefined) delete payload.warning_threshold
    if (payload.specification === '') delete payload.specification
    await updateStockApi(editId.value, payload)
    ElMessage.success('修改成功')
    dialogVisible.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleDelete(id: number) {
  try {
    await deleteStockApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.text-danger { color: #f56c6c; }
</style>
