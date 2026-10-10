import {
  AlarmClock, ArrowDown, ArrowLeft, Bell, Box, Connection, DataAnalysis, Delete,
  Download, Expand, Files, FirstAidKit, Fold, Food, Grid, House,
  InfoFilled, Lock, Money, Notebook, OfficeBuilding, Plus, Refresh,
  Sell, Setting, Stamp, Suitcase, TrendCharts, Upload, User, UserFilled,
} from '@element-plus/icons-vue'
import type { App } from 'vue'

/**
 * 项目实际用到的 Element Plus 图标白名单（31 个）。
 *
 * 这里必须用「具名导入 + 显式映射」，不要改回 `import * as Icons` 再按字符串取。
 * 原因：`import *` 配合动态属性访问（Icons[name]）会让打包器无法 tree-shaking，
 * 整个图标库（300+ 组件）都会进产物；具名导入后未用到的图标会被静态剔除。
 * 组件注册名保持与图标原名一致 —— 模板里的 <component :is="'Grid'" /> 这类
 * 字符串引用依赖同名注册，改名会导致图标空白。
 */
const ICONS = {
  AlarmClock, ArrowDown, ArrowLeft, Bell, Box, Connection, DataAnalysis, Delete,
  Download, Expand, Files, FirstAidKit, Fold, Food, Grid, House,
  InfoFilled, Lock, Money, Notebook, OfficeBuilding, Plus, Refresh,
  Sell, Setting, Stamp, Suitcase, TrendCharts, Upload, User, UserFilled,
}

export function registerIcons(app: App) {
  for (const [name, comp] of Object.entries(ICONS)) {
    app.component(name, comp)
  }
}
