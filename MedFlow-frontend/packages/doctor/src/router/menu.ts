import type { MenuItem } from '@medflow/shared'

export const doctorMenu: MenuItem[] = [
  { path: '/doctor/dashboard', label: '工作台', icon: 'HomeFilled' },
  { path: '/doctor/appointments', label: '挂号·诊断', icon: 'Calendar' },
  { path: '/doctor/diagnosis-records', label: '诊断记录', icon: 'Document' },
  { path: '/doctor/orders', label: '订单查看', icon: 'Goods' },
  { path: '/doctor/patients', label: '我的病人', icon: 'User' },
  { path: '/doctor/notifications', label: '通知中心', icon: 'Bell' },
]
