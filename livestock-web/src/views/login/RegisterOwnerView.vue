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
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  padding: 20px;
}
.register-card {
  width: 460px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  font-size: 22px;
  color: #2E7D32;
  margin-bottom: 28px;
}
.w-full {
  width: 100%;
}
.links {
  text-align: center;
  a { color: #2E7D32; font-size: 13px; }
}
.species-group {
  display: flex;
  gap: 20px;
}
</style>
