<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">饲喂记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 提交饲喂记录
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="日期范围">
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
        <el-form-item label="圈舍">
          <el-select v-model="query.pen_id" placeholder="全部" clearable filterable style="width: 160px" @change="search">
            <el-option v-for="p in penOptions" :key="p.id" :label="p.pen_code + ' (' + p.pen_type + ')'" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时段">
          <el-select v-model="query.time_period" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="o in FEED_TIME_PERIOD_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
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
        <el-table-column prop="feed_date" label="饲喂日期" width="110" />
        <el-table-column prop="time_period" label="时段" width="70" />
        <el-table-column label="圈舍" width="100">
          <template #default="{ row }">{{ penNameMap[row.pen_id] || row.pen_id }}</template>
        </el-table-column>
        <el-table-column label="饲喂头数" width="90">
          <template #default="{ row }">{{ row.animal_count ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="实际精料(kg)" width="110">
          <template #default="{ row }">{{ row.actual_concentrate ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="实际青贮(kg)" width="110">
          <template #default="{ row }">{{ row.actual_silage ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="实际干草(kg)" width="110">
          <template #default="{ row }">{{ row.actual_hay ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="成本(元)" width="100">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: 600;">{{ row.feed_cost ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="投喂状态" width="90">
          <template #default="{ row }">
            <el-tag :type="feedStatusColor(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="auditStatusColor(row.audit_status)" size="small">{{ row.audit_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑饲喂记录' : '提交饲喂记录'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="饲喂日期" prop="feed_date">
          <el-date-picker v-model="form.feed_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="时段" prop="time_period">
          <el-radio-group v-model="form.time_period">
            <el-radio v-for="o in FEED_TIME_PERIOD_OPTIONS" :key="o.value" :label="o.value">{{ o.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="圈舍" prop="pen_id">
          <el-select v-model="form.pen_id" placeholder="请选择圈舍" filterable style="width: 100%">
            <el-option v-for="p in penOptions" :key="p.id" :label="p.pen_code + ' (' + p.pen_type + ')'" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="饲喂方案">
          <el-select v-model="form.plan_id" placeholder="可选，选了自动带计划重量" clearable filterable style="width: 100%" @change="onPlanChange">
            <el-option v-for="p in planOptions" :key="p.id" :label="p.plan_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">实际投喂（kg）</el-divider>
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">精料</span>
              <el-input-number v-model="form.actual_concentrate" :min="0" :precision="2" :step="1" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">青贮</span>
              <el-input-number v-model="form.actual_silage" :min="0" :precision="2" :step="1" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">干草</span>
              <el-input-number v-model="form.actual_hay" :min="0" :precision="2" :step="1" style="width: 100%" />
            </div>
          </el-col>
        </el-row>
        <el-form-item label="饲喂头数">
          <el-input-number v-model="form.animal_count" :min="0" :max="9999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="投喂状态">
          <el-radio-group v-model="form.status">
            <el-radio label="未投喂">未投喂</el-radio>
            <el-radio label="已投喂">已投喂</el-radio>
            <el-radio label="已跳过">已跳过</el-radio>
          </el-radio-group>
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
  getFeedingRecordListApi, addFeedingRecordApi, updateFeedingRecordApi,
  deleteFeedingRecordApi, auditFeedingRecordApi, type FeedingRecord,
} from '@/api/feeding'
import { getFeedingPlanListApi, type FeedingPlan } from '@/api/feeding'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { useAuthStore } from '@/stores/auth'
import { FEED_TIME_PERIOD_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const { species, speciesZh } = useSpecies()
// 场主才能审核
const canAudit = computed(() => authStore.userType !== 3)

const list = ref<FeedingRecord[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 圈舍下拉选项
const penOptions = ref<PenInfo[]>([])
const penNameMap = computed(() => {
  const m: Record<number, string> = {}
  penOptions.value.forEach(p => { m[p.id] = `${p.pen_code}(${p.pen_type})` })
  return m
})
// 方案下拉选项
const planOptions = ref<FeedingPlan[]>([])

const dateRange = ref<string[]>([])
const query = reactive<{ feed_date_start: string; feed_date_end: string; pen_id: number | undefined; time_period: string; audit_status: string }>({
  feed_date_start: '',
  feed_date_end: '',
  pen_id: undefined,
  time_period: '',
  audit_status: '',
})

// 新增/编辑表单
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  feed_date: new Date().toISOString().slice(0, 10),
  time_period: '早',
  pen_id: undefined as number | undefined,
  plan_id: undefined as number | undefined,
  actual_concentrate: undefined as number | undefined,
  actual_silage: undefined as number | undefined,
  actual_hay: undefined as number | undefined,
  animal_count: undefined as number | undefined,
  status: '未投喂',
  remark: '',
})

const formRules: FormRules = {
  feed_date: [{ required: true, message: '请选择饲喂日期', trigger: 'change' }],
  time_period: [{ required: true, message: '请选择时段', trigger: 'change' }],
  pen_id: [{ required: true, message: '请选择圈舍', trigger: 'change' }],
}

// 审核弹窗
const auditDialogVisible = ref(false)
const auditAction = ref('通过')
const auditSaving = ref(false)
const auditRecordId = ref(0)
const auditForm = reactive({ remark: '' })

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.feed_date_start = val[0]
    query.feed_date_end = val[1]
  } else {
    query.feed_date_start = ''
    query.feed_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.feed_date_start = ''
  query.feed_date_end = ''
  query.pen_id = undefined
  query.time_period = ''
  query.audit_status = ''
  search()
}

