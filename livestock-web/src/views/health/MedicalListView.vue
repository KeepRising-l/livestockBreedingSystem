<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">诊疗记录</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增诊疗
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="诊疗日期">
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
        <el-form-item label="病情类型">
          <el-input v-model="query.disease_type" placeholder="如感冒/腹泻" clearable style="width: 130px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="诊疗状态">
          <el-select v-model="query.treatment_status" placeholder="全部" clearable style="width: 110px" @change="search">
            <el-option v-for="(label, key) in TREATMENT_STATUS_MAP" :key="key" :label="label" :value="key" />
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
        <el-table-column prop="medical_date" label="诊疗日期" width="110" />
        <el-table-column prop="ear_tag" label="耳标" width="90" />
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="breed" label="品种" width="100" />
        <el-table-column prop="disease_type" label="病情类型" width="110" />
        <el-table-column prop="symptom" label="主要症状" min-width="130" show-overflow-tooltip />
        <el-table-column prop="medicine" label="诊疗用药" min-width="130" show-overflow-tooltip />
        <el-table-column label="诊疗状态" width="100">
          <template #default="{ row }">
            <el-tag :type="treatmentStatusColor(row.treatment_status)" size="small">{{ row.treatment_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditStatusColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑诊疗记录' : '新增诊疗记录'" width="620px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="诊疗日期" prop="medical_date">
              <el-date-picker v-model="form.medical_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发病日期">
              <el-date-picker v-model="form.onset_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="耳标" prop="ear_tag">
              <el-input v-model="form.ear_tag" placeholder="请输入耳标，如 0101" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="畜种" prop="species">
              <el-select v-model="form.species" placeholder="请选择" style="width: 100%">
                <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="病情类型" prop="disease_type">
          <el-input v-model="form.disease_type" placeholder="如 感冒/腹泻/肺炎/外伤" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="主要症状">
          <el-input v-model="form.symptom" type="textarea" :rows="2" placeholder="如 精神萎靡、食欲下降、发热" />
        </el-form-item>
        <el-form-item label="诊疗用药" prop="medicine">
          <el-input v-model="form.medicine" type="textarea" :rows="2" placeholder="如 青霉素钠 160万IU、板蓝根注射液" />
        </el-form-item>
        <el-form-item label="治疗方案">
          <el-input v-model="form.treatment_plan" type="textarea" :rows="2" placeholder="如 隔离观察，每日注射青霉素 2 次，连用 3 天" />
        </el-form-item>
        <el-form-item label="诊疗状态" prop="treatment_status">
          <el-radio-group v-model="form.treatment_status">
            <el-radio v-for="(label, key) in TREATMENT_STATUS_MAP" :key="key" :label="key">{{ label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="康复日期">
          <el-date-picker v-model="form.cure_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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
  getMedicalListApi, addMedicalApi, updateMedicalApi, deleteMedicalApi,
  auditMedicalApi, type MedicalRecord,
} from '@/api/health'
import { useAuthStore } from '@/stores/auth'
import { SPECIES_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
// 场主才能审核
const canAudit = computed(() => authStore.userType !== 3)

const TREATMENT_STATUS_MAP: Record<string, string> = {
  '治疗中': '治疗中',
  '已康复': '已康复',
  '死亡': '死亡',
}

const list = ref<MedicalRecord[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dateRange = ref<string[]>([])
const query = reactive<{ medical_date_start: string; medical_date_end: string; ear_tag: string; disease_type: string; species: string; treatment_status: string; audit_status: string }>({
  medical_date_start: '',
  medical_date_end: '',
  ear_tag: '',
  disease_type: '',
  species: '',
  treatment_status: '',
  audit_status: '',
})

// 新增/编辑表单
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  medical_date: new Date().toISOString().slice(0, 10),
  onset_date: '',
  ear_tag: '',
  species: '',
  disease_type: '',
  symptom: '',
  medicine: '',
  treatment_plan: '',
  treatment_status: '治疗中',
  cure_date: '',
  remark: '',
})

const formRules: FormRules = {
  medical_date: [{ required: true, message: '请选择诊疗日期', trigger: 'change' }],
  ear_tag: [{ required: true, message: '请输入耳标', trigger: 'blur' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  disease_type: [{ required: true, message: '请输入病情类型', trigger: 'blur' }],
  medicine: [{ required: true, message: '请输入诊疗用药', trigger: 'blur' }],
  treatment_status: [{ required: true, message: '请选择诊疗状态', trigger: 'change' }],
}

// 审核弹窗
const auditDialogVisible = ref(false)
const auditAction = ref('通过')
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditForm = reactive({ remark: '' })

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.medical_date_start = val[0]
    query.medical_date_end = val[1]
  } else {
    query.medical_date_start = ''
    query.medical_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.medical_date_start = ''
  query.medical_date_end = ''
  query.ear_tag = ''
  query.disease_type = ''
  query.species = ''
  query.treatment_status = ''
  query.audit_status = ''
  search()
}

function treatmentStatusColor(s: string) {
  const m: Record<string, string> = { '治疗中': 'warning', '已康复': 'success', '死亡': 'danger' }
  return m[s] || 'info'
}

function auditStatusColor(s: string) {
  const m: Record<string, string> = { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }
  return m[s] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.medical_date_start) params.medical_date_start = query.medical_date_start
    if (query.medical_date_end) params.medical_date_end = query.medical_date_end
    if (query.ear_tag) params.ear_tag = query.ear_tag
    if (query.disease_type) params.disease_type = query.disease_type
    if (query.species) params.species = query.species
    if (query.treatment_status) params.treatment_status = query.treatment_status
    if (query.audit_status) params.audit_status = query.audit_status
    const res = await getMedicalListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    medical_date: new Date().toISOString().slice(0, 10),
    onset_date: '',
    ear_tag: '',
    species: '',
    disease_type: '',
    symptom: '',
    medicine: '',
    treatment_plan: '',
    treatment_status: '治疗中',
    cure_date: '',
    remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: MedicalRecord) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    medical_date: row.medical_date,
    onset_date: row.onset_date || '',
    ear_tag: row.ear_tag,
    species: row.species,
    disease_type: row.disease_type,
    symptom: row.symptom || '',
    medicine: row.medicine,
    treatment_plan: row.treatment_plan || '',
    treatment_status: row.treatment_status,
    cure_date: row.cure_date || '',
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
    if (!payload.onset_date) delete payload.onset_date
    if (!payload.symptom) delete payload.symptom
    if (!payload.treatment_plan) delete payload.treatment_plan
    if (!payload.cure_date) delete payload.cure_date
    if (!payload.remark) delete payload.remark
    if (isEdit.value) {
      await updateMedicalApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addMedicalApi(payload)
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

async function handleDelete(id: number) {
  try {
    await deleteMedicalApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

function handleAudit(row: MedicalRecord, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditMedicalApi(auditRecordId.value, {
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
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
