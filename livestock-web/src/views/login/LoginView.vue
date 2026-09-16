<template>
  <div class="login-page">
    <!-- 全息背景层：login-bg2 图像 + 数据网格 + 扫描线 -->
    <div class="bg-layer"></div>
    <div class="bg-grid"></div>
    <div class="bg-vignette"></div>
    <div class="bg-scanline"></div>

    <!-- 左侧：品牌与能力标识（仅大屏展示，不承载业务信息） -->
    <aside class="brand-panel">
      <div class="brand-head">
        <span class="tech-pulse"></span>
        <span class="brand-status">SYSTEM ONLINE</span>
      </div>

      <h1 class="brand-title">智能养殖信息管理系统</h1>
      <p class="brand-sub">Smart Livestock Information Management System</p>

      <div class="brand-ring">
        <div class="ring ring-outer"></div>
        <div class="ring ring-mid"></div>
        <div class="ring ring-inner"></div>
        <div class="ring-core">AI</div>
      </div>

      <ul class="brand-tags">
        <li v-for="tag in capabilities" :key="tag">
          <span class="tag-dot"></span>{{ tag }}
        </li>
      </ul>
    </aside>

    <!-- 右侧：登录面板 -->
    <section class="login-card hud-frame">
      <i class="corner corner-tr"></i>
      <i class="corner corner-bl"></i>
      <div class="card-glowline"></div>

      <header class="card-logo">
        <div class="logo-badge">
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <path
              d="M4 20V9.5L12 4l8 5.5V20h-5.5v-6h-5v6H4z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linejoin="round"
            />
          </svg>
        </div>
        <h2>智能养殖信息管理系统</h2>
        <p>Smart Livestock Information Management System</p>
      </header>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入账号或手机号"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            prefix-icon="Lock"
          />
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
    </section>
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
  username: '',
  password: '',
})

/** 品牌面板展示的四大能力标签（纯装饰文案，不含业务数据） */
const capabilities = ['数据实时采集', '智能分析决策', '全流程溯源', '可视化监控']

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
  position: relative;
  min-height: 100dvh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 480px;
  align-items: center;
  gap: 24px;
  padding: 40px 7% 40px 5%;
  overflow: hidden;
  background: #02071a;
}

/* ---------------------------------------------------- 背景层 */
.bg-layer {
  position: absolute;
  inset: 0;
  background: url('/login-bg2.jpg') no-repeat center center / cover;
  /* 缓慢推近，营造"全息投影"的呼吸感 */
  animation: bg-drift 26s ease-in-out infinite alternate;
}

@keyframes bg-drift {
  from { transform: scale(1); }
  to { transform: scale(1.06); }
}

/* 数据网格：让背景具备"数据化"底纹 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.07) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(120% 100% at 50% 50%, #000 30%, transparent 85%);
  -webkit-mask-image: radial-gradient(120% 100% at 50% 50%, #000 30%, transparent 85%);
  animation: grid-slide 12s linear infinite;
}

@keyframes grid-slide {
  from { background-position: 0 0, 0 0; }
  to { background-position: 44px 44px, 44px 44px; }
}

/* 左右明暗控制：左侧保留全息细节，右侧压暗以便承载表单 */
.bg-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(100deg,
      rgba(2, 7, 26, 0.34) 0%,
      rgba(2, 7, 26, 0.30) 42%,
      rgba(2, 7, 26, 0.82) 68%,
      rgba(2, 7, 26, 0.94) 100%),
    radial-gradient(120% 90% at 50% 50%, transparent 42%, rgba(2, 7, 26, 0.72) 100%);
}

/* 扫描线：自上而下循环掠过 */
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

/* ---------------------------------------------------- 品牌面板 */
.brand-panel {
  position: relative;
  z-index: 1;
  max-width: 520px;
  animation: fade-up 0.8s ease both;
}

.brand-head {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 5px 14px;
  border: 1px solid rgba(34, 211, 238, 0.4);
  border-radius: 999px;
  background: rgba(6, 24, 48, 0.5);
  backdrop-filter: blur(10px);
  margin-bottom: 22px;
}

.brand-status {
  font-family: var(--tech-font-mono);
  font-size: 11px;
  letter-spacing: 2px;
  color: #7fe6f7;
}

.brand-title {
  margin: 0 0 12px;
  font-size: 36px;
  line-height: 1.28;
  font-weight: 700;
  letter-spacing: 3px;
  color: #eaf6ff;
  text-shadow: 0 0 34px rgba(34, 211, 238, 0.55), 0 0 80px rgba(43, 127, 255, 0.3);
}

.brand-sub {
  margin: 0 0 30px;
  font-size: 12px;
  letter-spacing: 1.6px;
  color: #7fa8c9;
  text-transform: uppercase;
}

