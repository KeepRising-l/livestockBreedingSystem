<template>
  <div>
    <h2 class="page-title">字典管理</h2>

    <el-row :gutter="16">
      <!-- 左侧：字典类型 -->
      <el-col :span="9">
        <el-card>
          <template #header>
            <div class="flex-between">
              <span>字典类型</span>
              <el-button type="primary" size="small" @click="handleAddType" v-if="isAdmin">
                <el-icon><Plus /></el-icon> 新增
              </el-button>
            </div>
          </template>

          <el-input v-model="typeQuery.dict_name" placeholder="搜索类型名称" clearable size="small" class="mb-12" @keyup.enter="loadTypeList">
            <template #append>
              <el-button @click="loadTypeList">查</el-button>
            </template>
          </el-input>

          <el-table
            :data="typeList"
            v-loading="typeLoading"
            highlight-current-row
            @current-change="handleTypeSelect"
            size="small"
            :max-height="520"
          >
            <el-table-column prop="dict_name" label="名称" min-width="100" />
            <el-table-column prop="dict_type" label="类型标识" min-width="120">
              <template #default="{ row }">
                <span style="font-family: monospace; font-size: 12px;">{{ row.dict_type }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="70">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '正常' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" v-if="isAdmin">
              <template #default="{ row }">
                <el-button link type="warning" size="small" @click.stop="handleEditType(row as DictTypeInfo)">编</el-button>
                <el-popconfirm title="删除类型？其下有数据时无法删除" @confirm="handleDeleteType(row.id)" v-if="isAdmin">
                  <template #reference>
                    <el-button link type="danger" size="small" @click.stop>删</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="text-right mt-12">
            <el-pagination
              v-model:current-page="typePageNum"
              v-model:page-size="typePageSize"
              :total="typeTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, prev, pager, next"
              small
              @size-change="loadTypeList"
              @current-change="loadTypeList"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：字典数据 -->
      <el-col :span="15">
        <el-card>
          <template #header>
            <div class="flex-between">
              <span>
                字典数据
                <el-tag v-if="currentType" type="primary" size="small" class="ml-8">{{ currentType.dict_type }}</el-tag>
                <span v-if="currentType" class="text-gray ml-8" style="font-size:12px;">{{ currentType.dict_name }}</span>
              </span>
              <el-button type="primary" size="small" @click="handleAddData" v-if="isAdmin && currentType">
                <el-icon><Plus /></el-icon> 新增数据
              </el-button>
            </div>
          </template>

          <div v-if="!currentType" class="text-center text-gray" style="padding: 60px 0;">
            <el-icon size="32"><ArrowLeft /></el-icon>
            <p class="mt-8">请从左侧选择一个字典类型</p>
          </div>

          <template v-else>
            <el-input v-model="dataQuery.dict_label" placeholder="搜索标签" clearable size="small" class="mb-12" @keyup.enter="loadDataList">
              <template #append>
                <el-button @click="loadDataList">查</el-button>
              </template>
            </el-input>

            <el-table :data="dataList" v-loading="dataLoading" size="small" :max-height="460">
              <el-table-column prop="dict_sort" label="排序" width="60" />
              <el-table-column prop="dict_label" label="标签" min-width="100" />
              <el-table-column prop="dict_value" label="键值" min-width="120">
                <template #default="{ row }">
                  <span style="font-family: monospace; font-size: 12px;">{{ row.dict_value }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="dict_extra" label="扩展信息" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.dict_extra" style="font-family: monospace; font-size: 12px;">{{ row.dict_extra }}</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                    {{ row.status === 1 ? '正常' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" v-if="isAdmin">
                <template #default="{ row }">
                  <el-button link type="warning" size="small" @click="handleEditData(row as DictDataInfo)">编</el-button>
                  <el-popconfirm title="确定删除该字典数据？" @confirm="handleDeleteData(row.id)" v-if="isAdmin">
                    <template #reference>
                      <el-button link type="danger" size="small" @click.stop>删</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
            <div class="text-right mt-12">
              <el-pagination
                v-model:current-page="dataPageNum"
                v-model:page-size="dataPageSize"
                :total="dataTotal"
                :page-sizes="[20, 50, 100]"
                layout="total, sizes, prev, pager, next"
                small
                @size-change="loadDataList"
                @current-change="loadDataList"
              />
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 字典类型新增/编辑 -->
    <el-dialog v-model="typeDialog" :title="typeIsEdit ? '编辑字典类型' : '新增字典类型'" width="480px">
      <el-form :model="typeForm" :rules="typeRules" ref="typeFormRef" label-width="90px">
        <el-form-item label="名称" prop="dict_name">
          <el-input v-model="typeForm.dict_name" placeholder="如：用户类型" />
        </el-form-item>
        <el-form-item label="类型标识" prop="dict_type">
          <el-input v-model="typeForm.dict_type" placeholder="如：sys_user_type" :disabled="typeIsEdit" />
          <div style="color:#6b8ba4;font-size:12px;">规范：sys_ 前缀 + 下划线分隔，创建后不可修改</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="typeForm.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="typeForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialog = false">取消</el-button>
        <el-button type="primary" :loading="typeSaving" @click="handleSaveType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 字典数据新增/编辑 -->
    <el-dialog v-model="dataDialog" :title="dataIsEdit ? '编辑字典数据' : '新增字典数据'" width="480px">
      <el-form :model="dataForm" :rules="dataRules" ref="dataFormRef" label-width="90px">
        <el-form-item label="所属类型">
          <el-input :model-value="currentType?.dict_type" disabled />
        </el-form-item>
        <el-form-item label="标签" prop="dict_label">
          <el-input v-model="dataForm.dict_label" placeholder="显示文本" />
        </el-form-item>
        <el-form-item label="键值" prop="dict_value">
          <el-input v-model="dataForm.dict_value" placeholder="存储值" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="dataForm.dict_sort" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="扩展信息">
          <el-input v-model="dataForm.dict_extra" type="textarea" :rows="2" placeholder='JSON 格式，如 {"species":"cattle"}' />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="dataForm.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dataDialog = false">取消</el-button>
        <el-button type="primary" :loading="dataSaving" @click="handleSaveData">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  getDictTypeListApi, addDictTypeApi, updateDictTypeApi, deleteDictTypeApi,
  getDictDataListApi, addDictDataApi, updateDictDataApi, deleteDictDataApi,
  type DictTypeInfo, type DictDataInfo,
} from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.userType === 1)

