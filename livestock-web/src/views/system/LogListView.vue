<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">日志管理</h2>
      <el-button type="danger" plain @click="handleClear">
        <el-icon><Delete /></el-icon> 清空{{ activeTab === 'oper' ? '操作' : '登录' }}日志
      </el-button>
    </div>

    <el-card>
      <el-tabs v-model="activeTab">
        <!-- 操作日志 -->
        <el-tab-pane label="操作日志" name="oper">
          <el-form inline class="mb-16" @submit.prevent>
            <el-form-item label="操作人">
              <el-input v-model="operQuery.username" placeholder="操作账号" clearable style="width: 160px" @keyup.enter="handleSearch" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="operQuery.status" placeholder="全部" clearable style="width: 110px">
                <el-option label="成功" :value="1" />
                <el-option label="失败" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">查询</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="operLogs" v-loading="operLoading" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="oper_name" label="操作人" width="100" />
            <el-table-column prop="method" label="方式" width="70">
              <template #default="{ row }">
                <el-tag :type="row.method === 'DELETE' ? 'danger' : row.method === 'PUT' ? 'warning' : 'primary'" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作功能" min-width="180">
              <template #default="{ row }">
                <el-tooltip :content="row.oper_url || ''" placement="top" :disabled="!row.oper_url">
                  <span>{{ row.title || row.oper_url || '-' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="business_type" label="业务类型" width="90">
              <template #default="{ row }">{{ row.business_type || '-' }}</template>
            </el-table-column>
            <el-table-column prop="oper_ip" label="IP" width="130">
              <template #default="{ row }">{{ row.oper_ip || '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="70">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '成功' : '失败' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_msg" label="错误信息" min-width="150">
              <template #default="{ row }">
                <el-tooltip v-if="row.error_msg" :content="row.error_msg" placement="top">
                  <span class="ellipsis">{{ row.error_msg }}</span>
                </el-tooltip>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作时间" min-width="160">
              <template #default="{ row }">{{ formatTime(row.oper_time) }}</template>
            </el-table-column>
          </el-table>
          <div class="text-right mt-16">
            <el-pagination
              v-model:current-page="operPage"
              v-model:page-size="operSize"
              :total="operTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadOperLogs"
              @current-change="loadOperLogs"
            />
          </div>
        </el-tab-pane>

        <!-- 登录日志 -->
        <el-tab-pane label="登录日志" name="login">
          <el-form inline class="mb-16" @submit.prevent>
            <el-form-item label="账号">
              <el-input v-model="loginQuery.username" placeholder="登录账号" clearable style="width: 160px" @keyup.enter="handleSearch" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="loginQuery.status" placeholder="全部" clearable style="width: 110px">
                <el-option label="成功" :value="1" />
                <el-option label="失败" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">查询</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="loginLogs" v-loading="loginLoading" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="账号" width="120" />
            <el-table-column label="状态" width="70">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '成功' : '失败' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ip" label="IP" width="130">
              <template #default="{ row }">{{ row.ip || '-' }}</template>
            </el-table-column>
            <el-table-column prop="browser" label="浏览器" width="90">
              <template #default="{ row }">{{ row.browser || '-' }}</template>
            </el-table-column>
            <el-table-column prop="os" label="操作系统" width="90">
              <template #default="{ row }">{{ row.os || '-' }}</template>
            </el-table-column>
            <el-table-column prop="msg" label="消息" min-width="160">
              <template #default="{ row }">{{ row.msg || '-' }}</template>
            </el-table-column>
            <el-table-column label="登录时间" min-width="160">
              <template #default="{ row }">{{ formatTime(row.login_time) }}</template>
            </el-table-column>
          </el-table>
          <div class="text-right mt-16">
            <el-pagination
              v-model:current-page="loginPage"
              v-model:page-size="loginSize"
              :total="loginTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadLoginLogs"
              @current-change="loadLoginLogs"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import {
  getOperLogListApi, clearOperLogApi,
  getLoginLogListApi, clearLoginLogApi,
  type OperLogInfo, type LoginLogInfo,
} from '@/api/system'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref<'oper' | 'login'>('oper')

const operLogs = ref<OperLogInfo[]>([])
const operLoading = ref(false)
const operPage = ref(1)
const operSize = ref(10)
const operTotal = ref(0)
const operQuery = reactive<Record<string, any>>({ username: '', status: undefined })

const loginLogs = ref<LoginLogInfo[]>([])
const loginLoading = ref(false)
const loginPage = ref(1)
const loginSize = ref(10)
const loginTotal = ref(0)
const loginQuery = reactive<Record<string, any>>({ username: '', status: undefined })

/** 把 ISO 时间字符串（如 2026-09-01T21:42:28.123456）格式化成可读形式（2026-09-01 21:42:28） */
function formatTime(t: string | null | undefined) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

async function loadOperLogs() {
  operLoading.value = true
  try {
    const res = await getOperLogListApi({ ...operQuery, pageNum: operPage.value, pageSize: operSize.value })
    operLogs.value = res.data.list
    operTotal.value = res.data.total
  } finally {
    operLoading.value = false
  }
}

async function loadLoginLogs() {
  loginLoading.value = true
  try {
    const res = await getLoginLogListApi({ ...loginQuery, pageNum: loginPage.value, pageSize: loginSize.value })
    loginLogs.value = res.data.list
    loginTotal.value = res.data.total
  } finally {
    loginLoading.value = false
  }
}

function handleSearch() {
  if (activeTab.value === 'oper') {
    operPage.value = 1
    loadOperLogs()
  } else {
    loginPage.value = 1
    loadLoginLogs()
  }
}

async function handleClear() {
  const label = activeTab.value === 'oper' ? '操作' : '登录'
  try {
    await ElMessageBox.confirm(`确定清空全部${label}日志？该操作不可恢复`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    if (activeTab.value === 'oper') {
      await clearOperLogApi()
      loadOperLogs()
    } else {
      await clearLoginLogApi()
      loadLoginLogs()
    }
    ElMessage.success(`${label}日志已清空`)
  } catch { /* */ }
}

watch(activeTab, () => handleSearch())

onMounted(() => {
  loadOperLogs()
  loadLoginLogs()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.ellipsis { display: inline-block; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle; }
</style>
