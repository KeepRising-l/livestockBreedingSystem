<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">畜禽档案<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <div>
        <el-button type="success" @click="router.push(`/${species}/animal/individual-entry`)">
          <el-icon><Plus /></el-icon> 个体入栏
        </el-button>
        <el-button type="warning" @click="router.push(`/${species}/animal/batch-entry`)">
          <el-icon><Upload /></el-icon> 批量入栏
        </el-button>
        <el-popconfirm title="确定批量删除选中档案？" @confirm="handleBatchDelete" v-if="selectedIds.length">
          <template #reference>
            <el-button type="danger" :disabled="!selectedIds.length">
              批量删除 ({{ selectedIds.length }})
            </el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="耳标">
          <el-input v-model="query.ear_tag" placeholder="模糊搜索" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="query.breed" placeholder="品种" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="query.gender" placeholder="全部" clearable style="width: 100px">
            <el-option v-for="g in GENDER_OPTIONS" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="(label, key) in ANIMAL_STATUS_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 档案列表 -->
    <el-card>
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        @selection-change="(rows: AnimalInfo[]) => selectedIds = rows.map(r => r.id)"
        @row-click="(row: AnimalInfo) => router.push(`/${species}/animal/${row.id}`)"
        style="cursor: pointer"
      >
        <el-table-column type="selection" width="50" @click.stop />
        <el-table-column prop="ear_tag" label="耳标" width="100" />
        <el-table-column prop="species" label="畜种" width="60" />
        <el-table-column prop="breed" label="品种" width="140" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="growth_stage" label="生长阶段" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.growth_stage" size="small" type="success">{{ row.growth_stage }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '在栏' ? 'success' : row.status === '已出栏' ? 'info' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="80" />
        <el-table-column prop="birth_date" label="出生日期" width="120" />
        <el-table-column prop="in_date" label="入栏日期" width="120" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="router.push(`/${species}/animal/${row.id}`)">详情</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAnimalListApi, batchDeleteAnimalApi, type AnimalInfo } from '@/api/animal'
import { GENDER_OPTIONS, ANIMAL_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage } from 'element-plus'

const router = useRouter()
const { species, speciesZh } = useSpecies()

const list = ref<AnimalInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const selectedIds = ref<number[]>([])

const query = reactive({
  ear_tag: '',
  breed: '',
  gender: '',
  status: '',
})

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.ear_tag = ''
  query.breed = ''
  query.gender = ''
  query.status = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const res = await getAnimalListApi({
      ...query,
      species: speciesZh.value,
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    })
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

async function handleBatchDelete() {
  try {
    await batchDeleteAnimalApi(selectedIds.value)
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    loadData()
  } catch {
    // handled
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
