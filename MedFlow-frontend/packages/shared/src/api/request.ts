import axios from 'axios'
import { getToken, removeToken } from '../auth/token'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
})

// 请求拦截：自动带 token
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 跳登录（已在登录页则不跳，让页面显示错误提示）
request.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const isLoginPage = window.location.pathname.endsWith('/login')
      if (!isLoginPage) {
        removeToken()
        const role = window.location.pathname.split('/')[1]
        window.location.href = `/${role}/login`
      }
    }
    return Promise.reject(err)
  },
)

export default request
