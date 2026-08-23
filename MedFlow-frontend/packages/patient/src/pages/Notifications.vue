<template>
  <div class="page">
    <!-- Master-Detail 主体 -->
    <div class="notify-body">
      <!-- 左侧：Outlook 风格列表 -->
      <div class="notify-body__list">
        <!-- 标签页 -->
        <div class="notify-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['notify-tab', { active: activeTab === tab.key }]"
            @click="switchTab(tab.key)"
          >
            {{ tab.label }} ({{ tabTotal(tab.key) }})
          </button>
        </div>

        <!-- 滚动列表 -->
        <div
          class="notify-list"
          ref="listRef"
          @scroll="handleScroll"
          v-loading="loading"
        >
          <div
            v-for="item in currentList"
            :key="item.id"
            :class="['notify-item', { selected: selectedId === item.id, unread: !item.is_read }]"
            @click="handleRowClick(item)"
          >
            <div class="notify-item__head">
              <span class="notify-item__type">
                {{ typeLabel(item.type) }}
                <span v-if="item.type === 'SYSTEM_IMPORTANT'" class="type-tag important">重点</span>
                <span v-else-if="item.type === 'SYSTEM'" class="type-tag normal">其他</span>
              </span>
              <span class="notify-item__time">{{ formatDateTime(item.created_at) }}</span>
            </div>
            <div class="notify-item__title">
              <span v-if="!item.is_read" class="unread-dot"></span>
              {{ item.title }}
            </div>
            <div class="notify-item__preview">{{ item.content }}</div>
          </div>
          <div v-if="loadingMore" class="notify-list__loading">加载中...</div>
          <div v-if="noMore && currentList.length > 0" class="notify-list__nomore">没有更多了</div>
          <div v-if="!loading && currentList.length === 0" class="notify-list__empty">暂无通知</div>
        </div>
      </div>

      <!-- 右侧：详情面板 -->
      <div class="notify-body__detail">
        <template v-if="selectedItem">
          <h3 class="detail-title">{{ selectedItem.title }}</h3>
          <div class="detail-meta">
            <span class="detail-type">{{ typeLabel(selectedItem.type) }}</span>
            <span class="detail-time">{{ formatDateTime(selectedItem.created_at) }}</span>
            <el-tag v-if="!selectedItem.is_read" type="primary" size="small">未读</el-tag>
            <el-tag v-else type="info" size="small">已读</el-tag>
          </div>
          <el-divider />
          <div class="detail-content">{{ selectedItem.content }}</div>
          <div v-if="!selectedItem.is_read" class="detail-action">
            <el-button type="primary" size="small" @click="handleMarkRead(selectedItem)">标记已读</el-button>
          </div>
        </template>
        <template v-else>
          <div class="detail-empty">
            <el-icon :size="48" color="#dcdfe6"><Message /></el-icon>
            <p>选择要阅读的项目</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject, nextTick } from 'vue'
import { Message } from '@element-plus/icons-vue'
import { notificationsApi, formatDateTime } from '@medflow/shared'
import type { Notification } from '@medflow/shared'

const tabs: { key: TabKey; label: string }[] = [
  { key: 'DISPENSE', label: '取药通知' },
  { key: 'SYSTEM', label: '系统通知' },
]
type TabKey = 'DISPENSE' | 'SYSTEM'

const activeTab = ref<TabKey>('DISPENSE')

// 每个标签页独立的列表和分页状态
const dataMap = ref<Record<TabKey, { list: Notification[]; total: number; page: number; noMore: boolean }>>({
  DISPENSE: { list: [], total: 0, page: 1, noMore: false },
  SYSTEM: { list: [], total: 0, page: 1, noMore: false },
})

const pageSize = 20
const loading = ref(false)
const loadingMore = ref(false)

const currentData = computed(() => dataMap.value[activeTab.value])
const currentList = computed(() => currentData.value.list)
const noMore = computed(() => currentData.value.noMore)

const selectedItem = ref<Notification | null>(null)
const selectedId = computed(() => selectedItem.value?.id ?? null)

const listRef = ref<HTMLElement | null>(null)

const typeLabel = (t: string) => {
  const map: Record<string, string> = {
    SYSTEM_IMPORTANT: '系统公告',
    SYSTEM: '系统公告',
    APPOINTMENT: '挂号通知',
    DISPENSE: '诊疗取药',
  }
  return map[t] || t
}

