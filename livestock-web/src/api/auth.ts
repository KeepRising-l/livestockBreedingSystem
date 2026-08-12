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

export interface TokenResult {
  access_token: string
  token_type: string
}

export interface RegisterResult {
  user_id: number
  farm_id: number
}

export interface MenuNode {
  id: number
  parent_id: number
  menu_name: string
  menu_type: string
  path: string | null
  perms: string | null
  icon: string | null
  children: MenuNode[]
}

export interface PermissionsResult {
  user_id: number
  username: string
  user_type: number
  farm_id: number | null
  post: string | null
  roles: string[]
  perms: string[]
  menus: MenuNode[]
}

export function loginApi(params: LoginParams) {
  return http.post<any, { data: TokenResult }>('/auth/login', params)
}

export function getPermissionsApi() {
  return http.get<any, { data: PermissionsResult }>('/auth/permissions')
}

export function registerOwnerApi(params: OwnerRegisterParams) {
  return http.post<any, { data: RegisterResult }>('/auth/register/owner', params)
}
