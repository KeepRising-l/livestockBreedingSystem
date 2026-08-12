import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { SPECIES_CODE_MAP } from '@/utils/constants'
import { queryDictDataByTypeApi } from '@/api/system'

/**
 * 多畜种（P3-6 A）：当前畜种上下文
 * 从路由参数 :species 读取（cattle/sheep/pig）
 * - species：路由值（英文，feeding 方案表用）
 * - speciesZh：中文畜种（animal/health/breeding 等表用）
 * - breedOptions + loadBreedOptions：当前畜种可选品种（按 sys_breed 字典 dict_extra.species 过滤）
 */
export function useSpecies() {
  const route = useRoute()
  const species = computed(() => (route.params.species as string) || 'cattle')
  const speciesZh = computed(() => SPECIES_CODE_MAP[species.value] || '牛')

  const breedOptions = ref<{ label: string; value: string }[]>([])

  async function loadBreedOptions() {
    try {
      const res = await queryDictDataByTypeApi('sys_breed')
      const list = (res.data as any[]) || []
      breedOptions.value = list
        .filter((d) => {
          try {
            const extra = JSON.parse(d.dict_extra || '{}')
            return !extra.species || extra.species === species.value
          } catch {
            return false
          }
        })
        .map((d) => ({ label: d.dict_label, value: d.dict_label }))
    } catch {
      breedOptions.value = []
    }
  }

  return { species, speciesZh, breedOptions, loadBreedOptions }
}
