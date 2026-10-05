<template>
  <div
    class="metric-card"
    :class="{ 'is-clickable': clickable }"
    :style="{ '--mc-color': color, '--mc-color-soft': colorSoft }"
    @click="clickable && emit('click')"
  >
    <div class="mc-top">
      <div v-if="icon" class="mc-icon">
        <el-icon :size="20"><component :is="icon" /></el-icon>
      </div>
      <div class="mc-text">
        <div class="mc-value">
          <!-- 数字带滚动动画；非数字（如养殖场名）直接展示 -->
          <span class="mc-num">{{ isNumeric ? formatted : textValue }}</span>
          <span v-if="unit" class="mc-unit">{{ unit }}</span>
        </div>
        <div class="mc-label">{{ label }}</div>
      </div>
    </div>
    <div v-if="sub" class="mc-sub">{{ sub }}</div>
    <div v-if="trendText" class="mc-trend" :class="trendUp ? 'is-up' : 'is-down'">
      {{ trendUp ? '▲' : '▼' }} {{ trendText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useCountUp } from '@/composables/useCountUp'

const props = withDefaults(
  defineProps<{
    label: string
    /** 数值（number 会滚动；string 原样显示） */
    value: number | string | null | undefined
    /** 单位，如「头」「元」「%」 */
    unit?: string
    /** 主色（决定数字色、图标底色） */
    color?: string
    /** 图标名（Element Plus 图标，需在 utils/icons.ts 白名单内） */
    icon?: string
    /** 副标题 */
    sub?: string
    /** 环比文案，如「较昨日 +2」，配合 trendUp 决定箭头方向 */
    trendText?: string
    trendUp?: boolean
    clickable?: boolean
  }>(),
  {
    unit: '',
    color: '#15803d',
    icon: '',
    sub: '',
    trendText: '',
    trendUp: true,
    clickable: false,
  },
)

const emit = defineEmits<{ click: [] }>()

const numericValue = computed(() => (typeof props.value === 'number' ? props.value : null))
const isNumeric = computed(() => typeof props.value === 'number')
const textValue = computed(() => (props.value === null || props.value === undefined ? '-' : String(props.value)))

const { display, decimals } = useCountUp(numericValue, { duration: 900 })

/** 千分位 + 按需小数位 */
const formatted = computed(() => {
  const n = display.value ?? 0
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals.value,
    maximumFractionDigits: decimals.value,
  })
})

/** 主色的浅色版本（图标底色 / 顶部渐变） */
const colorSoft = computed(() => {
  const hex = (props.color || '#15803d').replace('#', '')
  const full = hex.length === 3 ? hex.split('').map((c) => c + c).join('') : hex
  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, 0.12)`
})
</script>

<style scoped lang="scss">
.metric-card {
  position: relative;
  height: 100%;
  padding: 18px 20px;
  border-radius: var(--tech-radius, 16px);
  border: 1px solid var(--tech-line, rgba(21,128,61, 0.18));
  background: #fff;
  box-shadow: 0 8px 26px rgba(23,58,40, 0.08);
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;

  /* 顶部随主色的渐变高光 */
  &::before {
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: linear-gradient(90deg, var(--mc-color), transparent 85%);
    opacity: 0.85;
  }

  /* HUD 右下角标 */
  &::after {
    content: '';
    position: absolute;
    right: 10px;
    bottom: 10px;
    width: 10px;
    height: 10px;
    border-right: 2px solid var(--mc-color);
    border-bottom: 2px solid var(--mc-color);
    opacity: 0.35;
    pointer-events: none;
  }

  &.is-clickable {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
      border-color: var(--mc-color);
      box-shadow: 0 14px 32px rgba(23,58,40, 0.14);
    }
  }
}

.mc-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mc-icon {
  flex: none;
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--mc-color-soft);
  color: var(--mc-color);
  border: 1px solid var(--mc-color-soft);
}

.mc-text {
  min-width: 0;
}

.mc-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  line-height: 1.15;
}

.mc-num {
  font-family: var(--tech-font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 26px;
  font-weight: 700;
  color: var(--mc-color);
  letter-spacing: 0.5px;
}

.mc-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--tech-text-sub, #475569);
}

.mc-label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--tech-text-sub, #475569);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mc-sub {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--tech-line, rgba(21,128,61, 0.18));
  font-size: 12px;
  color: var(--tech-text-dim, #94a3b8);
}

.mc-trend {
  margin-top: 6px;
  font-size: 12px;

  &.is-up { color: #17954d; }
  &.is-down { color: #b91c1c; }
}
</style>
