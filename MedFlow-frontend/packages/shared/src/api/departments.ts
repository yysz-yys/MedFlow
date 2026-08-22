import request from './request'
import type { Department, PageResponse } from '../types'

export function listDepartments(params?: { page?: number; page_size?: number; keyword?: string; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<Department>>('/departments', { params })
}

export function createDepartment(params: { name: string; description?: string }) {
  return request.post<Department>('/departments', params)
}

export function updateDepartment(id: number, params: { name?: string; description?: string }) {
  return request.put(`/departments/${id}`, params)
}

export function deleteDepartment(id: number) {
  return request.delete(`/departments/${id}`)
}

export function restoreDepartment(id: number) {
  return request.put(`/departments/${id}/restore`)
}
