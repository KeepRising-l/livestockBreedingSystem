import http from './request'

export interface PenInfo {
  id: number
  farm_id: number
  pen_code: string
  pen_type: string
  /** 所属畜种：牛/羊/猪；null 表示「待归属」（历史数据或未指定畜种时新建的圈舍） */
  species: string | null
  capacity: number
  current_count: number
  status: number
  remark: string | null
  create_time: string | null
}

export function getPenListApi(params: {
  pen_type?: string
  species?: string
  keyword?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/pen/list', { params })
}

export function getPenDetailApi(id: number) {
  return http.get(`/pen/${id}`)
}

export function addPenApi(params: {
  pen_code: string
  pen_type: string
  species?: string
  capacity: number
  remark?: string
}) {
  return http.post('/pen/add', params)
}

/** 批量添加中被跳过的编号及原因 */
export interface PenBatchSkipped {
  code: string
  reason: string
}

/** 批量添加结果 */
export interface PenBatchAddResult {
  created: number
  created_codes: string[]
  skipped: PenBatchSkipped[]
}

export function batchAddPenApi(params: {
  species?: string
  pen_type: string
  capacity: number
  remark?: string
  /** 编号列表（优先使用，前端预览后可手工编辑） */
  codes?: string[]
  /** 编号前缀 + 起始序号 + 数量（codes 为空时由服务端生成，如 A/1/12 -> A01~A12） */
  prefix?: string
  start_no?: number
  count?: number
}) {
  return http.post('/pen/batch-add', params)
}

export function updatePenApi(id: number, params: Partial<PenInfo>) {
  return http.put(`/pen/update/${id}`, params)
}

export function deletePenApi(id: number) {
  return http.delete(`/pen/${id}`)
}

export function getPenAnimalsApi(id: number, params?: { pageNum?: number; pageSize?: number }) {
  return http.get(`/pen/${id}/animals`, { params })
}
