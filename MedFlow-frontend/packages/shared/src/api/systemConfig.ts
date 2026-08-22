import request from './request'
import type { SystemConfig, PageResponse } from '../types'

export function listSystemConfig(params?: { page?: number; page_size?: number; keyword?: string; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<SystemConfig>>('/system-config', { params })
}

export function createSystemConfig(params: { config_key: string; config_value: string; description?: string }) {
  return request.post('/system-config', params)
}

export function updateSystemConfig(id: number, params: { config_value?: string; description?: string }) {
  return request.put(`/system-config/${id}`, params)
}

export function deleteSystemConfig(id: number) {
  return request.delete(`/system-config/${id}`)
}

export function getByKey(key: string) {
  return request.get<SystemConfig>('/system-config/by-key', { params: { key } })
}
