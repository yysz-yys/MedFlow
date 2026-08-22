<template>
  <div class="app-layout">
    <!-- 侧边栏 — 固定占满屏幕高度 -->
    <aside class="app-aside" :style="{ width: asideWidth, backgroundColor: asideColor }">
      <div class="logo">{{ logo }}</div>
      <el-menu
        :default-active="currentRoute"
        router
        :background-color="asideColor"
        text-color="#ffffff80"
        active-text-color="#ffffff"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧区域 -->
    <div class="app-right">
      <!-- 顶栏 -->
      <header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <!-- 通知铃铛 -->
          <el-badge v-if="showNotificationBell" :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-icon class="notification-bell" @click="goNotifications">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path fill="currentColor" d="M816 768h-24V428c0-141.1-104.3-257.7-240-277.1V112c0-22.1-17.9-40-40-40s-40 17.9-40 40v38.9c-135.7 19.4-240 136-240 277.1v340h-24c-17.7 0-32 14.3-32 32v32c0 4.4 3.6 8 8 8h216c0 61.8 50.2 112 112 112s112-50.2 112-112h216c4.4 0 8-3.6 8-8v-32c0-17.7-14.3-32-32-32zM512 888c-26.5 0-48-21.5-48-48h96c0 26.5-21.5 48-48 48zM304 724V428c0-114.9 93.1-208 208-208s208 93.1 208 208v296H304z"/>
              </svg>
            </el-icon>
          </el-badge>
          <!-- 用户头像下拉 -->
          <el-dropdown @command="handleCommand" trigger="click" placement="bottom-end">
            <div class="user-avatar" :style="avatarUrl ? { backgroundImage: `url(${avatarUrl})`, backgroundSize: 'cover' } : { background: avatarColor }">
              <span v-if="!avatarUrl">{{ userInitial }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区 — 只有这里滚动 -->
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, provide, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import * as authApi from '../api/auth'
import * as notificationsApi from '../api/notifications'


export interface MenuItem {
  path: string
  label: string
  icon: string
}

const props = withDefaults(defineProps<{
  logo?: string
  menuItems?: MenuItem[]
  asideWidth?: string
  showNotificationBell?: boolean
  avatarColor?: string
  asideColor?: string
}>(), {
  logo: '云诊易',
  menuItems: () => [],
  asideWidth: '220px',
  showNotificationBell: false,
  avatarColor: '#409eff',
  asideColor: '#001529',
})

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => route.path)

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const avatarPath = ref<string | null>(null)
const avatarUrl = computed(() => {
  if (!avatarPath.value) return ''
  return API_BASE.replace('/api/v1', '') + '/uploads/' + avatarPath.value
})
const userInitial = computed(() => (authStore.user?.name || '?')[0])

const unreadCount = ref(0)

async function fetchUnreadCount() {
  if (!props.showNotificationBell) return
  try {
    const res = await notificationsApi.getUnreadCount()
    unreadCount.value = res.data.unread_count
  } catch { /* ignore */ }
}

provide('refreshUnreadCount', fetchUnreadCount)

// 路由切换时自动刷新未读数
watch(() => route.path, () => {
  fetchUnreadCount()
})

// 每30秒轮询未读数
let unreadTimer: ReturnType<typeof setInterval> | null = null

function goNotifications() {
  const app = route.path.split('/')[1]
  router.push(`/${app}/notifications`)
}

async function fetchAvatar() {
  try {
    const res = await authApi.getAvatar()
    avatarPath.value = res.data.avatar
  } catch { /* ignore */ }
}

function handleCommand(cmd: string) {
  const app = route.path.split('/')[1]
  if (cmd === 'profile') {
    router.push(`/${app}/profile`)
  } else if (cmd === 'logout') {
    authStore.logout().then(() => {
      router.push(`/${app}/login`)
    })
  }
}

onMounted(() => {
  authStore.fetchMe()
  fetchAvatar()
  fetchUnreadCount()
  if (props.showNotificationBell) {
    unreadTimer = setInterval(fetchUnreadCount, 30000)
  }
})

onUnmounted(() => {
  if (unreadTimer) clearInterval(unreadTimer)
})
</script>

<style scoped>
/* ===== 根容器：占满视口，禁止全局滚动 ===== */
.app-layout {
  display: flex;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

/* ===== 侧边栏：固定全高 ===== */
.app-aside {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-aside :deep(.el-menu) {
  flex: 1;
  border-right: none;
  overflow-y: auto;
}

.logo {
  flex-shrink: 0;
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
}

/* ===== 右侧区域 ===== */
.app-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ===== 顶栏 ===== */
.app-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-right: 8px;
}

.notification-bell {
  font-size: 22px;
  color: #606266;
  cursor: pointer;
  transition: color 0.2s;
}

.notification-bell:hover {
  color: var(--el-color-primary);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #fff;
  cursor: pointer;
  overflow: hidden;
  background-size: cover;
  background-position: center;
}

/* ===== 内容区：只有这里滚动 ===== */
.app-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
