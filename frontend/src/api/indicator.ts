import service from './axios'

export interface IndicatorParams {
  indicator_id?: number
  district_id?: number
  district_ids?: number[]
  major_id?: number
  type_id?: number
  start_date?: string
  end_date?: string
  page?: number
  size?: number
  order_by?: string
  desc?: boolean
  circle_id?: number
}

export interface IndicatorData {
  indicator_id: number
  indicator_name: string
  value: number
  stat_date: string
  district_id?: number
  district_name?: string
  score?: number
  benchmark?: number
  challenge?: number
  exemption?: number
  zero_tolerance?: number
  // Add other fields as per backend model
}

export interface District {
  district_id: number
  district_name: string
  simple_name: string
}

export interface Center {
  center_id: number
  district_id?: number
  center_name: string
}

export interface Major {
  major_id: number
  major_name: string
  major_code: string
}

export interface EvaluationType {
  type_id: number
  type_name: string
}

export interface IndicatorSimple {
  indicator_id: number
  indicator_name: string
}

export interface IndicatorFull {
  indicator_id: number
  indicator_name: string
  unit?: string
  category_id?: number
  major_id?: number
  type_id?: number
  is_positive: number
  data_owner?: string
  data_dept?: string
  description?: string
  status?: number
  version?: number
}

export interface PageResponse<T> { data: T[]; total: number; page: number; size: number }

export interface IndicatorDataCreate {
  indicator_id: number
  district_id: number
  stat_date: string
  value: number
  score?: number
  type_id?: number
  benchmark?: number
  challenge?: number
  exemption?: number
  zero_tolerance?: number
}

export interface IndicatorDataResponse {
  items: IndicatorData[]
  total: number
}

export interface CenterDataItem {
  id: number
  indicator_id: number
  indicator_name: string
  center_id: number
  center_name: string
  district_id?: number
  district_name?: string
  stat_date: string
  value?: number
  benchmark?: number
  challenge?: number
  score?: number
}

export interface CenterDataResponse {
  items: CenterDataItem[]
  total: number
}

export interface CenterParams {
  indicator_id?: number
  center_id?: number
  district_id?: number
  start_date?: string
  end_date?: string
  major_id?: number
  type_id?: number
  page?: number
  size?: number
  order_by?: string
  desc?: boolean
}

export interface CenterDataCreate {
  indicator_id: number
  center_id: number
  stat_date: string
  value: number
  type_id?: number
  benchmark?: number
  challenge?: number
  score?: number
}

export interface CenterDataDeletePayload {
  ids?: number[]
  indicator_id?: number
  center_id?: number
  district_id?: number
  start_date?: string
  end_date?: string
}

export interface IndicatorDataDeletePayload {
  ids?: number[]
  indicator_id?: number
  district_id?: number
  start_date?: string
  end_date?: string
}

export const getIndicatorData = (params?: IndicatorParams) => {
  return service.get<any, IndicatorDataResponse>('/metrics/query', { params })
}

export const getCenterData = (params?: CenterParams) => {
  return service.get<any, CenterDataResponse>('/metrics/center/query', { params })
}

export const getSnapshotData = (params?: Omit<IndicatorParams, 'start_date' | 'end_date'>) => {
  return service.get<any, IndicatorDataResponse>('/metrics/snapshot', { params })
}

export const getDistricts = () => {
  return service.get<any, District[]>('/metrics/districts')
}

export const getCenters = (params?: { district_id?: number }) => {
  return service.get<any, Center[]>('/metrics/centers', { params })
}

export const getMajors = () => {
  return service.get<any, Major[]>('/metrics/majors')
}

export const getEvaluationTypes = () => {
  return service.get<any, EvaluationType[]>('/metrics/evaluation_types')
}

export const getCircles = () => {
  return service.get<any, number[]>('/metrics/circles')
}

export const getIndicatorsList = () => {
  return service.get<any, IndicatorSimple[]>('/metrics/list')
}

export const getIndicatorsByType = (type_id: number) => {
  return service.get<any, IndicatorSimple[]>('/metrics/indicators_by_type', { params: { type_id } })
}

export const getIndicatorSeries = (params: { indicator_id: number, district_id?: number, start_date?: string, end_date?: string, size?: number }) => {
  return service.get<any, IndicatorDataResponse>('/metrics/series', { params })
}

export const getIndicatorSuggestions = (params: { q: string, type_id?: number, size?: number }) => {
  return service.get<any, IndicatorSimple[]>('/metrics/indicators/search', { params })
}
export const createIndicatorData = (data: IndicatorDataCreate) => {
  return service.post<any, IndicatorData>('/metrics/data', data)
}

