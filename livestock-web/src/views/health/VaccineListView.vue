<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">防疫记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <div>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新增防疫
        </el-button>
        <el-button type="success" @click="handleBatchAdd">
          <el-icon><Files /></el-icon> 批量防疫
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="防疫日期">
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
        <el-form-item label="耳标">
          <el-input v-model="query.ear_tag" placeholder="请输入耳标" clearable style="width: 130px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="疫苗类型">
          <el-select v-model="query.vaccine_type" placeholder="全部" clearable filterable style="width: 160px" @change="search">
            <el-option v-for="v in vaccineTypeOptions" :key="v" :label="v" :value="v" />
          </el-select>
        </el-form-item>
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
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

    <!-- 记录列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="vaccine_date" label="防疫日期" width="110" />
        <el-table-column prop="ear_tag" label="耳标" width="90" />
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="breed" label="品种" width="100" />
        <el-table-column prop="vaccine_type" label="疫苗类型" width="130" />
        <el-table-column prop="vaccine_name" label="疫苗名称" min-width="100" show-overflow-tooltip />
        <el-table-column prop="dosage" label="剂量" width="90" />
        <el-table-column prop="next_vaccine_date" label="下次接种" width="110">
          <template #default="{ row }">{{ row.next_vaccine_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditStatusColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="110" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click.stop="handleEdit(row as VaccineRecord)" v-if="row.audit_status === '待审核'">编辑</el-button>
            <el-button link type="success" size="small" @click.stop="handleAudit(row as VaccineRecord, '通过')" v-if="canAudit && row.audit_status === '待审核'">通过</el-button>
            <el-button link type="danger" size="small" @click.stop="handleAudit(row as VaccineRecord, '驳回')" v-if="canAudit && row.audit_status === '待审核'">驳回</el-button>
            <el-popconfirm title="确定删除该记录？" @confirm="handleDelete(row.id)" v-if="row.audit_status !== '通过'">
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑防疫记录' : '新增防疫记录'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="110px">
        <el-form-item label="防疫日期" prop="vaccine_date">
          <el-date-picker v-model="form.vaccine_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="耳标" prop="ear_tag">
          <el-input v-model="form.ear_tag" placeholder="请输入耳标，如 0101" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="畜种" prop="species">
          <el-select v-model="form.species" placeholder="请选择" style="width: 100%" disabled>
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="疫苗类型" prop="vaccine_type">
          <el-select v-model="form.vaccine_type" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="v in vaccineTypeOptions" :key="v" :label="v" :value="v" />
          </el-select>
        </el-form-item>
        <el-form-item label="疫苗名称">
          <el-input v-model="form.vaccine_name" placeholder="疫苗名称（可选）" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="接种剂量">
          <el-input v-model="form.dosage" placeholder="如 2ml/头" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="下次接种日期">
          <el-date-picker v-model="form.next_vaccine_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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

    <!-- 批量新增弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量防疫（同一疫苗类型）" width="640px">
      <el-alert type="info" :closable="false" show-icon class="mb-16"
        title="批量防疫为同一疫苗类型接种到多个耳标；可按圈舍批量带入，也可手动输入，系统会为每个耳标生成一条防疫记录" />
      <el-form :model="batchForm" :rules="batchRules" ref="batchFormRef" label-width="110px">
        <el-form-item label="防疫日期" prop="vaccine_date">
          <el-date-picker v-model="batchForm.vaccine_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="畜种" prop="species">
          <el-select v-model="batchForm.species" placeholder="请选择" style="width: 100%" disabled>
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="疫苗类型" prop="vaccine_type">
          <el-select v-model="batchForm.vaccine_type" placeholder="请选择" filterable allow-create style="width: 100%">
            <el-option v-for="v in vaccineTypeOptions" :key="v" :label="v" :value="v" />
          </el-select>
        </el-form-item>
        <el-form-item label="疫苗名称">
          <el-input v-model="batchForm.vaccine_name" placeholder="疫苗名称（可选）" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="接种剂量">
          <el-input v-model="batchForm.dosage" placeholder="如 2ml/头" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="下次接种日期">
          <el-date-picker v-model="batchForm.next_vaccine_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>

        <el-divider content-position="left">按圈舍选择</el-divider>
        <el-form-item label="圈舍">
          <el-select
            v-model="selectedPenIds"
            multiple
            filterable
            clearable
            :loading="penLoading"
            no-data-text="当前畜种暂无在栏圈舍"
            placeholder="选择圈舍后自动带入该圈舍全部在栏耳标"
            style="width: 100%"
            @change="handlePenChange"
          >
            <el-option
              v-for="p in penGroups"
              :key="p.pen_id"
              :label="`${p.pen_code}（${p.current_count} 头）`"
              :value="p.pen_id"
            />
          </el-select>
          <div class="pen-tip">可多选圈舍；取消某个圈舍时，只移除由该圈舍自动带入的耳标，手动添加的耳标会保留。</div>
        </el-form-item>
        <el-form-item label="手动添加耳标" prop="ear_tags">
          <el-select
            v-model="batchForm.ear_tags"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            collapse-tags-tooltip
            placeholder="输入耳标后回车添加，可多选"
            style="width: 100%"
            @remove-tag="handleEarTagRemove"
          >
            <el-option v-for="a in animalOptions" :key="a.ear_tag" :label="`${a.ear_tag} (${a.breed})`" :value="a.ear_tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="已选耳标">
          <div class="selected-tags">
            <div class="selected-summary">
              <span>
                已选 <b>{{ batchForm.ear_tags.length }}</b> 头
                <template v-if="batchForm.ear_tags.length">
                  （圈舍带入 {{ penSourcedCount }} 头，手动 {{ manualSourcedCount }} 头）
                </template>
              </span>
              <el-button link type="danger" size="small" :disabled="!batchForm.ear_tags.length" @click="clearSelectedEarTags">
                清空已选
              </el-button>
            </div>
            <div class="tag-wrap">
              <el-tag v-for="tag in batchForm.ear_tags" :key="tag" class="mr-8 tag-item" size="small" closable @close="removeEarTag(tag)">{{ tag }}</el-tag>
              <span v-if="!batchForm.ear_tags.length" class="c-gray">暂未选择</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="batchForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSaving" @click="handleBatchSave">确认批量防疫</el-button>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  getVaccineListApi, addVaccineApi, updateVaccineApi, deleteVaccineApi,
  auditVaccineApi, batchAddVaccineApi, getVaccinePenAnimalsApi,
  type VaccineRecord, type VaccinePenGroup,
} from '@/api/health'
import { getAnimalListApi, type AnimalInfo } from '@/api/animal'
import { queryDictDataByTypeApi } from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import { SPECIES_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const { species, speciesZh } = useSpecies()
// 场主才能审核
const canAudit = computed(() => authStore.userType !== 3)

const list = ref<VaccineRecord[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 字典里的疫苗类型
const vaccineTypeOptions = ref<string[]>([])
// 档案耳标（批量新增可选）
const animalOptions = ref<AnimalInfo[]>([])

const dateRange = ref<string[]>([])
const query = reactive<{ vaccine_date_start: string; vaccine_date_end: string; ear_tag: string; vaccine_type: string; species: string; audit_status: string }>({
  vaccine_date_start: '',
  vaccine_date_end: '',
  ear_tag: '',
  vaccine_type: '',
  species: speciesZh.value,
  audit_status: '',
})

// 新增/编辑表单
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  vaccine_date: dayjs().format('YYYY-MM-DD'),
  ear_tag: '',
  species: speciesZh.value,
  vaccine_type: '',
  vaccine_name: '',
  dosage: '',
  next_vaccine_date: '',
  remark: '',
})

