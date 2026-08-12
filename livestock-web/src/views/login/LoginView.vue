<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">智能养殖信息管理系统</h1>
      <p class="subtitle">Livestock Management System</p>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号或手机号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="w-full" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="links">
        <router-link to="/register/owner">注册养殖场</router-link>
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
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch {
    // 错误已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  font-size: 22px;
  color: #2E7D32;
  margin-bottom: 4px;
}
.subtitle {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-bottom: 32px;
}
.w-full {
  width: 100%;
}
.links {
  text-align: center;
  margin-bottom: 12px;
  a { color: #2E7D32; font-size: 13px; }
}
.tips {
  text-align: center;
  color: #bbb;
  font-size: 12px;
}
</style>
