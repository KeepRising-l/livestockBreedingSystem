import http from './request'

// ============ 类型定义 ============

export interface FeedingPlan {
  id: number
  farm_id: number
  species: string
  plan_name: string
  applicable_stage: string
  applicable_pen_type: string | null
  feed_times_per_day: number
  concentrate_weight: number | null
  silage_weight: number | null
  hay_weight: number | null
  concentrate_price: number | null
  silage_price: number | null
  hay_price: number | null
  est_cost_per_day: number | null
  status: number
  remark: string | null
  create_time: string | null
}

export interface FeedingRecord {
  id: number
  farm_id: number
  feed_date: string
  time_period: string
  pen_id: number
  pen_type: string | null
  plan_id: number | null
  plan_concentrate: number | null
  plan_silage: number | null
  plan_hay: number | null
  actual_concentrate: number | null
  actual_silage: number | null
  actual_hay: number | null
  animal_count: number | null
  feed_cost: number | null
  status: string
  audit_status: string
  operator_user_id: number | null
  feed_time: string | null
  remark: string | null
  create_time: string | null
}

// ============ 饲喂方案 ============

export function getFeedingPlanListApi(params: {
  species?: string
  applicable_stage?: string
  status?: number
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/feeding/plan/list', { params })
}

export function getFeedingPlanDetailApi(id: number) {
  return http.get(`/feeding/plan/${id}`)
}

export function addFeedingPlanApi(params: Partial<FeedingPlan>) {
  return http.post('/feeding/plan/add', params)
}

export function updateFeedingPlanApi(id: number, params: Partial<FeedingPlan>) {
  return http.put(`/feeding/plan/update/${id}`, params)
}

export function deleteFeedingPlanApi(id: number) {
  return http.delete(`/feeding/plan/${id}`)
}

// ============ 饲喂记录 ============

export function getFeedingRecordListApi(params: {
  feed_date_start?: string
  feed_date_end?: string
  pen_id?: number
  species?: string
  time_period?: string
  audit_status?: string
  status?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/feeding/record/list', { params })
}

export function getFeedingRecordDetailApi(id: number) {
  return http.get(`/feeding/record/${id}`)
}

export function addFeedingRecordApi(params: Partial<FeedingRecord>) {
  return http.post('/feeding/record/add', params)
}

/** 批量提交里的单个圈舍明细 */
export interface FeedingRecordBatchItem {
  pen_id: number
  actual_concentrate?: number
  actual_silage?: number
  actual_hay?: number
  animal_count?: number
  status?: string
  remark?: string
}

/** 批量提交：一次按多个圈舍生成多条饲喂记录（同日同时段已有记录的圈舍会被跳过） */
export function batchAddFeedingRecordApi(params: {
  feed_date: string
  time_period: string
  plan_id?: number
  status?: string
  remark?: string
  items: FeedingRecordBatchItem[]
}) {
  return http.post('/feeding/record/batch-add', params)
}

export function updateFeedingRecordApi(id: number, params: Partial<FeedingRecord>) {
  return http.put(`/feeding/record/update/${id}`, params)
}

export function deleteFeedingRecordApi(id: number) {
  return http.delete(`/feeding/record/${id}`)
}

export function auditFeedingRecordApi(id: number, params: { audit_status: string; remark?: string }) {
  return http.post(`/feeding/record/audit/${id}`, params)
}
