import request from './request'
import type { Prescription, PrescriptionCreateParams, PrescriptionItemInput } from '../types'

export function listPrescriptions(params?: { patient_id?: number; doctor_id?: number }) {
  return request.get<Prescription[]>('/prescriptions', { params })
}

export function getPrescription(id: number) {
  return request.get<Prescription>(`/prescriptions/${id}`)
}

export function createPrescription(params: PrescriptionCreateParams) {
  return request.post('/prescriptions', params)
}

export function updatePrescription(id: number, items: PrescriptionItemInput[]) {
  return request.put(`/prescriptions/${id}`, { items })
}
