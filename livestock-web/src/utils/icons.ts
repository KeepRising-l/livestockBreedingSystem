import * as Icons from '@element-plus/icons-vue'
import type { App, Component } from 'vue'

/**
 * 项目实际用到的 Element Plus 图标白名单。
 * 之前是全量注册 300+ 个图标，拖慢每次组件渲染；这里只注册用到的，避免首屏 JS 和运行时开销。
 */
const ICON_NAMES = [
  'ArrowDown', 'ArrowLeft', 'Bell', 'Box', 'Connection', 'DataAnalysis', 'Delete',
  'Download', 'Expand', 'Files', 'FirstAidKit', 'Fold', 'Food', 'Grid', 'House',
  'InfoFilled', 'Lock', 'Money', 'Notebook', 'OfficeBuilding', 'Plus', 'Refresh',
  'Sell', 'Setting', 'Stamp', 'Suitcase', 'TrendCharts', 'Upload', 'User', 'UserFilled',
]

export function registerIcons(app: App) {
  const all = Icons as Record<string, Component>
  for (const name of ICON_NAMES) {
    if (all[name]) app.component(name, all[name])
  }
}
