import { registerTheme } from 'echarts/core'

/**
 * ECharts 生态自然主题（'tech'，风格：Organic Biophilic）
 *
 * 亮色背景下统一注册全局图表主题，与 design-system/smart-livestock/MASTER.md 同源：
 *   - 透明画布，交由卡片的白色面板承载
 *   - 大地绿主导的离散色板（草绿/天空蓝/收获金/沃土棕/松针青），与全站 --tech-* 令牌同源
 *   - 坐标轴、分隔线、图例、提示框统一柔和自然化
 *
 * 各页面 option 中显式声明的属性优先级高于主题，因此不会影响已有数据配置。
 */

/** 离散色板：大地绿 → 天空蓝 → 收获金 → 草叶绿 → 沃土棕 → 松针青 → 抹茶绿 → 石板灰 */
export const TECH_CHART_PALETTE = [
  '#15803d',
  '#0ea5e9',
  '#a16207',
  '#22c55e',
  '#8b4513',
  '#0f766e',
  '#84cc16',
  '#94a3b8',
]

/** 供业务复用的语义色（与视图内配色保持一致；键名为历史命名，cyan 现持有主色绿） */
export const TECH_CHART_COLORS = {
  cyan: '#15803d',
  blue: '#0ea5e9',
  green: '#22c55e',
  amber: '#a16207',
  violet: '#8b4513',
  rose: '#dc2626',
  slate: '#64748b',
}

const AXIS_LINE = 'rgba(21,128,61, 0.28)'
const AXIS_SPLIT = 'rgba(21,128,61, 0.12)'
const AXIS_LABEL = '#64748b'

registerTheme('tech', {
  color: TECH_CHART_PALETTE,
  backgroundColor: 'transparent',

  textStyle: {
    color: '#334155',
    fontFamily: "'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif",
  },

  title: {
    textStyle: { color: '#14532d', fontWeight: 600 },
    subtextStyle: { color: '#64748b' },
  },

  legend: {
    textStyle: { color: '#475569' },
    inactiveColor: '#64748b',
    itemWidth: 12,
    itemHeight: 8,
  },

  tooltip: {
    backgroundColor: '#ffffff',
    borderColor: 'rgba(21,128,61, 0.35)',
    borderWidth: 1,
    padding: [10, 14],
    textStyle: { color: '#14532d', fontSize: 13 },
    extraCssText: 'backdrop-filter: blur(12px); border-radius: 8px; box-shadow: 0 12px 32px rgba(23,58,40, 0.16);',
    axisPointer: {
      lineStyle: { color: 'rgba(21,128,61, 0.6)', width: 1, type: 'dashed' },
      crossStyle: { color: 'rgba(21,128,61, 0.6)' },
      shadowStyle: { color: 'rgba(21,128,61, 0.08)' },
      label: {
        backgroundColor: '#ffffff',
        borderColor: 'rgba(21,128,61, 0.4)',
        borderWidth: 1,
        color: '#14532d',
      },
    },
  },

  grid: {
    borderColor: AXIS_SPLIT,
    containLabel: true,
  },

  /* ---- 类目轴 ---- */
  categoryAxis: {
    axisLine: { show: true, lineStyle: { color: AXIS_LINE } },
    axisTick: { show: false, lineStyle: { color: AXIS_LINE } },
    axisLabel: { color: AXIS_LABEL, fontSize: 12 },
    splitLine: { show: false, lineStyle: { color: AXIS_SPLIT } },
    splitArea: { show: false },
  },

  /* ---- 数值轴 ---- */
  valueAxis: {
    axisLine: { show: false, lineStyle: { color: AXIS_LINE } },
    axisTick: { show: false, lineStyle: { color: AXIS_LINE } },
    axisLabel: { color: AXIS_LABEL, fontSize: 12 },
    splitLine: { show: true, lineStyle: { color: AXIS_SPLIT, type: 'dashed' } },
    splitArea: { show: false },
  },

  line: {
    symbol: 'circle',
    symbolSize: 6,
    smooth: true,
    lineStyle: { width: 2.5 },
    itemStyle: { borderWidth: 0 },
  },

  bar: {
    itemStyle: { borderRadius: [6, 6, 0, 0] },
  },

  pie: {
    itemStyle: { borderColor: '#ffffff', borderWidth: 2 },
    label: { color: '#334155' },
    labelLine: { lineStyle: { color: AXIS_LINE } },
  },

  /* 其他可能被用到的图表类型，给出一致的文字色兜底 */
  scatter: { itemStyle: { borderWidth: 0 } },
  radar: {
    axisName: { color: '#475569' },
    splitLine: { lineStyle: { color: AXIS_SPLIT } },
    splitArea: { areaStyle: { color: ['rgba(34,197,94,0.03)', 'rgba(34,197,94,0.07)'] } },
    axisLine: { lineStyle: { color: AXIS_LINE } },
  },
  gauge: {
    axisLine: { lineStyle: { color: [[1, 'rgba(21,128,61, 0.18)']] } },
    axisLabel: { color: AXIS_LABEL },
    detail: { color: '#15803d' },
    title: { color: '#475569' },
  },
  dataZoom: {
    textStyle: { color: '#475569' },
    borderColor: AXIS_LINE,
    fillerColor: 'rgba(21,128,61, 0.14)',
    handleStyle: { color: '#15803d' },
    dataBackground: {
      lineStyle: { color: AXIS_LINE },
      areaStyle: { color: 'rgba(21,128,61, 0.1)' },
    },
  },
})
