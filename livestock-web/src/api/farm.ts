import http from './request'

export interface FarmInfo {
  id: number
  farm_name: string
  owner_user_id: number
  phone: string | null
  livestock_types: string
  address: string | null
  status: number
  create_time: string | null
}

export interface Employee {
  id: number
  username: string
  real_name: string
  phone: string
  user_type: number
  farm_id: number | null
  post: string | null
  status: number
  create_time: string | null
}

export interface FarmListItem {
  id: number
  farm_name: string
  livestock_types: string
}

export function getFarmListApi() {
  return http.get<any, { data: FarmListItem[] }>('/farm/list')
}

export function getFarmInfoApi() {
  return http.get<any, { data: FarmInfo }>('/farm/info')
}

export function updateFarmApi(params: Partial<FarmInfo>) {
  return http.put('/farm/update', params)
}

export function getEmployeesApi(params: { pageNum?: number; pageSize?: number }) {
  return http.get('/farm/employees', { params })
}

export function addEmployeeApi(params: any) {
  return http.post('/farm/employees', params)
}

export function updateEmployeeApi(id: number, params: any) {
  return http.put(`/farm/employees/${id}`, params)
}

export function deleteEmployeeApi(id: number) {
  return http.delete(`/farm/employees/${id}`)
}
