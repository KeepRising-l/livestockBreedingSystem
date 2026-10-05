<template>
  <div>
    <div class="page-header">
      <el-button link type="primary" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <el-button type="primary" plain @click="importVisible = true">
        <el-icon><Upload /></el-icon> 从 Excel 导入
      </el-button>
    </div>
    <h2 class="page-title mt-16">批量入栏</h2>
    <el-card class="form-card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" size="default">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="畜种" prop="species">
              <el-select v-model="form.species" disabled style="width: 100%">
                <el-option :label="speciesZh" :value="speciesZh" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品种" prop="breed">
              <el-select v-model="form.breed" placeholder="请选择品种" clearable filterable style="width: 100%">
                <el-option v-for="b in breedOptions" :key="b.value" :label="b.label" :value="b.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-radio-group v-model="form.gender">
                <el-radio v-for="g in GENDER_OPTIONS" :key="g.value" :value="g.value">{{ g.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数量" prop="count">
              <el-input-number v-model="form.count" :min="1" :max="999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源" prop="source">
              <el-select v-model="form.source" placeholder="请选择" clearable style="width: 100%">
                <el-option v-for="s in SOURCE_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出生日期" prop="birth_date">
              <el-date-picker
                v-model="form.birth_date"
                type="date"
                placeholder="选择日期（必填）"
                style="width: 100%"
                value-format="YYYY-MM-DD"
                :disabled-date="(d: Date) => d.getTime() > Date.now()"
              />
              <div v-if="agePreview" class="tip">
                当前日龄约 {{ agePreview.age }} 天，整批生长阶段：{{ agePreview.stage }}
                （由系统按日龄自动匹配）
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入栏日期" prop="in_date">
              <el-date-picker v-model="form.in_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit">确认批量入栏</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果展示 -->
    <el-dialog v-model="resultVisible" title="批量入栏结果" width="600px">
      <template v-if="result">
        <div class="result-info">
          <p><strong>总数：</strong>{{ result.total }} 只</p>
          <p><strong>生长阶段：</strong>{{ result.stage }}</p>
          <p><strong>分配圈舍类型：</strong>{{ result.pen_type }}</p>
        </div>
        <el-table :data="result.plan" class="mt-16">
          <el-table-column prop="pen_code" label="圈舍编号" width="120" />
          <el-table-column prop="count" label="分配数量" width="100" />
          <el-table-column prop="ear_tags" label="耳标列表">
            <template #default="{ row }">
              <el-tag v-for="tag in row.ear_tags" :key="tag" class="mr-8" size="small">{{ tag }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button type="primary" @click="goToList">返回档案列表</el-button>
      </template>
    </el-dialog>

    <!-- Excel 导入 -->
    <el-dialog v-model="importVisible" title="从 Excel 导入" width="720px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" show-icon>
        <p>模板列：品种 / 性别 / 出生日期 / 入栏日期 / 来源 / 备注，每行代表 1 头，逐头自动分配圈舍并生成耳标。</p>
        <p>出生日期必填（格式 YYYY-MM-DD）：系统据此自动推算日龄和生长阶段，留空的行将被拒绝导入；入栏日期格式同上，可留空。有问题的行会自动跳过，不影响其它行。</p>
      </el-alert>
      <div class="mt-16 flex-gap">
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon> 下载模板
        </el-button>
        <el-upload
          accept=".xlsx,.xls"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
        >
          <el-button type="primary" plain>
            <el-icon><Upload /></el-icon> 选择 Excel 文件
          </el-button>
        </el-upload>
      </div>

      <template v-if="preview.length">
        <el-divider />
        <el-table :data="preview" size="small" border max-height="280">
          <el-table-column prop="row" label="行号" width="70" />
          <el-table-column prop="breed" label="品种" width="140" />
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column prop="birth_date" label="出生日期" width="110" />
          <el-table-column prop="in_date" label="入栏日期" width="110" />
          <el-table-column prop="source" label="来源" width="80" />
          <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        </el-table>
        <el-alert v-if="parseErrors.length" class="mt-16" type="warning" :closable="false" show-icon
          :title="`${parseErrors.length} 处问题（将自动跳过）：`" :description="parseErrors.join('；')" />
      </template>
      <template v-else-if="parseErrors.length">
        <el-alert class="mt-16" type="error" :closable="false" show-icon :title="parseErrors.join('；')" />
      </template>

      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" :disabled="!validCount" @click="handleImport">
          确认导入{{ validCount ? `（${validCount} 头）` : '' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入结果 -->
    <el-dialog v-model="importResultVisible" title="导入结果" width="640px">
      <div class="result-info">
        <p><strong>成功：</strong>{{ importResult?.success }} 头</p>
        <p><strong>失败：</strong>{{ importResult?.failed }} 行</p>
      </div>
      <el-table v-if="failedRows.length" :data="failedRows" size="small" border max-height="260">
        <el-table-column prop="row" label="行号" width="70" />
        <el-table-column prop="breed" label="品种" width="120" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="error" label="失败原因" />
      </el-table>
      <el-empty v-else description="全部导入成功" :image-size="60" />
      <template #footer>
        <el-button @click="importResultVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToList">查看档案列表</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { batchCreateAnimalApi, importAnimalsApi } from '@/api/animal'
import { GENDER_OPTIONS, SOURCE_OPTIONS, calcAgeDays, determineGrowthStage } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { readExcel, downloadImportTemplate, fmtDateCell } from '@/utils/excel'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const { species, speciesZh, breedOptions, loadBreedOptions } = useSpecies()

const formRef = ref<FormInstance>()
const saving = ref(false)
const resultVisible = ref(false)
const result = ref<any>(null)

// Excel 导入相关
const importVisible = ref(false)
const importing = ref(false)
const preview = ref<any[]>([])
const parseErrors = ref<string[]>([])
const importResult = ref<any>(null)
const importResultVisible = ref(false)
const validCount = computed(() => preview.value.filter((r: any) => r.valid).length)
const failedRows = computed(() => (importResult.value?.results || []).filter((r: any) => !r.ok))

const form = reactive({
  species: speciesZh.value,
  breed: '',
  gender: '母',
  count: 1,
  source: '',
  birth_date: '',
  in_date: new Date().toISOString().split('T')[0],
  remark: '',
})

const rules: FormRules = {
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  breed: [{ required: true, message: '请输入品种', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  count: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  birth_date: [{ required: true, message: '请选择出生日期（必填，用于自动计算日龄和生长阶段）', trigger: 'change' }],
  in_date: [{ required: true, message: '请选择入栏日期', trigger: 'change' }],
}

/** 出生日期联动：实时显示日龄 + 自动匹配的生长阶段（整批同一出生日期） */
const agePreview = computed(() => {
  const age = calcAgeDays(form.birth_date)
  if (age === null) return null
  return { age, stage: determineGrowthStage(form.species, age) }
})

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const res = await batchCreateAnimalApi({
      species: form.species,
      breed: form.breed,
      gender: form.gender,
      count: form.count,
      birth_date: form.birth_date || undefined,
      in_date: form.in_date || undefined,
      source: form.source || undefined,
      remark: form.remark || undefined,
    })
    ElMessage.success('批量入栏成功')
    result.value = res.data
    resultVisible.value = true
  } catch {
    // handled
  } finally {
    saving.value = false
  }
}

function downloadTemplate() {
  downloadImportTemplate()
}

async function handleFileChange(uploadFile: any) {
  const file = uploadFile.raw as File
  if (!file) return
  preview.value = []
  parseErrors.value = []
  try {
    const { headers, rows } = await readExcel(file)
    // 表头容错：如"出生日期（必填）"也能匹配到"出生日期"列
    const col = (name: string) => headers.findIndex((h) => h === name || h.startsWith(name))
    const iBreed = col('品种')
    const iGender = col('性别')
    const iBirth = col('出生日期')
    const iIn = col('入栏日期')
    const iSource = col('来源')
    const iRemark = col('备注')
    if (iBreed === -1 || iGender === -1) {
      parseErrors.value.push('缺少必填列：品种/性别')
      return
    }
    const dateRe = /^\d{4}-\d{2}-\d{2}$/
    const errs: string[] = []
    const list = rows.map((r, idx) => {
      const rowNum = idx + 2 // 含表头
      const breed = String(r[iBreed] ?? '').trim()
      const gender = String(r[iGender] ?? '').trim()
      const birth = fmtDateCell(r[iBirth])
      const inDate = fmtDateCell(r[iIn])
      const source = iSource === -1 ? '' : String(r[iSource] ?? '').trim()
      const remark = iRemark === -1 ? '' : String(r[iRemark] ?? '').trim()
      if (!breed) errs.push(`第 ${rowNum} 行：品种为空`)
      if (!['公', '母'].includes(gender)) errs.push(`第 ${rowNum} 行：性别须为 公/母`)
      // 出生日期必填：留空/格式错误/晚于今天的行都拒绝导入
      if (!birth) errs.push(`第 ${rowNum} 行：出生日期必填（用于自动计算日龄和生长阶段）`)
      else if (!dateRe.test(birth)) errs.push(`第 ${rowNum} 行：出生日期格式应为 YYYY-MM-DD`)
      else if (birth > new Date().toISOString().split('T')[0]) errs.push(`第 ${rowNum} 行：出生日期不能晚于今天`)
      if (inDate && !dateRe.test(inDate)) errs.push(`第 ${rowNum} 行：入栏日期格式应为 YYYY-MM-DD`)
      const valid = !!breed && ['公', '母'].includes(gender)
        && !!birth && dateRe.test(birth) && birth <= new Date().toISOString().split('T')[0]
      return { row: rowNum, breed, gender, birth_date: birth, in_date: inDate, source, remark, valid }
    })
    parseErrors.value = errs
    preview.value = list
  } catch {
    parseErrors.value = ['文件解析失败，请确认上传的是 .xlsx/.xls 文件']
  }
}

async function handleImport() {
  const rows = preview.value
    .filter((r: any) => r.valid)
    .map((r: any) => ({
      breed: r.breed,
      gender: r.gender,
      birth_date: r.birth_date || undefined,
      in_date: r.in_date || undefined,
      source: r.source || undefined,
      remark: r.remark || undefined,
    }))
  if (!rows.length) {
    ElMessage.warning('没有可导入的有效行')
    return
  }
  importing.value = true
  try {
    const res = await importAnimalsApi({ species: speciesZh.value, rows })
    importResult.value = res.data
    importResultVisible.value = true
    importVisible.value = false
    preview.value = []
    parseErrors.value = []
  } catch {
    // handled
  } finally {
    importing.value = false
  }
}

function goToList() {
  resultVisible.value = false
  importResultVisible.value = false
  router.push(`/${species.value}/animal/list`)
}

onMounted(() => loadBreedOptions())

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  loadBreedOptions()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mt-16 { margin-top: 16px; }
.mr-8 { margin-right: 8px; }
.flex-gap { display: flex; align-items: center; gap: 12px; }
.form-card { max-width: 900px; }
.result-info { line-height: 2; }
.tip { color: #64748b; font-size: 12px; margin-top: 4px; line-height: 1.6; }
</style>