function feedStatusColor(s: string) {
  const m: Record<string, string> = { '未投喂': 'info', '已投喂': 'success', '已跳过': 'warning' }
  return m[s] || 'info'
}

function auditStatusColor(s: string) {
  const m: Record<string, string> = { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }
  return m[s] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value, species: speciesZh.value }
    if (query.feed_date_start) params.feed_date_start = query.feed_date_start
    if (query.feed_date_end) params.feed_date_end = query.feed_date_end
    if (query.pen_id) params.pen_id = query.pen_id
    if (query.time_period) params.time_period = query.time_period
    if (query.audit_status) params.audit_status = query.audit_status
    const res = await getFeedingRecordListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadPenOptions() {
  try {
    const res = await getPenListApi({ pageNum: 1, pageSize: 100, species: speciesZh.value })
    penOptions.value = (res.data as any).list || []
  } catch {
    // ignored
  }
}

async function loadPlanOptions() {
  try {
    const res = await getFeedingPlanListApi({ pageNum: 1, pageSize: 100, status: 1, species: species.value })
    planOptions.value = (res.data as any).list || []
  } catch {
    // ignored
  }
}

function onPlanChange(planId: number | undefined) {
  // 选了方案不自动填实际值，只做提示
  if (!planId) return
  const p = planOptions.value.find(x => x.id === planId)
  if (p) {
    ElMessage.info(`方案：${p.plan_name}，单只计划 精${p.concentrate_weight ?? '-'} / 青贮${p.silage_weight ?? '-'} / 干草${p.hay_weight ?? '-'} kg`)
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    feed_date: new Date().toISOString().slice(0, 10),
    time_period: '早',
    pen_id: undefined,
    plan_id: undefined,
    actual_concentrate: undefined,
    actual_silage: undefined,
    actual_hay: undefined,
    animal_count: undefined,
    status: '未投喂',
    remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: FeedingRecord) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    feed_date: row.feed_date,
    time_period: row.time_period,
    pen_id: row.pen_id,
    plan_id: row.plan_id ?? undefined,
    actual_concentrate: row.actual_concentrate ?? undefined,
    actual_silage: row.actual_silage ?? undefined,
    actual_hay: row.actual_hay ?? undefined,
    animal_count: row.animal_count ?? undefined,
    status: row.status,
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
    if (!payload.plan_id) delete payload.plan_id
    if (isEdit.value) {
      await updateFeedingRecordApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addFeedingRecordApi(payload)
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
    await deleteFeedingRecordApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

function handleAudit(row: FeedingRecord, action: string) {
  auditRecordId.value = row.id
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  auditSaving.value = true
  try {
    await auditFeedingRecordApi(auditRecordId.value, {
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
  loadPenOptions()
  loadPlanOptions()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }

.feed-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 18px; }
.feed-field-label { font-size: 13px; color: #606266; padding-left: 2px; }
</style>
