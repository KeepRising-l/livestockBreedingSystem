<template>
  <VChart theme="tech" v-bind="$attrs" />
</template>

<script setup lang="ts">
/**
 * TechChart —— vue-echarts 的轻量包装。
 *
 * 作用：为全站图表默认注入 'tech' 暗色科技主题，避免每个页面重复写 theme="tech"。
 * 用法与原 vue-echarts 完全一致：把 `import VChart from 'vue-echarts'`
 * 换成 `import VChart from '@/components/TechChart.vue'` 即可，模板无需改动。
 */
import VChart from 'vue-echarts'
import '@/utils/echarts-theme'

defineOptions({ inheritAttrs: false })
</script>
