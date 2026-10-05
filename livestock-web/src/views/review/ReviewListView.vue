<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">审核中心</h2>
      <el-alert v-if="!canAudit" type="info" :closable="false" show-icon
        title="员工只能查看待审核记录，审核需养殖场主权限" />
    </div>

    <el-card>
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane name="all">
          <template #label>
            全部 <el-badge v-if="counts.total" :value="counts.total" type="danger" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane v-for="(name, bt) in TABS" :key="bt" :name="bt">
          <template #label>
            {{ name }} <el-badge v-if="tabCount(bt)" :value="tabCount(bt)" type="danger" class="tab-badge" />
          </template>
        </el-tab-pane>
      </el-tabs>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="类型" width="100" v-if="activeTab === 'all'">
          <template #default="{ row }">
            <el-tag size="small">{{ row.business_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容摘要" min-width="260">
          <template #default="{ row }">
            <span>{{ row.summary }}</span>
            <el-tooltip placement="top" :content="JSON.stringify(row.detail || {})">
              <el-icon class="detail-icon"><InfoFilled /></el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="提交人" width="110">
          <template #default="{ row }">{{ row.operator_name || row.operator_user_id || '-' }}</template>
        </el-table-column>
        <el-table-column label="提交时间" width="170">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" v-if="canAudit">
          <template #default="{ row }">
            <el-button link type="success" size="small" @click.stop="handleAudit(row as ReviewItem, '通过')">通过</el-button>
            <el-button link type="danger" size="small" @click.stop="handleAudit(row as ReviewItem, '驳回')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="text-right mt-16" v-if="activeTab !== 'all'">
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
      <el-empty v-if="!loading && !list.length" description="暂无待审核记录" />
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog v-model="auditDialogVisible" :title="`审核 - ${auditAction}`" width="420px">
      <el-form :model="auditForm" label-width="80px">
        <el-form-item label="记录">
          <div class="c-gray">{{ auditTarget?.summary }}</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="auditForm.remark" type="textarea" :rows="3" placeholder="审核备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button :type="auditAction === '通过' ? 'success' : 'danger'" :loading="auditSaving" @click="confirmAudit">
          确认{{ auditAction }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  getReviewCountsApi, getReviewListApi, getReviewPendingApi, auditReviewApi,
  type ReviewItem, type ReviewCounts, type BusinessType,
} from '@/api/review'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const canAudit = computed(() => authStore.userType !== 3)

const TABS: Record<string, string> = {
  feeding: '饲喂记录',
  purchase: '进货记录',
  consume: '领用记录',
  vaccine: '防疫记录',
  medical: '诊疗记录',
  mating: '配种记录',
}

const activeTab = ref('all')
const list = ref<ReviewItem[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const counts = reactive<ReviewCounts>({ feeding: 0, purchase: 0, consume: 0, vaccine: 0, medical: 0, mating: 0, total: 0 })

const auditDialogVisible = ref(false)
const auditAction = ref<'通过' | '驳回'>('通过')
const auditSaving = ref(false)
const auditTarget = ref<ReviewItem | null>(null)
const auditForm = reactive({ remark: '' })

function formatTime(t: string | null) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

function tabCount(bt: string) {
  return (counts as any)[bt] || 0
}

async function loadCounts() {
  try {
    const res = await getReviewCountsApi()
    Object.assign(counts, res.data)
  } catch {
    // handled by interceptor
  }
}

async function loadData() {
  loading.value = true
  try {
    if (activeTab.value === 'all') {
      const res = await getReviewPendingApi({ limit: 100 })
      const data = res.data as any
      list.value = data.list || []
      total.value = data.total || 0
    } else {
      const res = await getReviewListApi({
        business_type: activeTab.value as BusinessType,
        pageNum: pageNum.value,
        pageSize: pageSize.value,
      })
      const data = res.data as any
      list.value = data.list || []
      total.value = data.total || 0
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function onTabChange() {
  pageNum.value = 1
  loadData()
}

function handleAudit(row: ReviewItem, action: '通过' | '驳回') {
  auditTarget.value = row
  auditAction.value = action
  auditForm.remark = ''
  auditDialogVisible.value = true
}

async function confirmAudit() {
  if (!auditTarget.value) return
  auditSaving.value = true
  try {
    const payload: any = {
      business_type: auditTarget.value.business_type,
      business_id: auditTarget.value.id,
      audit_status: auditAction.value,
    }
    if (auditForm.remark) payload.remark = auditForm.remark
    await auditReviewApi(payload)
    ElMessage.success(`已${auditAction.value}`)
    auditDialogVisible.value = false
    loadCounts()
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    auditSaving.value = false
  }
}

onMounted(() => {
  loadCounts()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.tab-badge { margin-left: 4px; }
.detail-icon { margin-left: 6px; cursor: help; color: #64748b; vertical-align: -2px; }
.c-gray { color: #475569; }
</style>
