import request from './request'
import type { DiagnosisRecord, DiagnosisCreateParams } from '../types'

export function listDiagnosisRecords(params?: { patient_id?: number; doctor_id?: number }) {
  return request.get<DiagnosisRecord[]>('/diagnosis-records', { params })
}

export function getDiagnosisRecord(id: number) {
  return request.get<DiagnosisRecord>(`/diagnosis-records/${id}`)
}

export function createDiagnosisRecord(params: DiagnosisCreateParams) {
  return request.post('/diagnosis-records', params)
}

export function updateDiagnosisRecord(id: number, params: {
  chief_complaint?: string; diagnosis_result?: string; prescription_advice?: string
}) {
  return request.put(`/diagnosis-records/${id}`, params)
}
