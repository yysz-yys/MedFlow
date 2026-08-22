import request from './request'
import type { Appointment, AppointmentCreateParams } from '../types'

export function listAppointments(params?: {
  status?: number; patient_id?: number; doctor_id?: number
  date?: string; start_date?: string; end_date?: string
}) {
  return request.get<Appointment[]>('/appointments', { params })
}

export function createAppointment(params: AppointmentCreateParams) {
  return request.post<Appointment>('/appointments', params)
}

export function updateAppointment(id: number, params: { doctor_id?: number }) {
  return request.put(`/appointments/${id}`, params)
}

export function cancelAppointment(id: number) {
  return request.post(`/appointments/${id}/cancel`)
}

export function restoreAppointment(id: number) {
  return request.post(`/appointments/${id}/restore`)
}

export function completeAppointment(id: number) {
  return request.post(`/appointments/${id}/complete`)
}

export function uncompleteAppointment(id: number) {
  return request.post(`/appointments/${id}/uncomplete`)
}
