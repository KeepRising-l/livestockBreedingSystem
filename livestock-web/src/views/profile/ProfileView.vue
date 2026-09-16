<template>
  <div>
    <h2 class="page-title">个人中心</h2>
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>基本信息</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">{{ info.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="账号类型">{{ userTypeText }}</el-descriptions-item>
            <el-descriptions-item label="就职岗位">{{ info.post || '-' }}</el-descriptions-item>
            <el-descriptions-item label="所属养殖场">{{ authStore.farmInfo?.farm_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="养殖种类">{{ authStore.farmInfo?.livestock_types || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>我的角色与权限</template>
          <div class="mb-16">
            <span class="perm-label">角色：</span>
            <el-tag v-for="r in info.roles" :key="r" class="mr-8">{{ r }}</el-tag>
            <span v-if="!info.roles.length" class="perm-empty">-</span>
          </div>
          <div>
            <span class="perm-label">权限模块：</span>
            <el-tag v-for="p in info.perms" :key="p" type="success" class="mr-8">{{ p }}</el-tag>
            <span v-if="!info.perms.length" class="perm-empty">-</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getPermissionsApi, type PermissionsResult } from '@/api/auth'

const authStore = useAuthStore()
const info = ref<PermissionsResult>({
  user_id: 0, username: '', user_type: 0, farm_id: null, post: null,
  roles: [], perms: [], menus: [],
})

const userTypeText = computed(() => {
  const map: Record<number, string> = { 1: '超级管理员', 2: '养殖场主', 3: '养殖场员工' }
  return map[info.value.user_type] || '-'
})

onMounted(async () => {
  try {
    const res = await getPermissionsApi()
    info.value = res.data
  } catch {
    // 忽略，接口异常不阻塞页面
  }
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #eaf6ff; }
.mb-16 { margin-bottom: 16px; }
.mr-8 { margin-right: 8px; }
.perm-label { font-size: 14px; color: #a8c6e0; }
.perm-empty { color: #6d8dab; }
</style>
