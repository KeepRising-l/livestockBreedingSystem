import http from './request'

export interface SaleCandidate {
  id: number
  ear_tag: string
  species: string
  breed: string
  gender: string
  pen_id: number | null
  in_date: string | null
  growth_stage: string | null
  status: string
}

export interface SaleOrder {
  id: number
  order_no: string
  customer: string
  customer_phone: string | null
  animal_count: number
  total_weight: number
  unit_price: number
  total_amount: number
  order_date: string
  settle_status: string
  settle_time: string | null
  species: string | null
  remark: string | null
  create_time: string | null
}

export interface SaleOrderDetail {
  id: number
  order_id: number
  ear_tag: string
  species: string
  breed: string | null
  weight: number
  raise_days: number | null
  feed_cost: number | null
  medicine_cost: number | null
  labor_cost: number | null
  consumable_cost: number | null
  total_cost: number | null
  sale_amount: number | null
  profit: number | null
  profit_rate: number | null
}

export interface CostExpense {
  id: number
  farm_id: number
  expense_type: string
  amount: number
  expense_date: string
  voucher_no: string | null
  remark: string | null
  create_time: string | null
}

export interface SalaryRecord {
  id: number
  user_id: number
  username: string | null
  real_name: string | null
  post: string
  pay_month: string
  base_salary: number
  bonus: number
  deduct: number
  actual_pay: number
  pay_time: string | null
  status: string
  remark: string | null
}

export interface ProfitSummary {
  order_count: number
  animal_count: number
  total_amount: number
  total_cost: number
  total_profit: number
  profit_rate: number
  expense_amount: number
  net_profit: number
}

// ============ 出栏销售 ============

export function getSaleCandidatesApi(params: { species?: string; growth_stage?: string; keyword?: string }) {
  return http.get<any, { data: SaleCandidate[] }>('/finance/sale/candidates', { params })
}

export function saleOutApi(params: {
  customer: string
  customer_phone?: string
  unit_price: number
  order_date?: string
  remark?: string
  items: { ear_tag: string; weight: number }[]
}) {
  return http.post('/finance/sale/out', params)
}

export function getSaleListApi(params: any) {
  return http.get('/finance/sale/list', { params })
}

export function getSaleDetailApi(id: number) {
  return http.get(`/finance/sale/${id}`)
}

export function settleSaleApi(id: number) {
  return http.post(`/finance/sale/settle/${id}`)
}

// ============ 成本支出 ============

export function addExpenseApi(params: any) {
  return http.post('/finance/expense/add', params)
}

export function getExpenseListApi(params: any) {
  return http.get('/finance/expense/list', { params })
}

export function updateExpenseApi(id: number, params: any) {
  return http.put(`/finance/expense/${id}`, params)
}

export function deleteExpenseApi(id: number) {
  return http.delete(`/finance/expense/${id}`)
}

// ============ 利润汇总 ============

export function getProfitSummaryApi(params: { start_date?: string; end_date?: string }) {
  return http.get<any, { data: ProfitSummary }>('/finance/profit/summary', { params })
}

// ============ 薪资记录 ============

export function generateSalaryApi(payMonth: string) {
  return http.post('/finance/salary/generate', { pay_month: payMonth })
}

export function getSalaryListApi(params: any) {
  return http.get('/finance/salary/list', { params })
}

export function paySalaryApi(id: number) {
  return http.post(`/finance/salary/pay/${id}`)
}
