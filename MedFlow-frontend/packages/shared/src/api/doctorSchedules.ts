import request from './request'
import type { DoctorSchedule } from '../types'

export function listSchedules(params?: {
  doctor_id?: number
  department_id?: number
  work_date_from?: string
  work_date_to?: string
  date?: string
}) {
  return request.get<DoctorSchedule[]>('/doctor-schedules', { params })
}

export function createSchedule(params: {
  doctor_id: number; work_date: string; start_time: string; end_time: string; max_patients?: number
}) {
  return request.post('/doctor-schedules', params)
}

export function updateSchedule(id: number, params: Record<string, any>) {
  return request.put(`/doctor-schedules/${id}`, params)
}

export function deleteSchedule(id: number) {
  return request.delete(`/doctor-schedules/${id}`)
}

export interface TemplateSlot {
  weekday: number
  start_time: string
  end_time: string
  max_patients: number
}

export function listTemplates(doctorId: number) {
  return request.get<DoctorSchedule[]>('/doctor-schedules/templates', { params: { doctor_id: doctorId } })
}

export function saveTemplate(params: { doctor_id: number; items: TemplateSlot[] }) {
  return request.post('/doctor-schedules/templates', params)
}

export function deleteTemplate(doctorId: number) {
  return request.delete('/doctor-schedules/templates', { params: { doctor_id: doctorId } })
}

export function reapplyTemplate(params: { department_id: number; work_date_from: string; work_date_to: string }) {
  return request.post('/doctor-schedules/reapply', params)
}
