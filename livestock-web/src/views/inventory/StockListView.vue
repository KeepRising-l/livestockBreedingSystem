<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">物资库存</h2>
      <el-button type="primary" @click="handleAdd" v-if="canEdit">
        <el-icon><Plus /></el-icon> 新增物资
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

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑物资' : '新增物资'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="物资类型" prop="material_type">
          <el-select v-model="form.material_type" placeholder="请选择" style="width: 100%" :disabled="isEdit">
            <el-option v-for="o in MATERIAL_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="物资名称" prop="material_name">
          <el-input v-model="form.material_name" placeholder="如：玉米精料" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" placeholder="如：50kg/袋" />
        </el-form-item>
        <el-form-item label="初始库存" prop="quantity" v-if="!isEdit">
          <el-input-number v-model="form.quantity" :min="0" :precision="2" style="width: 100%" />
          <div style="color:#999;font-size:12px;">首次入库可填0，后续通过进货记录增加</div>
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="form.unit" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="u in MATERIAL_UNIT_OPTIONS" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
          <div style="color:#999;font-size:12px;">元/单位；进货审核通过后按移动加权平均自动更新，用于出栏药品成本核算</div>
        </el-form-item>
        <el-form-item label="预警阈值">
          <el-input-number v-model="form.warning_threshold" :min="0" :precision="2" style="width: 100%" />
          <div style="color:#999;font-size:12px;">库存低于此值时标记为缺货</div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { getStockListApi, addStockApi, updateStockApi, deleteStockApi, type MaterialStock } from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'
import { MATERIAL_TYPE_OPTIONS, MATERIAL_UNIT_OPTIONS, STOCK_STATUS_MAP } from '@/utils/constants'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canEdit = computed(() => authStore.userType !== 3)

const list = ref<MaterialStock[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive<{ material_type: string; material_name: string; status: string; is_shortage: number | undefined }>({
  material_type: '', material_name: '', status: '', is_shortage: undefined,
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)

const form = reactive({
  material_type: '饲料',
  material_name: '',
  specification: '',
  quantity: 0,
  unit: 'kg',
  unit_price: undefined as number | undefined,
  warning_threshold: undefined as number | undefined,
  production_date: '',
  expiry_date: '',
  remark: '',
})

const formRules: FormRules = {
  material_type: [{ required: true, message: '请选择物资类型', trigger: 'change' }],
  material_name: [{ required: true, message: '请输入物资名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入初始库存', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
}

function typeColor(t: string): TagProps['type'] {
  return ({ '饲料': 'success', '疫苗': 'warning', '兽药': 'danger' } as Record<string, TagProps['type']>)[t] || 'info'
}
function statusColor(s: string): TagProps['type'] {
  return ({ '正常': 'success', '即将过期': 'warning', '已过期': 'danger' } as Record<string, TagProps['type']>)[s] || 'info'
}

function search() { pageNum.value = 1; loadData() }
function resetSearch() {
  query.material_type = ''; query.material_name = ''; query.status = ''; query.is_shortage = undefined
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.material_type) params.material_type = query.material_type
    if (query.material_name) params.material_name = query.material_name
    if (query.status) params.status = query.status
    if (query.is_shortage !== undefined) params.is_shortage = query.is_shortage
    const res = await getStockListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {} finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    material_type: '饲料', material_name: '', specification: '',
    quantity: 0, unit: 'kg', unit_price: undefined,
    warning_threshold: undefined,
    production_date: '', expiry_date: '', remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: MaterialStock) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    material_type: row.material_type,
    material_name: row.material_name,
    specification: row.specification || '',
    quantity: 0,
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
    if (payload.production_date === '') delete payload.production_date
    if (payload.expiry_date === '') delete payload.expiry_date
    if (payload.warning_threshold === undefined) delete payload.warning_threshold
    if (payload.specification === '') delete payload.specification
    if (isEdit.value) {
      await updateStockApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addStockApi(payload)
      ElMessage.success('添加成功')
    }
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
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.text-danger { color: #f56c6c; }
</style>
