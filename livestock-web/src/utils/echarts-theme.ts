import { registerTheme } from 'echarts/core'

/**
 * ECharts 科技主题（'tech'）
 *
 * 深色背景下 ECharts 默认主题的坐标轴/图例/文字是深灰色，几乎不可读。
 * 这里注册一套与 login-bg2 视觉语言一致的全局主题：
 *   - 透明画布，交由卡片的玻璃面板承载
 *   - 青色系离散色板（与全站 --tech-* 令牌同源）
 *   - 坐标轴、分隔线、图例、提示框统一暗色霓虹化
 *
 * 各页面 option 中显式声明的属性优先级高于主题，因此不会影响已有数据配置。
 */

/** 离散色板：青 → 蓝 → 薄荷 → 琥珀 → 紫 → 玫红 */
export const TECH_CHART_PALETTE = [
  '#22d3ee',
  '#4a95ff',
  '#00e6a8',
  '#ffb020',
  '#a78bfa',
  '#ff6b85',
  '#7fe6f7',
  '#5b7f9e',
]

/** 供业务复用的语义色（与视图内配色保持一致） */
export const TECH_CHART_COLORS = {
  cyan: '#22d3ee',
  blue: '#4a95ff',
  green: '#00e6a8',
  amber: '#ffb020',
  violet: '#a78bfa',
  rose: '#ff6b85',
  slate: '#5b7f9e',
}

const AXIS_LINE = 'rgba(34, 211, 238, 0.28)'
const AXIS_SPLIT = 'rgba(34, 211, 238, 0.12)'
const AXIS_LABEL = '#8fa9bf'

registerTheme('tech', {
  color: TECH_CHART_PALETTE,
  backgroundColor: 'transparent',

  textStyle: {
    color: '#cfe4f5',
    fontFamily: "'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif",
  },

  title: {
    textStyle: { color: '#eaf6ff', fontWeight: 600 },
    subtextStyle: { color: '#8fa9bf' },
  },

  legend: {
    textStyle: { color: '#a8c6e0' },
    inactiveColor: '#5b7f9e',
    itemWidth: 12,
    itemHeight: 8,
  },

  tooltip: {
    backgroundColor: 'rgba(8, 28, 54, 0.96)',
    borderColor: 'rgba(34, 211, 238, 0.35)',
    borderWidth: 1,
    padding: [10, 14],
    textStyle: { color: '#eaf6ff', fontSize: 13 },
    extraCssText: 'backdrop-filter: blur(12px); border-radius: 8px; box-shadow: 0 12px 32px rgba(0,6,20,.6);',
    axisPointer: {
      lineStyle: { color: 'rgba(34, 211, 238, 0.6)', width: 1, type: 'dashed' },
      crossStyle: { color: 'rgba(34, 211, 238, 0.6)' },
      shadowStyle: { color: 'rgba(34, 211, 238, 0.08)' },
      label: {
        backgroundColor: 'rgba(8, 28, 54, 0.96)',
        borderColor: 'rgba(34, 211, 238, 0.4)',
        borderWidth: 1,
        color: '#eaf6ff',
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
    smooth: false,
    lineStyle: { width: 2.5 },
    itemStyle: { borderWidth: 0 },
  },

  bar: {
    itemStyle: { borderRadius: [4, 4, 0, 0] },
  },

  pie: {
    itemStyle: { borderColor: 'rgba(2, 7, 26, 0.85)', borderWidth: 2 },
    label: { color: '#cfe4f5' },
    labelLine: { lineStyle: { color: AXIS_LINE } },
  },

  /* 其他可能被用到的图表类型，给出一致的文字色兜底 */
  scatter: { itemStyle: { borderWidth: 0 } },
  radar: {
    axisName: { color: '#a8c6e0' },
    splitLine: { lineStyle: { color: AXIS_SPLIT } },
    splitArea: { areaStyle: { color: ['rgba(34,211,238,0.03)', 'rgba(34,211,238,0.07)'] } },
    axisLine: { lineStyle: { color: AXIS_LINE } },
  },
  gauge: {
    axisLine: { lineStyle: { color: [[1, 'rgba(34, 211, 238, 0.18)']] } },
    axisLabel: { color: AXIS_LABEL },
    detail: { color: '#22d3ee' },
    title: { color: '#a8c6e0' },
  },
  dataZoom: {
    textStyle: { color: '#a8c6e0' },
    borderColor: AXIS_LINE,
    fillerColor: 'rgba(34, 211, 238, 0.14)',
    handleStyle: { color: '#22d3ee' },
    dataBackground: {
      lineStyle: { color: AXIS_LINE },
      areaStyle: { color: 'rgba(34, 211, 238, 0.1)' },
    },
  },
})
