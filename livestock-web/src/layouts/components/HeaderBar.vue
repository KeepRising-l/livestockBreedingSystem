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
      <!-- 系统状态 + 实时时钟（数据化读数） -->
      <div class="sys-clock" title="系统运行状态">
        <span class="tech-pulse"></span>
        <span class="clock-text tech-metric">{{ clock }}</span>
      </div>

      <!-- 超管农场选择器：只要有农场就展示，始终能看到当前操作的是哪个养殖场 -->
      <el-select
        v-if="authStore.userType === 1 && authStore.farmList.length >= 1"
        :model-value="authStore.selectedFarmId"
        @update:model-value="handleFarmSwitch"
        size="small"
        class="farm-selector"
        placeholder="请选择养殖场"
      >
        <el-option
          v-for="f in authStore.farmList"
          :key="f.id"
          :label="f.farm_name"
          :value="f.id"
        />
      </el-select>

      <!-- 消息铃铛（缺口6：审核结果通知，未读角标） -->
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="msg-badge">
        <el-icon class="msg-bell" :size="20" @click="router.push('/messages')">
          <Bell />
        </el-icon>
      </el-badge>

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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

defineProps<{ isCollapse: boolean }>()
const emit = defineEmits<{ toggle: [] }>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 未读数统一从 auth store 读取（标记已读后同步刷新角标，无需手动刷新页面）
const unreadCount = computed(() => authStore.unreadCount)

/** 顶栏实时时钟：仅展示当前时间，不做业务数据呈现 */
const clock = ref('')
let clockTimer: ReturnType<typeof setInterval> | undefined

function tick() {
  clock.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

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

onMounted(() => {
  tick()
  clockTimer = setInterval(tick, 1000)
  authStore.refreshUnreadCount()
})

onBeforeUnmount(() => {
  if (clockTimer) clearInterval(clockTimer)
})

// 路由变化时刷新未读数（如从消息页标记已读返回、审核操作后跳转）
watch(() => route.fullPath, authStore.refreshUnreadCount)
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
  gap: 14px;
  min-width: 0;
}

.collapse-btn {
  cursor: pointer;
  color: #5b7d95;
  padding: 5px;
  border-radius: 7px;
  transition: color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    color: #37bcd8;
    background: rgba(15, 168, 201, 0.12);
    box-shadow: 0 0 14px rgba(15, 168, 201, 0.28);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 系统状态 + 时钟 */
.sys-clock {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 30px;
  padding: 0 13px;
  margin-right: 16px;
  border: 1px solid rgba(15, 168, 201, 0.24);
  border-radius: 999px;
  background: rgba(236, 244, 250, 0.62);
  backdrop-filter: blur(8px);

  .clock-text {
    font-size: 12.5px;
    letter-spacing: 0.8px;
    color: #5ecbe2;
    white-space: nowrap;
  }
}

.msg-badge {
  margin-right: 16px;
}

.msg-bell {
  cursor: pointer;
  color: #5b7d95;
  transition: color 0.2s ease, filter 0.2s ease;

  &:hover {
    color: #37bcd8;
    filter: drop-shadow(0 0 10px rgba(15, 168, 201, 0.8));
  }
}

.farm-selector {
  margin-right: 16px;
  width: 180px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  color: #2b4b63;
  font-size: 13.5px;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;

  &:hover {
    background: rgba(15, 168, 201, 0.12);
    border-color: rgba(15, 168, 201, 0.32);
    color: #0e2f47;
  }
}

.ml-1 { margin-left: 4px; }
.ml-2 { margin-left: 8px; }

@media (max-width: 900px) {
  .sys-clock { display: none; }
  .farm-selector { width: 132px; }
}
</style>