const formRules: FormRules = {
  vaccine_date: [{ required: true, message: '请选择防疫日期', trigger: 'change' }],
  ear_tag: [{ required: true, message: '请输入耳标', trigger: 'blur' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  vaccine_type: [{ required: true, message: '请选择疫苗类型', trigger: 'change' }],
}

// 批量表单
const batchDialogVisible = ref(false)
const batchSaving = ref(false)
const batchFormRef = ref<FormInstance>()
const batchForm = reactive({
  vaccine_date: dayjs().format('YYYY-MM-DD'),
  species: speciesZh.value,
  vaccine_type: '',
  vaccine_name: '',
  dosage: '',
  next_vaccine_date: '',
  ear_tags: [] as string[],
  remark: '',
})

const batchRules: FormRules = {
  vaccine_date: [{ required: true, message: '请选择防疫日期', trigger: 'change' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  vaccine_type: [{ required: true, message: '请选择疫苗类型', trigger: 'change' }],
  ear_tags: [{ required: true, message: '请至少选择一个耳标', trigger: 'change' }],
}

// 批量防疫-按圈舍选择
const penGroups = ref<VaccinePenGroup[]>([])
const penLoading = ref(false)
const selectedPenIds = ref<number[]>([])
// 已生效的圈舍选择（@change 时对比新增/移除）
let appliedPenIds = new Set<number>()
// 耳标来源标记：key=耳标，value=带入该耳标的圈舍ID；无记录表示用户手动添加
const earTagSources = reactive<Record<string, number>>({})

// 已选耳标中由圈舍带入 / 手动添加的数量
const penSourcedCount = computed(() =>
  batchForm.ear_tags.filter(tag => earTagSources[tag] !== undefined).length
)
const manualSourcedCount = computed(() => batchForm.ear_tags.length - penSourcedCount.value)

// 审核弹窗
const auditDialogVisible = ref(false)
const auditAction = ref('通过')
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditForm = reactive({ remark: '' })

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.vaccine_date_start = val[0]
    query.vaccine_date_end = val[1]
  } else {
    query.vaccine_date_start = ''
    query.vaccine_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.vaccine_date_start = ''
  query.vaccine_date_end = ''
  query.ear_tag = ''
  query.vaccine_type = ''
  query.species = speciesZh.value
  query.audit_status = ''
  search()
}

function auditStatusColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }
  return m[s] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.vaccine_date_start) params.vaccine_date_start = query.vaccine_date_start
    if (query.vaccine_date_end) params.vaccine_date_end = query.vaccine_date_end
    if (query.ear_tag) params.ear_tag = query.ear_tag
    if (query.vaccine_type) params.vaccine_type = query.vaccine_type
    if (query.species) params.species = query.species
    if (query.audit_status) params.audit_status = query.audit_status
    const res = await getVaccineListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadVaccineTypeOptions() {
  try {
    const res = await queryDictDataByTypeApi('sys_vaccine_type')
    const items = (res.data as any) || []
    vaccineTypeOptions.value = items.map((x: any) => x.dict_label)
  } catch {
    vaccineTypeOptions.value = ['口蹄疫', '布病', '小反刍兽疫', '猪瘟', '蓝耳病', '伪狂犬', '牛结节性皮肤病']
  }
}

async function loadAnimalOptions() {
  try {
    const res = await getAnimalListApi({ pageNum: 1, pageSize: 100, species: speciesZh.value })
    animalOptions.value = (res.data as any).list || []
  } catch {
    // ignored
  }
}

async function loadPenGroups() {
  penLoading.value = true
  try {
    const res = await getVaccinePenAnimalsApi({ species: speciesZh.value })
    penGroups.value = (res.data as VaccinePenGroup[]) || []
  } catch {
    penGroups.value = []
  } finally {
    penLoading.value = false
  }
}

// 把某个圈舍的全部在栏耳标并入已选；已存在的（含手动添加的）不重复添加、也不改来源
function addTagsFromPen(pen: VaccinePenGroup) {
  for (const animal of pen.animals) {
    if (!batchForm.ear_tags.includes(animal.ear_tag)) {
      batchForm.ear_tags.push(animal.ear_tag)
      earTagSources[animal.ear_tag] = pen.pen_id
    }
  }
}

// 只移除来源为该圈舍的耳标，手动添加的耳标不动
function removeTagsByPen(penId: number) {
  const removing = batchForm.ear_tags.filter(tag => earTagSources[tag] === penId)
  if (!removing.length) return
  const removingSet = new Set(removing)
  batchForm.ear_tags = batchForm.ear_tags.filter(tag => !removingSet.has(tag))
  removing.forEach(tag => { delete earTagSources[tag] })
}

// 圈舍多选变化：新增圈舍自动带入耳标；取消圈舍回退该圈舍带入的耳标
function handlePenChange(ids: number[]) {
  const next = new Set(ids)
  appliedPenIds.forEach(penId => {
    if (!next.has(penId)) removeTagsByPen(penId)
  })
  next.forEach(penId => {
    if (!appliedPenIds.has(penId)) {
      const pen = penGroups.value.find(p => p.pen_id === penId)
      if (pen) addTagsFromPen(pen)
    }
  })
  appliedPenIds = next
  batchFormRef.value?.clearValidate('ear_tags')
}

function removeEarTag(tag: string) {
  batchForm.ear_tags = batchForm.ear_tags.filter(x => x !== tag)
  delete earTagSources[tag]
  batchFormRef.value?.clearValidate('ear_tags')
}

// el-select 的下拉标签移除事件参数类型为 unknown，转成耳标字符串后统一处理
function handleEarTagRemove(tag: unknown) {
  removeEarTag(String(tag))
}

// 清空已选：耳标、圈舍选择和来源标记一起重置，避免界面状态不一致
function clearSelectedEarTags() {
  batchForm.ear_tags = []
  selectedPenIds.value = []
  appliedPenIds = new Set()
  Object.keys(earTagSources).forEach(tag => { delete earTagSources[tag] })
  batchFormRef.value?.clearValidate('ear_tags')
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    vaccine_date: dayjs().format('YYYY-MM-DD'),
    ear_tag: '',
    species: speciesZh.value,
    vaccine_type: '',
    vaccine_name: '',
    dosage: '',
    next_vaccine_date: '',
    remark: '',
  })
  dialogVisible.value = true
}

