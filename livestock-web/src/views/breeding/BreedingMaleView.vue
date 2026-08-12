<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">公畜档案</h2>
      <el-alert type="info" :closable="false" show-icon style="max-width: 480px"
        title="仅展示处于「繁育期 / 妊娠」的可繁育公畜，供配种登记时选畜" />
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
        <el-table-column prop="ear_tag" label="耳标" width="100" />
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="breed" label="品种" min-width="120" />
        <el-table-column prop="growth_stage" label="生长阶段" width="90" />
        <el-table-column label="圈舍" width="90">
          <template #default="{ row }">{{ row.pen_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column prop="birth_date" label="出生日期" width="110">
          <template #default="{ row }">{{ row.birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="copyTag(row.ear_tag)">复制耳标</el-button>
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
import { getBreedMalesApi, type BreedAnimal } from '@/api/breeding'
import { SPECIES_OPTIONS } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const list = ref<BreedAnimal[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const query = reactive<{ species: string; keyword: string }>({ species: '', keyword: '' })

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  query.species = ''
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
