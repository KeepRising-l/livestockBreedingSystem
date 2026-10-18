<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">配种记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增配种
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="配种日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 260px"
            @change="onDateChange"
          />
        </el-form-item>
        <el-form-item label="母畜耳标">
          <el-input v-model="query.female_tag" placeholder="请输入母畜耳标" clearable style="width: 130px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px" @change="search">
            <el-option v-for="(label, key) in MATING_STATUS_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="query.audit_status" placeholder="全部" clearable style="width: 110px" @change="search">
            <el-option v-for="(label, key) in AUDIT_STATUS_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 记录列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="mating_date" label="配种日期" width="110" />
        <el-table-column prop="female_tag" label="母畜耳标" width="90" />
        <el-table-column prop="male_tag" label="公畜耳标" width="90">
          <template #default="{ row }">{{ row.male_tag || '-' }}</template>
        </el-table-column>
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="mating_type" label="配种方式" width="100" />
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expected_birth_date" label="预产期" width="110">
          <template #default="{ row }">{{ row.expected_birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="剩余天数" width="90">
          <template #default="{ row }">
            <span v-if="row.remain_days === null || row.remain_days === undefined">-</span>
            <el-tag v-else-if="row.remain_days >= 0" size="small">{{ row.remain_days }}天</el-tag>
            <el-tag v-else type="danger" size="small">已到期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pregnancy_check_result" label="孕检结果" width="90">
          <template #default="{ row }">{{ row.pregnancy_check_result || '-' }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="handleDetail(row as MatingRecord)">详情</el-button>
            <template v-if="canAudit && row.audit_status === '待审核'">
              <el-button link type="success" size="small" @click.stop="handleAudit(row as MatingRecord, '通过')">通过</el-button>
              <el-button link type="danger" size="small" @click.stop="handleAudit(row as MatingRecord, '驳回')">驳回</el-button>
            </template>
            <el-button link type="success" size="small" @click.stop="handleCheck(row as MatingRecord)" v-if="row.audit_status === '通过' && !row.pregnancy_check_result && row.status !== '配种失败'">孕检</el-button>
            <el-button link type="primary" size="small" @click.stop="handleEdit(row as MatingRecord)" v-if="!row.pregnancy_check_result">编辑</el-button>
            <el-popconfirm title="确定删除该配种记录？" @confirm="handleDelete(row.id)" v-if="row.audit_status !== '通过'">
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

    <!-- 审核弹窗 -->
    <el-dialog v-model="auditDialogVisible" :title="`审核配种记录 - ${auditAction}`" width="420px">
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

    <!-- 详情弹窗（所有行可见，只读） -->
    <el-dialog v-model="detailDialogVisible" title="配种记录详情" width="720px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="配种日期">{{ detailRow.mating_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="母畜耳标">{{ detailRow.female_tag || '-' }}</el-descriptions-item>
        <el-descriptions-item label="公畜耳标">{{ detailRow.male_tag || '-' }}</el-descriptions-item>
        <el-descriptions-item label="畜种">{{ detailRow.species || '-' }}</el-descriptions-item>
        <el-descriptions-item label="配种方式">{{ detailRow.mating_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="精液来源">{{ detailRow.semen_source || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">
          <el-tag :type="auditColor(detailRow.audit_status || '')" size="small">{{ detailRow.audit_status || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusColor(detailRow.status || '')" size="small">{{ detailRow.status || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="预产期">{{ detailRow.expected_birth_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="剩余天数">{{ remainDaysText(detailRow.remain_days) }}</el-descriptions-item>
        <el-descriptions-item label="孕检日期">{{ detailRow.pregnancy_check_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="孕检结果">{{ detailRow.pregnancy_check_result || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailRow.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ formatDateTime(detailRow.create_time) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑配种记录' : '新增配种记录'" width="540px">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="mb-16"
        :title="isEdit
          ? '保存后记录将退回「待审核」，需场主重新审核通过才生效（母畜妊娠状态一并回退）'
          : '提交后进入「待审核」，场主审核通过才会把母畜登记为妊娠'"
      />
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="母畜耳标" prop="female_tag">
          <el-select v-model="form.female_tag" filterable placeholder="选择可繁育母畜" style="width: 100%" :disabled="isEdit">
            <el-option v-for="a in femaleOptions" :key="a.ear_tag" :label="`${a.ear_tag} (${a.species}·${a.breed}·${a.growth_stage}${a.physio_status ? '·' + a.physio_status : ''})`" :value="a.ear_tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="公畜耳标">
          <el-select v-model="form.male_tag" filterable clearable placeholder="选择公畜（可选）" style="width: 100%">
            <el-option v-for="a in maleOptions" :key="a.ear_tag" :label="`${a.ear_tag} (${a.species}·${a.breed})`" :value="a.ear_tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="畜种" prop="species">
          <el-select v-model="form.species" placeholder="请选择" style="width: 100%" disabled>
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="配种日期" prop="mating_date">
          <el-date-picker v-model="form.mating_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="配种方式" prop="mating_type">
          <el-select v-model="form.mating_type" placeholder="请选择" style="width: 100%">
            <el-option v-for="t in MATING_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="精液来源" v-if="form.mating_type === '人工受精'">
          <el-input v-model="form.semen_source" placeholder="精液来源（可选）" clearable style="width: 100%" />
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

    <!-- 孕检弹窗 -->
    <el-dialog v-model="checkDialogVisible" title="孕检登记" width="440px">
      <el-form :model="checkForm" :rules="checkRules" ref="checkFormRef" label-width="90px">
        <el-form-item label="孕检日期" prop="pregnancy_check_date">
          <el-date-picker v-model="checkForm.pregnancy_check_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="孕检结果" prop="pregnancy_check_result">
          <el-radio-group v-model="checkForm.pregnancy_check_result">
            <el-radio v-for="r in PREGNANCY_RESULT_OPTIONS" :key="r.value" :value="r.value">{{ r.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="checkForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="checkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="checkSaving" @click="confirmCheck">确认孕检</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  getMatingListApi, addMatingApi, updateMatingApi, deleteMatingApi, auditMatingApi,
  pregnancyCheckApi, getBreedFemalesApi, getBreedMalesApi,
  type MatingRecord, type BreedAnimal,
} from '@/api/breeding'
import { useAuthStore } from '@/stores/auth'
import { SPECIES_OPTIONS, MATING_TYPE_OPTIONS, MATING_STATUS_MAP, PREGNANCY_RESULT_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { formatDateTime } from '@/utils/format'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
// 场主/超管才能审核（与饲喂记录一致）
const canAudit = computed(() => authStore.userType !== 3)

const { species, speciesZh } = useSpecies()

const list = ref<MatingRecord[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const femaleOptions = ref<BreedAnimal[]>([])
const maleOptions = ref<BreedAnimal[]>([])

const dateRange = ref<string[]>([])
const query = reactive<{ female_tag: string; species: string; status: string; audit_status: string; mating_date_start: string; mating_date_end: string }>({
  female_tag: '',
  species: speciesZh.value,
  status: '',
  audit_status: '',
  mating_date_start: '',
  mating_date_end: '',
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  female_tag: '',
  male_tag: '',
  species: speciesZh.value,
  mating_date: dayjs().format('YYYY-MM-DD'),
  mating_type: '本交',
  semen_source: '',
  remark: '',
})

const formRules: FormRules = {
  female_tag: [{ required: true, message: '请选择母畜', trigger: 'change' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  mating_date: [{ required: true, message: '请选择配种日期', trigger: 'change' }],
  mating_type: [{ required: true, message: '请选择配种方式', trigger: 'change' }],
}

const checkDialogVisible = ref(false)
const checkSaving = ref(false)
const checkFormRef = ref<FormInstance>()
const checkMatingId = ref(0)
const checkForm = reactive({ pregnancy_check_date: dayjs().format('YYYY-MM-DD'), pregnancy_check_result: '阳性', remark: '' })
const checkRules: FormRules = {
  pregnancy_check_date: [{ required: true, message: '请选择孕检日期', trigger: 'change' }],
  pregnancy_check_result: [{ required: true, message: '请选择孕检结果', trigger: 'change' }],
}

function statusColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '待孕检': 'warning', '成功怀孕': 'success', '配种失败': 'danger' }
  return m[s] || 'info'
}

function auditColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }
  return m[s] || 'info'
}

/** 剩余天数展示：为空 -，负数显示「已到期」 */
function remainDaysText(v: number | null | undefined): string {
  if (v === null || v === undefined) return '-'
  return v >= 0 ? `${v}天` : '已到期'
}

// ========== 审核 ==========
const auditDialogVisible = ref(false)
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditAction = ref('通过')
const auditForm = reactive({ remark: '' })

function handleAudit(row: MatingRecord, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditMatingApi(auditRecordId.value, {
      audit_status: auditAction.value,
      remark: auditForm.remark,
    })
    ElMessage.success(`已${auditAction.value}`)
    auditDialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    auditSaving.value = false
  }
}

// ========== 详情（只读，所有行可见） ==========
const detailDialogVisible = ref(false)
const detailRow = ref<Partial<MatingRecord>>({})

function handleDetail(row: MatingRecord) {
  detailRow.value = row
  detailDialogVisible.value = true
}

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.mating_date_start = val[0]
    query.mating_date_end = val[1]
  } else {
    query.mating_date_start = ''
    query.mating_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.female_tag = ''
  query.species = speciesZh.value
  query.status = ''
  query.audit_status = ''
  query.mating_date_start = ''
  query.mating_date_end = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.female_tag) params.female_tag = query.female_tag
    if (query.species) params.species = query.species
    if (query.status) params.status = query.status
    if (query.audit_status) params.audit_status = query.audit_status
    if (query.mating_date_start) params.mating_date_start = query.mating_date_start
    if (query.mating_date_end) params.mating_date_end = query.mating_date_end
    const res = await getMatingListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [f, m] = await Promise.all([
      getBreedFemalesApi({ pageSize: 100, species: speciesZh.value }),
      getBreedMalesApi({ pageSize: 100, species: speciesZh.value }),
    ])
    femaleOptions.value = (f.data as any)?.list || []
    maleOptions.value = (m.data as any)?.list || []
  } catch {
    // handled by interceptor
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    female_tag: '',
    male_tag: '',
    species: speciesZh.value,
    mating_date: dayjs().format('YYYY-MM-DD'),
    mating_type: '本交',
    semen_source: '',
    remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: MatingRecord) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    female_tag: row.female_tag,
    male_tag: row.male_tag || '',
    species: row.species,
    mating_date: row.mating_date,
    mating_type: row.mating_type,
    semen_source: row.semen_source || '',
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
    if (!payload.male_tag) delete payload.male_tag
    if (!payload.semen_source) delete payload.semen_source
    if (!payload.remark) delete payload.remark
    if (isEdit.value) {
      await updateMatingApi(editId.value, payload)
      // 已通过的记录改动会退回待审核（后端同步回退母畜妊娠标记）
      ElMessage.success('已保存，需场主重新审核通过才生效')
    } else {
      await addMatingApi(payload)
      ElMessage.success('已提交，等待场主审核')
    }
    dialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteMatingApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

function handleCheck(row: MatingRecord) {
  checkMatingId.value = row.id
  Object.assign(checkForm, { pregnancy_check_date: dayjs().format('YYYY-MM-DD'), pregnancy_check_result: '阳性', remark: '' })
  checkDialogVisible.value = true
}

async function confirmCheck() {
  const valid = await checkFormRef.value?.validate().catch(() => false)
  if (!valid) return
  checkSaving.value = true
  try {
    await pregnancyCheckApi(checkMatingId.value, { ...checkForm })
    ElMessage.success('孕检已登记')
    checkDialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    checkSaving.value = false
  }
}

onMounted(() => {
  loadOptions()
  loadData()
})

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
  loadOptions()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
