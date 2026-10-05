<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">通知公告</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增公告
      </el-button>
    </div>

    <el-card>
      <el-table :data="notices" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="notice_title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.notice_type === '公告' ? 'danger' : 'info'" size="small">{{ row.notice_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '已发布' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_by" label="发布人" width="100">
          <template #default="{ row }">{{ row.create_by || '-' }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="发布时间" min-width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row as NoticeInfo)">详情</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row as NoticeInfo)">编辑</el-button>
            <el-popconfirm title="确定删除该公告？" @confirm="handleDelete(row as NoticeInfo)">
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
          @size-change="loadNotices"
          @current-change="loadNotices"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑公告' : '新增公告'" width="560px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="标题" prop="notice_title">
          <el-input v-model="form.notice_title" placeholder="公告标题" maxlength="100" />
        </el-form-item>
        <el-form-item label="类型" prop="notice_type">
          <el-radio-group v-model="form.notice_type">
            <el-radio value="公告">公告</el-radio>
            <el-radio value="通知">通知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容" prop="notice_content">
          <el-input v-model="form.notice_content" type="textarea" :rows="6" placeholder="公告内容" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">发布</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="viewVisible" title="公告详情" width="520px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="标题">{{ viewData.notice_title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ viewData.notice_type }}</el-descriptions-item>
        <el-descriptions-item label="发布人">{{ viewData.create_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发布时间">{{ viewData.create_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div class="notice-content">{{ viewData.notice_content || '-' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getNoticeListApi, addNoticeApi, updateNoticeApi, deleteNoticeApi, getNoticeApi, type NoticeInfo } from '@/api/system'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const notices = ref<NoticeInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive<Record<string, any>>({ notice_title: '', notice_type: '公告', notice_content: '', status: 1 })
const formRules: FormRules = {
  notice_title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

const viewVisible = ref(false)
const viewData = reactive<Partial<NoticeInfo>>({})

async function loadNotices() {
  loading.value = true
  try {
    const res = await getNoticeListApi({ pageNum: pageNum.value, pageSize: pageSize.value })
    notices.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, { notice_title: '', notice_type: '公告', notice_content: '', status: 1 })
  dialogVisible.value = true
}

function handleEdit(row: NoticeInfo) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, { notice_title: row.notice_title, notice_type: row.notice_type, notice_content: row.notice_content || '', status: row.status })
  dialogVisible.value = true
}

async function handleView(row: NoticeInfo) {
  try {
    const res = await getNoticeApi(row.id)
    Object.assign(viewData, res.data)
    viewVisible.value = true
  } catch { /* */ }
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateNoticeApi(editId.value, {
        notice_title: form.notice_title, notice_type: form.notice_type,
        notice_content: form.notice_content, status: form.status,
      })
      ElMessage.success('修改成功')
    } else {
      await addNoticeApi({
        notice_title: form.notice_title, notice_type: form.notice_type,
        notice_content: form.notice_content, status: form.status,
      })
      ElMessage.success('发布成功')
    }
    dialogVisible.value = false
    loadNotices()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: NoticeInfo) {
  try {
    await deleteNoticeApi(row.id)
    ElMessage.success('已删除')
    loadNotices()
  } catch { /* */ }
}

onMounted(loadNotices)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.notice-content { white-space: pre-wrap; line-height: 1.7; }
</style>
