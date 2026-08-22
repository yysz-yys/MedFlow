<template>
  <div class="page">
    <!-- 顶部操作栏 -->
    <div class="notify-header">
      <el-button type="primary" @click="showSendDialog = true">发送通知</el-button>
    </div>

    <!-- Master-Detail 主体 -->
    <div class="notify-body">
      <!-- 左侧：Outlook 风格列表 -->
      <div class="notify-body__list">
        <!-- 标签页 -->
        <div class="notify-tabs">
          <button
            :class="['notify-tab', { active: activeTab === 'important' }]"
            @click="switchTab('important')"
          >
            重点 ({{ importantTotal }})
          </button>
          <button
            :class="['notify-tab', { active: activeTab === 'normal' }]"
            @click="switchTab('normal')"
          >
            其他 ({{ normalTotal }})
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
            v-for="item in list"
            :key="item.id"
            :class="['notify-item', { selected: selectedId === item.id }]"
            @click="handleRowClick(item)"
          >
            <div class="notify-item__head">
              <span class="notify-item__type">{{ typeLabel(item.type) }}</span>
              <span class="notify-item__time">{{ formatDateTime(item.created_at) }}</span>
            </div>
            <div class="notify-item__title">{{ item.title }}</div>
            <div class="notify-item__preview">{{ item.content }}</div>
          </div>
          <div v-if="loadingMore" class="notify-list__loading">加载中...</div>
          <div v-if="noMore" class="notify-list__nomore">没有更多了</div>
        </div>
      </div>

      <!-- 右侧：详情面板 -->
      <div class="notify-body__detail">
        <template v-if="selectedItem">
          <h3 class="detail-title">{{ selectedItem.title }}</h3>
          <div class="detail-meta">
            <span class="detail-type">{{ typeLabel(selectedItem.type) }}</span>
            <span class="detail-time">{{ formatDateTime(selectedItem.created_at) }}</span>
          </div>
          <el-divider />
          <div class="detail-content">{{ selectedItem.content }}</div>
          <div class="detail-recipients">
            接收人数：<strong>{{ selectedItem.recipient_count }}</strong> 人
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

    <!-- 发送弹窗 -->
    <el-dialog v-model="showSendDialog" title="发送系统通知" width="640px" destroy-on-close>
      <el-form :model="sendForm" label-width="80px">
        <el-form-item label="通知标题" required>
          <el-input v-model="sendForm.title" placeholder="请输入通知标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="通知等级" required>
          <el-radio-group v-model="sendForm.level">
            <el-radio value="important">重点通知</el-radio>
            <el-radio value="normal">其他通知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="通知内容" required>
          <el-input
            v-model="sendForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入通知内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <div class="send-hint">
        此通知将发送给所有用户
      </div>
      <template #footer>
        <el-button @click="showSendDialog = false">取消</el-button>
        <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Message } from '@element-plus/icons-vue'
import { notificationsApi, formatDateTime } from '@medflow/shared'
import type { AdminNotificationItem } from '@medflow/shared'

// ---- 标签页 ----
const activeTab = ref<'important' | 'normal'>('important')

// ---- 双份数据 ----
const importantList = ref<AdminNotificationItem[]>([])
const normalList = ref<AdminNotificationItem[]>([])
const importantTotal = ref(0)
const normalTotal = ref(0)
const importantPage = ref(1)
const normalPage = ref(1)
const pageSize = 20
const loading = ref(false)
const loadingMore = ref(false)
const noMore = ref(false)

const list = computed(() => activeTab.value === 'important' ? importantList.value : normalList.value)

const selectedItem = ref<AdminNotificationItem | null>(null)
const selectedId = computed(() => selectedItem.value?.id ?? null)

const listRef = ref<HTMLElement | null>(null)

// ---- 发送弹窗 ----
const showSendDialog = ref(false)
const sending = ref(false)
const sendForm = reactive({ title: '', content: '', level: 'important' as 'important' | 'normal' })

const typeLabel = (t: string) => {
  const map: Record<string, string> = {
    SYSTEM_IMPORTANT: '系统公告',
    SYSTEM: '系统公告',
    APPOINTMENT: '挂号通知',
    DISPENSE: '诊疗取药',
  }
  return map[t] || t
}

