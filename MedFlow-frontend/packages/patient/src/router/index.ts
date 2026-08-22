import { createRouter, createWebHistory } from 'vue-router'
import { requireAuth } from '@medflow/shared'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/patient/login',
    },
    {
      path: '/patient/login',
      name: 'PatientLogin',
      component: () => import('../pages/Login.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/patient/register',
      name: 'PatientRegister',
      component: () => import('../pages/Register.vue'),
      meta: { title: '注册' },
    },
    {
      path: '/patient',
      component: () => import('../pages/Layout.vue'),
      beforeEnter: requireAuth,
      children: [
        {
          path: '',
          redirect: '/patient/dashboard',
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../pages/Dashboard.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'book',
          name: 'BookAppointment',
          component: () => import('../pages/BookAppointment.vue'),
          meta: { title: '预约挂号' },
        },
        {
          path: 'my-appointments',
          name: 'MyAppointments',
          component: () => import('../pages/MyAppointments.vue'),
          meta: { title: '我的挂号' },
        },
        {
          path: 'diagnosis',
          name: 'MyDiagnosis',
          component: () => import('../pages/MyDiagnosis.vue'),
          meta: { title: '我的诊断' },
        },
        {
          path: 'orders',
          name: 'MyOrders',
          component: () => import('../pages/MyOrders.vue'),
          meta: { title: '我的订单' },
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
  if (to.path.startsWith('/patient') && to.path !== '/patient/login' && to.path !== '/patient/register') {
    if (role !== '2') {
      next('/patient/login')
      return
    }
  }
  next()
})

export default router
