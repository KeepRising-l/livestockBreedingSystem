import http from './request'

export interface AnimalInfo {
  id: number
  farm_id: number
  ear_tag: string
  species: string
  breed: string
  pen_id: number | null
  gender: string
  birth_date: string | null
  in_date: string | null
  out_date: string | null
  growth_stage: string | null
  physio_status: string | null
  status: string
  source: string | null
  sire_tag: string | null
  dam_tag: string | null
  remark: string | null
  create_time: string | null
}

export interface AnimalQuery {
  ear_tag?: string
  species?: string
  pen_id?: number
  breed?: string
  gender?: string
  status?: string
  physio_status?: string
  pageNum?: number
  pageSize?: number
}

export interface AnimalHistoryInfo {
  id: number
  farm_id: number
  ear_tag: string
  species: string
  breed: string
  pen_id: number | null
  gender: string
  birth_date: string | null
  in_date: string | null
  out_date: string | null
  growth_stage: string | null
  physio_status: string | null
  status: string | null
  source: string | null
  sire_tag: string | null
  dam_tag: string | null
  remark: string | null
  delete_time: string | null
  create_time: string | null
}

export interface AnimalHistoryQuery {
  ear_tag?: string
  species?: string
  breed?: string
  gender?: string
  status?: string
  pageNum?: number
  pageSize?: number
}

export function getAnimalListApi(params: AnimalQuery) {
  return http.get('/animal/list', { params })
}

export function getAnimalDetailApi(id: number) {
  return http.get(`/animal/${id}`)
}

export function createAnimalApi(params: any) {
  return http.post('/animal/individual', params)
}

export function batchCreateAnimalApi(params: any) {
  return http.post('/animal/batch', params)
}

export function importAnimalsApi(params: { species: string; rows: any[] }) {
  return http.post('/animal/import', params)
}

export function batchDeleteAnimalApi(ids: number[]) {
  return http.post('/animal/batch/batch-delete', { ids })
}

export function updateAnimalApi(id: number, params: any) {
  return http.put(`/animal/update/${id}`, params)
}

/** 转入其他圈舍（自动重生耳标，缺口5） */
export function transferAnimalApi(id: number, target_pen_id: number) {
  return http.post(`/animal/transfer/${id}`, { target_pen_id })
}

/** 移出圈舍（缺口5） */
export function removeFromPenApi(id: number) {
  return http.post(`/animal/remove-from-pen/${id}`)
}

export function generateEarTagApi(pen_id: number, species?: string) {
  return http.get('/animal/ear-tag/generate', { params: { pen_id, species } })
}

export function getAnimalHistoryListApi(params: AnimalHistoryQuery) {
  return http.get('/animal/history/list', { params })
}

export function restoreAnimalApi(historyId: number) {
  return http.post(`/animal/history/restore/${historyId}`)
}
