<template>
  <div class="book-page">
    <!-- 左侧：科室侧栏 -->
    <aside class="dept-sidebar">
      <div class="sidebar-search">
        <el-input
          v-model="deptSearch"
          placeholder="搜索科室"
          clearable
        />
      </div>
      <div class="sidebar-list">
        <div
          v-for="d in filteredDepts"
          :key="d.id"
          class="dept-card"
          :class="{ selected: selectedDeptId === d.id }"
          @click="selectDept(d.id)"
        >
          <div class="dept-card-header" @click.stop="toggleDept(d.id)">
            <span class="dept-name">{{ d.name }}</span>
            <span class="dept-count">{{ doctorCountMap[d.id] ?? 0 }}人</span>
            <span class="dept-arrow">{{ expandedDeptIds.has(d.id) ? '▲' : '▼' }}</span>
          </div>
          <div v-if="expandedDeptIds.has(d.id)" class="dept-card-body">
            {{ d.description || '暂无描述' }}
          </div>
        </div>
        <div v-if="filteredDepts.length === 0" class="sidebar-empty">无匹配科室</div>
      </div>
    </aside>

    <!-- 右侧：内容区 -->
    <div class="right-panel">
      <!-- 未选科室时的提示 -->
      <div v-if="!selectedDeptId" class="right-empty">
        <el-empty description="请先选择科室" />
      </div>

      <!-- 面包屑 -->
      <div v-if="selectedDeptId" class="breadcrumb">
        <span
          class="breadcrumb-item"
          :class="{ clickable: !!selectedDoctorId }"
          @click="selectedDoctorId ? backToDept() : undefined"
        >
          {{ selectedDept?.name }}
        </span>
        <template v-if="selectedDoctor">
          <span class="breadcrumb-sep">&gt;</span>
          <span class="breadcrumb-item current">{{ selectedDoctor.name }}</span>
        </template>
      </div>

      <!-- 医生卡片区 -->
      <div v-if="selectedDeptId" class="doctor-section">
        <div class="section-header">
          <span class="section-title">选择医生</span>
          <el-input
            v-model="doctorSearch"
            placeholder="搜索医生姓名/职称"
            clearable
            class="doctor-search-input"
          />
        </div>

        <!-- 有医生 -->
        <div v-if="filteredDoctors.length > 0" class="doctor-grid">
          <div
            v-for="d in filteredDoctors"
            :key="d.id"
            class="doctor-card"
            :class="{ selected: selectedDoctorId === d.id }"
            @click="selectDoctor(d.id)"
          >
            <div class="doctor-avatar">{{ d.name[0] }}</div>
            <div class="doctor-info">
              <div class="doctor-name">{{ d.name }}</div>
              <div class="doctor-title">{{ d.title || '暂无职称' }}</div>
              <div class="doctor-dept">{{ d.department_name || '暂无科室' }}</div>
            </div>
          </div>
        </div>

        <!-- 无医生空状态 -->
        <div v-else class="doctor-empty">
          <el-empty :description="doctorSearch ? '无匹配医生' : '该科室暂未安排医生'" />
        </div>
      </div>

      <!-- 时段卡片区 -->
      <div v-if="selectedDoctorId" class="schedule-section">
        <div class="section-header">
          <span class="section-title">{{ selectedDoctor?.name }} · 可约时段</span>
        </div>

        <div class="schedule-body">
          <!-- 加载中 -->
          <div v-if="loadingSchedules" class="schedule-loading" v-loading="true" style="min-height:120px" />

          <!-- 有排班 — 按日期分组 -->
          <div v-else-if="availableSchedules.length > 0" class="schedule-grid">
            <div
              v-for="group in groupedSchedules"
              :key="group.date"
              class="schedule-card"
            >
              <div class="schedule-date">{{ group.date }}&emsp;&emsp;{{ formatWeekday(group.date) }}</div>
              <div class="schedule-slots">
                <div
                  v-for="s in group.slots"
                  :key="s.id"
                  class="schedule-slot"
                  :class="{
                    selected: selectedScheduleId === s.id,
                    full: s.patient_booked || s.booked_count >= s.max_patients,
                  }"
                  @click="!s.patient_booked && s.booked_count < s.max_patients && selectSchedule(s.id)"
                >
                  <span class="slot-time">{{ bookableWindow(s) }}</span>
                  <span class="slot-remain">
                    {{ s.patient_booked ? '已预约' : '余 ' + (s.max_patients - s.booked_count) + ' 号' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 无排班空状态 -->
          <div v-else class="schedule-empty">
            <el-empty description="该医生暂无可用时段" />
          </div>
        </div>

        <!-- 确认按钮 — 固定在底部，不随滚动 -->
        <div v-if="availableSchedules.length > 0" class="schedule-actions">
          <el-button
            type="primary"
            :disabled="!selectedScheduleId"
            :loading="submitting"
            @click="handleSubmit"
          >
            确认挂号
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { departmentsApi, doctorsApi, doctorSchedulesApi, appointmentsApi } from '@medflow/shared'
import type { Department, Doctor, DoctorSchedule } from '@medflow/shared'

const router = useRouter()

// ========== 数据 ==========
const depts = ref<Department[]>([])
const doctors = ref<Doctor[]>([])
const schedules = ref<DoctorSchedule[]>([])

// ========== 选择状态 ==========
const selectedDeptId = ref<number | null>(null)
const selectedDoctorId = ref<number | null>(null)
const selectedScheduleId = ref<number | null>(null)
const submitting = ref(false)

// ========== UI 状态 ==========
const deptSearch = ref('')
const doctorSearch = ref('')
const expandedDeptIds = ref<Set<number>>(new Set())
const loadingSchedules = ref(false)

// ========== 计算属性 ==========

/** 所有科室的医生数量（页面加载时一次性获取用于计数） */
const doctorCountMap = computed(() => {
  const map: Record<number, number> = {}
  for (const d of doctors.value) {
    if (d.department_id) {
      map[d.department_id] = (map[d.department_id] ?? 0) + 1
    }
  }
  return map
})

/** 搜索过滤后的科室列表 */
const filteredDepts = computed(() => {
  if (!deptSearch.value) return depts.value
  const kw = deptSearch.value.toLowerCase()
  return depts.value.filter(d => d.name.toLowerCase().includes(kw))
})

/** 当前选中科室对象 */
const selectedDept = computed(() =>
  depts.value.find(d => d.id === selectedDeptId.value) ?? null
)

/** 当前选中科室下的医生（搜索过滤后） */
const filteredDoctors = computed(() => {
  const list = doctors.value.filter(d => d.department_id === selectedDeptId.value)
  if (!doctorSearch.value) return list
  const kw = doctorSearch.value.toLowerCase()
  return list.filter(d =>
    d.name.toLowerCase().includes(kw) || (d.title || '').toLowerCase().includes(kw)
  )
})

/** 当前选中医生对象 */
const selectedDoctor = computed(() =>
  doctors.value.find(d => d.id === selectedDoctorId.value) ?? null
)

/** 当天 ~ 未来一周（含当天共8天）的可约时段 */
const availableSchedules = computed(() => {
  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)
  const max = new Date(today)
  max.setDate(max.getDate() + 7)
  const maxStr = max.toISOString().slice(0, 10)
  return schedules.value.filter(s =>
    s.work_date >= todayStr && s.work_date <= maxStr &&
    timeToMinutes(s.end_time) - timeToMinutes(s.start_time) > 30
  )
})

/** 按 work_date 分组后的可约时段 */
const groupedSchedules = computed(() => {
  const map = new Map<string, DoctorSchedule[]>()
  for (const s of availableSchedules.value) {
    const list = map.get(s.work_date) ?? []
    list.push(s)
    map.set(s.work_date, list)
  }
  return Array.from(map.entries()).map(([date, slots]) => ({ date, slots }))
})

// ========== 方法 ==========

/** 折叠/展开科室卡片 */
function toggleDept(id: number) {
  const next = new Set(expandedDeptIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedDeptIds.value = next
}

/** 点击科室 — 选中该科室医生，同时自动展开介绍 */
function selectDept(id: number) {
  if (selectedDeptId.value === id) return
  selectedDeptId.value = id
  selectedDoctorId.value = null
  selectedScheduleId.value = null
  schedules.value = []
  doctorSearch.value = ''
  const next = new Set(expandedDeptIds.value)
  next.add(id)
  expandedDeptIds.value = next
}

/** 点击医生 — 选中并加载该医生排班 */
async function selectDoctor(id: number) {
  selectedDoctorId.value = id
  selectedScheduleId.value = null
  loadingSchedules.value = true
  try {
    const res = await doctorSchedulesApi.listSchedules({ doctor_id: id })
    schedules.value = res.data
  } finally {
    loadingSchedules.value = false
  }
}

/** 点击时段卡片 */
function selectSchedule(id: number) {
  selectedScheduleId.value = id
}

/** 面包屑返回 — 清除医生和时段选择 */
function backToDept() {
  selectedDoctorId.value = null
  selectedScheduleId.value = null
  schedules.value = []
}

/** 根据日期字符串（YYYY-MM-DD）返回中文星期 */
function formatWeekday(dateStr: string): string {
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const d = new Date(dateStr)
  return weekdays[d.getDay()] ?? ''
}

/** 解析 HH:MM:SS 为分钟数 */
function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

/** 分钟数转 HH:MM */
function minutesToTime(m: number): string {
  const h = Math.floor(m / 60).toString().padStart(2, '0')
  const mm = (m % 60).toString().padStart(2, '0')
  return `${h}:${mm}`
}

/** 时段是否可预约（时长 > 30分钟） */
function isSlotBookable(s: { start_time: string; end_time: string }): boolean {
  return timeToMinutes(s.end_time) - timeToMinutes(s.start_time) > 30
}

/** 可预约时间段：开始后30分钟 ~ 结束前30分钟 */
function bookableWindow(s: { start_time: string; end_time: string }): string {
  const start = timeToMinutes(s.start_time) + 30
  const end = timeToMinutes(s.end_time) - 30
  return `${minutesToTime(start)} - ${minutesToTime(end)}`
}

/** 确认挂号 */
async function handleSubmit() {
  submitting.value = true
  try {
    await appointmentsApi.createAppointment({
      doctor_id: selectedDoctorId.value!,
      schedule_id: selectedScheduleId.value!,
    })
    ElMessage.success('挂号成功')
    router.push('/patient/my-appointments')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '挂号失败')
  } finally {
    submitting.value = false
  }
}

// ========== 生命周期 ==========
onMounted(async () => {
  const [d, doc] = await Promise.all([
    departmentsApi.listDepartments({ page_size: 999 }),
    doctorsApi.listDoctors({ page_size: 999 }),
  ])
  depts.value = d.data.items
  doctors.value = doc.data.items
})
</script>

<style scoped>
/* ===== 整体布局 ===== */
.book-page {
  display: flex;
  gap: 0;
  height: 100%;
}

/* ===== 左侧科室侧栏 ===== */
.dept-sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
  padding-right: 16px;
}

