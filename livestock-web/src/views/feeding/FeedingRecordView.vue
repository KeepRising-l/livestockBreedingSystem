<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">饲喂记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleBatchAdd">
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
            <el-button link type="warning" size="small" @click.stop="handleEdit(row as FeedingRecord)">编辑</el-button>
            <el-button link type="success" size="small" @click.stop="handleAudit(row as FeedingRecord, '通过')" v-if="canAudit && row.audit_status === '待审核'">通过</el-button>
            <el-button link type="danger" size="small" @click.stop="handleAudit(row as FeedingRecord, '驳回')" v-if="canAudit && row.audit_status === '待审核'">驳回</el-button>
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
      <el-alert
        v-if="isEdit && editWasAudited"
        type="warning"
        :closable="false"
        show-icon
        title="该记录已审核过，保存后将重置为「待审核」，需重新审核"
        class="mb-16"
      />
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="饲喂日期" prop="feed_date">
          <el-date-picker v-model="form.feed_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="时段" prop="time_period">
          <el-radio-group v-model="form.time_period" :disabled="isEdit">
            <el-radio v-for="o in FEED_TIME_PERIOD_OPTIONS" :key="o.value" :label="o.value">{{ o.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="圈舍" prop="pen_id">
          <el-select v-model="form.pen_id" placeholder="请选择圈舍" filterable style="width: 100%" :disabled="isEdit">
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

    <!-- 批量提交弹窗：可多选圈舍，一次按圈舍生成多条饲喂记录 -->
    <el-dialog v-model="batchVisible" title="提交饲喂记录" width="1000px" top="6vh">
      <el-form :model="batchForm" label-width="90px" size="default">
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="饲喂日期" required>
              <el-date-picker v-model="batchForm.feed_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时段" required>
              <el-radio-group v-model="batchForm.time_period">
                <el-radio v-for="o in FEED_TIME_PERIOD_OPTIONS" :key="o.value" :label="o.value">{{ o.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="投喂状态">
              <el-radio-group v-model="batchForm.status">
                <el-radio label="未投喂">未投喂</el-radio>
                <el-radio label="已投喂">已投喂</el-radio>
                <el-radio label="已跳过">已跳过</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="16">
            <el-form-item label="饲喂方案">
              <el-select
                v-model="batchForm.plan_id" placeholder="选择方案后自动带出投喂重量" clearable filterable
                style="width: 100%" @change="applyPlanToRows"
              >
                <el-option
                  v-for="p in planOptions" :key="p.id"
                  :label="`${p.plan_name}（单只 精${p.concentrate_weight ?? '-'}/青贮${p.silage_weight ?? '-'}/干草${p.hay_weight ?? '-'} kg）`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="备注">
              <el-input v-model="batchForm.remark" placeholder="选填" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="选择圈舍" required>
          <el-select
            v-model="batchPenIds" multiple filterable collapse-tags collapse-tags-tooltip
            placeholder="可多选圈舍，选中后自动生成对应饲喂行" style="width: 100%"
            @change="syncBatchRows"
          >
            <el-option
              v-for="p in penOptions" :key="p.id"
              :label="`${p.pen_code}（${p.pen_type}）存栏 ${p.current_count}/${p.capacity}`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <el-alert
        type="info" :closable="false" class="mb-8"
        title="投喂头数默认取该圈舍实际存栏；重量为整圈合计，默认 = 方案单只重量 × 存栏头数，仍可用加减调整。同一天同一时段已有记录的圈舍会自动跳过。"
      />

      <el-table :data="batchRows" size="small" border max-height="330" empty-text="请先选择圈舍">
        <el-table-column label="圈舍" width="110">
          <template #default="{ row }">{{ row.pen_code }}（{{ row.pen_type }}）</template>
        </el-table-column>
        <el-table-column label="饲喂头数" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.animal_count" :min="0" :max="9999" size="small"
              controls-position="right" style="width: 100%" @change="onRowCountChange(row as BatchRow)"
            />
          </template>
        </el-table-column>
        <el-table-column label="精料(kg)" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.actual_concentrate" :min="0" :precision="2" :step="1" size="small"
              controls-position="right" style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="青贮(kg)" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.actual_silage" :min="0" :precision="2" :step="1" size="small"
              controls-position="right" style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="干草(kg)" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.actual_hay" :min="0" :precision="2" :step="1" size="small"
              controls-position="right" style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="默认值来源" min-width="160">
          <template #default>
            <span class="plan-hint">{{ planHint }}</span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <span class="footer-left">已选 {{ batchRows.length }} 个圈舍，将生成 {{ batchRows.length }} 条记录</span>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSaving" @click="handleBatchSave">批量提交</el-button>
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
  getFeedingRecordListApi, batchAddFeedingRecordApi, updateFeedingRecordApi,
  deleteFeedingRecordApi, auditFeedingRecordApi, type FeedingRecord,
} from '@/api/feeding'
import { getFeedingPlanListApi, type FeedingPlan } from '@/api/feeding'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { useAuthStore } from '@/stores/auth'
import { FEED_TIME_PERIOD_OPTIONS, AUDIT_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

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
const editWasAudited = ref(false)
const form = reactive({
  feed_date: dayjs().format('YYYY-MM-DD'),
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

function feedStatusColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '未投喂': 'info', '已投喂': 'success', '已跳过': 'warning' }
  return m[s] || 'info'
}

function auditStatusColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '待审核': 'warning', '通过': 'success', '驳回': 'danger' }
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
  // 编辑单条记录时只做提示；批量弹窗里选方案会自动回填重量
  if (!planId) return
  const p = planOptions.value.find(x => x.id === planId)
  if (p) {
    ElMessage.info(`方案：${p.plan_name}，单只计划 精${p.concentrate_weight ?? '-'} / 青贮${p.silage_weight ?? '-'} / 干草${p.hay_weight ?? '-'} kg`)
  }
}

// ============ 批量提交（多圈舍一次生成多条） ============
interface BatchRow {
  pen_id: number
  pen_code: string
  pen_type: string
  animal_count: number
  actual_concentrate: number
  actual_silage: number
  actual_hay: number
}

const batchVisible = ref(false)
const batchSaving = ref(false)
const batchPenIds = ref<number[]>([])
const batchRows = ref<BatchRow[]>([])
const batchForm = reactive({
  feed_date: dayjs().format('YYYY-MM-DD'),
  time_period: '早',
  plan_id: undefined as number | undefined,
  status: '已投喂',
  remark: '',
})

const currentPlan = computed(() => planOptions.value.find(p => p.id === batchForm.plan_id))
const planHint = computed(() => {
  const p = currentPlan.value
  if (!p) return '未选方案，手动填写重量'
  return `方案单只：精${p.concentrate_weight ?? 0} / 青贮${p.silage_weight ?? 0} / 干草${p.hay_weight ?? 0} kg`
})

/** 整圈重量 = 方案单只重量 × 存栏头数（方案里是按 kg/只·次 配置的） */
function calcBatchWeight(perAnimal: number | null | undefined, count: number): number {
  if (!perAnimal || !count) return 0
  return Math.round(perAnimal * count * 100) / 100
}

function fillRowWeights(row: BatchRow) {
  const p = currentPlan.value
  row.actual_concentrate = calcBatchWeight(p?.concentrate_weight, row.animal_count)
  row.actual_silage = calcBatchWeight(p?.silage_weight, row.animal_count)
  row.actual_hay = calcBatchWeight(p?.hay_weight, row.animal_count)
}

/** 换方案：按当前头数重算所有行的默认重量 */
function applyPlanToRows() {
  batchRows.value.forEach(fillRowWeights)
}

/** 改头数：该行重量跟着按比例重算 */
function onRowCountChange(row: BatchRow) {
  fillRowWeights(row)
}

/** 圈舍多选变化：保留已填过的行，新增的行按存栏和方案生成默认值 */
function syncBatchRows() {
  const existed = new Map(batchRows.value.map(r => [r.pen_id, r]))
  batchRows.value = batchPenIds.value
    .map(id => {
      const old = existed.get(id)
      if (old) return old
      const pen = penOptions.value.find(x => x.id === id)
      if (!pen) return null
      const row: BatchRow = {
        pen_id: pen.id,
        pen_code: pen.pen_code,
        pen_type: pen.pen_type,
        // 饲喂头数默认绑定圈舍实际存栏
        animal_count: Number(pen.current_count || 0),
        actual_concentrate: 0,
        actual_silage: 0,
        actual_hay: 0,
      }
      fillRowWeights(row)
      return row
    })
    .filter((r): r is BatchRow => r !== null)
}

function handleBatchAdd() {
  Object.assign(batchForm, {
    feed_date: dayjs().format('YYYY-MM-DD'),
    time_period: '早',
    plan_id: undefined,
    status: '已投喂',
    remark: '',
  })
  batchPenIds.value = []
  batchRows.value = []
  batchVisible.value = true
}

async function handleBatchSave() {
  if (!batchRows.value.length) {
    ElMessage.warning('请先选择圈舍')
    return
  }
  if (!batchForm.feed_date) {
    ElMessage.warning('请选择饲喂日期')
    return
  }
  batchSaving.value = true
  try {
    const payload: any = {
      feed_date: batchForm.feed_date,
      time_period: batchForm.time_period,
      status: batchForm.status,
      items: batchRows.value.map(r => ({
        pen_id: r.pen_id,
        animal_count: r.animal_count,
        actual_concentrate: r.actual_concentrate || undefined,
        actual_silage: r.actual_silage || undefined,
        actual_hay: r.actual_hay || undefined,
      })),
    }
    if (batchForm.plan_id) payload.plan_id = batchForm.plan_id
    if (batchForm.remark) payload.remark = batchForm.remark
    const res = await batchAddFeedingRecordApi(payload)
    const data = res.data as any
    ElMessage.success((res as any).msg || `提交成功 ${data?.created ?? 0} 条`)
    if (data?.skipped?.length) {
      ElMessage.warning(
        `已跳过：${data.skipped.map((s: any) => `${s.pen_code || s.pen_id}（${s.reason}）`).join('；')}`,
      )
    }
    batchVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    batchSaving.value = false
  }
}

function handleEdit(row: FeedingRecord) {
  isEdit.value = true
  editId.value = row.id
  editWasAudited.value = row.audit_status !== '待审核'
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
  // 该弹窗只用于「编辑已有记录」；新增走批量提交（可一次选多个圈舍）
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.plan_id) delete payload.plan_id
    await updateFeedingRecordApi(editId.value, payload)
    ElMessage.success(editWasAudited.value ? '修改成功，已重置为待审核，需重新审核' : '修改成功')
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

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
  loadPenOptions()
  loadPlanOptions()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }

.feed-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 18px; }
.feed-field-label { font-size: 13px; color: #5b7d95; padding-left: 2px; }
.mb-8 { margin-bottom: 8px; }
.plan-hint { font-size: 12px; color: #6b8ba4; }
.footer-left { float: left; line-height: 32px; font-size: 13px; color: #6b8ba4; }
</style>
