<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">薪资配置</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增配置
      </el-button>
    </div>
    <el-card>
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="post" label="岗位" width="120">
          <template #default="{ row }">
            <el-tag type="info">{{ row.post }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_salary" label="基础薪资" width="120">
          <template #default="{ row }">
            <span class="salary">{{ Number(row.base_salary).toFixed(2) }} 元</span>
          </template>
        </el-table-column>
        <el-table-column prop="bonus_ratio" label="奖金比例" width="110">
          <template #default="{ row }">
            <span v-if="row.bonus_ratio != null">{{ row.bonus_ratio }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="deduct_rule" label="扣罚规则" min-width="180">
          <template #default="{ row }">
            <span v-if="row.deduct_rule">{{ row.deduct_rule }}</span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="140">
          <template #default="{ row }">
            <span v-if="row.remark">{{ row.remark }}</span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row as SalaryConfig)">编辑</el-button>
            <el-popconfirm title="确定删除该薪资配置？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
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
          @size-change="loadConfigs"
          @current-change="loadConfigs"
        />
      </div>
    </el-card>

    <!-- 新增/编辑薪资配置弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑薪资配置' : '新增薪资配置'" width="480px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="岗位" prop="post">
          <el-select v-model="form.post" placeholder="请选择岗位" style="width: 100%" :disabled="isEdit" @change="onPostChange">
            <el-option v-for="(_, key) in POST_MAP" :key="key" :label="key" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="基础薪资" prop="base_salary">
          <el-input-number v-model="form.base_salary" :min="0" :precision="2" :step="100" style="width: 100%" placeholder="元/月" />
        </el-form-item>
        <el-form-item label="奖金比例" prop="bonus_ratio">
          <el-input-number v-model="form.bonus_ratio" :min="0" :max="100" :precision="2" :step="1" style="width: 100%" placeholder="按绩效发放的比例 %" />
        </el-form-item>
        <el-form-item label="扣罚规则" prop="deduct_rule">
          <el-input v-model="form.deduct_rule" placeholder="如：迟到一次扣 50 元" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getSalaryConfigsApi, addSalaryConfigApi, updateSalaryConfigApi, deleteSalaryConfigApi,
  type SalaryConfig,
} from '@/api/farm'
import { POST_MAP, DEFAULT_SALARY_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const configs = ref<SalaryConfig[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)

const form = reactive({
  post: '',
  base_salary: 4500,
  bonus_ratio: null as number | null,
  deduct_rule: '',
  status: 1,
  remark: '',
})

const formRules: FormRules = {
  post: [{ required: true, message: '请选择岗位', trigger: 'change' }],
  base_salary: [{ required: true, message: '请输入基础薪资', trigger: 'blur' }],
}

async function loadConfigs() {
  loading.value = true
  try {
    const res = await getSalaryConfigsApi({ pageNum: pageNum.value, pageSize: pageSize.value })
    const data = res.data as any
    configs.value = data.list || []
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
  form.post = ''
  form.base_salary = 4500
  form.bonus_ratio = null
  form.deduct_rule = ''
  form.status = 1
  form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row: SalaryConfig) {
  isEdit.value = true
  editId.value = row.id
  form.post = row.post
  form.base_salary = Number(row.base_salary)
  form.bonus_ratio = row.bonus_ratio
  form.deduct_rule = row.deduct_rule || ''
  form.status = row.status
  form.remark = row.remark || ''
  dialogVisible.value = true
}

function onPostChange(post: string) {
  if (!isEdit.value && DEFAULT_SALARY_MAP[post] != null) {
    form.base_salary = DEFAULT_SALARY_MAP[post]
  }
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = {
      post: form.post,
      base_salary: form.base_salary,
      bonus_ratio: form.bonus_ratio ?? undefined,
      deduct_rule: form.deduct_rule || undefined,
      status: form.status,
      remark: form.remark || undefined,
    }
    if (isEdit.value) {
      await updateSalaryConfigApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addSalaryConfigApi(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadConfigs()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteSalaryConfigApi(id)
    ElMessage.success('已删除')
    loadConfigs()
  } catch {
    // handled by interceptor
  }
}

onMounted(loadConfigs)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.salary { font-weight: 600; color: #e6a23c; }
.muted { color: #6b8ba4; }
</style>
