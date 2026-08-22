import request from './request'
import type { PageResponse, Notification, NotificationCreateParams, AdminNotificationItem, AdminNotificationListParams } from '../types'

export function listNotifications(params?: { page?: number; page_size?: number; type?: string }) {
  return request.get<PageResponse<Notification>>('/notifications', { params })
}

export function getUnreadCount() {
  return request.get<{ unread_count: number }>('/notifications/unread-count')
}

export function createNotification(params: NotificationCreateParams) {
  return request.post<{ message: string; recipients: number }>('/notifications', params)
}

export function markRead(id: number) {
  return request.put(`/notifications/${id}/read`)
}


export function adminListNotifications(params?: AdminNotificationListParams) {
  return request.get<PageResponse<AdminNotificationItem>>('/notifications/admin', { params })
}
