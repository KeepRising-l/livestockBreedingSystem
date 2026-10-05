import { ref, watch, onUnmounted, type Ref } from 'vue'

export interface CountUpOptions {
  /** 动画时长（ms） */
  duration?: number
  /** 延迟启动（等布局稳定，ms） */
  delay?: number
  /** 小数位；不传则按目标值自动推断（整数 0 位，小数 2 位） */
  decimals?: number
}

/**
 * 数字滚动：目标值变化（含首次拿到异步数据）时，从 0 递增到目标值。
 * - 每次挂载都从 0 开始（进入页面即有滚动效果）
 * - 尊重系统「减少动效」偏好：直接显示终值
 */
export function useCountUp(source: Ref<number | null | undefined>, options: CountUpOptions = {}) {
  const duration = options.duration ?? 900
  const delay = options.delay ?? 60
  const display = ref(0)
  const decimals = ref(0)
  let raf = 0
  let timer: ReturnType<typeof setTimeout> | undefined

  const reduceMotion =
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  function stop() {
    if (raf) cancelAnimationFrame(raf)
    if (timer) clearTimeout(timer)
    raf = 0
    timer = undefined
  }

  function animate(to: number) {
    stop()
    decimals.value = options.decimals ?? (Number.isInteger(to) ? 0 : 2)
    if (reduceMotion || duration <= 0) {
      display.value = to
      return
    }
    display.value = 0
    timer = setTimeout(() => {
      const start = performance.now()
      const step = (now: number) => {
        const p = Math.min(1, (now - start) / duration)
        const eased = 1 - Math.pow(1 - p, 3) // easeOutCubic
        display.value = to * eased
        if (p < 1) {
          raf = requestAnimationFrame(step)
        } else {
          display.value = to
          raf = 0
        }
      }
      raf = requestAnimationFrame(step)
    }, delay)
  }

  watch(
    source,
    (v) => {
      if (typeof v === 'number' && Number.isFinite(v)) {
        animate(v)
      } else {
        stop()
        display.value = 0
      }
    },
    { immediate: true },
  )

  onUnmounted(stop)

  return { display, decimals }
}
