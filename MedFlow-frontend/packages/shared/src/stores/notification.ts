import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as notificationsApi from '../api/notifications'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)

  async function fetchUnreadCount() {
    try {
      const res = await notificationsApi.getUnreadCount()
      unreadCount.value = res.data.unread_count
    } catch {
      unreadCount.value = 0
    }
  }

  function increment(n = 1) { unreadCount.value += n }
  function decrement(n = 1) { unreadCount.value = Math.max(0, unreadCount.value - n) }

  return { unreadCount, fetchUnreadCount, increment, decrement }
})