function handleBatchAdd() {
  Object.assign(batchForm, {
    vaccine_date: dayjs().format('YYYY-MM-DD'),
    species: speciesZh.value,
    vaccine_type: '',
    vaccine_name: '',
    dosage: '',
    next_vaccine_date: '',
    ear_tags: [],
    remark: '',
  })
  // 重置按圈舍选择状态，并按当前畜种重新拉取在栏畜禽
  selectedPenIds.value = []
  appliedPenIds = new Set()
  penGroups.value = []
  Object.keys(earTagSources).forEach(tag => { delete earTagSources[tag] })
  batchDialogVisible.value = true
  loadPenGroups()
}

function handleEdit(row: VaccineRecord) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    vaccine_date: row.vaccine_date,
    ear_tag: row.ear_tag,
    species: row.species,
    vaccine_type: row.vaccine_type,
    vaccine_name: row.vaccine_name || '',
    dosage: row.dosage || '',
    next_vaccine_date: row.next_vaccine_date || '',
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
    if (!payload.vaccine_name) delete payload.vaccine_name
    if (!payload.dosage) delete payload.dosage
    if (!payload.next_vaccine_date) delete payload.next_vaccine_date
    if (!payload.remark) delete payload.remark
    if (isEdit.value) {
      await updateVaccineApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addVaccineApi(payload)
      ElMessage.success('提交成功，等待审核')
    }
    dialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleBatchSave() {
  const valid = await batchFormRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!batchForm.ear_tags.length) {
    ElMessage.warning('请至少选择一个耳标')
    return
  }
  batchSaving.value = true
  try {
    const payload: any = { ...batchForm }
    if (!payload.vaccine_name) delete payload.vaccine_name
    if (!payload.dosage) delete payload.dosage
    if (!payload.next_vaccine_date) delete payload.next_vaccine_date
    if (!payload.remark) delete payload.remark
    const res = await batchAddVaccineApi(payload)
    const total = (res.data as any)?.total || 0
    ElMessage.success(`批量提交成功，共 ${total} 条，等待审核`)
    batchDialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    batchSaving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteVaccineApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

function handleAudit(row: VaccineRecord, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditVaccineApi(auditRecordId.value, {
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

onMounted(() => {
  loadVaccineTypeOptions()
  loadAnimalOptions()
  loadData()
})

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
  loadVaccineTypeOptions()
  loadAnimalOptions()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mr-8 { margin-right: 8px; }
.c-gray { color: #6b8ba4; }
.pen-tip { margin-top: 4px; font-size: 12px; line-height: 1.5; color: #6b8ba4; }
.selected-tags { width: 100%; }
.selected-summary { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.selected-summary b { color: #0e2f47; }
.tag-wrap { display: flex; flex-wrap: wrap; max-height: 128px; overflow-y: auto; }
.tag-item { margin-bottom: 8px; }
</style>
