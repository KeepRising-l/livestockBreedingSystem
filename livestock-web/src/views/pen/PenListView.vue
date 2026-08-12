<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">圈舍管理<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleAdd" v-if="canEdit">
        <el-icon><Plus /></el-icon> 新增圈舍
      </el-button>
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
        <el-table-column prop="pen_code" label="编号" width="100" />
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
            <el-button link type="warning" size="small" @click.stop="handleEdit(row)" v-if="canEdit">编辑</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getPenListApi, addPenApi, updatePenApi, deletePenApi, type PenInfo } from '@/api/pen'
import { useAuthStore } from '@/stores/auth'
import { PEN_TYPE_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

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
  capacity: 12,
  remark: '',
})

const formRules: FormRules = {
  pen_code: [{ required: true, message: '请输入圈舍编号', trigger: 'blur' }],
  pen_type: [{ required: true, message: '请选择圈舍类型', trigger: 'change' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.pen_type = ''
  search()
}

function penTypeColor(type: string) {
  const colors: Record<string, string> = { A: 'success', B: '', C: 'warning', D: 'danger' }
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
  form.capacity = 12
  form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row: PenInfo) {
  isEdit.value = true
  editId.value = row.id
  form.pen_code = row.pen_code
  form.pen_type = row.pen_type
  form.capacity = row.capacity
  form.remark = row.remark || ''
  dialogVisible.value = true
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
        capacity: form.capacity,
        remark: form.remark,
      })
      ElMessage.success('修改成功')
    } else {
      await addPenApi({ pen_code: form.pen_code, pen_type: form.pen_type, capacity: form.capacity, remark: form.remark })
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

async function handleDelete(id: number) {
  try {
    await deletePenApi(id)
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
</style>
