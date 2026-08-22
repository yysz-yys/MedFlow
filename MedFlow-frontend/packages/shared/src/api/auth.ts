import request from './request'
import type { User, LoginParams, LoginResult, RegisterParams, UpdateMeParams, ChangePasswordParams, ResetPasswordByCodeParams, SendCodeParams } from '../types'

export function login(params: LoginParams) {
  return request.post<LoginResult>('/auth/login', params)
}

export function logout() {
  return request.post('/auth/logout')
}

export function getMe() {
  return request.get<User>('/auth/me')
}

export function updateMe(params: UpdateMeParams) {
  return request.put('/auth/me', params)
}

export function changePassword(params: ChangePasswordParams) {
  return request.put('/auth/password', params)
}

export function sendCode(params: SendCodeParams) {
  return request.post('/auth/send-code', params)
}

export function resetPasswordByCode(params: ResetPasswordByCodeParams) {
  return request.post('/auth/reset-password-by-code', params)
}

export function getCaptcha() {
  return request.get<{ captcha_id: string; image: string }>('/auth/captcha')
}

export function register(params: RegisterParams) {
  return request.post<{ message: string; user_id: number }>('/auth/register', params)
}

export function uploadAvatar(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request.post<{ avatar: string }>('/auth/me/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getAvatar() {
  return request.get<{ avatar: string | null }>('/auth/me/avatar')
}