// ===== 字典类型 =====
const typeList = ref<DictTypeInfo[]>([])
const typeLoading = ref(false)
const typePageNum = ref(1)
const typePageSize = ref(20)
const typeTotal = ref(0)
const typeQuery = reactive({ dict_name: '', dict_type: '', status: undefined as number | undefined })
const currentType = ref<DictTypeInfo | null>(null)

const typeDialog = ref(false)
const typeIsEdit = ref(false)
const typeSaving = ref(false)
const typeFormRef = ref<FormInstance>()
const typeEditId = ref(0)
const typeForm = reactive({
  dict_name: '', dict_type: '', status: 1, remark: '',
})
const typeRules: FormRules = {
  dict_name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  dict_type: [{ required: true, message: '请输入类型标识', trigger: 'blur' }],
}

async function loadTypeList() {
  typeLoading.value = true
  try {
    const params: any = { pageNum: typePageNum.value, pageSize: typePageSize.value }
    if (typeQuery.dict_name) params.dict_name = typeQuery.dict_name
    if (typeQuery.dict_type) params.dict_type = typeQuery.dict_type
    if (typeQuery.status !== undefined) params.status = typeQuery.status
    const res = await getDictTypeListApi(params)
    const data = res.data as any
    typeList.value = data.list || []
    typeTotal.value = data.total || 0
  } catch {} finally { typeLoading.value = false }
}

function handleTypeSelect(row: DictTypeInfo | null) {
  currentType.value = row
  if (row) {
    dataPageNum.value = 1
    loadDataList()
  }
}

