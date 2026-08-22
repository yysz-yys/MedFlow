import type { MenuItem } from '@medflow/shared'

export const adminMenu: MenuItem[] = [
  { path: '/admin/dashboard', label: '工作台', icon: 'HomeFilled' },
  { path: '/admin/schedules', label: '排班管理', icon: 'Calendar' },
  { path: '/admin/departments', label: '科室管理', icon: 'OfficeBuilding' },
  { path: '/admin/drugs', label: '药品管理', icon: 'MedicineBottle' },
  { path: '/admin/orders', label: '订单管理', icon: 'Tickets' },
  { path: '/admin/personnel', label: '人员管理', icon: 'User' },
  { path: '/admin/config', label: '系统配置', icon: 'Setting' },
  { path: '/admin/dict', label: '数据字典', icon: 'Notebook' },
  { path: '/admin/logs', label: '操作日志', icon: 'Document' },
  { path: '/admin/notifications', label: '通知中心', icon: 'Bell' },
]
