<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">角色管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增角色
      </el-button>
    </div>

    <el-card class="mb-16">
      <el-form inline @submit.prevent>
        <el-form-item label="角色名称">
          <el-input v-model="query.role_name" placeholder="角色名称" clearable style="width: 180px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 110px">
            <el-option label="正常" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="role_name" label="角色名称" width="160" />
        <el-table-column prop="role_key" label="权限字符串" width="160">
          <template #default="{ row }"><el-tag type="info">{{ row.role_key }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column prop="remark" label="备注" min-width="200">
          <template #default="{ row }">{{ row.remark || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '正常' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该角色？" @confirm="handleDelete(row)">
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
          @size-change="loadRoles"
          @current-change="loadRoles"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑角色' : '新增角色'" width="480px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="form.role_name" placeholder="如：饲喂员" />
        </el-form-item>
        <el-form-item label="权限字符串" prop="role_key">
          <el-input v-model="form.role_key" :disabled="isEdit" placeholder="如：feeder / vet / breeder / keeper" />
        </el-form-item>
        <el-form-item label="显示顺序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getRoleListApi, addRoleApi, updateRoleApi, deleteRoleApi, type RoleInfo } from '@/api/system'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const roles = ref<RoleInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const query = reactive<Record<string, any>>({ role_name: '', status: undefined })

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive<Record<string, any>>({ role_name: '', role_key: '', sort: 0, status: 1, remark: '' })
const formRules: FormRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  role_key: [{ required: true, message: '请输入权限字符串', trigger: 'blur' }],
}

async function loadRoles() {
  loading.value = true
  try {
    const res = await getRoleListApi({ ...query, pageNum: pageNum.value, pageSize: pageSize.value })
    roles.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pageNum.value = 1
  loadRoles()
}

function handleReset() {
  query.role_name = ''
  query.status = undefined
  handleSearch()
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, { role_name: '', role_key: '', sort: 0, status: 1, remark: '' })
  dialogVisible.value = true
}

function handleEdit(row: RoleInfo) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, { role_name: row.role_name, role_key: row.role_key, sort: row.sort, status: row.status, remark: row.remark || '' })
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateRoleApi(editId.value, { role_name: form.role_name, sort: form.sort, status: form.status, remark: form.remark })
      ElMessage.success('修改成功')
    } else {
      await addRoleApi({ ...form })
      ElMessage.success('新增角色成功')
    }
    dialogVisible.value = false
    loadRoles()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: RoleInfo) {
  try {
    await deleteRoleApi(row.id)
    ElMessage.success('已删除')
    loadRoles()
  } catch { /* */ }
}

onMounted(loadRoles)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