function handleAddType() {
  typeIsEdit.value = false
  typeEditId.value = 0
  Object.assign(typeForm, { dict_name: '', dict_type: '', status: 1, remark: '' })
  typeDialog.value = true
}

function handleEditType(row: DictTypeInfo) {
  typeIsEdit.value = true
  typeEditId.value = row.id
  Object.assign(typeForm, {
    dict_name: row.dict_name, dict_type: row.dict_type,
    status: row.status, remark: row.remark || '',
  })
  typeDialog.value = true
}

async function handleSaveType() {
  const valid = await typeFormRef.value?.validate().catch(() => false)
  if (!valid) return
  typeSaving.value = true
  try {
    const payload: any = { ...typeForm }
    if (typeIsEdit.value) {
      delete payload.dict_type
      await updateDictTypeApi(typeEditId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addDictTypeApi(payload)
      ElMessage.success('添加成功')
    }
    typeDialog.value = false
    loadTypeList()
  } catch {} finally { typeSaving.value = false }
}

async function handleDeleteType(id: number) {
  try {
    await deleteDictTypeApi(id)
    ElMessage.success('删除成功')
    if (currentType.value?.id === id) {
      currentType.value = null
      dataList.value = []
    }
    loadTypeList()
  } catch {}
}

// ===== 字典数据 =====
const dataList = ref<DictDataInfo[]>([])
const dataLoading = ref(false)
const dataPageNum = ref(1)
const dataPageSize = ref(50)
const dataTotal = ref(0)
const dataQuery = reactive({ dict_label: '' })

const dataDialog = ref(false)
const dataIsEdit = ref(false)
const dataSaving = ref(false)
const dataFormRef = ref<FormInstance>()
const dataEditId = ref(0)
const dataForm = reactive({
  dict_label: '', dict_value: '', dict_sort: 0, dict_extra: '', status: 1,
})
const dataRules: FormRules = {
  dict_label: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  dict_value: [{ required: true, message: '请输入键值', trigger: 'blur' }],
}

async function loadDataList() {
  if (!currentType.value) return
  dataLoading.value = true
  try {
    const params: any = {
      dict_type: currentType.value.dict_type,
      pageNum: dataPageNum.value, pageSize: dataPageSize.value,
    }
    if (dataQuery.dict_label) params.dict_label = dataQuery.dict_label
    const res = await getDictDataListApi(params)
    const data = res.data as any
    dataList.value = data.list || []
    dataTotal.value = data.total || 0
  } catch {} finally { dataLoading.value = false }
}

function handleAddData() {
  dataIsEdit.value = false
  dataEditId.value = 0
  Object.assign(dataForm, { dict_label: '', dict_value: '', dict_sort: 0, dict_extra: '', status: 1 })
  dataDialog.value = true
}

function handleEditData(row: DictDataInfo) {
  dataIsEdit.value = true
  dataEditId.value = row.id
  Object.assign(dataForm, {
    dict_label: row.dict_label, dict_value: row.dict_value,
    dict_sort: row.dict_sort, dict_extra: row.dict_extra || '',
    status: row.status,
  })
  dataDialog.value = true
}

async function handleSaveData() {
  const valid = await dataFormRef.value?.validate().catch(() => false)
  if (!valid) return
  dataSaving.value = true
  try {
    const payload: any = { ...dataForm }
    if (payload.dict_extra === '') delete payload.dict_extra
    if (dataIsEdit.value) {
      await updateDictDataApi(dataEditId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addDictDataApi({ ...payload, dict_type: currentType.value!.dict_type })
      ElMessage.success('添加成功')
    }
    dataDialog.value = false
    loadDataList()
  } catch {} finally { dataSaving.value = false }
}

async function handleDeleteData(id: number) {
  try {
    await deleteDictDataApi(id)
    ElMessage.success('删除成功')
    loadDataList()
  } catch {}
}

onMounted(loadTypeList)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #0e2f47; }
.mb-12 { margin-bottom: 12px; }
.mt-8 { margin-top: 8px; }
.mt-12 { margin-top: 12px; }
.ml-8 { margin-left: 8px; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-gray { color: #6b8ba4; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
