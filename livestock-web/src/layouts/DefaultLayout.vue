<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <Sidebar :is-collapse="isCollapse" />
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <HeaderBar :is-collapse="isCollapse" @toggle="isCollapse = !isCollapse" />
      </el-header>
      <el-main>
        <router-view />
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
}
.app-aside {
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
}
.app-header {
  height: 56px !important;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  padding: 0 16px;
}
.el-main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