// ---- 加载数据 ----
async function fetchTabData(type: 'important' | 'normal', page: number, append: boolean) {
  const typeValue = type === 'important' ? 'SYSTEM_IMPORTANT' : 'SYSTEM'
  const params: any = { page, page_size: pageSize, type: typeValue }

  const res = await notificationsApi.adminListNotifications(params)
  if (type === 'important') {
    if (append) {
      importantList.value.push(...res.data.items)
    } else {
      importantList.value = res.data.items
    }
    importantTotal.value = res.data.total
  } else {
    if (append) {
      normalList.value.push(...res.data.items)
    } else {
      normalList.value = res.data.items
    }
    normalTotal.value = res.data.total
  }
  return res.data.items.length
}

async function switchTab(tab: 'important' | 'normal') {
  if (activeTab.value === tab) return
  activeTab.value = tab
  selectedItem.value = null
  noMore.value = false
  const page = tab === 'important' ? importantPage.value : normalPage.value
  if (page === 1 && list.value.length === 0) {
    await loadFirst()
  }
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = 0
}

async function loadFirst() {
  loading.value = true
  try {
    const tab = activeTab.value
    if (tab === 'important') {
      importantPage.value = 1
    } else {
      normalPage.value = 1
    }
    const count = await fetchTabData(tab, 1, false)
    noMore.value = count < pageSize
  } catch {
    ElMessage.error('加载通知列表失败')
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || noMore.value) return
  loadingMore.value = true
  try {
    const tab = activeTab.value
    let nextPage: number
    if (tab === 'important') {
      nextPage = importantPage.value + 1
    } else {
      nextPage = normalPage.value + 1
    }
    const count = await fetchTabData(tab, nextPage, true)
    if (count < pageSize) noMore.value = true
    if (tab === 'important') {
      importantPage.value = nextPage
    } else {
      normalPage.value = nextPage
    }
  } catch {
    ElMessage.error('加载更多失败')
  } finally {
    loadingMore.value = false
  }
}

function handleScroll() {
  const el = listRef.value
  if (!el) return
  const threshold = 80
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - threshold) {
    loadMore()
  }
}

function handleRowClick(item: AdminNotificationItem) {
  selectedItem.value = item
}

// ---- 发送 ----
async function handleSend() {
  if (!sendForm.title || !sendForm.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  sending.value = true
  try {
    const type = sendForm.level === 'important' ? 'SYSTEM_IMPORTANT' : 'SYSTEM'
    await notificationsApi.createNotification({ title: sendForm.title, content: sendForm.content, type })
    ElMessage.success('通知已发送')
    showSendDialog.value = false
    sendForm.title = ''
    sendForm.content = ''
    sendForm.level = 'important'
    // 刷新当前标签页
    await loadFirst()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  // 预加载两个标签页的第一页数据
  await fetchTabData('important', 1, false)
  noMore.value = importantList.value.length < pageSize
  fetchTabData('normal', 1, false).then((count) => {
    // 不在主流程阻塞
  })
})
</script>

<style scoped>
.notify-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-bottom: 16px;
}

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
  padding: 12px 16px;
  border: none;
  background: #f5f7fa;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  text-align: center;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.notify-tab:hover {
  color: #409eff;
}
.notify-tab.active {
  color: #409eff;
  background: #fff;
  border-bottom-color: #409eff;
}

/* 列表区域 */
.notify-list {
  flex: 1;
  overflow-y: auto;
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
.notify-item__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notify-item__preview {
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notify-list__loading,
.notify-list__nomore {
  text-align: center;
  padding: 16px;
  font-size: 13px;
  color: #c0c4cc;
}

/* ---- 右侧详情 ---- */
.notify-body__detail {
  flex: 1;
  min-width: 0;
  padding: 24px;
  overflow-y: auto;
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
}
.detail-recipients {
  margin-top: 24px;
  color: #909399;
  font-size: 13px;
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

/* ---- 发送弹窗 ---- */
.send-hint {
  margin-top: -8px;
  padding-left: 80px;
  font-size: 13px;
  color: #909399;
}
</style>
