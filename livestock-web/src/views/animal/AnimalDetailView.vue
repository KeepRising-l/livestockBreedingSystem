<template>
  <div>
    <el-button link type="primary" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon> 返回
    </el-button>
    <h2 class="page-title mt-16">档案详情</h2>
    <el-card v-loading="loading">
      <template v-if="animal">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="耳标">{{ animal.ear_tag }}</el-descriptions-item>
          <el-descriptions-item label="畜种">{{ animal.species }}</el-descriptions-item>
          <el-descriptions-item label="品种">{{ animal.breed }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ animal.gender }}</el-descriptions-item>
          <el-descriptions-item label="生长阶段">
            <el-tag v-if="animal.growth_stage" type="success">{{ animal.growth_stage }}</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="生理状态">
            <el-tag v-if="animal.physio_status" :type="physioTagType(animal.physio_status)">{{ animal.physio_status }}</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag>{{ animal.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ animal.source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="出生日期">{{ animal.birth_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="入栏日期">{{ animal.in_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="出栏日期">{{ animal.out_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="父本耳标">{{ animal.sire_tag || '-' }}</el-descriptions-item>
          <el-descriptions-item label="母本耳标">{{ animal.dam_tag || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="3">{{ animal.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <el-empty v-else description="档案不存在" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { type TagProps } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { getAnimalDetailApi, type AnimalInfo } from '@/api/animal'

const route = useRoute()
const router = useRouter()

const animal = ref<AnimalInfo | null>(null)
const loading = ref(false)

function physioTagType(status: string): TagProps['type'] {
  return ({ 发情: 'warning', 妊娠: 'success', 泌乳: 'info', 休情: 'primary', 淘汰: 'danger' } as Record<string, TagProps['type']>)[status] || 'info'
}

onMounted(async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getAnimalDetailApi(id)
    animal.value = res.data as any
  } catch {
    //
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #eaf6ff; }
.mt-16 { margin-top: 16px; }
</style>
