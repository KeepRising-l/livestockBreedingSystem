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
