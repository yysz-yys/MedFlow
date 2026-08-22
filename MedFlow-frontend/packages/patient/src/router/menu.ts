import type { MenuItem } from '@medflow/shared'

export const patientMenu: MenuItem[] = [
  { path: '/patient/dashboard', label: '工作台', icon: 'HomeFilled' },
  { path: '/patient/book', label: '预约挂号', icon: 'Calendar' },
  { path: '/patient/my-appointments', label: '我的挂号', icon: 'Tickets' },
  { path: '/patient/diagnosis', label: '我的诊断', icon: 'Document' },
  { path: '/patient/orders', label: '我的订单', icon: 'Goods' },
  { path: '/patient/notifications', label: '通知中心', icon: 'Bell' },
]
