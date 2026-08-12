<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">饲喂方案</h2>
      <el-button type="primary" @click="handleAdd" v-if="canEdit">
        <el-icon><Plus /></el-icon> 新增方案
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 140px" @change="search">
            <el-option v-for="o in SPECIES_CODE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 140px" @change="search">
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 方案列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="plan_name" label="方案名称" min-width="140" />
        <el-table-column label="畜种" width="80">
          <template #default="{ row }">{{ SPECIES_CODE_MAP[row.species] || row.species }}</template>
        </el-table-column>
        <el-table-column prop="applicable_stage" label="适用阶段" width="110" />
        <el-table-column label="适用圈舍" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.applicable_pen_type" size="small">{{ PEN_TYPE_MAP[row.applicable_pen_type] || row.applicable_pen_type }}</el-tag>
            <span v-else>全部</span>
          </template>
        </el-table-column>
        <el-table-column prop="feed_times_per_day" label="日喂次数" width="90" />
        <el-table-column label="精料(kg/次)" width="110">
          <template #default="{ row }">{{ row.concentrate_weight ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="青贮(kg/次)" width="110">
          <template #default="{ row }">{{ row.silage_weight ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="干草(kg/次)" width="110">
          <template #default="{ row }">{{ row.hay_weight ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="预计日成本(元)" width="120">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: 600;">{{ row.est_cost_per_day ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click.stop="handleEdit(row)" v-if="canEdit">编辑</el-button>
            <el-popconfirm :title="row.status === 1 ? '确定停用该方案？' : '确定启用该方案？'" @confirm="handleToggleStatus(row)" v-if="canEdit">
              <template #reference>
                <el-button link :type="row.status === 1 ? 'info' : 'success'" size="small" @click.stop>
                  {{ row.status === 1 ? '停用' : '启用' }}
                </el-button>
              </template>
            </el-popconfirm>
            <el-popconfirm title="确定删除该方案？" @confirm="handleDelete(row.id)" v-if="canEdit">
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑方案' : '新增方案'" width="640px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="方案名称" prop="plan_name">
          <el-input v-model="form.plan_name" placeholder="如 育肥牛方案V1" />
        </el-form-item>
        <el-form-item label="适用畜种" prop="species">
          <el-select v-model="form.species" placeholder="请选择" style="width: 100%">
            <el-option v-for="o in SPECIES_CODE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用生长阶段" prop="applicable_stage">
          <el-input v-model="form.applicable_stage" placeholder="如 育肥期 / 保育期" />
        </el-form-item>
        <el-form-item label="适用圈舍类型">
          <el-select v-model="form.applicable_pen_type" placeholder="不限" clearable style="width: 100%">
            <el-option v-for="(label, key) in PEN_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="每日投喂次数" prop="feed_times_per_day">
          <el-input-number v-model="form.feed_times_per_day" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
        <el-divider content-position="left">饲料计划（kg/只·次）</el-divider>
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">精料</span>
              <el-input-number v-model="form.concentrate_weight" :min="0" :precision="2" :step="0.5" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">青贮</span>
              <el-input-number v-model="form.silage_weight" :min="0" :precision="2" :step="0.5" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">干草</span>
              <el-input-number v-model="form.hay_weight" :min="0" :precision="2" :step="0.5" style="width: 100%" />
            </div>
          </el-col>
        </el-row>
        <el-divider content-position="left">饲料单价（元/吨）</el-divider>
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">精料</span>
              <el-input-number v-model="form.concentrate_price" :min="0" :precision="2" :step="100" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">青贮</span>
              <el-input-number v-model="form.silage_price" :min="0" :precision="2" :step="100" style="width: 100%" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feed-field">
              <span class="feed-field-label">干草</span>
              <el-input-number v-model="form.hay_price" :min="0" :precision="2" :step="100" style="width: 100%" />
            </div>
          </el-col>
        </el-row>
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
import { getFeedingPlanListApi, addFeedingPlanApi, updateFeedingPlanApi, deleteFeedingPlanApi, type FeedingPlan } from '@/api/feeding'
import { useAuthStore } from '@/stores/auth'
import { PEN_TYPE_MAP, SPECIES_CODE_OPTIONS, SPECIES_CODE_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canEdit = computed(() => authStore.userType !== 3)

const list = ref<FeedingPlan[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive<{ species: string; status: number | undefined }>({ species: '', status: undefined })

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)

const form = reactive({
  plan_name: '',
  species: 'cattle',
  applicable_stage: '',
  applicable_pen_type: '' as string,
  feed_times_per_day: 2,
  concentrate_weight: undefined as number | undefined,
  silage_weight: undefined as number | undefined,
  hay_weight: undefined as number | undefined,
  concentrate_price: undefined as number | undefined,
  silage_price: undefined as number | undefined,
  hay_price: undefined as number | undefined,
  remark: '',
})

const formRules: FormRules = {
  plan_name: [{ required: true, message: '请输入方案名称', trigger: 'blur' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  applicable_stage: [{ required: true, message: '请输入适用阶段', trigger: 'blur' }],
  feed_times_per_day: [{ required: true, message: '请输入投喂次数', trigger: 'blur' }],
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.species = ''
  query.status = undefined
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.species) params.species = query.species
    if (query.status !== undefined) params.status = query.status
    const res = await getFeedingPlanListApi(params)
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
    plan_name: '', species: 'cattle', applicable_stage: '', applicable_pen_type: '',
    feed_times_per_day: 2,
    concentrate_weight: undefined, silage_weight: undefined, hay_weight: undefined,
    concentrate_price: undefined, silage_price: undefined, hay_price: undefined,
    remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: FeedingPlan) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    plan_name: row.plan_name,
    species: row.species,
    applicable_stage: row.applicable_stage,
    applicable_pen_type: row.applicable_pen_type || '',
    feed_times_per_day: row.feed_times_per_day,
    concentrate_weight: row.concentrate_weight ?? undefined,
    silage_weight: row.silage_weight ?? undefined,
    hay_weight: row.hay_weight ?? undefined,
    concentrate_price: row.concentrate_price ?? undefined,
    silage_price: row.silage_price ?? undefined,
    hay_price: row.hay_price ?? undefined,
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
    if (payload.applicable_pen_type === '') delete payload.applicable_pen_type
    if (isEdit.value) {
      await updateFeedingPlanApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addFeedingPlanApi(payload)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleToggleStatus(row: FeedingPlan) {
  try {
    await updateFeedingPlanApi(row.id, { status: row.status === 1 ? 0 : 1 })
    ElMessage.success(row.status === 1 ? '已停用' : '已启用')
    loadData()
  } catch {
    // handled by interceptor
  }
}

async function handleDelete(id: number) {
  try {
    await deleteFeedingPlanApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

onMounted(loadData)
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
