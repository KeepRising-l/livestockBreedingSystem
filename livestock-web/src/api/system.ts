import http from './request'

// ========== 字典类型 ==========
export interface DictTypeInfo {
  id: number
  dict_name: string
  dict_type: string
  status: number
  remark: string | null
  create_time: string | null
}

export interface DictTypeQuery {
  dict_name?: string
  dict_type?: string
  status?: number
  pageNum?: number
  pageSize?: number
}

export function getDictTypeListApi(params: DictTypeQuery) {
  return http.get('/system/dict/type/list', { params })
}

export function addDictTypeApi(data: Partial<DictTypeInfo>) {
  return http.post('/system/dict/type/add', data)
}

export function updateDictTypeApi(id: number, data: Partial<DictTypeInfo>) {
  return http.put(`/system/dict/type/update/${id}`, data)
}

export function deleteDictTypeApi(id: number) {
  return http.delete(`/system/dict/type/${id}`)
}

// ========== 字典数据 ==========
export interface DictDataInfo {
  id: number
  dict_type: string
  dict_label: string
  dict_value: string
  dict_sort: number
  dict_extra: string | null
  status: number
  create_time: string | null
}

export interface DictDataQuery {
  dict_type?: string
  dict_label?: string
  status?: number
  pageNum?: number
  pageSize?: number
}

export function getDictDataListApi(params: DictDataQuery) {
  return http.get('/system/dict/data/list', { params })
}

export function queryDictDataByTypeApi(dictType: string) {
  return http.get(`/system/dict/data/query/${dictType}`)
}

export function addDictDataApi(data: Partial<DictDataInfo>) {
  return http.post('/system/dict/data/add', data)
}

export function updateDictDataApi(id: number, data: Partial<DictDataInfo>) {
  return http.put(`/system/dict/data/update/${id}`, data)
}

export function deleteDictDataApi(id: number) {
  return http.delete(`/system/dict/data/${id}`)
}

// ========== 用户管理（超管） ==========
export interface UserInfo {
  id: number
  username: string
  real_name: string
  phone: string
  user_type: number
  farm_id: number | null
  farm_name: string | null
  post: string | null
  status: number
  role_names: string[]
  create_time: string | null
}

export function getSystemUserListApi(params: Record<string, any>) {
  return http.get<any, { data: { list: UserInfo[]; total: number } }>('/system/user/list', { params })
}

export function addSystemUserApi(data: Record<string, any>) {
  return http.post('/system/user/add', data)
}

export function updateSystemUserApi(id: number, data: Record<string, any>) {
  return http.put(`/system/user/update/${id}`, data)
}

export function deleteSystemUserApi(id: number) {
  return http.delete(`/system/user/${id}`)
}

export function resetUserPasswordApi(id: number, newPassword: string) {
  return http.post(`/system/user/reset-password/${id}`, { new_password: newPassword })
}

export function assignUserRolesApi(id: number, roleIds: number[]) {
  return http.post(`/system/user/assign-roles/${id}`, { role_ids: roleIds })
}

export function getUserRolesApi(id: number) {
  return http.get<any, { data: { role_ids: number[] } }>(`/system/user/roles/${id}`)
}

// ========== 角色管理（超管） ==========
export interface RoleInfo {
  id: number
  role_name: string
  role_key: string
  sort: number
  status: number
  remark: string | null
  create_time: string | null
}

export function getRoleListApi(params: { role_name?: string; status?: number; pageNum?: number; pageSize?: number }) {
  return http.get<any, { data: { list: RoleInfo[]; total: number } }>('/system/role/list', { params })
}

export function addRoleApi(data: Partial<RoleInfo>) {
  return http.post('/system/role/add', data)
}

export function updateRoleApi(id: number, data: Partial<RoleInfo>) {
  return http.put(`/system/role/update/${id}`, data)
}

export function deleteRoleApi(id: number) {
  return http.delete(`/system/role/${id}`)
}

// ========== 菜单管理（超管） ==========
export interface MenuInfo {
  id: number
  parent_id: number
  menu_name: string
  menu_type: string
  path: string | null
  component: string | null
  perms: string | null
  icon: string | null
  sort: number
  visible: number
  status: number
  children?: MenuInfo[]
}

export function getMenuListApi(params?: { menu_name?: string; status?: number }) {
  return http.get<any, { data: MenuInfo[] }>('/system/menu/list', { params })
}

export function addMenuApi(data: Record<string, any>) {
  return http.post('/system/menu/add', data)
}

export function updateMenuApi(id: number, data: Record<string, any>) {
  return http.put(`/system/menu/update/${id}`, data)
}

export function deleteMenuApi(id: number) {
  return http.delete(`/system/menu/${id}`)
}

// ========== 日志管理（超管） ==========
export interface LoginLogInfo {
  id: number
  username: string
  user_id: number | null
  ip: string | null
  browser: string | null
  os: string | null
  status: number
  msg: string | null
  login_time: string | null
}

export interface OperLogInfo {
  id: number
  title: string | null
  business_type: string | null
  method: string
  oper_url: string | null
  oper_user_id: number | null
  oper_name: string | null
  oper_ip: string | null
  status: number
  error_msg: string | null
  oper_time: string | null
}

export function getLoginLogListApi(params: Record<string, any>) {
  return http.get<any, { data: { list: LoginLogInfo[]; total: number } }>('/system/log/login/list', { params })
}

export function clearLoginLogApi() {
  return http.delete('/system/log/login/clear')
}

export function getOperLogListApi(params: Record<string, any>) {
  return http.get<any, { data: { list: OperLogInfo[]; total: number } }>('/system/log/oper/list', { params })
}

export function clearOperLogApi() {
  return http.delete('/system/log/oper/clear')
}

// ========== 通知公告（管理超管 / 已发布所有登录用户） ==========
export interface NoticeInfo {
  id: number
  notice_title: string
  notice_type: string
  notice_content: string | null
  status: number
  create_by: string | null
  create_time: string | null
}

export function getNoticeListApi(params: { notice_title?: string; notice_type?: string; status?: number; pageNum?: number; pageSize?: number }) {
  return http.get<any, { data: { list: NoticeInfo[]; total: number } }>('/system/notice/list', { params })
}

export function getPublishedNoticesApi() {
  return http.get<any, { data: NoticeInfo[] }>('/system/notice/published')
}

export function getNoticeApi(id: number) {
  return http.get<any, { data: NoticeInfo }>(`/system/notice/${id}`)
}

export function addNoticeApi(data: Partial<NoticeInfo>) {
  return http.post('/system/notice/add', data)
}

export function updateNoticeApi(id: number, data: Partial<NoticeInfo>) {
  return http.put(`/system/notice/update/${id}`, data)
}

export function deleteNoticeApi(id: number) {
  return http.delete(`/system/notice/${id}`)
}

// ============ 站内消息（缺口6：审核结果通知） ============

export interface SysMessage {
  id: number
  farm_id: number
  receiver_user_id: number
  message_type: string
  title: string
  content: string | null
  related_module: string | null
  related_id: number | null
  is_read: number
  read_time: string | null
  create_time: string | null
}

export function getMessageListApi(params: { is_read?: number; pageNum?: number; pageSize?: number }) {
  return http.get<any, { data: { list: SysMessage[]; total: number } }>('/system/message/list', { params })
}

export function getUnreadMessageCountApi() {
  return http.get<any, { data: { count: number } }>('/system/message/unread-count')
}

export function markMessageReadApi(id: number) {
  return http.put(`/system/message/read/${id}`)
}

export function markAllMessagesReadApi() {
  return http.put('/system/message/read-all')
}
