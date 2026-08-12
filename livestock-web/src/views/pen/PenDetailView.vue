<template>
  <div>
    <el-button link type="primary" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon> 返回
    </el-button>
    <h2 class="page-title mt-16">圈舍详情</h2>

    <el-card class="mb-16" v-loading="loading">
      <template v-if="pen">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="圈舍编号">{{ pen.pen_code }}</el-descriptions-item>
          <el-descriptions-item label="圈舍类型">
            <el-tag>{{ PEN_TYPE_MAP[pen.pen_type] || pen.pen_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="pen.status === 1 ? 'success' : 'info'">{{ pen.status === 1 ? '正常' : '空闲' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="容量">{{ pen.capacity }}</el-descriptions-item>
          <el-descriptions-item label="当前存栏">{{ pen.current_count }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ pen.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-progress
          class="mt-16"
          :percentage="pen.capacity ? Math.min(100, Math.round(pen.current_count / pen.capacity * 100)) : 0"
          :stroke-width="20"
          text-inside
          :status="pen.current_count >= pen.capacity ? 'success' : undefined"
          :format="progressFormat"
        />
      </template>
    </el-card>

    <h3 class="section-title">圈舍内畜禽</h3>
    <el-card>
      <el-table :data="animals" v-loading="animalLoading" stripe>
        <el-table-column prop="ear_tag" label="耳标" width="100" />
        <el-table-column prop="species" label="畜种" width="60" />
        <el-table-column prop="breed" label="品种" width="140" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="growth_stage" label="生长阶段" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '在栏' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="in_date" label="入栏日期" width="120" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="router.push(`/animal/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!animalLoading && animals.length === 0" description="暂无畜禽" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPenDetailApi, getPenAnimalsApi, type PenInfo } from '@/api/pen'
import { PEN_TYPE_MAP } from '@/utils/constants'
import type { AnimalInfo } from '@/api/animal'

const route = useRoute()
const router = useRouter()

const pen = ref<PenInfo | null>(null)
const animals = ref<AnimalInfo[]>([])
const loading = ref(false)
const animalLoading = ref(false)

async function loadPen() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getPenDetailApi(id)
    pen.value = res.data as any
  } catch {
    router.back()
  } finally {
    loading.value = false
  }
}

async function loadAnimals() {
  animalLoading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getPenAnimalsApi(id, { pageNum: 1, pageSize: 100 })
    const data = res.data as any
    animals.value = data.list || data || []
  } catch {
    // handled
  } finally {
    animalLoading.value = false
  }
}

function progressFormat(percentage: number) {
  if (pen.value && pen.value.current_count >= pen.value.capacity) return '已住满'
  return `${percentage}%`
}

onMounted(() => {
  loadPen()
  loadAnimals()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.section-title { font-size: 16px; font-weight: 600; margin: 20px 0 12px; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
</style>
