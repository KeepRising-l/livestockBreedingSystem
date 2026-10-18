<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">圈舍管理<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <div v-if="canEdit">
        <el-button @click="handleBatchAdd">
          <el-icon><Plus /></el-icon> 批量添加
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新增圈舍
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="圈舍类型">
          <el-select v-model="query.pen_type" placeholder="全部" clearable style="width: 140px" @change="search">
            <el-option v-for="(label, key) in PEN_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 圈舍列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe @row-click="(row: PenInfo) => router.push(`/${species}/pen/${row.id}`)" style="cursor: pointer">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="编号" width="150">
          <template #default="{ row }">
            <span>{{ row.pen_code }}</span>
            <!-- 未归属畜种的圈舍会在各畜种列表里都出现，显式标记以免被当成"串了数据" -->
            <el-tag v-if="!row.species" type="warning" size="small" class="ml-1">待归属</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pen_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="penTypeColor(row.pen_type)">{{ PEN_TYPE_MAP[row.pen_type] || row.pen_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column prop="current_count" label="当前存栏" width="100" />
        <el-table-column label="存栏率" min-width="130">
          <template #default="{ row }">
            <el-progress
              :key="row.id"
              :percentage="progressReady ? Math.min(100, Math.round(row.current_count / row.capacity * 100)) : 0"
              :stroke-width="16"
              text-inside
              :status="row.current_count >= row.capacity ? 'success' : undefined"
              :format="(percentage: number) => row.current_count >= row.capacity ? '已住满' : `${percentage}%`"
            />
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="router.push(`/${species}/pen/${row.id}`)">详情</el-button>
            <el-button link type="warning" size="small" @click.stop="handleEdit(row as PenInfo)" v-if="canEdit">编辑</el-button>
            <el-popconfirm title="确定删除该圈舍？" @confirm="handleDelete(row.id)" v-if="canEdit">
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑圈舍' : '新增圈舍'" width="480px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="圈舍编号" prop="pen_code">
          <el-input v-model="form.pen_code" placeholder="如 A01" />
          <div class="tip">编号在「所属畜种」范围内唯一，牛/羊/猪 可以各自都有 A01</div>
        </el-form-item>
        <el-form-item label="所属畜种" prop="species">
          <el-select v-model="form.species" placeholder="请选择" style="width: 100%">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="圈舍类型" prop="pen_type">
          <el-select v-model="form.pen_type" placeholder="请选择" style="width: 100%">
            <el-option v-for="(label, key) in PEN_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量添加圈舍" width="560px">
      <el-form :model="batchForm" :rules="batchFormRules" ref="batchFormRef" label-width="100px">
        <el-form-item label="所属畜种" prop="species">
          <el-select v-model="batchForm.species" placeholder="请选择" style="width: 100%">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="圈舍类型" prop="pen_type">
          <el-select v-model="batchForm.pen_type" placeholder="请选择" style="width: 100%">
            <el-option v-for="(label, key) in PEN_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="batchForm.capacity" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="编号前缀" prop="prefix">
          <el-input v-model="batchForm.prefix" placeholder="字母，如 A" maxlength="10" />
        </el-form-item>
        <el-form-item label="起始序号" prop="start_no">
          <el-input-number v-model="batchForm.start_no" :min="1" :max="999999" style="width: 100%" />
          <div class="tip">序号统一补 2 位，如 1 → 01</div>
        </el-form-item>
        <el-form-item label="数量" prop="count">
          <el-input-number v-model="batchForm.count" :min="1" :max="BATCH_MAX_COUNT" style="width: 100%" />
          <div class="tip">单次最多添加 {{ BATCH_MAX_COUNT }} 个圈舍</div>
        </el-form-item>
        <el-form-item label="编号列表" prop="codesText">
          <el-input
            v-model="batchForm.codesText"
            type="textarea"
            :rows="6"
            placeholder="每行一个编号，也可用空格、逗号分隔"
          />
          <div class="tip">已按「前缀 + 起始序号」生成，可直接编辑；修改上方规则会重新生成（共 {{ batchCodeCount }} 个编号）</div>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="batchForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSaving" @click="handleBatchSave">确定添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  getPenListApi, addPenApi, updatePenApi, deletePenApi, batchAddPenApi,
  type PenInfo, type PenBatchAddResult, type PenBatchSkipped,
} from '@/api/pen'
import { useAuthStore } from '@/stores/auth'
import { PEN_TYPE_MAP, SPECIES_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage, type FormInstance, type FormItemRule, type FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const { species, speciesZh } = useSpecies()
const canEdit = computed(() => authStore.userType !== 3)

const list = ref<PenInfo[]>([])
const loading = ref(false)
const progressReady = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive({ pen_type: '' })

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)

const form = reactive({
  pen_code: '',
  pen_type: 'A',
  species: '牛' as string,
  capacity: 12,
  remark: '',
})

const formRules: FormRules = {
  pen_code: [{ required: true, message: '请输入圈舍编号', trigger: 'blur' }],
  pen_type: [{ required: true, message: '请选择圈舍类型', trigger: 'change' }],
  species: [{ required: true, message: '请选择所属畜种', trigger: 'change' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
}

// ===== 批量添加 =====
const BATCH_MAX_COUNT = 50
const BATCH_CODE_RE = /^[A-Za-z]+\d{1,6}$/
const BATCH_PREFIX_RE = /^[A-Za-z]{1,10}$/

const batchDialogVisible = ref(false)
const batchSaving = ref(false)
const batchFormRef = ref<FormInstance>()

const batchForm = reactive({
  species: '牛' as string,
  pen_type: 'A',
  capacity: 12,
  prefix: 'A',
  start_no: 1,
  count: 10,
  codesText: '',
  remark: '',
})

/** 按「前缀 + 起始序号 + 数量」生成编号，序号统一补 2 位 */
function generateBatchCodes(): string[] {
  const prefix = batchForm.prefix.trim()
  if (!BATCH_PREFIX_RE.test(prefix)) return []
  const count = Math.max(0, Math.min(BATCH_MAX_COUNT, Number(batchForm.count) || 0))
  const start = Number(batchForm.start_no) || 1
  return Array.from({ length: count }, (_, i) => `${prefix}${String(start + i).padStart(2, '0')}`)
}

/** 解析编号列表：支持换行、空格、中英文逗号/分号分隔 */
function parseBatchCodes(): string[] {
  return batchForm.codesText
    .split(/[\s,，;；]+/)
    .map((code) => code.trim())
    .filter(Boolean)
}

const batchCodeCount = computed(() => parseBatchCodes().length)

/** 规则变化时重新生成预览；用户手工编辑的内容会被覆盖（弹窗内有提示） */
function syncBatchCodes() {
  batchForm.codesText = generateBatchCodes().join('\n')
}

watch(
  () => [batchForm.prefix, batchForm.start_no, batchForm.count],
  () => syncBatchCodes(),
)

const validateBatchCodes: FormItemRule['validator'] = (_rule, _value, callback) => {
  const codes = parseBatchCodes()
  if (!codes.length) {
    callback(new Error('请填写要创建的圈舍编号'))
    return
  }
  if (codes.length > BATCH_MAX_COUNT) {
    callback(new Error(`单次最多添加 ${BATCH_MAX_COUNT} 个圈舍`))
    return
  }
  const invalid = codes.find((code) => code.length > 20 || !BATCH_CODE_RE.test(code))
  if (invalid) {
    callback(new Error(`编号「${invalid}」格式不正确，应为字母前缀 + 数字序号，如 A01`))
    return
  }
  callback()
}

const batchFormRules: FormRules = {
  species: [{ required: true, message: '请选择所属畜种', trigger: 'change' }],
  pen_type: [{ required: true, message: '请选择圈舍类型', trigger: 'change' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
  prefix: [
    { required: true, message: '请输入编号前缀', trigger: 'blur' },
    { pattern: BATCH_PREFIX_RE, message: '编号前缀只能是 1~10 位字母，如 A', trigger: 'blur' },
  ],
  start_no: [{ required: true, message: '请输入起始序号', trigger: 'blur' }],
  count: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  codesText: [{ validator: validateBatchCodes, trigger: 'blur' }],
}

function handleBatchAdd() {
  batchForm.species = speciesZh.value
  batchForm.pen_type = 'A'
  batchForm.capacity = 12
  batchForm.prefix = 'A'
  batchForm.start_no = 1
  batchForm.count = 10
  batchForm.remark = ''
  syncBatchCodes()
  batchDialogVisible.value = true
  nextTick(() => batchFormRef.value?.clearValidate())
}

function formatBatchSkipped(skipped: PenBatchSkipped[]): string {
  const detail = skipped.slice(0, 3).map((item) => `${item.code}：${item.reason}`).join('；')
  return skipped.length > 3 ? `${detail} 等 ${skipped.length} 条` : detail
}

async function handleBatchSave() {
  const valid = await batchFormRef.value?.validate().catch(() => false)
  if (!valid) return
  const codes = parseBatchCodes()
  batchSaving.value = true
  try {
    const res = await batchAddPenApi({
      species: batchForm.species,
      pen_type: batchForm.pen_type,
      capacity: batchForm.capacity,
      remark: batchForm.remark,
      codes,
    })
    const data = res.data as PenBatchAddResult
    const created = data?.created || 0
    const skipped = data?.skipped || []
    if (!created) {
      // 一条都没建成时保留弹窗，方便按提示调整编号后重试
      ElMessage.warning({
        message: `未创建圈舍，跳过 ${skipped.length} 条：${formatBatchSkipped(skipped)}`,
        duration: 6000,
      })
      return
    }
    if (skipped.length) {
      ElMessage.warning({
        message: `成功 ${created} 条，跳过 ${skipped.length} 条：${formatBatchSkipped(skipped)}`,
        duration: 6000,
      })
    } else {
      ElMessage.success(`成功添加 ${created} 个圈舍`)
    }
    batchDialogVisible.value = false
    await loadData()
  } catch {
    // handled by interceptor
  } finally {
    batchSaving.value = false
  }
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.pen_type = ''
  search()
}

function penTypeColor(type: string): TagProps['type'] {
  const colors: Record<string, TagProps['type']> = { A: 'success', B: 'info', C: 'warning', D: 'danger' }
  return colors[type] || 'info'
}

async function loadData() {
  loading.value = true
  progressReady.value = false
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value, species: speciesZh.value }
    if (query.pen_type) params.pen_type = query.pen_type
    const res = await getPenListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
    // 等进度条以 0% 渲染一帧后，再切到真实百分比，播放填充动画
    await nextTick()
    progressReady.value = true
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  form.pen_code = ''
  form.pen_type = 'A'
  // 默认归属当前路由所在的畜种，避免新建后跑到别的畜种列表去
  form.species = speciesZh.value
  form.capacity = 12
  form.remark = ''
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function handleEdit(row: PenInfo) {
  isEdit.value = true
  editId.value = row.id
  form.pen_code = row.pen_code
  form.pen_type = row.pen_type
  form.species = row.species || ''
  form.capacity = row.capacity
  form.remark = row.remark || ''
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updatePenApi(editId.value, {
        pen_code: form.pen_code,
        pen_type: form.pen_type,
        species: form.species,
        capacity: form.capacity,
        remark: form.remark,
      })
      ElMessage.success('修改成功')
    } else {
      await addPenApi({
        pen_code: form.pen_code,
        pen_type: form.pen_type,
        species: form.species,
        capacity: form.capacity,
        remark: form.remark,
      })
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    // 等列表刷新完成再解除 saving，避免"提示已成功但列表还没变"的错觉
    await loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deletePenApi(id)
    ElMessage.success('删除成功')
    await loadData()
  } catch {
    // handled by interceptor
  }
}

// 切换畜种时，路由参数变化不会重建组件（同一条路由记录），必须主动重新拉取，
// 否则会一直停留在上一个畜种的圈舍数据上
watch(species, () => {
  pageNum.value = 1
  query.pen_type = ''
  loadData()
})

onMounted(loadData)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.tip { color: #6b8ba4; font-size: 12px; margin-top: 4px; line-height: 1.6; }
</style>
