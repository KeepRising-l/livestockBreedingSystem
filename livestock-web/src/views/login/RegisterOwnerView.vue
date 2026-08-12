<template>
  <div class="login-container">
    <div class="register-card">
      <h1 class="title">注册养殖场</h1>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleRegister">
        <el-form-item prop="farm_name">
          <el-input v-model="form.farm_name" placeholder="养殖场名称" />
        </el-form-item>
        <el-form-item prop="livestock_types">
          <el-checkbox-group v-model="livestockList" class="species-group">
            <el-checkbox label="牛" />
            <el-checkbox label="羊" />
            <el-checkbox label="猪" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="登录账号" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="密码（最少6位）" />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="确认密码" />
        </el-form-item>
        <el-form-item prop="real_name">
          <el-input v-model="form.real_name" placeholder="您的姓名" />
        </el-form-item>
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="w-full" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="links">
        <router-link to="/login">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { registerOwnerApi } from '@/api/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const livestockList = ref<string[]>(['牛'])

const form = reactive({
  farm_name: '',
  username: '',
  password: '',
  confirmPassword: '',
  real_name: '',
  phone: '',
})

const validatePass = (_rule: any, value: string, callback: any) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  farm_name: [{ required: true, message: '请输入养殖场名称', trigger: 'blur' }],
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '请输入有效手机号', trigger: 'blur' }],
}

async function handleRegister() {
  if (livestockList.value.length === 0) {
    ElMessage.warning('请至少选择一种养殖种类')
    return
  }
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await registerOwnerApi({
      farm_name: form.farm_name,
      username: form.username,
      password: form.password,
      real_name: form.real_name,
      phone: form.phone,
      livestock_types: livestockList.value.join(','),
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // 错误已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 20px 7% 20px 20px;
  background: url('/login-bg.jpg') no-repeat center center / cover;
  position: relative;
  overflow: hidden;

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
.register-card {
  position: relative;
  z-index: 1;
  width: 460px;
  max-width: 100%;
  padding: 32px 36px 28px;
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
}
.title {
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  color: #0a4a66;
  margin-bottom: 24px;
  letter-spacing: 1px;
}
.w-full {
  width: 100%;
}
.links {
  text-align: center;
  margin-top: 12px;
  a { color: #0ea5c9; font-size: 13px; &:hover { color: #0b85a5; } }
}
.species-group {
  display: flex;
  gap: 20px;
}
</style>