function tabTotal(key: TabKey) {
  return dataMap.value[key].total
}

async function fetchTabData(tab: TabKey, page: number, append: boolean) {
  const res = await notificationsApi.listNotifications({ page, page_size: pageSize, type: tab })
  const data = dataMap.value[tab]
  if (append) {
    data.list.push(...res.data.items)
  } else {
    data.list = res.data.items
  }
  data.total = res.data.total
  data.page = page
  data.noMore = res.data.items.length < pageSize
}

async function loadFirst() {
  loading.value = true
  try {
    const tab = activeTab.value
    await fetchTabData(tab, 1, false)
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || noMore.value) return
  loadingMore.value = true
  try {
    const tab = activeTab.value
    const nextPage = dataMap.value[tab].page + 1
    await fetchTabData(tab, nextPage, true)
  } catch {
    /* ignore */
  } finally {
    loadingMore.value = false
  }
}

async function switchTab(tab: TabKey) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  selectedItem.value = null
  const data = dataMap.value[tab]
  // 已有数据则直接展示，否则加载
  if (data.list.length === 0 && data.total === 0) {
    await loadFirst()
  }
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = 0
}

let lastScrollTop = 0

function handleScroll() {
  const el = listRef.value
  if (!el) return
  if (el.scrollTop <= lastScrollTop) {
    lastScrollTop = el.scrollTop
    return
  }
  lastScrollTop = el.scrollTop
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) {
    loadMore()
  }
}

function handleRowClick(item: Notification) {
  selectedItem.value = item
}

const refreshUnreadCount = inject<() => void>('refreshUnreadCount', () => {})

async function handleMarkRead(item: Notification) {
  try {
    await notificationsApi.markRead(item.id)
    item.is_read = 1
    refreshUnreadCount()
  } catch { /* ignore */ }
}

// 启动时预加载所有标签页的第一页
onMounted(async () => {
  await fetchTabData('DISPENSE', 1, false)
  fetchTabData('SYSTEM', 1, false)
  await nextTick()
})
</script>

<style scoped>
/* ---- 主体 ---- */
.notify-body {
  display: flex;
  gap: 0;
  height: calc(100vh - 160px);
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
}

/* ---- 左侧列表 ---- */
.notify-body__list {
  width: 40%;
  min-width: 360px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
}

.notify-tabs {
  display: flex;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.notify-tab {
  flex: 1;
  padding: 12px 8px;
  border: none;
  background: #f5f7fa;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  text-align: center;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}
.notify-tab:hover {
  color: #409eff;
}
.notify-tab.active {
  color: #409eff;
  background: #fff;
  border-bottom-color: #409eff;
}

.notify-list {
  flex: 1;
  overflow-y: scroll;
  padding: 0;
}

.notify-item {
  padding: 14px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f2f2f2;
  transition: background 0.15s;
}
.notify-item:hover {
  background: #f5f7fa;
}
.notify-item.selected {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
  padding-left: 13px;
}
.notify-item.unread {
  background: #fafafa;
}

.notify-item__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.notify-item__type {
  font-size: 12px;
  color: #909399;
}
.notify-item__time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
  margin-left: 8px;
}

.type-tag {
  display: inline-block;
  font-size: 11px;
  padding: 0 6px;
  border-radius: 3px;
  margin-left: 4px;
  line-height: 18px;
}
.type-tag.important {
  color: #f56c6c;
  background: #fef0f0;
}
.type-tag.normal {
  color: #909399;
  background: #f5f5f5;
}
.notify-item__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}
.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  flex-shrink: 0;
}
.notify-item__preview {
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notify-list__loading,
.notify-list__nomore,
.notify-list__empty {
  text-align: center;
  padding: 32px 16px;
  font-size: 13px;
  color: #c0c4cc;
}

/* ---- 右侧详情 ---- */
.notify-body__detail {
  flex: 1;
  min-width: 0;
  padding: 24px;
  overflow-y: scroll;
}

.detail-title {
  margin: 0 0 12px;
  font-size: 18px;
  color: #303133;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}
.detail-type {
  font-size: 13px;
  color: #909399;
}
.detail-time {
  font-size: 13px;
  color: #909399;
}
.detail-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
  margin-bottom: 16px;
}
.detail-action {
  margin-top: 16px;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
}
.detail-empty p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