.sidebar-search {
  flex-shrink: 0;
  margin-bottom: 12px;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dept-card {
  cursor: pointer;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: #fff;
}

.dept-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dept-card.selected {
  border-color: var(--el-color-primary);
}

.dept-card-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  gap: 8px;
}

.dept-name {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.dept-count {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.dept-arrow {
  font-size: 10px;
  color: #c0c4cc;
  flex-shrink: 0;
}

.dept-card-body {
  padding: 0 14px 12px;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

.sidebar-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 30px 0;
  font-size: 14px;
}

/* ===== 右侧内容区 ===== */
.right-panel {
  flex: 1;
  min-width: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
}

.right-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== 面包屑 ===== */
.breadcrumb {
  flex-shrink: 0;
  padding: 12px 0;
  font-size: 15px;
  color: #303133;
}

.breadcrumb-item {
  color: #303133;
}

.breadcrumb-item.clickable {
  color: var(--el-color-primary);
  cursor: pointer;
}

.breadcrumb-item.clickable:hover {
  text-decoration: underline;
}

.breadcrumb-item.current {
  color: #303133;
  font-weight: 500;
}

.breadcrumb-sep {
  margin: 0 8px;
  color: #c0c4cc;
}

/* ===== 医生卡片区 ===== */
.doctor-section {
  flex-shrink: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.doctor-search-input {
  width: 220px;
}

.doctor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.doctor-card {
  cursor: pointer;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 14px;
}

.doctor-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.doctor-card.selected {
  border-color: var(--el-color-primary);
}

.doctor-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #67c23a;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  flex-shrink: 0;
}

.doctor-info {
  flex: 1;
  min-width: 0;
}

.doctor-info .doctor-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.doctor-info .doctor-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 2px;
}

.doctor-info .doctor-dept {
  font-size: 12px;
  color: #909399;
}

.doctor-empty {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

/* ===== 时段卡片区 ===== */
.schedule-section {
  flex: 1;
  min-height: 0;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}

.schedule-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.schedule-card {
  border: 2px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.schedule-date {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 4px;
}

.schedule-slots {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.schedule-slot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  gap: 12px;
}

.schedule-slot:hover {
  border-color: var(--el-color-primary);
  background: #fdf6f6;
}

.schedule-slot.selected {
  border-color: var(--el-color-primary);
}

.schedule-slot.full,
.schedule-slot.full:hover {
  cursor: not-allowed;
  background: #f5f5f5;
  border-color: #e4e7ed;
  box-shadow: none;
}

.schedule-slot.full .slot-time,
.schedule-slot.full .slot-remain {
  color: #c0c4cc;
}

.slot-time {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
}

.slot-remain {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-color-primary);
  white-space: nowrap;
  flex-shrink: 0;
}

.schedule-empty {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.schedule-loading {
  display: flex;
  justify-content: center;
  align-items: center;
}

.schedule-actions {
  flex-shrink: 0;
  margin-top: 16px;
  padding: 12px 0;
  display: flex;
  justify-content: center;
  border-top: 1px solid #ebeef5;
}
</style>
