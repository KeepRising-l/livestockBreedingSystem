<template>
  <div>
    <el-button link type="primary" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon> 返回
    </el-button>
    <h2 class="page-title mt-16">圈舍详情<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>

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
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="router.push(`/${species}/animal/${row.id}`)">详情</el-button>
            <el-button link type="warning" size="small" @click="openTransfer(row as AnimalInfo)">转舍</el-button>
            <el-popconfirm title="移出后该畜禽不再属于任何圈舍，重新入舍时耳标将自动更新，确定移出？"
              @confirm="handleRemove(row as AnimalInfo)">
              <template #reference>
                <el-button link type="danger" size="small">移出</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!animalLoading && animals.length === 0" description="暂无畜禽" />
    </el-card>

    <!-- 转入其他圈舍弹窗 -->
    <el-dialog v-model="transferVisible" :title="`转入其他圈舍 - ${transferAnimal?.ear_tag}`" width="480px">
      <el-form label-width="90px">
        <el-form-item label="目标圈舍">
          <el-select v-model="targetPenId" placeholder="请选择目标圈舍" filterable style="width: 100%">
            <el-option v-for="p in penOptions" :key="p.id" :value="p.id"
              :label="`${p.pen_code}（${PEN_TYPE_MAP[p.pen_type] || p.pen_type} ${p.current_count}/${p.capacity}）`"
              :disabled="p.current_count >= p.capacity" />
          </el-select>
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon
          title="转入后耳标将按新圈舍重新生成（前两位=圈舍号，后两位=序号）" />
      </el-form>
      <template #footer>
        <el-button @click="transferVisible = false">取消</el-button>
        <el-button type="primary" :loading="transferSaving" @click="handleTransfer">确认转入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPenDetailApi, getPenAnimalsApi, getPenListApi, type PenInfo } from '@/api/pen'
import { transferAnimalApi, removeFromPenApi, type AnimalInfo } from '@/api/animal'
import { PEN_TYPE_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const { species, speciesZh } = useSpecies()

const pen = ref<PenInfo | null>(null)
const animals = ref<AnimalInfo[]>([])
const loading = ref(false)
const animalLoading = ref(false)

const transferVisible = ref(false)
const transferSaving = ref(false)
const transferAnimal = ref<AnimalInfo | null>(null)
const targetPenId = ref<number>()
const penOptions = ref<PenInfo[]>([])

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
    const res = await getPenAnimalsApi(id, { pageNum: 1, pageSize: 100, species: speciesZh.value } as any)
    const data = res.data as any
    animals.value = data.list || data || []
  } catch {
    // handled
  } finally {
    animalLoading.value = false
  }
}

async function loadPenOptions() {
  try {
    const res = await getPenListApi({ pageNum: 1, pageSize: 100 } as any)
    const data = res.data as any
    penOptions.value = (data.list || []).filter((p: PenInfo) => p.id !== pen.value?.id)
  } catch {
    // handled
  }
}

function openTransfer(row: AnimalInfo) {
  transferAnimal.value = row
  targetPenId.value = undefined
  transferVisible.value = true
  loadPenOptions()
}

async function handleTransfer() {
  if (!transferAnimal.value || !targetPenId.value) {
    ElMessage.warning('请选择目标圈舍')
    return
  }
  transferSaving.value = true
  try {
    await transferAnimalApi(transferAnimal.value.id, targetPenId.value)
    ElMessage.success('转舍成功，耳标已更新')
    transferVisible.value = false
    loadPen()
    loadAnimals()
  } catch {
    // handled
  } finally {
    transferSaving.value = false
  }
}

async function handleRemove(row: AnimalInfo) {
  try {
    await removeFromPenApi(row.id)
    ElMessage.success(`耳标 ${row.ear_tag} 已移出圈舍`)
    loadPen()
    loadAnimals()
  } catch {
    // handled
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
.page-title { font-size: 20px; font-weight: 600; color: #eaf6ff; }
.section-title { font-size: 16px; font-weight: 600; margin: 20px 0 12px; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
</style>
