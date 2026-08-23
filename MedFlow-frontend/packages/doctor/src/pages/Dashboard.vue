<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div v-loading="cardsLoading" class="stats-row">
      <div class="stat-card">
        <div class="stat-num">{{ stats.todayPending }}</div>
        <div class="stat-label">今日待诊</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.weekScheduleDays }}</div>
        <div class="stat-label">本周排班天</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.monthCompleted }}</div>
        <div class="stat-label">本月接诊</div>
      </div>
    </div>

    <!-- 双栏 -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="10">
        <div class="panel">
          <div class="panel-title">今日待就诊</div>
          <div v-loading="aptLoading" class="panel-body">
            <el-result v-if="aptError" icon="error" title="加载失败">
              <template #extra>
                <el-button type="primary" size="small" @click="fetchTodayList">重试</el-button>
              </template>
            </el-result>
            <el-empty v-else-if="!aptLoading && todayList.length === 0" description="今日暂无待就诊患者" />
            <div v-else class="apt-list">
              <div v-for="item in todayList" :key="item.id" class="apt-item">
                <div class="apt-time">
                  <span class="dot"></span>
                  <span>{{ periodLabel(item.schedule_start_time || item.appointment_time) }} {{ toTimeStr(item.schedule_start_time || item.appointment_time) }}-{{ toTimeStr(item.schedule_end_time || item.appointment_time) }}</span>
                </div>
                <div class="apt-info">
                  <div class="apt-name">{{ item.patient_name }}</div>
                  <div class="apt-booked" v-if="item.appointment_time">
                    📅 预约于 {{ formatAppointmentTime(item.appointment_time) }}
                  </div>
                  <div class="apt-meta">#{{ item.id }} <el-tag size="small" type="warning">待就诊</el-tag></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="panel">
          <div class="panel-title">我的排班</div>
          <div v-loading="schLoading" class="panel-body">
            <el-result v-if="schError" icon="error" title="加载失败">
              <template #extra>
                <el-button type="primary" size="small" @click="fetchScheduleDays">重试</el-button>
              </template>
            </el-result>
            <el-empty v-else-if="!schLoading && scheduleDays.length === 0" description="本周暂无排班" />
            <div v-else class="schedule-table-wrap">
              <table class="schedule-table">
                <thead>
                  <tr>
                    <th class="period-th"></th>
                    <th
                      v-for="(hdr, hi) in weekDayHeaders"
                      :key="hi"
                      :class="{ 'is-today': hdr.isToday }"
                    >
                      <div>{{ hdr.weekday }}</div>
                      <div class="day-date">{{ hdr.date }}</div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in scheduleTable" :key="ri">
                    <td class="period-td">{{ periodNames[ri] }}</td>
                    <td
                      v-for="(cell, ci) in row"
                      :key="ci"
                      :class="{ 'is-today': weekDayHeaders[ci].isToday, 'is-empty': cell.isEmpty }"
                    >
                      <template v-if="!cell.isEmpty">
                        <div class="cell-label">{{ cell.label }}</div>
                        <div class="cell-max">限{{ cell.maxPatients }}人</div>
                      </template>
                      <template v-else>
                        <span class="cell-rest">休</span>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { appointmentsApi, doctorSchedulesApi, systemConfigApi, parseScheduleConfig, type SchedulePeriods } from '@medflow/shared'
import type { Appointment, DoctorSchedule } from '@medflow/shared'

const todayList = ref<Appointment[]>([])
const scheduleDays = ref<ScheduleDay[]>([])
const aptLoading = ref(true)
const schLoading = ref(true)
const stats = reactive({ todayPending: 0, weekScheduleDays: 0, monthCompleted: 0 })
const cardsLoading = ref(false)
const aptError = ref(false)
const schError = ref(false)
const schedulePeriods = ref<SchedulePeriods>(parseScheduleConfig())

// ---- 日期工具 ----
function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function monthStartStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

/** 获取本周一~周日的日期范围，与管理端排班周保持一致 */
function getWeekRange(): { from: string; to: string } {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - day + (day === 0 ? -6 : 1))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  const fmt = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { from: fmt(monday), to: fmt(sunday) }
}

const weekNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

/** 将 "HH:MM" 转为分钟数 */
function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

/** 从 schedule_start_time(HH:MM) 或 appointment_time(ISO) 中提取 HH:MM */
function toTimeStr(value: string | null): string {
  if (!value) return '--:--'
  if (value.includes('T')) return value.split('T')[1]?.slice(0, 5) || '--:--'
  return value.length >= 5 ? value.slice(0, 5) : '--:--'
}

/** 根据时间字符串(HH:MM 或 ISO)和系统时段配置判断时段 */
function periodLabel(startTime: string | null): string {
  if (!startTime) return ''
  const timeStr = toTimeStr(startTime)
  if (timeStr === '--:--') return ''
  const total = timeToMinutes(timeStr)
  const p = schedulePeriods.value
  if (total < timeToMinutes(p.afternoon.start)) return '上午'
  if (total < timeToMinutes(p.evening.start)) return '下午'
  if (total < 24 * 60) return '晚上'
  return ''
}

/** 格式化预约时间为 "M月D日 HH:MM" */
function formatAppointmentTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

interface ScheduleDay {
  key: string
  label: string
  isToday: boolean
  slots: DoctorSchedule[]
}

interface ScheduleTableCell {
  label: string       // "上午✓" 或 "09:00-11:00"
  maxPatients: number
  isEmpty: boolean
}

/** 行标签：从配置中提取"上午"/"下午"/"晚上" */
const periodNames = computed(() =>
  schedulePeriods.value.all.map(p => p.label.split(' ')[0])
)

