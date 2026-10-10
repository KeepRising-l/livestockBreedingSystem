/// <reference types="vitest/config" />
import { existsSync, readdirSync } from 'node:fs'
import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

/**
 * Element Plus 按需引入（ElementPlusResolver）会把组件样式编译成
 * `element-plus/es/components/<name>/style/css` 这类深层导入。
 *
 * 这类深层模块 Vite 启动扫描时常常扫不到，于是页面首次用到某个组件时才「现场发现」，
 * 触发 [optimizer] bundling dependencies → "optimized dependencies changed. reloading"
 * —— 整页强制刷新，这就是开发时点菜单"卡一下/闪一下"的根源。
 *
 * 坑：optimizeDeps.include 里的通配符是在**文件系统**上展开的，写 `.../style/css`
 * 匹配不到任何文件（真实文件名是 css.mjs），glob 会静默失效。所以这里改成直接枚举
 * 磁盘上真实存在的组件样式，保证启动时一次性全部预构建完。
 */
const EP_COMPONENTS_DIR = resolve(__dirname, 'node_modules/element-plus/es/components')
const epComponentStyleDeps = existsSync(EP_COMPONENTS_DIR)
  ? readdirSync(EP_COMPONENTS_DIR)
      .filter((name) => existsSync(resolve(EP_COMPONENTS_DIR, name, 'style/css.mjs')))
      .map((name) => `element-plus/es/components/${name}/style/css`)
  : []

export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需自动导入（组件 + 样式），去掉全量引入以提升渲染性能
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // 显式预构建：见上方注释。目标是消灭开发期「运行中发现新依赖 → 重新预构建 → 整页刷新」
  optimizeDeps: {
    include: [
      'vue', 'vue-router', 'pinia', 'axios', 'dayjs', '@vueuse/core',
      'element-plus/es',
      '@element-plus/icons-vue',
      'echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers',
      'vue-echarts',
      ...epComponentStyleDeps,
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'happy-dom',
    include: ['src/**/*.{spec,test}.ts'],
  },
})
