<template>
  <div class="page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索医生或科室"
        clearable
        :prefix-icon="Search"
      />
      <el-select
        v-model="statusFilter"
        placeholder="状态"
        clearable
        style="width:110px"
        @change="fetchData"
      >
        <el-option label="待就诊" :value="1" />
        <el-option label="已完成" :value="2" />
        <el-option label="已取消" :value="0" />
      </el-select>
    </div>

    <!-- 卡片网格 -->
    <div v-loading="loading" class="card-grid">
      <el-empty v-if="!loading && sortedList.length === 0" description="暂无挂号记录" />
      <div
        v-for="item in sortedList"
        :key="item.id"
        class="appointment-card"
        :class="{ 'is-today': isToday(item.appointment_time) }"
      >
        <div class="card-date">{{ formatDate(item.appointment_time) }}</div>
        <div class="card-doctor-dept">{{ item.doctor_name }} · {{ item.department_name || '-' }}</div>
        <div class="card-schedule">
          <template v-if="item.schedule_start_time && item.schedule_end_time">
            {{ item.schedule_start_time }} ~ {{ item.schedule_end_time }}
          </template>
          <template v-else>-</template>
        </div>
        <div class="card-time">挂号时间: {{ formatDateTime(item.created_at) }}</div>
        <div class="card-status">
          <el-tag :type="statusTagType(item.status)" size="small">{{ statusLabel(item.status) }}</el-tag>
        </div>
        <div class="card-action">
          <el-button
            v-if="item.status === 1"
            size="small"
            type="danger"
            @click="handleCancel(item)"
          >取消</el-button>
          <el-tooltip
            v-else-if="item.status === 0 && isSlotFull(item)"
            content="该时段已约满，无法恢复"
            placement="top"
          >
            <el-button size="small" type="primary" disabled>已约满</el-button>
          </el-tooltip>
          <el-button
            v-else-if="item.status === 0"
            size="small"
            type="primary"
            @click="handleRestore(item)"
          >恢复</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appointmentsApi, formatDateTime } from '@medflow/shared'
import type { Appointment } from '@medflow/shared'

const list = ref<Appointment[]>([])
const loading = ref(true)
const searchText = ref('')
const statusFilter = ref<number | undefined>(undefined)

/** 按搜索词过滤 */
const filteredList = computed(() => {
  const kw = searchText.value.trim().toLowerCase()
  if (!kw) return list.value
  return list.value.filter(item =>
    item.doctor_name.toLowerCase().includes(kw) ||
    (item.department_name || '').toLowerCase().includes(kw)
  )
})

function parseDate(dateStr: string): Date {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d)
}

/** 排序：未来日期升序 → 过去日期降序；同日按 schedule_start_time 升序 */
const sortedList = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayTs = today.getTime()

  const sorted = [...filteredList.value].sort((a, b) => {
    const dateA = a.appointment_time ? parseDate(a.appointment_time.slice(0, 10)) : null
    const dateB = b.appointment_time ? parseDate(b.appointment_time.slice(0, 10)) : null
    if (!dateA && !dateB) return 0
    if (!dateA) return 1
    if (!dateB) return -1

    const tsA = dateA.getTime()
    const tsB = dateB.getTime()
    const isFutureA = tsA >= todayTs
    const isFutureB = tsB >= todayTs

    // 未来在前，过去在后
    if (isFutureA && !isFutureB) return -1
    if (!isFutureA && isFutureB) return 1

    if (isFutureA && isFutureB) {
      // 未来：日期升序
      if (tsA !== tsB) return tsA - tsB
    } else {
      // 过去：日期降序（最近的过去在前）
      if (tsA !== tsB) return tsB - tsA
    }

    // 同日：按时段开始时间升序
    const ta = a.schedule_start_time || '99:99'
    const tb = b.schedule_start_time || '99:99'
    return ta.localeCompare(tb)
  })

  return sorted
})

function isToday(iso: string | null): boolean {
  if (!iso) return false
  const today = new Date()
  const date = parseDate(iso.slice(0, 10))
  return date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  return iso.slice(11, 16)
}

const weekNames = ['日', '一', '二', '三', '四', '五', '六']

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const d = parseDate(iso.slice(0, 10))
  const m = d.getMonth() + 1
  const day = d.getDate()
  const w = weekNames[d.getDay()]
  return `${m}月${day}日 周${w}`
}

function statusTagType(status: number): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 2) return 'success'
  if (status === 0) return 'info'
  return 'warning'
}

function statusLabel(status: number): string {
  if (status === 0) return '已取消'
  if (status === 1) return '待就诊'
  if (status === 2) return '已完成'
  return '-'
}

function isSlotFull(item: Appointment): boolean {
  if (item.schedule_max_patients == null || item.schedule_booked_count == null) return false
  return item.schedule_booked_count >= item.schedule_max_patients
}

async function fetchData() {
  loading.value = true
  try {
    const res = await appointmentsApi.listAppointments({ status: statusFilter.value })
    list.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleCancel(row: Appointment) {
  try {
    await ElMessageBox.confirm('确定要取消该挂号吗？')
    await appointmentsApi.cancelAppointment(row.id)
    ElMessage.success('挂号已取消')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleRestore(row: Appointment) {
  try {
    await ElMessageBox.confirm('确定要恢复该挂号吗？')
    await appointmentsApi.restoreAppointment(row.id)
    ElMessage.success('挂号已恢复')
    fetchData()
  } catch { /* 取消 */ }
}

onMounted(fetchData)
</script>

<style scoped>
.search-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 480px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.appointment-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  aspect-ratio: 1 / 1;
  transition: box-shadow 0.2s;
  min-height: 200px;
}

.appointment-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.appointment-card.is-today {
  border-color: #f0a0b0;
  background: linear-gradient(135deg, #fff5f7 0%, #fff 100%);
  box-shadow: 0 0 0 1px #f0a0b0 inset;
}

.card-date {
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}

.card-doctor-dept {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  flex-shrink: 0;
}

.card-schedule {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  flex-shrink: 0;
}

.card-time {
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}

.card-status {
  flex-shrink: 0;
}

.card-action {
  margin-top: auto;
  padding-top: 4px;
}

.card-action .el-button {
  width: 100%;
}
</style>
