<template>
  <div>
    <h2 class="page-title">养殖场信息</h2>
    <el-card class="info-card" v-loading="loading">
      <template v-if="farm">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="养殖场名称">{{ farm.farm_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ farm.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="养殖种类">
            <el-tag v-for="t in farm.livestock_types.split(',')" :key="t" class="mr-8" type="success">{{ t }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="地址">{{ farm.address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="farm.status === 1 ? 'success' : 'danger'">{{ farm.status === 1 ? '正常' : '停用' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ farm.create_time || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-button type="primary" class="mt-16" @click="showDialog = true" v-if="canManage">编辑信息</el-button>
      </template>
      <el-empty v-else description="暂无养殖场信息" />
    </el-card>

    <el-dialog v-model="showDialog" title="编辑养殖场信息" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="养殖场名称" prop="farm_name">
          <el-input v-model="form.farm_name" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getFarmInfoApi, updateFarmApi, type FarmInfo } from '@/api/farm'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const farm = ref<FarmInfo | null>(null)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const formRef = ref<FormInstance>()

const canManage = computed(() => authStore.userType === 1 || authStore.userType === 2)

const form = reactive({
  farm_name: '',
  phone: '',
  address: '',
})

const rules: FormRules = {
  farm_name: [{ required: true, message: '请输入养殖场名称', trigger: 'blur' }],
}

async function loadFarmInfo() {
  loading.value = true
  try {
    const res = await getFarmInfoApi()
    farm.value = res.data
    form.farm_name = res.data.farm_name
    form.phone = res.data.phone || ''
    form.address = res.data.address || ''
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await updateFarmApi({
      farm_name: form.farm_name,
      phone: form.phone,
      address: form.address,
    })
    ElMessage.success('保存成功')
    showDialog.value = false
    await loadFarmInfo()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

onMounted(loadFarmInfo)
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #0e2f47; }
.info-card { max-width: 900px; }
.mt-16 { margin-top: 16px; }
.mr-8 { margin-right: 8px; }
</style>
