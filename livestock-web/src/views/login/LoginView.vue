<template>
  <div class="login-page">
    <!-- 右侧登录卡片（背景图右侧留白区） -->
    <div class="login-card">
      <div class="card-logo">
        <span class="logo-badge">智</span>
        <h1>智能养殖信息管理系统</h1>
        <p>Smart Livestock Information Management System</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号或手机号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="w-full login-btn" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="links">
        <router-link to="/register/owner">还没有账号？注册养殖场</router-link>
      </div>
      <div class="tips">支持账号或手机号登录 · 初始账号 admin / admin123</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号或手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur', min: 1 }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    // 员工登录默认进入当前畜种工作台，超管/场主仍进数据大屏
    const redirect = (route.query.redirect as string) ||
      (authStore.userType === 3 ? `/${authStore.currentSpecies || 'cattle'}/workbench` : '/dashboard')
    router.push(redirect)
  } catch {
    // 错误已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 7%;
  background: url('/login-bg.jpg') no-repeat center center / cover;
  position: relative;
  overflow: hidden;

  // 半透明青色叠层：左侧压暗提科技感、右侧提亮留白区，保证卡片可读
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg,
      rgba(8, 44, 66, 0.22) 0%,
      rgba(8, 44, 66, 0.10) 42%,
      rgba(255, 255, 255, 0.28) 100%);
  }

  @media (max-width: 768px) {
    justify-content: center;
    padding: 16px;
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 40px 36px 30px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.70);
  backdrop-filter: blur(16px) saturate(1.5);
  -webkit-backdrop-filter: blur(16px) saturate(1.5);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 24px 64px rgba(14, 72, 98, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.85);

  // 本页青蓝色主题覆盖（仅作用于卡片内部表单/按钮）
  --el-color-primary: #0ea5c9;
  --el-color-primary-light-3: #46bfdb;
  --el-color-primary-light-5: #7cd3e8;
  --el-color-primary-light-7: #b1e5f3;
  --el-color-primary-light-8: #ceeef7;
  --el-color-primary-light-9: #e9f8fc;
  --el-color-primary-dark-2: #0b85a5;

  @media (max-width: 768px) {
    width: 100%;
    max-width: 420px;
  }
}

.card-logo {
  text-align: center;
  margin-bottom: 26px;

  .logo-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    border-radius: 14px;
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #0ea5c9, #0b5c99);
    box-shadow: 0 8px 20px rgba(14, 133, 165, 0.35);
    margin-bottom: 12px;
  }

  h1 {
    font-size: 20px;
    font-weight: 600;
    color: #0a4a66;
    margin: 0 0 6px;
    letter-spacing: 1px;
  }

  p {
    font-size: 12px;
    color: #7a9cb0;
    letter-spacing: 0.5px;
  }
}

.w-full { width: 100%; }

.login-btn {
  height: 44px;
  font-size: 16px;
  letter-spacing: 6px;
  border-radius: 8px;
}

.links {
  text-align: center;
  margin: 14px 0 12px;

  a {
    color: #0ea5c9;
    font-size: 13px;
    &:hover { color: #0b85a5; }
  }
}

.tips {
  text-align: center;
  color: #9db8c6;
  font-size: 12px;
}
</style>
