import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { getToken, isTokenExpired } from './token'

// 注意：在路由守卫里无法直接使用 pinia store（因为 pinia 尚未安装），
// 所以这里从 token payload 中解析角色。

function getRoleFromToken(): number | null {
  const token = getToken()
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // 后端 JWT 中 role 可能放在 payload 里，需确认。此处假设后续在 login 时也存入 localStorage
    return null // token payload 中不一定有 role，需要额外存储
  } catch {
    return null
  }
}

const ROLE_KEY = 'medflow_role'

export function setRole(role: number): void {
  localStorage.setItem(ROLE_KEY, String(role))
}

export function getRole(): number | null {
  const v = localStorage.getItem(ROLE_KEY)
  return v ? Number(v) : null
}

export function removeRole(): void {
  localStorage.removeItem(ROLE_KEY)
}

export function requireAuth(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const token = getToken()
  if (!token || isTokenExpired()) {
    const app = to.path.split('/')[1] // admin / doctor / patient
    next(`/${app}/login`)
    return
  }
  next()
}

export function requireRole(allowedRoles: number[]) {
  return (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    const role = getRole()
    if (role === null || !allowedRoles.includes(role)) {
      const app = to.path.split('/')[1]
      next(`/${app}/login`)
      return
    }
    next()
  }
}
