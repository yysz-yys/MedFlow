import request from './request'
import type { Patient, PageResponse } from '../types'

export function listPatients(params?: { keyword?: string; gender?: number; blood_type?: string; page?: number; page_size?: number; sort_by?: string; sort_order?: string }) {
  return request.get<PageResponse<Patient>>('/patients', { params })
}

export function createPatient(params: { email: string; password: string; name: string; gender?: number | null; birth_date?: string; address?: string; blood_type?: string; allergy_history?: string }) {
  return request.post<Patient>('/patients', params)
}

export function getPatient(id: number) {
  return request.get<Patient>(`/patients/${id}`)
}

export function updatePatient(id: number, params: Record<string, any>) {
  return request.put(`/patients/${id}`, params)
}

export function deletePatient(id: number) {
  return request.delete(`/patients/${id}`)
}

export function restorePatient(id: number) {
  return request.put(`/patients/${id}/restore`)
}

import type { DoctorPatient } from '../types'

export function listMyPatients(params?: { keyword?: string; gender?: number; page?: number; page_size?: number }) {
  return request.get<PageResponse<DoctorPatient>>('/doctors/me/patients', { params })
}
