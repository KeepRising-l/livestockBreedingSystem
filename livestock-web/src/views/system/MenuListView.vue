<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">菜单管理</h2>
      <el-button type="primary" @click="handleAdd(0)">
        <el-icon><Plus /></el-icon> 新增菜单
      </el-button>
    </div>

    <el-card>
      <el-table
        :data="menus"
        v-loading="loading"
        row-key="id"
        default-expand-all
        :tree-props="{ children: 'children' }"
        stripe
      >
        <el-table-column prop="menu_name" label="菜单名称" min-width="180">
          <template #default="{ row }">
            <el-tag v-if="row.menu_type === 'M'" type="warning" size="small" class="mr-8">目录</el-tag>
            <el-tag v-else-if="row.menu_type === 'C'" size="small" class="mr-8">菜单</el-tag>
            <el-tag v-else type="info" size="small" class="mr-8">按钮</el-tag>
            {{ row.menu_name }}
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路由地址" min-width="140">
          <template #default="{ row }">{{ row.path || '-' }}</template>
        </el-table-column>
        <el-table-column prop="perms" label="权限标识" min-width="160">
          <template #default="{ row }">
            <el-tag v-if="row.perms" type="info" size="small">{{ row.perms }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="icon" label="图标" width="90">
          <template #default="{ row }">{{ row.icon || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="70" />
        <el-table-column label="显示" width="70">
          <template #default="{ row }">
            <el-tag :type="row.visible === 1 ? 'success' : 'info'" size="small">{{ row.visible === 1 ? '显示' : '隐藏' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '正常' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleAdd(row.id)">新增下级</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row as MenuInfo)">编辑</el-button>
            <el-popconfirm title="确定删除该菜单？" @confirm="handleDelete(row as MenuInfo)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑菜单' : '新增菜单'" width="520px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="上级菜单">
          <el-tree-select
            v-model="form.parent_id"
            :data="parentTree"
            node-key="id"
            :props="{ label: 'menu_name', children: 'children' }"
            check-strictly
            :render-after-expand="false"
            style="width: 100%"
            placeholder="不选则为顶级菜单"
          />
        </el-form-item>
        <el-form-item label="菜单类型" prop="menu_type">
          <el-radio-group v-model="form.menu_type">
            <el-radio value="M">目录</el-radio>
            <el-radio value="C">菜单</el-radio>
            <el-radio value="F">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="菜单名称" prop="menu_name">
          <el-input v-model="form.menu_name" placeholder="如：用户管理" />
        </el-form-item>
        <el-form-item label="路由地址" v-if="form.menu_type !== 'F'">
          <el-input v-model="form.path" placeholder="如：user 或 /system" />
        </el-form-item>
        <el-form-item label="组件路径" v-if="form.menu_type === 'C'">
          <el-input v-model="form.component" placeholder="如：system/UserList" />
        </el-form-item>
        <el-form-item label="权限标识" v-if="form.menu_type === 'F' || form.menu_type === 'C'">
          <el-input v-model="form.perms" placeholder="如：system:user:list" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="如：Setting" />
        </el-form-item>
        <el-form-item label="显示顺序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="显示状态">
          <el-radio-group v-model="form.visible">
            <el-radio :value="1">显示</el-radio>
            <el-radio :value="0">隐藏</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
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
import { getMenuListApi, addMenuApi, updateMenuApi, deleteMenuApi, type MenuInfo } from '@/api/system'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const menus = ref<MenuInfo[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive<Record<string, any>>({
  parent_id: 0, menu_type: 'C', menu_name: '', path: '', component: '', perms: '', icon: '', sort: 0, visible: 1, status: 1,
})
const formRules: FormRules = {
  menu_name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  menu_type: [{ required: true, message: '请选择菜单类型', trigger: 'change' }],
}

const parentTree = computed<MenuInfo[]>(() => [
  { id: 0, parent_id: 0, menu_name: '顶级菜单', menu_type: 'M', path: null, component: null, perms: null, icon: null, sort: 0, visible: 1, status: 1, children: menus.value },
])

async function loadMenus() {
  loading.value = true
  try {
    const res = await getMenuListApi()
    menus.value = res.data
  } finally {
    loading.value = false
  }
}

function handleAdd(parentId: number) {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, { parent_id: parentId, menu_type: 'C', menu_name: '', path: '', component: '', perms: '', icon: '', sort: 0, visible: 1, status: 1 })
  dialogVisible.value = true
}

function handleEdit(row: MenuInfo) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    parent_id: row.parent_id, menu_type: row.menu_type, menu_name: row.menu_name,
    path: row.path || '', component: row.component || '', perms: row.perms || '',
    icon: row.icon || '', sort: row.sort, visible: row.visible, status: row.status,
  })
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = {
      parent_id: form.parent_id || 0, menu_type: form.menu_type, menu_name: form.menu_name,
      path: form.path || null, component: form.component || null, perms: form.perms || null,
      icon: form.icon || null, sort: form.sort, visible: form.visible, status: form.status,
    }
    if (isEdit.value) {
      await updateMenuApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addMenuApi(payload)
      ElMessage.success('新增菜单成功')
    }
    dialogVisible.value = false
    loadMenus()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: MenuInfo) {
  try {
    await deleteMenuApi(row.id)
    ElMessage.success('已删除')
    loadMenus()
  } catch { /* */ }
}

onMounted(loadMenus)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mr-8 { margin-right: 8px; }
</style>
