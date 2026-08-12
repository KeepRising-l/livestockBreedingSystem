<template>
  <div>
    <el-button link type="primary" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon> 返回
    </el-button>
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
              <el-date-picker v-model="form.birth_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { batchCreateAnimalApi } from '@/api/animal'
import { GENDER_OPTIONS, SOURCE_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const { species, speciesZh, breedOptions, loadBreedOptions } = useSpecies()

const formRef = ref<FormInstance>()
const saving = ref(false)
const resultVisible = ref(false)
const result = ref<any>(null)

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
  in_date: [{ required: true, message: '请选择入栏日期', trigger: 'change' }],
}

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

function goToList() {
  resultVisible.value = false
  router.push(`/${species.value}/animal/list`)
}

onMounted(() => loadBreedOptions())
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mt-16 { margin-top: 16px; }
.mr-8 { margin-right: 8px; }
.form-card { max-width: 900px; }
.result-info { line-height: 2; }
</style>
