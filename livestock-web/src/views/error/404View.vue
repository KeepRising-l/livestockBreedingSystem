<template>
  <div>
    <h2 class="page-title">404 - 页面不存在</h2>
    <el-card class="center-card">
      <el-result icon="warning" title="404" sub-title="抱歉，您访问的页面不存在">
        <template #extra>
          <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #0e2f47; }
.center-card { max-width: 500px; margin: 40px auto; text-align: center; }
</style>
