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
        <el-popconfirm title="确定批量删除选中档案？" @confirm="handleBatchDelete" v-if="selectedTotal">
          <template #reference>
            <el-button type="danger" :disabled="!selectedTotal">
              批量删除 ({{ selectedTotal }})
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
        <el-form-item label="生理状态">
          <el-select v-model="query.physio_status" placeholder="全部" clearable style="width: 110px">
            <el-option v-for="s in PHYSIO_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 分级展示：按圈舍分组 -->
    <div v-loading="loading" class="group-list">
      <template v-if="groups.length">
        <el-card v-for="g in groups" :key="g.pen_id ?? -1" class="group-card mb-16">
          <!-- 组头：圈舍汇总，点击展开/收起个体明细 -->
          <div class="group-header" @click="toggleGroup(g)">
            <el-icon class="expand-icon" :class="{ expanded: isExpanded(g) }">
              <ArrowRightBold />
            </el-icon>
            <span class="pen-code">{{ g.pen_code || '无圈舍' }}</span>
            <el-tag v-if="g.pen_type" size="small" effect="plain">{{ PEN_TYPE_MAP[g.pen_type] || g.pen_type }}</el-tag>
            <span class="summary-item">存栏 <strong>{{ g.count }}</strong>
              <template v-if="g.capacity != null"> / {{ g.capacity }}</template>
            </span>
            <span class="summary-item">公 {{ g.male_count }} · 母 {{ g.female_count }}</span>
            <span class="summary-item">
              品种构成：
              <el-tag v-for="b in g.breeds" :key="b.breed" size="small" class="mr-4">{{ b.breed }}×{{ b.count }}</el-tag>
            </span>
            <span class="summary-item" v-if="g.avg_age_days != null">平均日龄 {{ g.avg_age_days }} 天</span>
          </div>

          <!-- 组内个体明细 -->
          <el-collapse-transition>
            <div v-show="isExpanded(g)" class="group-body" @click.stop>
              <el-table
                :data="g.animals"
                stripe
                size="small"
                :ref="(el) => setTableRef(g, el)"
                @selection-change="(rows: AnimalInfo[]) => onSelectionChange(g, rows)"
                @row-click="(row: AnimalInfo) => router.push(`/${species}/animal/${row.id}`)"
                style="cursor: pointer"
              >
                <el-table-column type="selection" width="45" />
                <el-table-column prop="ear_tag" label="耳标" width="90" />
                <el-table-column prop="breed" label="品种" width="130" />
                <el-table-column prop="gender" label="性别" width="55" />
                <el-table-column label="日龄" width="90">
                  <template #default="{ row }">
                    <span v-if="row.age_days != null">{{ row.age_days }} 天</span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column label="生长阶段" width="100">
                  <template #default="{ row }">
                    <el-tag v-if="row.growth_stage" size="small" type="success">{{ row.growth_stage }}</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column label="生理状态" width="90">
                  <template #default="{ row }">
                    <el-tag v-if="row.physio_status" size="small" :type="physioTagType(row.physio_status)">{{ row.physio_status }}</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '在栏' ? 'success' : row.status === '已出栏' ? 'info' : 'warning'" size="small">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="source" label="来源" width="70" />
                <el-table-column prop="birth_date" label="出生日期" width="110" />
                <el-table-column prop="in_date" label="入栏日期" width="110" />
                <el-table-column label="操作" width="80" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click.stop="router.push(`/${species}/animal/${row.id}`)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-collapse-transition>
        </el-card>
      </template>
      <el-empty v-else-if="!loading" description="暂无档案数据" />
    </div>

    <div class="text-right mt-16">
      <el-pagination
        v-model:current-page="pageNum"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  getAnimalGroupedApi, batchDeleteAnimalApi,
  type AnimalInfo, type AnimalGroupInfo,
} from '@/api/animal'
import { GENDER_OPTIONS, ANIMAL_STATUS_MAP, PHYSIO_STATUS_OPTIONS, PEN_TYPE_MAP } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { type TagProps, ElMessage, type TableInstance } from 'element-plus'

const router = useRouter()
const { species, speciesZh } = useSpecies()

const groups = ref<AnimalGroupInfo[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(5)
const total = ref(0)

/** 展开的圈舍组（默认全部展开） */
const collapsed = ref<Set<number | string>>(new Set())

function groupKey(g: AnimalGroupInfo): number | string {
  return g.pen_id ?? 'none'
}

function isExpanded(g: AnimalGroupInfo): boolean {
  return !collapsed.value.has(groupKey(g))
}

function toggleGroup(g: AnimalGroupInfo) {
  const key = groupKey(g)
  const next = new Set(collapsed.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  collapsed.value = next
}

const query = reactive({
  ear_tag: '',
  breed: '',
  gender: '',
  status: '',
  physio_status: '',
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
  query.physio_status = ''
  search()
}

function physioTagType(status: string): TagProps['type'] {
  return ({ 正常: 'info', 发情: 'warning', 妊娠: 'success', 泌乳: 'info', 休情: 'primary', 淘汰: 'danger' } as Record<string, TagProps['type']>)[status] || 'info'
}

/** 跨组勾选：key=圈舍ID，value=选中的档案ID列表 */
const selectedMap = reactive<Record<string, number[]>>({})
const tableRefs = new Map<string, TableInstance>()

const selectedTotal = computed(() =>
  Object.values(selectedMap).reduce((sum, ids) => sum + ids.length, 0),
)

function setTableRef(g: AnimalGroupInfo, el: unknown) {
  if (el) {
    tableRefs.set(String(groupKey(g)), el as TableInstance)
  } else {
    tableRefs.delete(String(groupKey(g)))
  }
}

function onSelectionChange(g: AnimalGroupInfo, rows: AnimalInfo[]) {
  selectedMap[String(groupKey(g))] = rows.map((r) => r.id)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getAnimalGroupedApi({
      ...query,
      species: speciesZh.value,
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    })
    const data = res.data as any
    groups.value = data.list || []
    total.value = data.total || 0
    // 数据刷新后清空旧勾选（行已重新渲染）
    Object.keys(selectedMap).forEach((k) => delete selectedMap[k])
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

async function handleBatchDelete() {
  const ids = Object.values(selectedMap).flat()
  if (!ids.length) return
  try {
    await batchDeleteAnimalApi(ids)
    ElMessage.success('批量删除成功')
    loadData()
  } catch {
    // handled
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
.mr-4 { margin-right: 4px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }

.group-card :deep(.el-card__body) { padding: 12px 16px; }
.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex-wrap: wrap;
  user-select: none;
}
.expand-icon { transition: transform 0.2s; color: #8fa9bf; }
.expand-icon.expanded { transform: rotate(90deg); }
.pen-code { font-size: 16px; font-weight: 600; color: #eaf6ff; min-width: 56px; }
.summary-item { color: #8fa9bf; font-size: 13px; }
.summary-item strong { color: #eaf6ff; }
.group-body { margin-top: 12px; }
</style>
