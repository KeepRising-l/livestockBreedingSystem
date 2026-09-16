<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">母畜档案<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-alert type="info" :closable="false" show-icon style="max-width: 480px"
        title="仅展示处于「繁育期 / 妊娠」的可繁育母畜，供配种登记时选畜" />
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="耳标">
          <el-input v-model="query.keyword" placeholder="按耳标搜索" clearable style="width: 140px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="生理状态">
          <el-select v-model="query.physio_status" placeholder="全部" clearable style="width: 110px" @change="search">
            <el-option v-for="s in PHYSIO_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
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
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="ear_tag" label="耳标" width="100" />
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="breed" label="品种" min-width="120" />
        <el-table-column prop="growth_stage" label="生长阶段" width="90" />
        <el-table-column label="生理状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.physio_status" size="small" :type="physioTagType(row.physio_status)">{{ row.physio_status }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="圈舍" width="90">
          <template #default="{ row }">{{ row.pen_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column prop="birth_date" label="出生日期" width="110">
          <template #default="{ row }">{{ row.birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="copyTag(row.ear_tag)">复制耳标</el-button>
            <el-button link type="warning" size="small" @click="openStatusDialog(row as BreedAnimal)">设置状态</el-button>
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
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 设置生理状态弹窗 -->
    <el-dialog v-model="statusDialog.visible" title="设置母畜生理状态" width="420px">
      <el-form label-width="80px">
        <el-form-item label="耳标">
          <span>{{ statusDialog.earTag }}</span>
        </el-form-item>
        <el-form-item label="生理状态">
          <el-select v-model="statusDialog.status" placeholder="请选择" style="width: 100%">
            <el-option v-for="s in PHYSIO_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="savingStatus" @click="submitStatus">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { getBreedFemalesApi, setFemalePhysioStatusApi, type BreedAnimal } from '@/api/breeding'
import { SPECIES_OPTIONS, PHYSIO_STATUS_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage } from 'element-plus'

const { species, speciesZh } = useSpecies()

const list = ref<BreedAnimal[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive<{ species: string; keyword: string; physio_status: string }>({
  species: speciesZh.value,
  keyword: '',
  physio_status: '',
})

const savingStatus = ref(false)
const statusDialog = reactive<{ visible: boolean; earTag: string; status: string }>({
  visible: false,
  earTag: '',
  status: '',
})

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.species = speciesZh.value
  query.keyword = ''
  query.physio_status = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.species) params.species = query.species
    if (query.keyword) params.keyword = query.keyword
    if (query.physio_status) params.physio_status = query.physio_status
    const res = await getBreedFemalesApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function physioTagType(status: string): TagProps['type'] {
  return ({ 发情: 'warning', 妊娠: 'success', 泌乳: 'info', 休情: 'primary', 淘汰: 'danger' } as Record<string, TagProps['type']>)[status] || 'info'
}

function openStatusDialog(row: BreedAnimal) {
  statusDialog.earTag = row.ear_tag
  statusDialog.status = row.physio_status || '发情'
  statusDialog.visible = true
}

async function submitStatus() {
  if (!statusDialog.status) {
    ElMessage.warning('请选择生理状态')
    return
  }
  savingStatus.value = true
  try {
    await setFemalePhysioStatusApi(statusDialog.earTag, statusDialog.status)
    ElMessage.success('生理状态已更新')
    statusDialog.visible = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    savingStatus.value = false
  }
}

async function copyTag(tag: string) {
  try {
    await navigator.clipboard.writeText(tag)
    ElMessage.success(`已复制耳标 ${tag}`)
  } catch {
    ElMessage.info(`耳标：${tag}`)
  }
}

onMounted(loadData)

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
