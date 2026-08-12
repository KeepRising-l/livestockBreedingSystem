import http from './request'

export interface PenInfo {
  id: number
  farm_id: number
  pen_code: string
  pen_type: string
  capacity: number
  current_count: number
  status: number
  remark: string | null
  create_time: string | null
}

export function getPenListApi(params: {
  pen_type?: string
  keyword?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/pen/list', { params })
}

export function getPenDetailApi(id: number) {
  return http.get(`/pen/${id}`)
}

export function addPenApi(params: { pen_code: string; pen_type: string; capacity: number; remark?: string }) {
  return http.post('/pen/add', params)
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
