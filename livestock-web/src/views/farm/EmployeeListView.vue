<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">员工管理</h2>
      <el-button type="primary" @click="handleAdd" v-if="canManage">
        <el-icon><Plus /></el-icon> 添加员工
      </el-button>
    </div>
    <el-card>
      <el-table :data="employees" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="post" label="岗位" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.post" type="info">{{ row.post }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="160" fixed="right" v-if="canManage">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row as Employee)">编辑</el-button>
            <el-popconfirm title="确定删除该员工？" @confirm="handleDelete(row.id)">
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
          @size-change="loadEmployees"
          @current-change="loadEmployees"
        />
      </div>
    </el-card>

    <!-- 添加/编辑员工弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑员工' : '添加员工'" width="460px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="登录账号" prop="username">
          <el-input v-model="form.username" placeholder="员工登录用" />
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? undefined : 'password'">
          <el-input v-model="form.password" type="password" show-password :placeholder="isEdit ? '留空则不修改密码' : '至少6位'" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="11位手机号" />
        </el-form-item>
        <el-form-item label="岗位" prop="post">
          <el-select v-model="form.post" placeholder="请选择岗位" style="width: 100%">
            <el-option v-for="(_, key) in POST_MAP" :key="key" :label="key" :value="key" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存' : '确认添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getEmployeesApi, addEmployeeApi, updateEmployeeApi, deleteEmployeeApi, type Employee } from '@/api/farm'
import { useAuthStore } from '@/stores/auth'
import { POST_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const canManage = computed(() => authStore.userType !== 3)

const employees = ref<Employee[]>([])
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
  username: '',
  password: '',
  real_name: '',
  phone: '',
  post: '饲喂员',
})

const formRules: FormRules = {
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入有效手机号', trigger: 'blur' }],
  post: [{ required: true, message: '请选择岗位', trigger: 'change' }],
}

async function loadEmployees() {
  loading.value = true
  try {
    const res = await getEmployeesApi({ pageNum: pageNum.value, pageSize: pageSize.value })
    const data = res.data as any
    employees.value = data.list || []
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
  form.username = ''
  form.password = ''
  form.real_name = ''
  form.phone = ''
  form.post = '饲喂员'
  // 添加时密码必填
  formRules.password = [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }]
  dialogVisible.value = true
}

function handleEdit(row: Employee) {
  isEdit.value = true
  editId.value = row.id
  form.username = row.username
  form.password = ''
  form.real_name = row.real_name
  form.phone = row.phone
  form.post = row.post || '饲喂员'
  // 编辑时密码选填
  delete formRules.password
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateEmployeeApi(editId.value, {
        username: form.username,
        password: form.password || undefined,
        real_name: form.real_name,
        phone: form.phone,
        post: form.post,
      })
      ElMessage.success('修改成功')
    } else {
      await addEmployeeApi({
        farm_id: 0,
        username: form.username,
        password: form.password,
        real_name: form.real_name,
        phone: form.phone,
        post: form.post,
      })
      ElMessage.success('添加员工成功')
    }
    dialogVisible.value = false
    loadEmployees()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteEmployeeApi(id)
    ElMessage.success('已删除')
    loadEmployees()
  } catch {
    // handled by interceptor
  }
}

onMounted(loadEmployees)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
