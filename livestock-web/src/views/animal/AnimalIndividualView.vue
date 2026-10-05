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
              <el-date-picker
                v-model="form.birth_date"
                type="date"
                placeholder="选择日期（必填）"
                style="width: 100%"
                value-format="YYYY-MM-DD"
                :disabled-date="(d: Date) => d.getTime() > Date.now()"
              />
              <div v-if="agePreview" class="tip">
                当前日龄约 {{ agePreview.age }} 天，对应生长阶段：{{ agePreview.stage }}
                （阶段由系统按日龄自动匹配，无需填写）
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入栏日期" prop="in_date">
              <el-date-picker v-model="form.in_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="圈舍" prop="pen_id">
              <el-select
                v-model="form.pen_id"
                placeholder="留空则由系统自动分配"
                clearable
                filterable
                :loading="penLoading"
                style="width: 100%"
              >
                <el-option
                  v-for="p in penOptions"
                  :key="p.id"
                  :value="p.id"
                  :label="penLabel(p)"
                  :disabled="p.current_count >= p.capacity"
                >
                  <span>{{ p.pen_code }}</span>
                  <span class="pen-opt-meta">
                    {{ PEN_TYPE_MAP[p.pen_type] || p.pen_type }} · {{ p.current_count }}/{{ p.capacity }}
                    <template v-if="p.current_count >= p.capacity"> · 已满</template>
                    <template v-else> · 空位 {{ p.capacity - p.current_count }}</template>
                    <template v-if="!p.species"> · 待归属</template>
                  </span>
                </el-option>
              </el-select>
              <div class="tip">
                仅显示「{{ speciesZh }}」的圈舍，共 {{ penOptions.length }} 个（有空位 {{ availablePenCount }} 个）；
                留空则按生长阶段自动分配
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="耳标预览">
              <el-input v-model="earTagPreview" disabled placeholder="选择圈舍后自动生成" />
              <el-button class="ml-8" @click="previewEarTag" :disabled="!form.pen_id">生成预览</el-button>
              <div class="tip">
                耳标 5 位 = 畜种位（牛1/羊2/猪3）+ 圈舍编号数字 + 入栏序号，如牛 A02 圈舍第 7 头 → 10207
              </div>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createAnimalApi, generateEarTagApi } from '@/api/animal'
import { getPenListApi, type PenInfo } from '@/api/pen'
import { GENDER_OPTIONS, SOURCE_OPTIONS, PEN_TYPE_MAP, calcAgeDays, determineGrowthStage } from '@/utils/constants'
import { useSpecies } from '@/composables/useSpecies'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const { species, speciesZh, breedOptions, loadBreedOptions } = useSpecies()

const formRef = ref<FormInstance>()
const saving = ref(false)
const earTagPreview = ref('')

/** 出生日期联动：实时显示日龄 + 自动匹配的生长阶段 */
const agePreview = computed(() => {
  const age = calcAgeDays(form.birth_date)
  if (age === null) return null
  return { age, stage: determineGrowthStage(form.species, age) }
})

/** 当前畜种的可选圈舍（后端按 species 过滤，只回本畜种 + 待归属的空圈舍） */
const penOptions = ref<PenInfo[]>([])
const penLoading = ref(false)

const availablePenCount = computed(
  () => penOptions.value.filter((p) => p.current_count < p.capacity).length,
)

/** 下拉项文案：编号（类型 已用/容量 · 空位/已满 · 是否待归属） */
function penLabel(p: PenInfo) {
  const type = PEN_TYPE_MAP[p.pen_type] || p.pen_type
  const state = p.current_count >= p.capacity ? '已满' : `空位 ${p.capacity - p.current_count}`
  const owner = p.species ? '' : ' · 待归属'
  return `${p.pen_code}（${type} ${p.current_count}/${p.capacity} · ${state}${owner}）`
}

async function loadPenOptions() {
  penLoading.value = true
  try {
    const res = await getPenListApi({ species: speciesZh.value, pageNum: 1, pageSize: 100 })
    penOptions.value = ((res.data as any)?.list || []) as PenInfo[]
  } catch {
    penOptions.value = []
  } finally {
    penLoading.value = false
  }
}

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
  birth_date: [{ required: true, message: '请选择出生日期（必填，用于自动计算日龄和生长阶段）', trigger: 'change' }],
  in_date: [{ required: true, message: '请选择入栏日期', trigger: 'change' }],
}

async function previewEarTag() {
  if (!form.pen_id) return
  try {
    // 传畜种：圈舍若尚未归属畜种，仍能按当前页面的畜种预览耳标
    const res = await generateEarTagApi(form.pen_id, form.species)
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

onMounted(() => {
  loadBreedOptions()
  loadPenOptions()
})

// 切换畜种时同一条路由记录不会重建组件，必须主动重新加载，
// 否则页面会一直停留在上一个畜种的数据上
watch(species, () => {
  // 畜种字段是 disabled 的展示项，也要跟着路由更新
  form.species = speciesZh.value
  // 已选圈舍属于上一个畜种，必须清掉，否则会提交到错误的圈舍（后端也会拒绝）
  form.pen_id = undefined
  earTagPreview.value = ''
  loadBreedOptions()
  loadPenOptions()
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #14532d; }
.mt-16 { margin-top: 16px; }
.ml-8 { margin-left: 8px; }
.form-card { max-width: 900px; }
.tip { color: #64748b; font-size: 12px; margin-top: 4px; line-height: 1.6; }
/* 下拉项右侧的规格说明，靠右淡显，避免与编号抢视线 */
.pen-opt-meta { float: right; color: #64748b; font-size: 12px; padding-left: 16px; }
</style>
