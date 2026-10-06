import { ref, reactive, type Ref } from 'vue'

/** 后端统一分页响应体的 data 部分（Result.ok 包裹后） */
export interface PagedData<T> {
  list?: T[]
  total?: number
}

export interface UsePagedListOptions<T, Q extends object> {
  /** 拉取函数：接收 pageNum/pageSize + 当前查询条件 */
  fetch: (params: Q & { pageNum: number; pageSize: number }) => Promise<{ data?: PagedData<T> }>
  /** 查询条件初始值（resetSearch 回到此状态）；空值字段不随请求发送 */
  query?: Q
  /** 每页条数，默认 10 */
  pageSize?: number
  /** 拉取成功后的联动处理（可选） */
  onSuccess?: (list: T[]) => void
}

/**
 * 列表页通用分页加载逻辑。
 * 收敛各视图复制粘贴的 pageNum/pageSize/total/query + loadData/search/resetSearch 样板；
 * 模板绑定名与原视图一致（list/loading/pageNum/pageSize/total/loadData/search/resetSearch），
 * 改造时模板无需变动。
 */
export function usePagedList<T, Q extends object = Record<string, never>>(
  options: UsePagedListOptions<T, Q>,
) {
  const list = ref<T[]>([]) as Ref<T[]>
  const loading = ref(false)
  const pageNum = ref(1)
  const pageSize = ref(options.pageSize ?? 10)
  const total = ref(0)
  const query = reactive({ ...(options.query ?? {}) }) as Q

  async function loadData() {
    loading.value = true
    try {
      // 空值字段不发送（undefined/''/null 剔除），与既有视图行为一致
      const params: Record<string, unknown> = {
        pageNum: pageNum.value,
        pageSize: pageSize.value,
      }
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined && v !== null && v !== '') params[k] = v
      }
      const res = await options.fetch(params as Q & { pageNum: number; pageSize: number })
      list.value = res.data?.list || []
      total.value = res.data?.total || 0
      options.onSuccess?.(list.value)
    } catch {
      // 错误已由 axios 拦截器统一提示
    } finally {
      loading.value = false
    }
  }

  /** 查询：回到第一页再加载 */
  function search() {
    pageNum.value = 1
    loadData()
  }

  /** 重置查询条件到初始值并刷新 */
  function resetSearch() {
    Object.assign(query, options.query ?? {})
    search()
  }

  return { list, loading, pageNum, pageSize, total, query, loadData, search, resetSearch }
}
