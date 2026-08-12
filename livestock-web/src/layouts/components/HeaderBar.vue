<template>
  <div class="header-bar">
    <div class="header-left">
      <el-icon class="collapse-btn" @click="emit('toggle')" :size="20">
        <Fold v-if="!isCollapse" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <!-- 超管农场选择器 -->
      <el-select
        v-if="authStore.userType === 1 && authStore.farmList.length > 1"
        :model-value="authStore.selectedFarmId"
        @update:model-value="handleFarmSwitch"
        size="small"
        class="farm-selector"
      >
        <el-option
          v-for="f in authStore.farmList"
          :key="f.id"
          :label="f.farm_name"
          :value="f.id"
        />
      </el-select>

      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <el-icon><UserFilled /></el-icon>
          <span class="ml-2">{{ authStore.farmInfo?.farm_name || '超级管理员' }}</span>
          <el-icon class="ml-1"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

defineProps<{ isCollapse: boolean }>()
const emit = defineEmits<{ toggle: [] }>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

function handleFarmSwitch(farmId: number) {
  const farmName = authStore.farmList.find(f => f.id === farmId)?.farm_name || ''
  authStore.switchFarm(farmId)
  ElMessage.success(`已切换到「${farmName}」, 页面即将刷新`)
  // 硬刷新，确保所有组件重新挂载并用新的 X-Farm-Id 请求数据
  setTimeout(() => window.location.reload(), 300)
}

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped lang="scss">
.header-bar {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  cursor: pointer;
  &:hover { color: var(--el-color-primary); }
}
.header-right {
  display: flex;
  align-items: center;
}
.farm-selector {
  margin-right: 16px;
  width: 180px;
}
.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  &:hover { background: #f0f2f5; }
}
.ml-1 { margin-left: 4px; }
.ml-2 { margin-left: 8px; }
</style>
