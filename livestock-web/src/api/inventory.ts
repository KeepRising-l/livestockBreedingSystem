import http from './request'

// ============ 类型定义 ============

export interface MaterialStock {
  id: number
  farm_id: number
  material_type: string
  material_name: string
  specification: string | null
  quantity: number | null
  unit: string | null
  unit_price: number | null
  warning_threshold: number | null
  production_date: string | null
  expiry_date: string | null
  status: string | null
  is_shortage: number | null
  manager_user_id: number | null
  remark: string | null
  create_time: string | null
}

export interface MaterialPurchase {
  id: number
  farm_id: number
  stock_id: number | null
  material_type: string
  material_name: string
  batch_no: string | null
  quantity: number | null
  unit: string | null
  cost_price: number | null
  total_cost: number | null
  production_date: string | null
  expiry_date: string | null
  supplier: string | null
  purchase_date: string
  audit_status: string
  operator_user_id: number | null
  remark: string | null
  create_time: string | null
}

export interface MaterialConsume {
  id: number
  farm_id: number
  stock_id: number | null
  material_type: string
  material_name: string
  batch_no: string | null
  quantity: number | null
  unit: string | null
  unit_price: number | null
  consume_date: string
  related_module: string | null
  related_id: number | null
  status: string | null
  audit_status: string
  consumer_user_id: number | null
  consumer_name: string | null
  remark: string | null
  create_time: string | null
}

// ============ 库存 ============

export function getStockListApi(params: {
  material_type?: string
  material_name?: string
  status?: string
  is_shortage?: number
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/inventory/stock/list', { params })
}

export function getStockDetailApi(id: number) {
  return http.get(`/inventory/stock/${id}`)
}

export function addStockApi(params: Partial<MaterialStock>) {
  return http.post('/inventory/stock/add', params)
}

/** 管理端增加库存（免审直接入库，后端落一条已通过的进货记录并同步库存） */
export function increaseStockApi(params: {
  material_type: string
  material_name: string
  quantity: number
  unit: string
  cost_price?: number
  batch_no?: string
  supplier?: string
  purchase_date?: string
  production_date?: string
  expiry_date?: string
  remark?: string
}) {
  return http.post('/inventory/stock/increase', params)
}

export function updateStockApi(id: number, params: Partial<MaterialStock>) {
  return http.put(`/inventory/stock/update/${id}`, params)
}

export function deleteStockApi(id: number) {
  return http.delete(`/inventory/stock/${id}`)
}

// ============ 进货 ============

export function getPurchaseListApi(params: {
  material_type?: string
  material_name?: string
  purchase_date_start?: string
  purchase_date_end?: string
  audit_status?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/inventory/purchase/list', { params })
}

export function getPurchaseDetailApi(id: number) {
  return http.get(`/inventory/purchase/${id}`)
}

export function addPurchaseApi(params: Partial<MaterialPurchase>) {
  return http.post('/inventory/purchase/add', params)
}

export function updatePurchaseApi(id: number, params: Partial<MaterialPurchase>) {
  return http.put(`/inventory/purchase/update/${id}`, params)
}

export function deletePurchaseApi(id: number) {
  return http.delete(`/inventory/purchase/${id}`)
}

export function auditPurchaseApi(id: number, params: { audit_status: string; remark?: string }) {
  return http.post(`/inventory/purchase/audit/${id}`, params)
}

// ============ 领用 ============

export function getConsumeListApi(params: {
  material_type?: string
  material_name?: string
  stock_id?: number
  consume_date_start?: string
  consume_date_end?: string
  audit_status?: string
  related_module?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/inventory/consume/list', { params })
}

export function getConsumeDetailApi(id: number) {
  return http.get(`/inventory/consume/${id}`)
}

export function addConsumeApi(params: Partial<MaterialConsume>) {
  return http.post('/inventory/consume/add', params)
}

export function updateConsumeApi(id: number, params: Partial<MaterialConsume>) {
  return http.put(`/inventory/consume/update/${id}`, params)
}

export function deleteConsumeApi(id: number) {
  return http.delete(`/inventory/consume/${id}`)
}

export function auditConsumeApi(id: number, params: { audit_status: string; remark?: string }) {
  return http.post(`/inventory/consume/audit/${id}`, params)
}
