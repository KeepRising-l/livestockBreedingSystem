<template>
  <div>
    <h2 class="page-title">403 - 无权限</h2>
    <el-card class="center-card">
      <el-result icon="warning" title="403" sub-title="抱歉，您没有权限访问此页面">
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
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #14532d; }
.center-card { max-width: 500px; margin: 40px auto; text-align: center; }
</style>
