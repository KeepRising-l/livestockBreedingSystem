import http from './request'
import type { ProfitSummary } from './finance'

export interface NameValue {
  name: string
  value: number
}

export interface TrendData {
  months: string[]
  values: number[]
}

export interface DashboardAlert {
  id: number
  alert_type: string
  animal_tag: string
  alert_content: string
  alert_date: string | null
}

export interface DashboardShortage {
  id: number
  material_name: string
  material_type: string
  quantity: number
}

export interface DashboardStats {
  kpi: {
    today_stock: number
    month_in: number
    month_out: number
    total_sale: number
    total_profit: number
    pending_audit: number
    pending_alert: number
    staff_count: number
  }
  todos: {
    pen_count: number
    shortage_count: number
    expiring_count: number
    expired_count: number
    alert_by_type: NameValue[]
    recent_alerts: DashboardAlert[]
    shortage_items: DashboardShortage[]
  }
  stock_trend: {
    months: string[]
    in_values: number[]
    out_values: number[]
  }
  species_dist: NameValue[]
  stage_dist: NameValue[]
}

export interface BreedingStats {
  current_stock: number
  species_dist: NameValue[]
  gender_dist: NameValue[]
  stage_dist: NameValue[]
  pen_dist: NameValue[]
  month_mating: number
  month_birth: number
  pregnant_count: number
  pregnancy_rate: number
  reproduction_rate: number
  avg_survival_rate: number
  pending_alert_count: number
  alert_dist: NameValue[]
  birth_trend: TrendData
}

export interface HealthStats {
  month_vaccine: number
  month_medical: number
  month_immunized_animals: number
  immunization_coverage: number
  month_medical_approved: number
  death_count: number
  morbidity_rate: number
  mortality_rate: number
  vaccine_dist: NameValue[]
  disease_dist: NameValue[]
  treatment_dist: NameValue[]
  health_trend: {
    months: string[]
    vaccine_values: number[]
    medical_values: number[]
  }
}

export interface MaterialNameDist {
  name: string
  /** 库存数量 */
  value: number
  unit: string
  /** 库存金额 = 数量 × 单价 */
  amount: number
  type: string
}

export interface MaterialStats {
  stock_count: number
  type_dist: NameValue[]
  status_dist: NameValue[]
  /** 各物资库存量分布（按物资名称，含单位与金额） */
  name_dist: MaterialNameDist[]
  shortage_count: number
  expired_count: number
  expiring_count: number
  month_purchase_amount: number
  month_consume: number
  consume_trend: TrendData
}

export interface FinanceStats {
  total: ProfitSummary
  month: ProfitSummary
  profit_trend: {
    months: string[]
    sale_values: number[]
    profit_values: number[]
  }
  expense_dist: NameValue[]
}

export function getDashboardStatsApi() {
  return http.get<any, { data: DashboardStats }>('/statistics/dashboard')
}

export function getBreedingStatsApi() {
  return http.get<any, { data: BreedingStats }>('/statistics/breeding')
}

export function getHealthStatsApi() {
  return http.get<any, { data: HealthStats }>('/statistics/health')
}

export function getMaterialStatsApi() {
  return http.get<any, { data: MaterialStats }>('/statistics/material')
}

export function getFinanceStatsApi() {
  return http.get<any, { data: FinanceStats }>('/statistics/finance')
}
