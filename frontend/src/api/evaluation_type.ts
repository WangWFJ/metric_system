import service from './axios'

export interface EvaluationTypeItem { type_id: number; type_name: string }
export interface PageResp<T> { data: T[]; total: number; page: number; size: number }

export const listEvaluationTypes = (params?: { q?: string; page?: number; size?: number }) => {
  return service.get<any, PageResp<EvaluationTypeItem>>('/evaluation_types/', { params })
}
export const createEvaluationType = (payload: { type_name: string }) => {
  return service.post<any, EvaluationTypeItem>('/evaluation_types/', payload)
}
export const updateEvaluationType = (id: number, payload: { type_name: string }) => {
  return service.put<any, EvaluationTypeItem>(`/evaluation_types/${id}`, payload)
}
export const deleteEvaluationType = (id: number) => {
  return service.delete(`/evaluation_types/${id}`)
}
