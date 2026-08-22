// API
export * as authApi from './api/auth'
export * as usersApi from './api/users'
export * as departmentsApi from './api/departments'
export * as doctorsApi from './api/doctors'
export * as doctorSchedulesApi from './api/doctorSchedules'
export * as patientsApi from './api/patients'
export * as drugsApi from './api/drugs'
export * as appointmentsApi from './api/appointments'
export * as diagnosisRecordsApi from './api/diagnosisRecords'
export * as prescriptionsApi from './api/prescriptions'
export * as drugOrdersApi from './api/drugOrders'
export * as filesApi from './api/files'
export * as notificationsApi from './api/notifications'
export * as dataDictApi from './api/dataDict'
export * as systemConfigApi from './api/systemConfig'
export * as auditLogsApi from './api/auditLogs'

// Types
export type * from './types'
export type { UserListItem } from './api/users'
export type { MenuItem } from './components/AppLayout.vue'

// Auth
export { getToken, setToken, removeToken, isTokenExpired } from './auth/token'
export { requireAuth, requireRole } from './auth/guards'

// Stores
export { useAuthStore } from './stores/auth'
export { useNotificationStore } from './stores/notification'

// Components
export { default as AppLayout } from './components/AppLayout.vue'

// Utils
export { getDictLabel, getDictOptions } from './utils/dict'
export { formatDate, formatDateTime, formatFileSize } from './utils/format'
export { parseScheduleConfig, type SchedulePeriod, type SchedulePeriods } from './utils/schedule'
