<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">领用记录</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 提交领用
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
        <el-form-item label="领用日期">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD"
            style="width: 260px" @change="onDateChange" />
        </el-form-item>
        <el-form-item label="关联模块">
          <el-select v-model="query.related_module" placeholder="全部" clearable style="width: 120px" @change="search">
            <el-option v-for="o in CONSUME_MODULE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
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
        <el-table-column prop="consume_date" label="领用日期" width="110" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.material_type)" size="small">{{ row.material_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="物资名称" min-width="140" />
        <el-table-column prop="consumer_name" label="领用人" width="90">
          <template #default="{ row }">{{ row.consumer_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="batch_no" label="批次号" width="120">
          <template #default="{ row }">{{ row.batch_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 600;">-{{ row.quantity }}</span>
            {{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column label="关联模块" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.related_module" type="info" size="small">{{ row.related_module }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="consumeStatusColor(row.status)" size="small">{{ row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click.stop="handleEdit(row as MaterialConsume)" v-if="row.audit_status === '待审核'">编辑</el-button>
            <el-button link type="success" size="small" @click.stop="handleAudit(row as MaterialConsume, '通过')" v-if="canAudit && row.audit_status === '待审核'">通过</el-button>
            <el-button link type="danger" size="small" @click.stop="handleAudit(row as MaterialConsume, '驳回')" v-if="canAudit && row.audit_status === '待审核'">驳回</el-button>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑领用记录' : '提交领用记录'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="库存物资" prop="stock_id" v-if="!isEdit">
          <el-select v-model="form.stock_id" placeholder="请选择库存物资" filterable style="width: 100%"
            @change="onStockChange">
            <el-option
              v-for="s in stockOptions"
              :key="s.id"
              :label="`${s.material_type} / ${s.material_name}（库存：${s.quantity} ${s.unit || ''}）`"
              :value="s.id"
            />
          </el-select>
          <div style="color:#6b8ba4;font-size:12px;">仅显示库存数量 > 0 的物资</div>
        </el-form-item>
        <el-form-item label="物资" v-else>
          <el-input :model-value="`${form.material_type} / ${form.material_name}`" disabled />
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
        <el-form-item label="批次号">
          <el-input v-model="form.batch_no" placeholder="如：YL20260810（可选）" />
        </el-form-item>
        <el-form-item label="领用日期" prop="consume_date">
          <el-date-picker v-model="form.consume_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联模块">
          <el-select v-model="form.related_module" placeholder="请选择" clearable style="width: 100%">
            <el-option v-for="o in CONSUME_MODULE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="如：早班投喂" />
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
import dayjs from 'dayjs'
import { ref, reactive, computed, onMounted } from 'vue'
import {
  getConsumeListApi, addConsumeApi, updateConsumeApi,
  deleteConsumeApi, auditConsumeApi, getStockListApi,
  type MaterialConsume, type MaterialStock,
} from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'
import { usePagedList } from '@/composables/usePagedList'
import {
  MATERIAL_TYPE_OPTIONS, MATERIAL_UNIT_OPTIONS,
  AUDIT_STATUS_MAP, CONSUME_MODULE_OPTIONS,
} from '@/utils/constants'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canAudit = computed(() => authStore.userType !== 3)

const {
  list, loading, pageNum, pageSize, total, query, loadData, search, resetSearch: resetQuery,
} = usePagedList<MaterialConsume, {
  material_type: string; material_name: string
  consume_date_start: string; consume_date_end: string
  audit_status: string; related_module: string
}>({
  fetch: getConsumeListApi,
  query: {
    material_type: '', material_name: '',
    consume_date_start: '', consume_date_end: '',
    audit_status: '', related_module: '',
  },
})

const dateRange = ref<string[]>([])
// 日期范围选择器独立于 query，重置时一并清空
function resetSearch() {
  dateRange.value = []
  resetQuery()
}

const stockOptions = ref<MaterialStock[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  stock_id: undefined as number | undefined,
  material_type: '',
  material_name: '',
  batch_no: '',
  quantity: undefined as number | undefined,
  unit: 'kg',
  consume_date: dayjs().format('YYYY-MM-DD'),
  related_module: '',
  remark: '',
})

const formRules: FormRules = {
  stock_id: [{ required: true, message: '请选择库存物资', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入领用数量', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  consume_date: [{ required: true, message: '请选择领用日期', trigger: 'change' }],
}

const auditDialogVisible = ref(false)
const auditAction = ref('通过')
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditForm = reactive({ remark: '' })

function typeColor(t: string): TagProps['type'] {
  return ({ '饲料': 'success', '疫苗': 'warning', '兽药': 'danger' } as Record<string, TagProps['type']>)[t] || 'info'
}
function auditColor(s: string): TagProps['type'] {
  return ({ '待审核': 'warning', '通过': 'success', '驳回': 'danger' } as Record<string, TagProps['type']>)[s] || 'info'
}
function consumeStatusColor(s: string | null): TagProps['type'] {
  return ({ '成功': 'success', '已撤销': 'info' } as Record<string, TagProps['type']>)[s || ''] || 'info'
}

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.consume_date_start = val[0]
    query.consume_date_end = val[1]
  } else {
    query.consume_date_start = ''
    query.consume_date_end = ''
  }
  search()
}

async function loadStockOptions() {
  try {
    const res = await getStockListApi({ pageSize: 100 })
    const data = res.data as any
    const all: MaterialStock[] = data.list || []
    // 仅展示库存 > 0 的物资
    stockOptions.value = all.filter(s => (s.quantity ?? 0) > 0)
  } catch {}
}

function onStockChange(stockId: number) {
  const s = stockOptions.value.find(x => x.id === stockId)
  if (s) {
    form.material_type = s.material_type
    form.material_name = s.material_name
    form.unit = s.unit || 'kg'
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    stock_id: undefined, material_type: '', material_name: '',
    batch_no: '', quantity: undefined, unit: 'kg',
    consume_date: dayjs().format('YYYY-MM-DD'),
    related_module: '', remark: '',
  })
  loadStockOptions()
  dialogVisible.value = true
}

function handleEdit(row: MaterialConsume) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    stock_id: row.stock_id ?? undefined,
    material_type: row.material_type,
    material_name: row.material_name,
    batch_no: row.batch_no || '',
    quantity: row.quantity ?? undefined,
    unit: row.unit || 'kg',
    consume_date: row.consume_date,
    related_module: row.related_module || '',
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
    if (payload.batch_no === '') delete payload.batch_no
    if (payload.related_module === '') delete payload.related_module
    if (payload.remark === '') delete payload.remark
    if (isEdit.value) {
      // 编辑时不需要 stock_id / material_type / material_name
      delete payload.stock_id
      delete payload.material_type
      delete payload.material_name
      await updateConsumeApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      // 新增只需 stock_id，后端会自动带出 material_type / material_name
      delete payload.material_type
      delete payload.material_name
      await addConsumeApi(payload)
      ElMessage.success('提交成功，等待审核')
    }
    dialogVisible.value = false
    loadData()
  } catch {} finally { saving.value = false }
}

async function handleDelete(id: number) {
  try {
    await deleteConsumeApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {}
}

function handleAudit(row: MaterialConsume, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditConsumeApi(auditRecordId.value, {
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
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
