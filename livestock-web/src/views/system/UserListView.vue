<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增用户
      </el-button>
    </div>

    <!-- 搜索 -->
    <el-card class="mb-16">
      <el-form inline @submit.prevent>
        <el-form-item label="账号">
          <el-input v-model="query.username" placeholder="登录账号" clearable style="width: 160px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="query.real_name" placeholder="真实姓名" clearable style="width: 140px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="query.user_type" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="(label, val) in USER_TYPE_MAP" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item label="养殖场">
          <el-select v-model="query.farm_id" placeholder="全部" clearable filterable style="width: 180px">
            <el-option v-for="f in farms" :key="f.id" :label="f.farm_name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 110px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.user_type === 1 ? 'danger' : row.user_type === 2 ? 'warning' : 'info'">
              {{ USER_TYPE_MAP[row.user_type] || row.user_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="farm_name" label="养殖场" min-width="120">
          <template #default="{ row }">{{ row.farm_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="post" label="岗位" width="90">
          <template #default="{ row }">{{ row.post || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" min-width="140">
          <template #default="{ row }">
            <template v-if="row.role_names.length">
              <el-tag v-for="rn in row.role_names" :key="rn" size="small" class="mr-8">{{ rn }}</el-tag>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row as UserInfo)">编辑</el-button>
            <el-button link type="warning" size="small" @click="handleResetPwd(row as UserInfo)">重置密码</el-button>
            <el-popconfirm title="确定删除该用户？" @confirm="handleDelete(row as UserInfo)">
              <template #reference>
                <el-button link type="danger" size="small" :disabled="row.user_type === 1">删除</el-button>
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
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="登录账号" prop="username">
              <el-input v-model="form.username" :disabled="isEdit" placeholder="登录用账号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" :prop="isEdit ? undefined : 'password'">
              <el-input v-model="form.password" type="password" show-password :placeholder="isEdit ? '留空则不修改' : '至少6位'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="form.real_name" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="11位手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用户类型" prop="user_type">
              <el-select v-model="form.user_type" style="width: 100%" :disabled="isEdit">
                <el-option label="养殖场主" :value="2" />
                <el-option label="员工" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="养殖场" prop="farm_id">
              <el-select v-model="form.farm_id" placeholder="请选择" filterable clearable style="width: 100%">
                <el-option v-for="f in farms" :key="f.id" :label="f.farm_name" :value="f.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.user_type === 3">
            <el-form-item label="岗位" prop="post">
              <el-select v-model="form.post" style="width: 100%">
                <el-option v-for="(_, key) in POST_MAP" :key="key" :label="key" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio :value="1">启用</el-radio>
                <el-radio :value="0">禁用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="角色">
              <el-select v-model="form.role_ids" multiple placeholder="选择角色" clearable style="width: 100%">
                <el-option v-for="r in roles" :key="r.id" :label="r.role_name" :value="r.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="pwdVisible" title="重置密码" width="420px">
      <el-form :model="pwdForm" :rules="pwdRules" ref="pwdRef" label-width="80px">
        <el-form-item label="账号">
          <span>{{ pwdForm.username }}</span>
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSavePwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getSystemUserListApi, addSystemUserApi, updateSystemUserApi, deleteSystemUserApi, resetUserPasswordApi, getUserRolesApi, type UserInfo } from '@/api/system'
import { getRoleListApi, type RoleInfo } from '@/api/system'
import { getFarmListApi, type FarmListItem } from '@/api/farm'
import { USER_TYPE_MAP, POST_MAP } from '@/utils/constants'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const users = ref<UserInfo[]>([])
const farms = ref<FarmListItem[]>([])
const roles = ref<RoleInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const query = reactive<Record<string, any>>({ username: '', real_name: '', user_type: undefined, farm_id: undefined, status: undefined })

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive<Record<string, any>>({
  username: '', password: '', real_name: '', phone: '',
  user_type: 3, farm_id: undefined, post: '饲喂员', status: 1, role_ids: [],
})

const formRules: FormRules = {
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入有效手机号', trigger: 'blur' }],
  user_type: [{ required: true, message: '请选择用户类型', trigger: 'change' }],
}

const pwdVisible = ref(false)
const pwdRef = ref<FormInstance>()
const pwdForm = reactive({ id: 0, username: '', new_password: '' })
const pwdRules: FormRules = { new_password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }] }

async function loadUsers() {
  loading.value = true
  try {
    const res = await getSystemUserListApi({ ...query, pageNum: pageNum.value, pageSize: pageSize.value })
    users.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pageNum.value = 1
  loadUsers()
}

function handleReset() {
  query.username = ''
  query.real_name = ''
  query.user_type = undefined
  query.farm_id = undefined
  query.status = undefined
  handleSearch()
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, { username: '', password: '', real_name: '', phone: '', user_type: 3, farm_id: undefined, post: '饲喂员', status: 1, role_ids: [] })
  formRules.password = [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }]
  dialogVisible.value = true
}

async function handleEdit(row: UserInfo) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    username: row.username, password: '', real_name: row.real_name, phone: row.phone,
    user_type: row.user_type, farm_id: row.farm_id, post: row.post || '饲喂员',
    status: row.status, role_ids: [],
  })
  delete formRules.password
  try {
    const r = await getUserRolesApi(row.id)
    form.role_ids = r.data.role_ids
  } catch { /* */ }
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateSystemUserApi(editId.value, {
        username: form.username,
        password: form.password || undefined,
        real_name: form.real_name,
        phone: form.phone,
        user_type: form.user_type,
        farm_id: form.farm_id || null,
        post: form.user_type === 3 ? form.post : null,
        status: form.status,
        role_ids: form.role_ids,
      })
      ElMessage.success('修改成功')
    } else {
      await addSystemUserApi({
        username: form.username, password: form.password, real_name: form.real_name,
        phone: form.phone, user_type: form.user_type, farm_id: form.farm_id || null,
        post: form.user_type === 3 ? form.post : null, status: form.status, role_ids: form.role_ids,
      })
      ElMessage.success('新增用户成功')
    }
    dialogVisible.value = false
    loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: UserInfo) {
  try {
    await deleteSystemUserApi(row.id)
    ElMessage.success('已删除')
    loadUsers()
  } catch { /* */ }
}

function handleResetPwd(row: UserInfo) {
  pwdForm.id = row.id
  pwdForm.username = row.username
  pwdForm.new_password = ''
  pwdVisible.value = true
}

async function handleSavePwd() {
  const valid = await pwdRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await resetUserPasswordApi(pwdForm.id, pwdForm.new_password)
    ElMessage.success('密码已重置')
    pwdVisible.value = false
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loadUsers()
  try {
    const f = await getFarmListApi()
    farms.value = f.data
  } catch { /* */ }
  try {
    const r = await getRoleListApi({ pageNum: 1, pageSize: 100 })
    roles.value = r.data.list
  } catch { /* */ }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mr-8 { margin-right: 8px; }
</style>
