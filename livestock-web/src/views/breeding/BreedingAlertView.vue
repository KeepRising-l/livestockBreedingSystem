<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">繁育预警<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 手动新增预警
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="预警日期">
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
        <el-form-item label="类型">
          <el-select v-model="query.alert_type" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="(label, key) in ALERT_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="耳标">
          <el-input v-model="query.animal_tag" placeholder="请输入耳标" clearable style="width: 120px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 110px" @change="search">
            <el-option v-for="(label, key) in ALERT_STATUS_MAP" :key="key" :label="label" :value="key" />
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
            <el-tag :type="typeColor(row.alert_type)" size="small">{{ row.alert_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="animal_tag" label="耳标" width="90" />
        <el-table-column prop="alert_date" label="预警日期" width="110" />
        <el-table-column prop="alert_content" label="预警内容" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.alert_content || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handle_time" label="处理时间" width="160">
          <template #default="{ row }">{{ row.handle_time || '-' }}</template>
        </el-table-column>
        <el-table-column prop="handle_remark" label="处理备注" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.handle_remark || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="handleAlert(row as BreedingAlert)" v-if="row.status === '待处理'">处理</el-button>
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

    <!-- 手动新增弹窗 -->
    <el-dialog v-model="addDialogVisible" title="手动新增预警" width="500px">
      <el-alert type="info" :closable="false" show-icon class="mb-16"
        title="日常预警由系统定时任务自动生成，此处仅用于补录或测试" />
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="90px">
        <el-form-item label="预警类型" prop="alert_type">
          <el-select v-model="addForm.alert_type" placeholder="请选择" style="width: 100%">
            <el-option v-for="(label, key) in ALERT_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联耳标" prop="animal_tag">
          <el-input v-model="addForm.animal_tag" placeholder="请输入耳标" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="预警日期" prop="alert_date">
          <el-date-picker v-model="addForm.alert_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="预警内容">
          <el-input v-model="addForm.alert_content" type="textarea" :rows="2" placeholder="预警内容（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addSaving" @click="confirmAdd">确认生成</el-button>
      </template>
    </el-dialog>

    <!-- 处理弹窗 -->
    <el-dialog v-model="handleDialogVisible" title="处理预警" width="440px">
      <el-form :model="handleForm" label-width="90px">
        <el-form-item label="处理结果" prop="status">
          <el-radio-group v-model="handleForm.status">
            <el-radio value="已处理">已处理</el-radio>
            <el-radio value="已忽略">已忽略</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="handleForm.handle_remark" type="textarea" :rows="2" placeholder="处理备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="handleSaving" @click="confirmHandle">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { ref, reactive, onMounted, watch } from 'vue'
import { getAlertListApi, addAlertApi, handleAlertApi, type BreedingAlert } from '@/api/breeding'
import { ALERT_TYPE_MAP, ALERT_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage, type FormInstance, type FormRules } from 'element-plus'

const { species, speciesZh } = useSpecies()

const list = ref<BreedingAlert[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dateRange = ref<string[]>([])
const query = reactive<{ alert_type: string; animal_tag: string; status: string; alert_date_start: string; alert_date_end: string }>({
  alert_type: '',
  animal_tag: '',
  status: '',
  alert_date_start: '',
  alert_date_end: '',
})

const addDialogVisible = ref(false)
const addSaving = ref(false)
const addFormRef = ref<FormInstance>()
const addForm = reactive({
  alert_type: '',
  animal_tag: '',
  alert_date: dayjs().format('YYYY-MM-DD'),
  alert_content: '',
})
const addRules: FormRules = {
  alert_type: [{ required: true, message: '请选择预警类型', trigger: 'change' }],
  animal_tag: [{ required: true, message: '请输入关联耳标', trigger: 'blur' }],
  alert_date: [{ required: true, message: '请选择预警日期', trigger: 'change' }],
}

const handleDialogVisible = ref(false)
const handleSaving = ref(false)
const handleAlertId = ref(0)
const handleForm = reactive({ status: '已处理', handle_remark: '' })

function typeColor(t: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '孕检': 'primary', '临产': 'danger', '未发情': 'warning' }
  return m[t] || 'info'
}

function statusColor(s: string): TagProps['type'] {
  const m: Record<string, TagProps['type']> = { '待处理': 'warning', '已处理': 'success', '已忽略': 'info' }
  return m[s] || 'info'
}

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.alert_date_start = val[0]
    query.alert_date_end = val[1]
  } else {
    query.alert_date_start = ''
    query.alert_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.alert_type = ''
  query.animal_tag = ''
  query.status = ''
  query.alert_date_start = ''
  query.alert_date_end = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value, species: speciesZh.value }
    if (query.alert_type) params.alert_type = query.alert_type
    if (query.animal_tag) params.animal_tag = query.animal_tag
    if (query.status) params.status = query.status
    if (query.alert_date_start) params.alert_date_start = query.alert_date_start
    if (query.alert_date_end) params.alert_date_end = query.alert_date_end
    const res = await getAlertListApi(params)
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
  Object.assign(addForm, {
    alert_type: '',
    animal_tag: '',
    alert_date: dayjs().format('YYYY-MM-DD'),
    alert_content: '',
  })
  addDialogVisible.value = true
}

async function confirmAdd() {
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return
  addSaving.value = true
  try {
    const payload: any = { ...addForm }
    if (!payload.alert_content) delete payload.alert_content
    await addAlertApi(payload)
    ElMessage.success('预警已生成')
    addDialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    addSaving.value = false
  }
}

function handleAlert(row: BreedingAlert) {
  handleAlertId.value = row.id
  Object.assign(handleForm, { status: '已处理', handle_remark: '' })
  handleDialogVisible.value = true
}

async function confirmHandle() {
  handleSaving.value = true
  try {
    const payload: any = { status: handleForm.status }
    if (handleForm.handle_remark) payload.handle_remark = handleForm.handle_remark
    await handleAlertApi(handleAlertId.value, payload)
    ElMessage.success('预警已处理')
    handleDialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    handleSaving.value = false
  }
}

onMounted(loadData)

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
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
