import request from './request'
import type { DrugOrder } from '../types'

export function listDrugOrders(params?: { date?: string; status?: number }) {
  return request.get<DrugOrder[]>('/drug-orders', { params })
}

export function cancelOrder(id: number) {
  return request.post(`/drug-orders/${id}/cancel`)
}

export function completeOrder(id: number) {
  return request.post(`/drug-orders/${id}/complete`)
}

export function uncompleteOrder(id: number) {
  return request.post(`/drug-orders/${id}/uncomplete`)
}

export function restoreOrder(id: number) {
  return request.post(`/drug-orders/${id}/restore`)
}
