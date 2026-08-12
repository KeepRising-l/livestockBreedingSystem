<template>
  <div class="login-page">
    <!-- 右侧登录卡片（背景图右侧留白区） -->
    <div class="login-card">
      <div class="card-logo">
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
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 7%;
  background: url('/login-bg.jpg') no-repeat center center / cover;
  position: relative;
  overflow: hidden;

  // 左右平滑溶解：左侧保留照片细节，向右渐变过渡到接近纯白的承载面，
  // 让右侧表单区域与背景融为一体，不再有生硬的卡片边界
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(100deg,
      rgba(9, 40, 60, 0.20) 0%,
      rgba(255, 255, 255, 0.10) 34%,
      rgba(255, 255, 255, 0.55) 58%,
      rgba(255, 255, 255, 0.96) 100%);
  }

  @media (max-width: 768px) {
    justify-content: center;
    padding: 16px;
    // 移动端表单居中，改为整体提亮的白色承载面保证可读性
    &::before {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.78) 100%);
    }
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 40px 36px 30px;
  border-radius: 18px;
  // 无边框无底色：表单表面由页面右侧的白色渐变承载，组件直接“嵌”进背景
  background: transparent;
  border: none;
  box-shadow: 0 30px 80px rgba(10, 40, 60, 0.08);

  // 本页青蓝色主题覆盖（仅作用于卡片内部表单/按钮）
  --el-color-primary: #0ea5c9;
  --el-color-primary-light-3: #46bfdb;
  --el-color-primary-light-5: #7cd3e8;
  --el-color-primary-light-7: #b1e5f3;
  --el-color-primary-light-8: #ceeef7;
  --el-color-primary-light-9: #e9f8fc;
  --el-color-primary-dark-2: #0b85a5;

  // 表单控件顺着页面左→右渐变：左缘透出照片、向右过渡到实白，与背景溶解方向一致
  :deep(.el-input__wrapper) {
    background: linear-gradient(100deg,
      rgba(255, 255, 255, 0.12) 0%,
      rgba(255, 255, 255, 0.30) 40%,
      rgba(255, 255, 255, 0.97) 80%);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-shadow: 0 0 0 1px rgba(14, 133, 165, 0.14) inset;
    transition: box-shadow 0.2s ease;
    &.is-focus {
      box-shadow: 0 0 0 1px var(--el-color-primary) inset, 0 6px 18px rgba(14, 133, 165, 0.12);
    }
  }

  @media (max-width: 768px) {
    width: 100%;
    max-width: 420px;
  }
}

.card-logo {
  text-align: center;
  margin-bottom: 30px;

  h1 {
    font-size: 26px;
    font-weight: 600;
    color: #0a4a66;
    margin: 0 0 8px;
    letter-spacing: 2px;
    line-height: 1.4;
    text-wrap: balance;
  }

  p {
    font-size: 12px;
    color: #7a9cb0;
    letter-spacing: 0.6px;
  }
}

.w-full { width: 100%; }

.login-btn {
  height: 44px;
  font-size: 16px;
  letter-spacing: 6px;
  border-radius: 8px;
  transition: all 0.25s ease;
  &:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(14, 133, 165, 0.28); }
  &:active { transform: translateY(0) scale(0.98); }
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
