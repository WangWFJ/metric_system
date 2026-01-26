import service from './axios'

export interface LoginData {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  role_id: number
  status: number
  phone?: string
}

export interface RoleItem { role_id: number; role_name: string; role_code: string }
export interface PageResp<T> { data: T[]; total: number; page: number; size: number }

export const listUsers = (params?: { q?: string; role_id?: number; status?: number; page?: number; size?: number }) => {
  return service.get<any, PageResp<UserInfo>>('/admin/users/', { params })
}
export const createUserAdmin = (payload: { username: string; password: string; phone: string; role_id: number; status?: number }) => {
  return service.post<any, UserInfo>('/admin/users/', payload)
}
export const updateUserAdmin = (id: number, payload: { password?: string; phone?: string; role_id?: number; status?: number }) => {
  return service.patch<any, UserInfo>(`/admin/users/${id}`, payload)
}
export const deleteUserAdmin = (id: number) => {
  return service.delete(`/admin/users/${id}`)
}
export const listRolesAdmin = () => {
  return service.get<any, RoleItem[]>('/admin/users/roles')
}

export const login = (data: LoginData) => {
  return service.post<any, TokenResponse>('/users/login', data)
}

export const getMe = () => {
  return service.get<any, UserInfo>('/users/me')
}

export const getMyPermissions = () => {
  return service.get<any, string[]>('/users/me/permissions')
}

export const updateMyPassword = (payload: { current_password: string; new_password: string; confirm_password: string }) => {
  return service.post('/users/me/password', payload)
}

export const updateMyProfile = (payload: { phone?: string }) => {
  return service.patch<any, UserInfo>('/users/me/profile', payload)
}
