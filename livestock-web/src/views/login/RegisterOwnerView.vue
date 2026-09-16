<template>
  <div class="register-page">
    <!-- 全息背景层：与登录页共用 login-bg2 视觉语言 -->
    <div class="bg-layer"></div>
    <div class="bg-grid"></div>
    <div class="bg-vignette"></div>
    <div class="bg-scanline"></div>

    <section class="register-card hud-corners">
      <i class="corner corner-tr"></i>
      <i class="corner corner-bl"></i>
      <div class="card-glowline"></div>

      <header class="card-head">
        <div class="head-badge">
          <el-icon :size="20"><OfficeBuilding /></el-icon>
        </div>
        <h1>注册养殖场</h1>
        <p>CREATE FARM ACCOUNT</p>
      </header>

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
          <el-button type="primary" :loading="loading" class="w-full submit-btn" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="links">
        <router-link to="/login">已有账号？去登录</router-link>
      </div>
    </section>
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
.register-page {
  position: relative;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  overflow: hidden;
  background: #02071a;
}

/* ---------------------------------------------------- 背景层（与登录页一致） */
.bg-layer {
  position: absolute;
  inset: 0;
  background: url('/login-bg2.jpg') no-repeat center center / cover;
  animation: bg-drift 26s ease-in-out infinite alternate;
}

@keyframes bg-drift {
  from { transform: scale(1); }
  to { transform: scale(1.06); }
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.07) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(120% 100% at 50% 50%, #000 30%, transparent 85%);
  -webkit-mask-image: radial-gradient(120% 100% at 50% 50%, #000 30%, transparent 85%);
}

.bg-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(2, 7, 26, 0.72) 0%, rgba(2, 7, 26, 0.88) 100%),
    radial-gradient(100% 80% at 50% 50%, transparent 30%, rgba(2, 7, 26, 0.8) 100%);
}

.bg-scanline {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 180px;
    background: linear-gradient(180deg, transparent, rgba(34, 211, 238, 0.14), transparent);
    animation: scan 7s linear infinite;
  }
}

@keyframes scan {
  0% { top: -200px; }
  100% { top: 100%; }
}

/* ---------------------------------------------------- 注册面板 */
.register-card {
  position: relative;
  z-index: 1;
  width: 480px;
  max-width: 100%;
  max-height: calc(100dvh - 48px);
  overflow-y: auto;
  padding: 34px 38px 28px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(9, 34, 64, 0.88), rgba(4, 17, 38, 0.94));
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 30px 80px rgba(0, 6, 20, 0.66), 0 0 60px rgba(34, 211, 238, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  animation: card-in 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;

  .corner {
    position: absolute;
    width: 18px;
    height: 18px;
    border-color: #22d3ee;
    opacity: 0.9;
    pointer-events: none;

    &.corner-tr {
      top: 7px;
      right: 7px;
      border-top: 2px solid;
      border-right: 2px solid;
      border-top-right-radius: 5px;
    }

    &.corner-bl {
      left: 7px;
      bottom: 7px;
      border-left: 2px solid;
      border-bottom: 2px solid;
      border-bottom-left-radius: 5px;
    }
  }
}

.card-glowline {
  position: absolute;
  top: 0;
  left: 12%;
  right: 12%;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, #22d3ee, transparent);
  animation: glowline 3.4s ease-in-out infinite;
}

@keyframes glowline {
  0%, 100% { opacity: 0.35; transform: scaleX(0.75); }
  50% { opacity: 1; transform: scaleX(1); }
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(26px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.card-head {
  text-align: center;
  margin-bottom: 24px;

  .head-badge {
    width: 46px;
    height: 46px;
    margin: 0 auto 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    color: #7fe6f7;
    border: 1px solid rgba(34, 211, 238, 0.42);
    background: radial-gradient(circle at 50% 30%, rgba(34, 211, 238, 0.28), rgba(43, 127, 255, 0.06));
    box-shadow: 0 0 26px rgba(34, 211, 238, 0.35), inset 0 0 18px rgba(34, 211, 238, 0.18);
  }

  h1 {
    margin: 0 0 7px;
    font-size: 21px;
    font-weight: 600;
    letter-spacing: 2px;
    color: #eaf6ff;
    text-shadow: 0 0 22px rgba(34, 211, 238, 0.4);
  }

  p {
    margin: 0;
    font-size: 11px;
    letter-spacing: 1.6px;
    color: #7fa8c9;
  }
}

.w-full { width: 100%; }

.submit-btn {
  height: 46px;
  font-size: 16px;
  letter-spacing: 6px;
  border-radius: 9px;
  background: linear-gradient(135deg, #14b8d8 0%, #2b7fff 100%);
  border: none;
  color: #f4fdff;
  box-shadow: 0 12px 30px rgba(43, 127, 255, 0.34);
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 45%;
    left: -60%;
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.42), transparent);
    transform: skewX(-18deg);
    transition: left 0.6s ease;
  }

  &:hover:not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 16px 38px rgba(34, 211, 238, 0.46);

    &::after { left: 115%; }
  }

  &:active:not(.is-loading) { transform: translateY(0) scale(0.985); }
}

.links {
  text-align: center;
  margin-top: 12px;

  a {
    font-size: 13px;
    color: #4fd8ef;
    text-decoration: none;
    transition: color 0.2s ease, text-shadow 0.2s ease;

    &:hover {
      color: #7fe6f7;
      text-shadow: 0 0 14px rgba(34, 211, 238, 0.7);
    }
  }
}

.species-group {
  display: flex;
  gap: 22px;
}

/* 表单控件：深色发光输入框（与登录页一致） */
:deep(.el-input__wrapper) {
  background-color: rgba(3, 14, 32, 0.72) !important;
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.24) inset !important;
  border-radius: 9px;

  &:hover {
    box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.45) inset !important;
  }

  &.is-focus {
    background-color: rgba(3, 16, 36, 0.92) !important;
    box-shadow: 0 0 0 1px #22d3ee inset, 0 0 20px rgba(34, 211, 238, 0.32) !important;
  }
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-checkbox__label) {
  color: #cfe4f5;
}
</style>
