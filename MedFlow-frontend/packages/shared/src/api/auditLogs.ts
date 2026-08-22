import request from './request'
import type { PageResponse, AuditLog } from '../types'

export function getAuditStatus() {
  return request.get<{ enabled: boolean }>('/audit-logs/status')
}

export function toggleAudit() {
  return request.put<{ enabled: boolean }>('/audit-logs/toggle')
}

export function listAuditLogs(params?: {
  user_id?: number; keyword?: string; role?: number; date_from?: string; date_to?: string; page?: number; page_size?: number; sort_by?: string; sort_order?: string
}) {
  return request.get<PageResponse<AuditLog>>('/audit-logs', { params })
}
