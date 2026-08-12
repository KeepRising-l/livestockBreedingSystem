<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">历史记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="search">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="耳标">
          <el-input v-model="query.ear_tag" placeholder="耳标号" clearable style="width: 140px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="o in SPECIES_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="query.breed" placeholder="品种" clearable style="width: 140px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="query.gender" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="o in GENDER_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="删除前状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px" @change="search">
            <el-option v-for="(label, key) in ANIMAL_STATUS_MAP" :key="key" :label="label" :value="key" />
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
        <el-table-column prop="ear_tag" label="耳标" width="90">
          <template #default="{ row }">
            <span style="font-weight: 600;">{{ row.ear_tag }}</span>
          </template>
        </el-table-column>
        <el-table-column label="畜种" width="70">
          <template #default="{ row }">
            <el-tag size="small">{{ row.species }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="breed" label="品种" min-width="120" />
        <el-table-column label="性别" width="60">
          <template #default="{ row }">{{ row.gender }}</template>
        </el-table-column>
        <el-table-column prop="birth_date" label="出生日期" width="110">
          <template #default="{ row }">{{ row.birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column prop="in_date" label="入栏日期" width="110">
          <template #default="{ row }">{{ row.in_date || '-' }}</template>
        </el-table-column>
        <el-table-column prop="growth_stage" label="生长阶段" width="100">
          <template #default="{ row }">{{ row.growth_stage || '-' }}</template>
        </el-table-column>
        <el-table-column label="删除前状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status" :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="80">
          <template #default="{ row }">{{ row.source || '-' }}</template>
        </el-table-column>
        <el-table-column prop="delete_time" label="删除日期" width="110">
          <template #default="{ row }">
            <span style="color: #f56c6c;">{{ row.delete_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              title="确定恢复该档案？将重新计入圈舍存栏"
              @confirm="handleRestore(row.id)"
            >
              <template #reference>
                <el-button link type="success" size="small">恢复</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!list.length && !loading" class="text-center mt-16 text-gray">
        暂无历史记录
      </div>
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
import { getAnimalHistoryListApi, restoreAnimalApi, type AnimalHistoryInfo } from '@/api/animal'
import { SPECIES_OPTIONS, GENDER_OPTIONS, ANIMAL_STATUS_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage } from 'element-plus'

const { species, speciesZh } = useSpecies()

const list = ref<AnimalHistoryInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive({
  ear_tag: '', species: speciesZh.value, breed: '', gender: '', status: '',
})

function statusColor(s: string) {
  return { '在栏': 'success', '种用': 'warning', '隔离': 'danger', '待出栏': 'info', '已出栏': 'info', '死亡': 'danger' }[s] || 'info'
}

function search() { pageNum.value = 1; loadData() }
function resetSearch() {
  query.ear_tag = ''; query.species = speciesZh.value; query.breed = ''; query.gender = ''; query.status = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.ear_tag) params.ear_tag = query.ear_tag
    if (query.species) params.species = query.species
    if (query.breed) params.breed = query.breed
    if (query.gender) params.gender = query.gender
    if (query.status) params.status = query.status
    const res = await getAnimalHistoryListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {} finally { loading.value = false }
}

async function handleRestore(historyId: number) {
  try {
    await restoreAnimalApi(historyId)
    ElMessage.success('恢复成功')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-gray { color: #999; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
