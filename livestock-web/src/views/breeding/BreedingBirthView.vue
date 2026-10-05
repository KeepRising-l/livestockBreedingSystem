<template>
  <div>
    <div class="flex-between mb-16">
      <h2 class="page-title">产犊记录<template v-if="speciesZh">（{{ speciesZh }}）</template></h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon> 新增产犊
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="query" size="default">
        <el-form-item label="生产日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 260px"
            @change="onDateChange"
          />
        </el-form-item>
        <el-form-item label="母畜耳标">
          <el-input v-model="query.female_tag" placeholder="请输入母畜耳标" clearable style="width: 130px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="畜种">
          <el-select v-model="query.species" placeholder="全部" clearable style="width: 100px" @change="search">
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 记录列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="birth_date" label="生产日期" width="110" />
        <el-table-column prop="female_tag" label="母畜耳标" width="90" />
        <el-table-column prop="species" label="畜种" width="70" />
        <el-table-column prop="total_count" label="总数" width="70" />
        <el-table-column prop="alive_count" label="成活" width="70" />
        <el-table-column prop="dead_count" label="死亡" width="70" />
        <el-table-column label="成活率" width="80">
          <template #default="{ row }">{{ row.survival_rate === null ? '-' : row.survival_rate + '%' }}</template>
        </el-table-column>
        <el-table-column prop="offspring_tags" label="仔畜耳标" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.offspring_tags || '-' }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="handleEdit(row as BirthRecord)">编辑</el-button>
            <el-popconfirm title="确定删除该产犊记录？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑产犊记录' : '新增产犊记录'" width="540px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="母畜耳标" prop="female_tag">
          <el-select v-model="form.female_tag" filterable placeholder="选择母畜" style="width: 100%" :disabled="isEdit">
            <el-option v-for="a in femaleOptions" :key="a.ear_tag" :label="`${a.ear_tag} (${a.species}·${a.breed})`" :value="a.ear_tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="畜种" prop="species">
          <el-select v-model="form.species" placeholder="请选择" style="width: 100%" disabled>
            <el-option v-for="s in SPECIES_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="生产日期" prop="birth_date">
          <el-date-picker v-model="form.birth_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联配种">
          <el-select v-model="form.mating_id" filterable clearable placeholder="关联配种记录（可选）" style="width: 100%">
            <el-option
              v-for="m in matingOptions"
              :key="m.id"
              :label="`${m.female_tag} 配种于 ${m.mating_date}（${m.status}）`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="产仔总数" prop="total_count">
          <el-input-number v-model="form.total_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="成活数量" prop="alive_count">
          <el-input-number v-model="form.alive_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="死亡数量" prop="dead_count">
          <el-input-number v-model="form.dead_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="仔畜耳标">
          <el-input v-model="form.offspring_tags" placeholder="逗号分隔，如 2503,2504" clearable style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import {
  getBirthListApi, addBirthApi, updateBirthApi, deleteBirthApi,
  getBreedFemalesApi, getMatingListApi,
  type BirthRecord, type BreedAnimal, type MatingRecord,
} from '@/api/breeding'
import { SPECIES_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const { species, speciesZh } = useSpecies()

const list = ref<BirthRecord[]>([])
const loading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const femaleOptions = ref<BreedAnimal[]>([])
const matingOptions = ref<MatingRecord[]>([])

const dateRange = ref<string[]>([])
const query = reactive<{ female_tag: string; species: string; birth_date_start: string; birth_date_end: string }>({
  female_tag: '',
  species: speciesZh.value,
  birth_date_start: '',
  birth_date_end: '',
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const editId = ref(0)
const form = reactive({
  female_tag: '',
  mating_id: undefined as number | undefined,
  species: speciesZh.value,
  birth_date: new Date().toISOString().slice(0, 10),
  total_count: 1,
  alive_count: 1,
  dead_count: 0,
  offspring_tags: '',
  remark: '',
})

const formRules: FormRules = {
  female_tag: [{ required: true, message: '请选择母畜', trigger: 'change' }],
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  birth_date: [{ required: true, message: '请选择生产日期', trigger: 'change' }],
}

function onDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    query.birth_date_start = val[0]
    query.birth_date_end = val[1]
  } else {
    query.birth_date_start = ''
    query.birth_date_end = ''
  }
  search()
}

function search() {
  pageNum.value = 1
  loadData()
}

function resetSearch() {
  dateRange.value = []
  query.female_tag = ''
  query.species = speciesZh.value
  query.birth_date_start = ''
  query.birth_date_end = ''
  search()
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { pageNum: pageNum.value, pageSize: pageSize.value }
    if (query.female_tag) params.female_tag = query.female_tag
    if (query.species) params.species = query.species
    if (query.birth_date_start) params.birth_date_start = query.birth_date_start
    if (query.birth_date_end) params.birth_date_end = query.birth_date_end
    const res = await getBirthListApi(params)
    const data = res.data as any
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [f, m] = await Promise.all([
      getBreedFemalesApi({ pageSize: 100, species: speciesZh.value }),
      getMatingListApi({ pageSize: 100, species: speciesZh.value }),
    ])
    femaleOptions.value = (f.data as any)?.list || []
    matingOptions.value = (m.data as any)?.list || []
  } catch {
    // handled by interceptor
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = 0
  Object.assign(form, {
    female_tag: '',
    mating_id: undefined,
    species: speciesZh.value,
    birth_date: new Date().toISOString().slice(0, 10),
    total_count: 1,
    alive_count: 1,
    dead_count: 0,
    offspring_tags: '',
    remark: '',
  })
  dialogVisible.value = true
}

function handleEdit(row: BirthRecord) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    female_tag: row.female_tag,
    mating_id: row.mating_id ?? undefined,
    species: row.species,
    birth_date: row.birth_date,
    total_count: row.total_count,
    alive_count: row.alive_count,
    dead_count: row.dead_count,
    offspring_tags: row.offspring_tags || '',
    remark: row.remark || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (form.alive_count + form.dead_count > form.total_count) {
    ElMessage.warning('成活数 + 死亡数不能大于产仔总数')
    return
  }
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.mating_id) delete payload.mating_id
    if (!payload.offspring_tags) delete payload.offspring_tags
    if (!payload.remark) delete payload.remark
    if (isEdit.value) {
      await updateBirthApi(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await addBirthApi(payload)
      ElMessage.success('产犊记录已登记')
    }
    dialogVisible.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteBirthApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // handled by interceptor
  }
}

onMounted(() => {
  loadOptions()
  loadData()
})

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  pageNum.value = 1
  loadOptions()
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #0e2f47; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.text-right { text-align: right; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
</style>
