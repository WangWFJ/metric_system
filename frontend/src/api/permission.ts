import service from './axios'

export interface PermissionItem {
  permission_id: number
  permission_code: string
  permission_name: string
  resource: string
  action: string
  status: number
  create_time?: string
}
export interface RoleItem { role_id: number; role_name: string; role_code: string; status?: number }
export interface PageResp<T> { data: T[]; total: number; page: number; size: number }

export const listPermissions = (params?: { q?: string; resource?: string; action?: string; status?: number; role_id?: number; page?: number; size?: number }) => {
  return service.get<any, PageResp<PermissionItem>>('/admin/permissions/list', { params })
}
export const createPermission = (payload: { permission_code: string; permission_name: string; resource: string; action: string; status?: number }) => {
  return service.post('/admin/permissions/', payload)
}
export const updatePermission = (id: number, payload: { permission_name?: string; resource?: string; action?: string; status?: number }) => {
  return service.patch(`/admin/permissions/${id}`, payload)
}
export const deletePermission = (id: number) => {
  return service.delete(`/admin/permissions/${id}`)
}
export const listRolesForPerm = () => {
  return service.get<any, RoleItem[]>('/admin/permissions/roles')
}
export const createRole = (payload: { role_code: string; role_name: string; status?: number }) => {
  return service.post('/admin/permissions/roles', payload)
}
export const updateRole = (role_id: number, payload: { role_name?: string; status?: number }) => {
  return service.patch(`/admin/permissions/roles/${role_id}`, payload)
}
export const deleteRole = (role_id: number) => {
  return service.delete(`/admin/permissions/roles/${role_id}`)
}
export const getRolePermissions = (role_id: number) => {
  return service.get<any, number[]>('/admin/permissions/role_permissions', { params: { role_id } })
}
export const assignRolePermissions = (payload: { role_id: number; permission_ids: number[] }) => {
  return service.post('/admin/permissions/role_permissions/assign', payload)
}
export const revokeRolePermissions = (payload: { role_id: number; permission_ids: number[] }) => {
  return service.post('/admin/permissions/role_permissions/revoke', payload)
}
