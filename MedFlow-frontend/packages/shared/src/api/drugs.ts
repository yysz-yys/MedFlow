import request from './request'
import type { Drug, PageResponse } from '../types'

export function listDrugs(params?: { page?: number; page_size?: number; keyword?: string; status?: number; unit?: string; stock_lte?: number; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<Drug>>('/drugs', { params })
}

export function createDrug(params: Omit<Drug, 'id' | 'created_at' | 'updated_at'>) {
  return request.post('/drugs', params)
}

export function updateDrug(id: number, params: Record<string, any>) {
  return request.put(`/drugs/${id}`, params)
}

export function deleteDrug(id: number) {
  return request.delete(`/drugs/${id}`)
}

export function restoreDrug(id: number) {
  return request.put(`/drugs/${id}/restore`)
}

export function adjustStock(id: number, change: number) {
  return request.put(`/drugs/${id}/stock`, { change })
}