export const updateIndicatorData = (data: IndicatorDataCreate) => {
  return service.post<any, IndicatorData>('/metrics/data/update', data)
}

export const uploadIndicatorData = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return service.post('/metrics/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getUploadTemplate = () => {
  return service.get('/metrics/upload/template', { responseType: 'blob' })
}

export const uploadCenterData = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return service.post('/metrics/center/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getCenterUploadTemplate = () => {
  return service.get('/metrics/center/upload/template', { responseType: 'blob' })
}

export const deleteIndicatorData = (payload: IndicatorDataDeletePayload) => {
  return service.delete('/metrics/data', { data: payload })
}

export const createCenterData = (data: CenterDataCreate) => {
  return service.post<any, CenterDataItem>('/metrics/center/data', data)
}

export const updateCenterData = (data: CenterDataCreate) => {
  return service.post<any, CenterDataItem>('/metrics/center/data/update', data)
}

export const deleteCenterData = (payload: CenterDataDeletePayload) => {
  return service.delete('/metrics/center/data', { data: payload })
}

export const listIndicators = (params?: { q?: string; type_id?: number; page?: number; size?: number }) => {
  return service.get<any, PageResponse<IndicatorFull>>('/metrics/indicators', { params })
}

export const createIndicator = (payload: IndicatorFull) => {
  return service.post<any, IndicatorFull>('/metrics/indicators', payload)
}

export const updateIndicator = (id: number, payload: IndicatorFull) => {
  return service.put<any, IndicatorFull>(`/metrics/indicators/${id}`, payload)
}

export const deleteIndicatorById = (id: number) => {
  return service.delete(`/metrics/indicators/${id}`)
}

export const getIndicatorsUploadTemplate = () => {
  return service.get('/metrics/indicators/upload/template', { responseType: 'blob' })
}

export const uploadIndicators = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return service.post('/metrics/indicators/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// Majors CRUD (admin)
export const listMajors = (params?: { q?: string; page?: number; size?: number }) => {
  return service.get<any, PageResponse<Major>>('/majors/', { params })
}

export const createMajor = (payload: { major_name: string; major_code: string }) => {
  return service.post<any, Major>('/majors/', payload)
}

export const updateMajor = (id: number, payload: { major_name: string; major_code: string }) => {
  return service.put<any, Major>(`/majors/${id}`, payload)
}

export const deleteMajorById = (id: number) => {
  return service.delete(`/majors/${id}`)
}

export const exportMetrics = (params: {
  indicator_id?: number
  district_id?: number
  district_ids?: number[]
  district_name?: string
  circle_id?: number
  start_date?: string
  end_date?: string
  major_id?: number
  type_id?: number
  order_by?: string
  desc?: boolean
}) => {
  return service.get('/metrics/export', { params, responseType: 'blob' })
}

export const exportMetricsSummary = (params: {
  indicator_id?: number
  district_id?: number
  district_ids?: number[]
  district_name?: string
  circle_id?: number
  start_date?: string
  end_date?: string
  major_id?: number
  type_id?: number
  order_by?: string
  desc?: boolean
}) => {
  return service.get('/metrics/export_v2', { params, responseType: 'blob' })
}

export const exportCenterMetrics = (params: CenterParams) => {
  return service.get('/metrics/center/export', { params, responseType: 'blob' })
}

export const exportCenterMetricsSummary = (params: CenterParams) => {
  return service.get('/metrics/center/export_v2', { params, responseType: 'blob' })
}

export interface IndicatorLatestItem {
  indicator_id: number
  indicator_name: string
  district_id: number
  district_name: string
  stat_date: string
  value?: number
  score?: number
}
export const getIndicatorLatestById = (params: { indicator_id?: number; indicator_name?: string; stat_date?: string }) => {
  return service.get<any, IndicatorLatestItem[]>('/metrics/by_name_or_id', { params })
}

export interface CenterLatestItem {
  indicator_id: number
  indicator_name: string
  center_id: number
  center_name: string
  district_id?: number
  district_name?: string
  stat_date: string
  value?: number
  score?: number
}

export const getCenterLatestById = (params: { indicator_id?: number; indicator_name?: string; stat_date?: string; district_id?: number }) => {
  return service.get<any, CenterLatestItem[]>('/metrics/center/by_name_or_id', { params })
}

export const getCenterSeries = (params: { indicator_id: number; center_id?: number; start_date?: string; end_date?: string; size?: number }) => {
  return service.get<any, CenterDataResponse>('/metrics/center/series', { params })
}
