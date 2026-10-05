<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">我的消息</h2>
      <el-button type="primary" plain :disabled="!unreadCount" @click="handleReadAll">全部已读</el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="mb-16">
      <el-form :inline="true" size="default">
        <el-form-item label="状态">
          <el-select v-model="query.is_read" placeholder="全部" clearable style="width: 120px" @change="search">
            <el-option label="未读" :value="0" />
            <el-option label="已读" :value="1" />
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
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_read === 0" type="danger" size="small">未读</el-tag>
            <span v-else class="text-muted">已读</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.message_type === '审核结果' ? 'warning' : 'info'" size="small">{{ row.message_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="content" label="内容" min-width="280" show-overflow-tooltip />
        <el-table-column label="接收时间" width="170">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.is_read === 0" link type="primary" size="small" @click="handleRead(row as SysMessage)">标记已读</el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无消息" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getMessageListApi, getUnreadMessageCountApi,
  markMessageReadApi, markAllMessagesReadApi, type SysMessage,
} from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const list = ref<SysMessage[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const unreadCount = ref(0)
const authStore = useAuthStore()

const query = reactive<{ is_read: number | undefined }>({ is_read: undefined })

function formatTime(t: string | null) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.is_read = undefined
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.is_read !== undefined) params.is_read = query.is_read
    const res = await getMessageListApi(params)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadUnread() {
  try {
    const res = await getUnreadMessageCountApi()
    unreadCount.value = res.data.count || 0
    authStore.unreadCount = unreadCount.value
  } catch {
    // handled
  }
}

async function handleRead(row: SysMessage) {
  try {
    await markMessageReadApi(row.id)
    ElMessage.success('已标记已读')
    loadData()
    loadUnread()
  } catch {
    // handled
  }
}

async function handleReadAll() {
  try {
    await markAllMessagesReadApi()
    ElMessage.success('已全部标记已读')
    loadData()
    loadUnread()
  } catch {
    // handled
  }
}

onMounted(() => {
  loadData()
  loadUnread()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.text-muted { color: #6b8ba4; }
</style>
