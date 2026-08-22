// ===== 通用 / Auth =====

export interface User {
  id: number
  email: string
  name: string
  phone: string | null
  role: number
  status: number
  last_login: string | null
  created_at: string
  updated_at: string
}

export interface LoginParams {
  email: string
  password?: string
  code?: string
  captcha_id?: string
  captcha_text?: string
}

export interface LoginResult {
  access_token: string
  user: User
}

export interface RegisterParams {
  email: string
  password: string
  name: string
  role: number
  code: string
}

export interface UpdateMeParams {
  name?: string
  phone?: string
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export interface ResetPasswordByCodeParams {
  email: string
  code: string
  new_password: string
}

export interface SendCodeParams {
  email: string
  scene: 'REGISTER' | 'LOGIN' | 'RESET_PASSWORD' | 'RESET'
  captcha_id?: string
  captcha_text?: string
}

export interface PageResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

// ===== 科室 =====

export interface Department {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

// ===== 医生 =====

export interface Doctor {
  id: number
  user_id: number
  department_id: number
  name: string
  title: string | null
  introduction: string | null
  department_name: string | null
  created_at: string | null
  deleted_at: string | null
}

export interface DoctorCreateParams {
  email: string
  password: string
  name: string
  department_id: number
  title?: string
  introduction?: string
}

// ===== 排班 =====

export interface DoctorSchedule {
  id: number
  doctor_id: number
  work_date: string
  start_time: string
  end_time: string
  max_patients: number
  booked_count: number
  patient_booked: boolean
  status: number
  created_at: string
  updated_at: string
}

export interface TemplateSlot {
  weekday: number
  start_time: string
  end_time: string
  max_patients: number
}

// ===== 病人 =====

export interface Patient {
  id: number
  user_id: number
  name: string
  gender: number
  birth_date: string | null
  address: string | null
  blood_type: string | null
  allergy_history: string | null
  created_at: string | null
  deleted_at: string | null
}

// ===== 药品 =====

export interface Drug {
  id: number
  name: string
  specification: string | null
  manufacturer: string | null
  unit: string | null
  price: number
  stock: number
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface DrugStockUpdate {
  change: number
}

// ===== 挂号 =====

export interface Appointment {
  id: number
  patient_id: number
  doctor_id: number
  department_id: number
  patient_name: string
  doctor_name: string
  department_name: string | null
  appointment_time: string | null
  schedule_start_time: string | null
  schedule_end_time: string | null
  schedule_max_patients: number | null
  schedule_booked_count: number | null
  status: number
  created_at: string | null
}

export interface AppointmentCreateParams {
  doctor_id: number
  schedule_id: number
}

// ===== 诊断 =====

export interface DiagnosisRecord {
  id: number
  appointment_id: number
  doctor_id: number
  patient_id: number
  chief_complaint: string | null
  diagnosis_result: string | null
  prescription_advice: string | null
  status: number
  created_at: string
  updated_at: string
  patient_name?: string | null
  doctor_name?: string | null
  department_name?: string | null
}

export interface DiagnosisCreateParams {
  appointment_id: number
  chief_complaint?: string
  diagnosis_result?: string
  prescription_advice?: string
}

// ===== 处方 =====

export interface PrescriptionItem {
  id: number
  drug_id: number
  drug_name: string
  specification: string | null
  unit: string | null
  quantity: number
  usage_method: string | null
  days: number | null
}

export interface Prescription {
  id: number
  diagnosis_id: number
  doctor_id: number
  patient_id: number
  items: PrescriptionItem[]
  created_at: string | null
}

export interface PrescriptionCreateParams {
  diagnosis_id: number
  items: PrescriptionItemInput[]
}

export interface PrescriptionItemInput {
  drug_id: number
  quantity: number
  usage_method?: string
  days?: number
}

// ===== 药品订单 =====

export interface DrugOrder {
  id: number
  prescription_id: number
  total_amount: number
  status: number
  patient_name: string
  doctor_name: string
  created_at: string | null
}

// ===== 通知 =====

export interface Notification {
  id: number
  user_id: number
  title: string
  content: string
  type: string
  is_read: number
  related_type: string | null
  related_id: number | null
  created_at: string
}

export interface NotificationCreateParams {
  user_id?: number | null
  title: string
  content: string
  type: 'APPOINTMENT' | 'DISPENSE' | 'SYSTEM' | 'SYSTEM_IMPORTANT'
}

export interface AdminNotificationItem {
  id: number
  title: string
  content: string
  type: string
  recipient_count: number
  created_at: string
}

export interface AdminNotificationListParams {
  page?: number
  page_size?: number
  title?: string
  type?: string
}

// ===== 数据字典 =====

export interface DataDict {
  id: number
  dict_type: string
  dict_key: number
  dict_label: string
  sort_order: number
}

// ===== 系统配置 =====

export interface SystemConfig {
  id: number
  config_key: string
  config_value: string
  description: string | null
  created_at: string
}

// ===== 操作日志 =====

export interface AuditLog {
  id: number
  user_id: number | null
  user_name: string | null
  role: number | null
  action: string
  target_type: string | null
  target_id: number | null
  detail: string | null
  ip_address: string | null
  created_at: string
}

// ===== 医生端病人 =====

export interface DiagnosisRecordItem {
  id: number
  chief_complaint: string | null
  diagnosis_result: string | null
  created_at: string | null
}

export interface DoctorPatient {
  id: number
  name: string | null
  gender: number | null
  birth_date: string | null
  address: string | null
  blood_type: string | null
  allergy_history: string | null
  phone: string | null
  avatar: string | null
  last_diagnosis_at: string | null
  diagnosis_records: DiagnosisRecordItem[]
}
