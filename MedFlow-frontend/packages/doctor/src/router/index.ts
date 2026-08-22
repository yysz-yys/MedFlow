import { createRouter, createWebHistory } from 'vue-router'
import { requireAuth } from '@medflow/shared'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/doctor/login',
    },
    {
      path: '/doctor/login',
      name: 'DoctorLogin',
      component: () => import('../pages/Login.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/doctor',
      component: () => import('../pages/Layout.vue'),
      beforeEnter: requireAuth,
      children: [
        {
          path: '',
          redirect: '/doctor/dashboard',
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../pages/Dashboard.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'patients',
          name: 'Patients',
          component: () => import('../pages/Patients.vue'),
          meta: { title: '我的病人' },
        },
        {
          path: 'appointments',
          name: 'Appointments',
          component: () => import('../pages/Appointments.vue'),
          meta: { title: '挂号·诊断' },
        },
        {
          path: 'diagnosis-records',
          name: 'DiagnosisRecords',
          component: () => import('../pages/DiagnosisRecords.vue'),
          meta: { title: '诊断记录' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('../pages/Orders.vue'),
          meta: { title: '订单查看' },
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
  if (to.path.startsWith('/doctor') && to.path !== '/doctor/login') {
    if (role !== '1') {
      next('/doctor/login')
      return
    }
  }
  next()
})

export default router
