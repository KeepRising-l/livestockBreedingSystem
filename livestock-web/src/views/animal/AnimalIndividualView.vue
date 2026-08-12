<template>
  <div>
    <el-button link type="primary" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon> 返回
    </el-button>
    <h2 class="page-title mt-16">个体入栏</h2>
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
          <el-col :span="12">
            <el-form-item label="圈舍ID" prop="pen_id">
              <el-input-number v-model="form.pen_id" :min="0" placeholder="留空自动分配" style="width: 100%" />
              <div class="tip">留空则系统自动分配圈舍</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="耳标预览">
              <el-input v-model="earTagPreview" disabled placeholder="选择圈舍后自动生成" />
              <el-button class="ml-8" @click="previewEarTag" :disabled="!form.pen_id">生成预览</el-button>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="父本耳标" prop="sire_tag">
              <el-input v-model="form.sire_tag" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="母本耳标" prop="dam_tag">
              <el-input v-model="form.dam_tag" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit">确认入栏</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createAnimalApi, generateEarTagApi } from '@/api/animal'
import { GENDER_OPTIONS, SOURCE_OPTIONS } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const { species, speciesZh, breedOptions, loadBreedOptions } = useSpecies()

const formRef = ref<FormInstance>()
const saving = ref(false)
const earTagPreview = ref('')

const form = reactive({
  species: speciesZh.value,
  breed: '',
  gender: '母',
  source: '',
  birth_date: '',
  in_date: new Date().toISOString().split('T')[0],
  pen_id: undefined as number | undefined,
  sire_tag: '',
  dam_tag: '',
  remark: '',
})

const rules: FormRules = {
  species: [{ required: true, message: '请选择畜种', trigger: 'change' }],
  breed: [{ required: true, message: '请输入品种', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  in_date: [{ required: true, message: '请选择入栏日期', trigger: 'change' }],
}

async function previewEarTag() {
  if (!form.pen_id) return
  try {
    const res = await generateEarTagApi(form.pen_id)
    const data = res.data as any
    earTagPreview.value = data.ear_tag || ''
  } catch {
    // handled
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await createAnimalApi({
      species: form.species,
      breed: form.breed,
      gender: form.gender,
      birth_date: form.birth_date || undefined,
      in_date: form.in_date || undefined,
      source: form.source || undefined,
      pen_id: form.pen_id || undefined,
      sire_tag: form.sire_tag || undefined,
      dam_tag: form.dam_tag || undefined,
      remark: form.remark || undefined,
    })
    ElMessage.success('入栏成功')
    router.push(`/${species.value}/animal/list`)
  } catch {
    // handled
  } finally {
    saving.value = false
  }
}

onMounted(() => loadBreedOptions())
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.mt-16 { margin-top: 16px; }
.ml-8 { margin-left: 8px; }
.form-card { max-width: 900px; }
.tip { color: #999; font-size: 12px; margin-top: 4px; }
</style>