/* 旋转 HUD 环：整体保持半透明，作为"投影叠层"而非实体色块，避免遮挡背景主体 */
.brand-ring {
  position: relative;
  width: 116px;
  height: 116px;
  margin-bottom: 28px;
  opacity: 0.7;

  .ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
  }

  .ring-outer {
    border: 1px dashed rgba(34, 211, 238, 0.4);
    animation: spin 18s linear infinite;
  }

  .ring-mid {
    inset: 13px;
    border: 1px solid transparent;
    border-top-color: rgba(34, 211, 238, 0.85);
    border-right-color: rgba(34, 211, 238, 0.2);
    animation: spin 6s linear infinite reverse;
  }

  .ring-inner {
    inset: 27px;
    border: 1px solid rgba(43, 127, 255, 0.34);
    animation: spin 10s linear infinite;
  }

  .ring-core {
    position: absolute;
    inset: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.22), transparent 72%);
    font-family: var(--tech-font-mono);
    font-size: 13px;
    letter-spacing: 1px;
    color: #a8e6f5;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.brand-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;

  li {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 15px;
    font-size: 12.5px;
    letter-spacing: 0.8px;
    color: #bcdcf0;
    border: 1px solid rgba(34, 211, 238, 0.28);
    border-radius: 6px;
    background: rgba(6, 24, 48, 0.42);
    backdrop-filter: blur(10px);
    transition: border-color 0.25s ease, color 0.25s ease, transform 0.25s ease;

    &:hover {
      border-color: rgba(34, 211, 238, 0.7);
      color: #eaf6ff;
      transform: translateY(-2px);
    }
  }

  .tag-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #22d3ee;
    box-shadow: 0 0 8px #22d3ee;
  }
}

@keyframes fade-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---------------------------------------------------- 登录面板 */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 42px 38px 30px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(9, 34, 64, 0.86), rgba(4, 17, 38, 0.92));
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 30px 80px rgba(0, 6, 20, 0.66), 0 0 60px rgba(34, 211, 238, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  animation: card-in 0.75s cubic-bezier(0.22, 1, 0.36, 1) both;

  /* 面板四角 HUD 标（TL/BR 由全局 .hud-corners 提供，此处补齐 TR/BL） */
  .corner {
    position: absolute;
    width: 18px;
    height: 18px;
    border-color: #22d3ee;
    opacity: 0.9;
    pointer-events: none;

    &.corner-tr {
      top: -1px;
      right: -1px;
      border-top: 2px solid;
      border-right: 2px solid;
      border-top-right-radius: 5px;
    }

    &.corner-bl {
      left: -1px;
      bottom: -1px;
      border-left: 2px solid;
      border-bottom: 2px solid;
      border-bottom-left-radius: 5px;
    }
  }
}

/* 顶部流动全息线 */
.card-glowline {
  position: absolute;
  top: -1px;
  left: 12%;
  right: 12%;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, #22d3ee, transparent);
  filter: blur(0.5px);
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

.card-logo {
  text-align: center;
  margin-bottom: 28px;

  .logo-badge {
    width: 52px;
    height: 52px;
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    color: #7fe6f7;
    border: 1px solid rgba(34, 211, 238, 0.42);
    background: radial-gradient(circle at 50% 30%, rgba(34, 211, 238, 0.28), rgba(43, 127, 255, 0.06));
    box-shadow: 0 0 26px rgba(34, 211, 238, 0.35), inset 0 0 18px rgba(34, 211, 238, 0.18);
  }

  h2 {
    margin: 0 0 8px;
    font-size: 21px;
    font-weight: 600;
    letter-spacing: 2px;
    line-height: 1.4;
    color: #eaf6ff;
    text-wrap: balance;
    text-shadow: 0 0 22px rgba(34, 211, 238, 0.4);
  }

  p {
    margin: 0;
    font-size: 11px;
    letter-spacing: 0.9px;
    color: #7fa8c9;
    text-transform: uppercase;
  }
}

.w-full { width: 100%; }

/* 登录按钮：渐变 + 高光扫过 */
.login-btn {
  height: 46px;
  font-size: 16px;
  letter-spacing: 6px;
  border-radius: 9px;
  background: linear-gradient(135deg, #14b8d8 0%, #2b7fff 100%);
  border: none;
  color: #f4fdff;
  box-shadow: 0 12px 30px rgba(43, 127, 255, 0.34);

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
  margin: 16px 0 10px;

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

.tips {
  text-align: center;
  font-size: 12px;
  color: #6d8dab;
}

/* 表单控件：深色发光输入框 */
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
  margin-bottom: 20px;
}

/* ---------------------------------------------------- 响应式 */
@media (max-width: 1080px) {
  .login-page {
    grid-template-columns: minmax(0, 1fr) minmax(0, 420px);
    padding: 32px 5%;
  }

  .brand-title { font-size: 28px; letter-spacing: 2px; }
  .brand-ring { width: 108px; height: 108px; }
}

@media (max-width: 860px) {
  .login-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  /* 小屏隐藏装饰性品牌面板，聚焦登录本身 */
  .brand-panel { display: none; }

  .login-card {
    width: 100%;
    max-width: 420px;
  }

  /* 背景整体压暗，保证表单可读性 */
  .bg-vignette {
    background: linear-gradient(180deg, rgba(2, 7, 26, 0.86) 0%, rgba(2, 7, 26, 0.92) 100%);
  }
}
</style>