/** 表头：周X + M/D 两行，匹配管理员排班表格式 */
interface DayHeader {
  weekday: string   // "周一"
  date: string      // "7/11"
  isToday: boolean
}

const weekDayHeaders = computed<DayHeader[]>(() =>
  scheduleDays.value.map(day => {
    const d = new Date(day.key + 'T00:00:00')
    return {
      weekday: weekNames[d.getDay()],
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      isToday: day.isToday,
    }
  })
)

const scheduleTable = computed<ScheduleTableCell[][]>(() => {
  const all = schedulePeriods.value.all
  return all.map((period, ri) => {
    const periodStart = timeToMinutes(period.start)
    // 上界用下一时段开始（最后一档用 24:00），确保时段间隙中的排班也能归入
    const upperBound = ri < all.length - 1
      ? timeToMinutes(all[ri + 1].start)
      : 24 * 60
    return scheduleDays.value.map(day => {
      const match = day.slots.find(s => {
        const startMin = timeToMinutes(s.start_time.slice(0, 5))
        return startMin >= periodStart && startMin < upperBound
      })
      if (match) {
        const start = match.start_time.slice(0, 5)
        const end = match.end_time.slice(0, 5)
        const isExact = start === period.start && end === period.end
        const label = isExact
          ? `${periodNames.value[ri]}✓`
          : `${start}-${end}`
        return { label, maxPatients: match.max_patients, isEmpty: false }
      }
      return { label: '', maxPatients: 0, isEmpty: true }
    })
  })
})

async function fetchTodayList() {
  aptLoading.value = true
  aptError.value = false
  try {
    const res = await appointmentsApi.listAppointments({ status: 1 })
    todayList.value = res.data.sort((a, b) =>
      (a.schedule_start_time || '').localeCompare(b.schedule_start_time || '')
    )
    stats.todayPending = todayList.value.length
  } catch {
    aptError.value = true
  } finally {
    aptLoading.value = false
  }
}

async function fetchScheduleDays() {
  const { from, to } = getWeekRange()
  const today = todayStr()
  schLoading.value = true
  schError.value = false
  try {
    const res = await doctorSchedulesApi.listSchedules({ work_date_from: from, work_date_to: to })
    const schList = res.data as DoctorSchedule[]
    const dayMap = new Map<string, DoctorSchedule[]>()
    for (const s of schList) {
      if (!dayMap.has(s.work_date)) dayMap.set(s.work_date, [])
      dayMap.get(s.work_date)!.push(s)
    }
    let weekDays = 0
    const days: ScheduleDay[] = []
    const startDate = new Date(new Date(from).getFullYear(), new Date(from).getMonth(), new Date(from).getDate())
    for (let i = 0; i < 7; i++) {
      const d = new Date(startDate)
      d.setDate(startDate.getDate() + i)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      const slots = (dayMap.get(key) || []).sort((a, b) => a.start_time.localeCompare(b.start_time))
      if (slots.length > 0) weekDays++
      days.push({
        key,
        label: `${weekNames[d.getDay()]} ${d.getMonth() + 1}月${d.getDate()}日`,
        isToday: key === today,
        slots,
      })
    }
    scheduleDays.value = days
    stats.weekScheduleDays = weekDays
  } catch {
    schError.value = true
  } finally {
    schLoading.value = false
  }
}

async function fetchSchedulePeriods() {
  try {
    const res = await systemConfigApi.getByKey('default_doctor_schedule')
    schedulePeriods.value = parseScheduleConfig(res.data.config_value)
  } catch { /* 使用默认时段 */ }
}

async function fetchMonthCompleted() {
  try {
    const res = await appointmentsApi.listAppointments({
      start_date: monthStartStr(),
      end_date: todayStr(),
    })
    stats.monthCompleted = (res.data as Appointment[]).filter(a => a.status === 2).length
  } catch { /* ignore */ }
}

onMounted(async () => {
  cardsLoading.value = true
  try {
    await fetchSchedulePeriods()
    await fetchTodayList()
    await fetchScheduleDays()
    await fetchMonthCompleted()
  } finally {
    cardsLoading.value = false
  }
})
</script>

<style scoped>
.stats-row {
  display: flex;
  gap: 16px;
}
.stat-card {
  flex: 1;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}
.stat-num {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  height: 100%;
}
.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  padding: 14px 16px;
  border-bottom: 1px solid #ebeef5;
  background: #fafafa;
}
.panel-body {
  padding: 12px 16px;
  min-height: 300px;
}

/* 待就诊列表 */
.apt-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.apt-item:last-child { border-bottom: none; }
.apt-time {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 60px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e6a23c;
  flex-shrink: 0;
}
.apt-info { flex: 1; }
.apt-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.apt-booked {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
.apt-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
.apt-meta .el-tag { margin-left: 6px; }

/* 排班表格 */
.schedule-table-wrap {
  overflow-x: auto;
}

.schedule-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.schedule-table th,
.schedule-table td {
  text-align: center;
  padding: 8px 4px;
  border: 1px solid #ebeef5;
}

.schedule-table th {
  background: #fafafa;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.schedule-table th.is-today,
.schedule-table td.is-today {
  background: #f0f9eb;
}

.period-th,
.period-td {
  font-weight: 600;
  color: #606266;
  background: #fafafa;
  white-space: nowrap;
  min-width: 36px;
}

.day-date {
  font-size: 11px;
  font-weight: 400;
  color: #909399;
  margin-top: 2px;
}

.cell-label {
  color: #303133;
  font-weight: 500;
  line-height: 1.5;
}

.cell-max {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.cell-rest {
  color: #c0c4cc;
}

.is-empty {
  color: #c0c4cc;
}
</style>
