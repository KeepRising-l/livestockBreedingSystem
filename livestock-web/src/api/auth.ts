import http from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface OwnerRegisterParams {
  farm_name: string
  username: string
  password: string
  real_name: string
  phone: string
  livestock_types: string
}

export interface EmployeeRegisterParams {
  farm_id: number
  username: string
  password: string
  real_name: string
  phone: string
  post: string
}

export interface TokenResult {
  access_token: string
  token_type: string
}

export interface RegisterResult {
  user_id: number
  farm_id: number
}

export function loginApi(params: LoginParams) {
  return http.post<any, { data: TokenResult }>('/auth/login', params)
}

export function registerOwnerApi(params: OwnerRegisterParams) {
  return http.post<any, { data: RegisterResult }>('/auth/register/owner', params)
}

export function registerEmployeeApi(params: EmployeeRegisterParams) {
  return http.post<any, { data: RegisterResult }>('/auth/register/employee', params)
}
