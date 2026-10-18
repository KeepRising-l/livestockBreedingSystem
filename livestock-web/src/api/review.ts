import http from './request'

// ============ 类型定义 ============

export type BusinessType = 'feeding' | 'purchase' | 'consume' | 'vaccine' | 'medical' | 'mating'

export interface ReviewItem {
  business_type: BusinessType
  business_name: string
  id: number
  create_time: string | null
  operator_user_id: number | null
  operator_name: string | null
  summary: string
  detail: Record<string, any>
}

export interface ReviewCounts {
  feeding: number
  purchase: number
  consume: number
  vaccine: number
  medical: number
  mating: number
  total: number
}

// ============ 接口 ============

export function getReviewCountsApi() {
  return http.get('/review/counts')
}

export function getReviewListApi(params: { business_type: BusinessType; pageNum?: number; pageSize?: number }) {
  return http.get('/review/list', { params })
}

export function getReviewPendingApi(params: { limit?: number } = {}) {
  return http.get('/review/pending', { params })
}

export function auditReviewApi(body: {
  business_type: BusinessType
  business_id: number
  audit_status: '通过' | '驳回'
  remark?: string
}) {
  return http.post('/review/audit', body)
}

/** 一键批量审核：business_type 留空表示全部类型 */
export function batchAuditReviewApi(body: {
  business_type?: BusinessType | 'all'
  audit_status: '通过' | '驳回'
  remark?: string
}) {
  return http.post('/review/batch-audit', body)
}

export interface BatchAuditResult {
  audit_status: string
  success: number
  failed: number
  failed_items: { business_type: string; business_id: number; summary: string; reason: string }[]
}
