import request from './request'
import type { PageResponse } from '../types'

export interface UserListItem {
  id: number
  email: string
  name: string
  phone: string | null
  role: number
  status: number
  last_login: string | null
  created_at: string
}

export function listUsers(params?: {
  role?: number; status?: number; keyword?: string; page?: number; page_size?: number
  sort_by?: string; sort_order?: string
}) {
  return request.get<PageResponse<UserListItem>>('/users', { params })
}

export function getUser(userId: number) {
  return request.get<UserListItem>(`/users/${userId}`)
}

export function updateUserStatus(userId: number, status: number) {
  return request.put(`/users/${userId}/status`, { status })
}

export function resetPassword(userId: number, params: { new_password?: string; email?: string }) {
  return request.post(`/users/${userId}/reset-password`, params)
}

export function resetUser(userId: number, params: { code: string; new_email?: string; new_password?: string }) {
  return request.post(`/users/${userId}/reset`, params)
}

export function createUser(params: { email: string; password: string; name: string; role: number; phone?: string }) {
  return request.post<UserListItem>('/users', params)
}

export function updateUser(userId: number, params: { name?: string; phone?: string | null; role?: number }) {
  return request.put(`/users/${userId}`, params)
}
