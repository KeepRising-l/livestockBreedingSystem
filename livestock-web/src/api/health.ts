import http from './request'

// ============ 类型定义 ============

export interface VaccineRecord {
  id: number
  farm_id: number
  vaccine_date: string
  ear_tag: string
  pen_id: number | null
  species: string
  breed: string | null
  growth_stage: string | null
  vaccine_type: string
  vaccine_name: string | null
  dosage: string | null
  next_vaccine_date: string | null
  audit_status: string
  operator_user_id: number | null
  remark: string | null
  create_time: string | null
}

/** 批量防疫-按圈舍选择：圈舍内单头在栏畜禽 */
export interface VaccinePenAnimal {
  ear_tag: string
  breed: string | null
  gender: string | null
  growth_stage: string | null
  status: string
}

/** 批量防疫-按圈舍选择：按圈舍分组的在栏畜禽 */
export interface VaccinePenGroup {
  pen_id: number
  pen_code: string
  species: string | null
  current_count: number
  animals: VaccinePenAnimal[]
}

export interface MedicalRecord {
  id: number
  farm_id: number
  medical_date: string
  ear_tag: string
  pen_id: number | null
  species: string
  breed: string | null
  growth_stage: string | null
  onset_date: string | null
  disease_type: string
  symptom: string | null
  medicine: string
  treatment_plan: string | null
  treatment_status: string
  cure_date: string | null
  audit_status: string
  operator_user_id: number | null
  remark: string | null
  create_time: string | null
}

// ============ 防疫记录 ============

/** 批量防疫-按圈舍选择：当前养殖场在栏畜禽（按圈舍分组，仅需 health 权限） */
export function getVaccinePenAnimalsApi(params: { species?: string }) {
  return http.get('/health/vaccine/pen-animals', { params })
}

export function getVaccineListApi(params: {
  vaccine_date_start?: string
  vaccine_date_end?: string
  ear_tag?: string
  vaccine_type?: string
  species?: string
  audit_status?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/health/vaccine/list', { params })
}

export function getVaccineDetailApi(id: number) {
  return http.get(`/health/vaccine/${id}`)
}

export function addVaccineApi(params: Partial<VaccineRecord>) {
  return http.post('/health/vaccine/add', params)
}

export function batchAddVaccineApi(params: {
  vaccine_date: string
  ear_tags: string[]
  species: string
  breed?: string
  growth_stage?: string
  vaccine_type: string
  vaccine_name?: string
  dosage?: string
  next_vaccine_date?: string
  remark?: string
}) {
  return http.post('/health/vaccine/batch-add', params)
}

export function updateVaccineApi(id: number, params: Partial<VaccineRecord>) {
  return http.put(`/health/vaccine/update/${id}`, params)
}

export function deleteVaccineApi(id: number) {
  return http.delete(`/health/vaccine/${id}`)
}

export function auditVaccineApi(id: number, params: { audit_status: string; remark?: string }) {
  return http.post(`/health/vaccine/audit/${id}`, params)
}

// ============ 诊疗记录 ============

export function getMedicalListApi(params: {
  medical_date_start?: string
  medical_date_end?: string
  ear_tag?: string
  disease_type?: string
  species?: string
  treatment_status?: string
  audit_status?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/health/medical/list', { params })
}

export function getMedicalDetailApi(id: number) {
  return http.get(`/health/medical/${id}`)
}

export function addMedicalApi(params: Partial<MedicalRecord>) {
  return http.post('/health/medical/add', params)
}

export function updateMedicalApi(id: number, params: Partial<MedicalRecord>) {
  return http.put(`/health/medical/update/${id}`, params)
}

export function deleteMedicalApi(id: number) {
  return http.delete(`/health/medical/${id}`)
}

export function auditMedicalApi(id: number, params: { audit_status: string; remark?: string }) {
  return http.post(`/health/medical/audit/${id}`, params)
}
