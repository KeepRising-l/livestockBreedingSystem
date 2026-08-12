import http from './request'

// ============ 类型定义 ============

export interface BreedAnimal {
  id: number
  ear_tag: string
  species: string
  breed: string
  gender: string
  growth_stage: string | null
  physio_status: string | null
  status: string
}

export interface MatingRecord {
  id: number
  farm_id: number
  female_tag: string
  male_tag: string | null
  species: string
  mating_date: string
  mating_type: string
  semen_source: string | null
  status: string
  pregnancy_check_date: string | null
  pregnancy_check_result: string | null
  expected_birth_date: string | null
  remain_days: number | null
  gestation_days: number | null
  remark: string | null
  create_time: string | null
}

export interface BirthRecord {
  id: number
  farm_id: number
  female_tag: string
  mating_id: number | null
  species: string
  birth_date: string
  total_count: number
  alive_count: number
  dead_count: number
  survival_rate: number | null
  offspring_tags: string | null
  remark: string | null
  create_time: string | null
}

export interface BreedingAlert {
  id: number
  farm_id: number
  alert_type: string
  animal_tag: string
  related_id: number | null
  alert_date: string
  alert_content: string | null
  status: string
  handle_time: string | null
  handle_by: number | null
  handle_remark: string | null
  create_time: string | null
}

// ============ 母畜 / 公畜列表 ============

export function getBreedFemalesApi(params: { species?: string; keyword?: string; physio_status?: string; pageNum?: number; pageSize?: number }) {
  return http.get('/breeding/females', { params })
}

export function getBreedMalesApi(params: { species?: string; keyword?: string; pageNum?: number; pageSize?: number }) {
  return http.get('/breeding/males', { params })
}

/** 设置母畜生理状态（发情/妊娠/泌乳/休情/淘汰） */
export function setFemalePhysioStatusApi(earTag: string, physio_status: string) {
  return http.put(`/breeding/females/${earTag}/physio-status`, { physio_status })
}

// ============ 配种记录 ============

export function getMatingListApi(params: {
  female_tag?: string
  male_tag?: string
  species?: string
  status?: string
  mating_date_start?: string
  mating_date_end?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/breeding/mating/list', { params })
}

export function getMatingDetailApi(id: number) {
  return http.get(`/breeding/mating/${id}`)
}

export function addMatingApi(params: Partial<MatingRecord>) {
  return http.post('/breeding/mating/add', params)
}

export function updateMatingApi(id: number, params: Partial<MatingRecord>) {
  return http.put(`/breeding/mating/update/${id}`, params)
}

export function deleteMatingApi(id: number) {
  return http.delete(`/breeding/mating/${id}`)
}

export function pregnancyCheckApi(id: number, params: { pregnancy_check_date: string; pregnancy_check_result: string; remark?: string }) {
  return http.post(`/breeding/mating/pregnancy-check/${id}`, params)
}

// ============ 产犊记录 ============

export function getBirthListApi(params: {
  female_tag?: string
  species?: string
  birth_date_start?: string
  birth_date_end?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/breeding/birth/list', { params })
}

export function getBirthDetailApi(id: number) {
  return http.get(`/breeding/birth/${id}`)
}

export function addBirthApi(params: Partial<BirthRecord>) {
  return http.post('/breeding/birth/add', params)
}

export function updateBirthApi(id: number, params: Partial<BirthRecord>) {
  return http.put(`/breeding/birth/update/${id}`, params)
}

export function deleteBirthApi(id: number) {
  return http.delete(`/breeding/birth/${id}`)
}

// ============ 繁育预警 ============

export function getAlertListApi(params: {
  alert_type?: string
  animal_tag?: string
  species?: string
  status?: string
  alert_date_start?: string
  alert_date_end?: string
  pageNum?: number
  pageSize?: number
}) {
  return http.get('/breeding/alert/list', { params })
}

export function addAlertApi(params: Partial<BreedingAlert>) {
  return http.post('/breeding/alert/add', params)
}

export function handleAlertApi(id: number, params: { status: string; handle_remark?: string }) {
  return http.post(`/breeding/alert/handle/${id}`, params)
}
