import request from './request'
import type { Doctor, DoctorCreateParams, PageResponse } from '../types'

export function listDoctors(params?: { department_id?: number; keyword?: string; page?: number; page_size?: number; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<Doctor>>('/doctors', { params })
}

export function createDoctor(params: DoctorCreateParams) {
  return request.post<Doctor>('/doctors', params)
}

export function updateDoctor(id: number, params: {
  name?: string; department_id?: number; title?: string; introduction?: string
}) {
  return request.put(`/doctors/${id}`, params)
}

export function deleteDoctor(id: number) {
  return request.delete(`/doctors/${id}`)
}

export function restoreDoctor(id: number) {
  return request.put(`/doctors/${id}/restore`)
}
