import { createRouter, createWebHistory } from 'vue-router'
import { requireAuth, requireRole } from '@medflow/shared'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/admin/login',
    },
    {
      path: '/admin/login',
      name: 'AdminLogin',
      component: () => import('../pages/Login.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/admin',
      component: () => import('../pages/Layout.vue'),
      beforeEnter: requireAuth,
      children: [
        {
          path: '',
          redirect: '/admin/dashboard',
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../pages/Dashboard.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'personnel',
          name: 'Personnel',
          component: () => import('../pages/Personnel.vue'),
          meta: { title: '人员管理' },
        },
        // 旧路由重定向 → 人员管理
        { path: 'users', redirect: '/admin/personnel' },
        { path: 'doctors', redirect: '/admin/personnel' },
        { path: 'patients', redirect: '/admin/personnel' },
        {
          path: 'departments',
          name: 'Departments',
          component: () => import('../pages/Departments.vue'),
          meta: { title: '科室管理' },
        },
        {
          path: 'schedules',
          name: 'Schedules',
          component: () => import('../pages/Schedules.vue'),
          meta: { title: '排班管理' },
        },
        {
          path: 'drugs',
          name: 'Drugs',
          component: () => import('../pages/Drugs.vue'),
          meta: { title: '药品管理' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('../pages/Orders.vue'),
          meta: { title: '订单管理' },
        },
        {
          path: 'config',
          name: 'Config',
          component: () => import('../pages/SystemConfig.vue'),
          meta: { title: '系统配置' },
        },
        {
          path: 'dict',
          name: 'Dict',
          component: () => import('../pages/DataDict.vue'),
          meta: { title: '数据字典' },
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('../pages/AuditLogs.vue'),
          meta: { title: '操作日志' },
        },
        {
          path: 'notifications',
          name: 'Notifications',
          component: () => import('../pages/Notifications.vue'),
          meta: { title: '通知中心' },
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('../pages/Profile.vue'),
          meta: { title: '个人信息' },
        },
      ],
    },
  ],
})

// 全局前置守卫：角色校验
router.beforeEach((to, from, next) => {
  const role = localStorage.getItem('medflow_role')
  if (to.path.startsWith('/admin') && to.path !== '/admin/login') {
    if (role !== '0') {
      next('/admin/login')
      return
    }
  }
  next()
})

export default router
