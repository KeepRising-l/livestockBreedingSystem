<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">公畜档案<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-alert type="info" :closable="false" show-icon style="max-width: 520px"
        title="仅展示处于「繁育期 / 妊娠」的可繁育公畜；健康状态/使用年限/配种记录为缺口4 新增能力" />
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
        <el-table-column prop="ear_tag" label="耳标" width="90" />
        <el-table-column prop="species" label="畜种" width="60" />
        <el-table-column prop="breed" label="品种" min-width="110" />
        <el-table-column label="圈舍" width="70">
          <template #default="{ row }">{{ row.pen_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="birth_date" label="出生日期" width="105">
          <template #default="{ row }">{{ row.birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="健康状态" width="90">
          <template #default="{ row }">
            <el-tag :type="healthColor(row.health_status)" size="small">{{ row.health_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="使用年限" width="90">
          <template #default="{ row }">
            <span v-if="row.service_years !== null && row.service_years !== undefined">{{ row.service_years }} 年</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="配种次数" width="110">
          <template #default="{ row }">
            <span v-if="row.success_count">{{ row.success_count }} 成功</span>
            <span v-if="row.mating_count"> / 共 {{ row.mating_count }} 次</span>
            <span v-if="!row.mating_count">-</span>
          </template>
        </el-table-column>
        <el-table-column label="最近配种" width="105">
          <template #default="{ row }">{{ row.last_mating_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="copyTag(row.ear_tag)">复制耳标</el-button>
            <el-button link type="warning" size="small" @click="openHealth(row as BreedMale)">健康档案</el-button>
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

    <!-- 编辑健康档案弹窗 -->
    <el-dialog v-model="healthVisible" :title="`公畜健康档案 - ${healthForm.ear_tag}`" width="480px">
      <el-form :model="healthForm" label-width="100px">
        <el-form-item label="健康状态" prop="health_status">
          <el-select v-model="healthForm.health_status" placeholder="请选择" style="width: 100%">
            <el-option v-for="h in HEALTH_STATUS_OPTIONS" :key="h" :label="h" :value="h" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用日期">
          <el-date-picker v-model="healthForm.use_start_date" type="date" value-format="YYYY-MM-DD"
            style="width: 100%" placeholder="使用年限计算起点" />
        </el-form-item>
        <el-form-item label="精液质量">
          <el-input v-model="healthForm.semen_quality" placeholder="如：活力良好（选填）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="healthForm.remark" type="textarea" :rows="2" placeholder="备注说明（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="healthVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveHealth">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getBreedMalesApi, updateMaleHealthApi, type BreedMale } from '@/api/breeding'
import { SPECIES_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type TagProps } from 'element-plus'

const { species, speciesZh } = useSpecies()

const HEALTH_STATUS_OPTIONS = ['健康', '亚健康', '淘汰']
const HEALTH_COLOR_MAP: Record<string, TagProps['type']> = {
  '健康': 'success', '亚健康': 'warning', '淘汰': 'danger',
}

const list = ref<BreedMale[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive<{ species: string; keyword: string }>({ species: speciesZh.value, keyword: '' })

const healthVisible = ref(false)
const saving = ref(false)
const healthForm = reactive({
  ear_tag: '',
  health_status: '健康',
  use_start_date: undefined as string | undefined,
  semen_quality: '',
  remark: '',
})

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.species = speciesZh.value
  query.keyword = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.species) params.species = query.species
    if (query.keyword) params.keyword = query.keyword
    const res = await getBreedMalesApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function healthColor(s: string): TagProps['type'] {
  return HEALTH_COLOR_MAP[s] || 'info'
}

function openHealth(row: BreedMale) {
  healthForm.ear_tag = row.ear_tag
  healthForm.health_status = row.health_status || '健康'
  healthForm.use_start_date = row.use_start_date || undefined
  healthForm.semen_quality = row.semen_quality || ''
  healthForm.remark = row.health_remark || ''
  healthVisible.value = true
}

async function saveHealth() {
  saving.value = true
  try {
    const payload: any = {
      health_status: healthForm.health_status,
      use_start_date: healthForm.use_start_date,
      semen_quality: healthForm.semen_quality || undefined,
      remark: healthForm.remark || undefined,
    }
    await updateMaleHealthApi(healthForm.ear_tag, payload)
    ElMessage.success('健康档案已更新')
    healthVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
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
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
