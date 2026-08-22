import request from './request'
import type { DataDict, PageResponse } from '../types'

export function listDataDict(params?: { type?: string; keyword?: string; page?: number; page_size?: number; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<DataDict>>('/data-dict', { params })
}

export function createDataDict(params: { dict_type: string; dict_key: number; dict_label: string; sort_order?: number }) {
  return request.post('/data-dict', params)
}

export function updateDataDict(id: number, params: Record<string, any>) {
  return request.put(`/data-dict/${id}`, params)
}

export function deleteDataDict(id: number) {
  return request.delete(`/data-dict/${id}`)
}
