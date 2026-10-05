<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <div class="aside-glow"></div>
      <Sidebar :is-collapse="isCollapse" />
    </el-aside>
    <el-container class="main-container">
      <el-header class="app-header">
        <HeaderBar :is-collapse="isCollapse" @toggle="isCollapse = !isCollapse" />
      </el-header>
      <el-main class="app-main">
        <div class="main-grid"></div>
        <div class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="tech-page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import HeaderBar from './components/HeaderBar.vue'

const isCollapse = ref(false)
</script>

<style scoped lang="scss">
.app-layout {
  height: 100vh;
  background: var(--tech-bg-deep);
}

/* ---------------------------------------------------- 侧边导航 */
.app-aside {
  position: relative;
  background: linear-gradient(180deg, #e6f6ea 0%, #e7f6eb 62%, #bbf7d0 100%);
  border-right: 1px solid rgba(21,128,61, 0.16);
  transition: width 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;

  /* 右缘自然光带 */
  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(180deg, transparent, rgba(21,128,61, 0.4), transparent);
    opacity: 0.6;
  }
}

.aside-glow {
  position: absolute;
  top: -80px;
  left: -60px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(21,128,61, 0.22), transparent 68%);
  pointer-events: none;
}

.main-container {
  min-width: 0;
}

/* ---------------------------------------------------- 顶部栏 */
.app-header {
  height: 58px !important;
  padding: 0 18px;
  display: flex;
  align-items: center;
  background: linear-gradient(90deg, rgba(232,247,235, 0.95), rgba(206,236,214, 0.92));
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(21,128,61, 0.16);
  box-shadow: 0 6px 24px rgba(23,58,40, 0.08);
  position: relative;
  z-index: 2;

  /* 底沿柔和光线 */
  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(21,128,61, 0.4), transparent);
    opacity: 0.5;
  }
}

/* ---------------------------------------------------- 内容区 */
.app-main {
  position: relative;
  padding: 20px;
  overflow-y: auto;
  background: transparent;
  min-height: 0;
}

/* 内容区有机光晕底纹（替代原数据网格） */
.main-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(720px 420px at 18% 0%, rgba(34,197,94, 0.08), transparent 65%),
    radial-gradient(640px 400px at 88% 30%, rgba(14,165,233, 0.06), transparent 62%),
    radial-gradient(560px 360px at 55% 100%, rgba(161,98,7, 0.05), transparent 65%);
  background-size: 100% 100%, 100% 100%, 100% 100%;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.9), transparent 82%);
  -webkit-mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.9), transparent 82%);
}

.main-content {
  position: relative;
  z-index: 1;
}

/* 页面切换动效：淡入 + 轻微上浮 */
.tech-page-enter-active,
.tech-page-leave-active {
  transition: opacity 0.26s ease, transform 0.26s ease;
}

.tech-page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.tech-page-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
