<template>
  <div class="schedule-grid-wrapper">
    <table class="schedule-grid">
      <thead>
        <tr>
          <th class="col-doctor"></th>
          <th v-for="d in weekDates" :key="d" :class="['col-day', { 'col-today': isToday(d) }]">
            {{ dayLabel(d) }}
          </th>
          <th class="col-template">模板</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="doc in doctors" :key="doc.id">
          <td class="col-doctor">{{ doc.name }}</td>
          <td
            v-for="date in weekDates"
            :key="`${doc.id}_${date}`"
            :class="cellClass(doc.id, date)"
            @mousedown.prevent="$emit('cellMouseDown', doc.id, date)"
            @mouseenter="$emit('cellMouseEnter', doc.id, date)"
            @mouseup="$emit('cellMouseUp')"
            @click="$emit('cellClick', doc.id, date)"
          >
            <div class="cell-inner">
              <template v-if="getCellSchedules(doc.id, date).length > 0">
                <el-tag
                  v-for="s in getCellSchedules(doc.id, date)"
                  :key="s.id"
                  :type="s.status === 1 ? 'success' : 'danger'"
                  size="small"
                  class="cell-tag"
                >
                  {{ slotLabel(s) }}
                </el-tag>
              </template>
            </div>
          </td>
          <td class="col-template" @click.stop="$emit('templateClick', doc.id)">
            <span :style="{ color: doctorTemplates[doc.id] ? '#409eff' : '#c0c4cc', cursor: 'pointer', fontSize: '16px' }">⚙</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="doctors.length === 0" class="grid-empty">
      该科室暂无医生
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Doctor, DoctorSchedule, SchedulePeriods } from '@medflow/shared'
import { formatDate } from '@/utils/week'

const DAY_NAMES = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const props = defineProps<{
  doctors: Doctor[]
  weekDates: string[]
  schedules: DoctorSchedule[]
  selectedCells: Array<{ doctorId: number; date: string }>
  doctorTemplates: Record<number, boolean>
  periods: SchedulePeriods
}>()

defineEmits<{
  cellClick: [doctorId: number, date: string]
  cellMouseDown: [doctorId: number, date: string]
  cellMouseEnter: [doctorId: number, date: string]
  cellMouseUp: []
  templateClick: [doctorId: number]
}>()

/** 按医生ID+日期为key缓存排班 */
const scheduleMap = computed(() => {
  const map: Record<string, DoctorSchedule[]> = {}
  for (const s of props.schedules) {
    const key = `${s.doctor_id}_${s.work_date}`
    if (!map[key]) map[key] = []
    map[key].push(s)
  }
  return map
})

function getCellSchedules(doctorId: number, date: string): DoctorSchedule[] {
  return scheduleMap.value[`${doctorId}_${date}`] ?? []
}

function dayLabel(dateStr: string): string {
  const d = new Date(dateStr)
  const m = d.getMonth() + 1
  const day = d.getDate()
  const w = d.getDay()
  return `${DAY_NAMES[w]} ${m}/${day}`
}

function isToday(dateStr: string): boolean {
  return dateStr === formatDate(new Date())
}

function slotLabel(s: DoctorSchedule): string {
  const start = s.start_time.substring(0, 5)
  const end = s.end_time.substring(0, 5)
  const p = props.periods
  if (start === p.morning.start && end === p.morning.end) return '上午✓'
  if (start === p.afternoon.start && end === p.afternoon.end) return '下午✓'
  if (start === p.evening.start && end === p.evening.end) return '晚上✓'
  return `${start}-${end}`
}

function cellClass(doctorId: number, date: string) {
  const selected = props.selectedCells.some(c => c.doctorId === doctorId && c.date === date)
  const hasSchedule = getCellSchedules(doctorId, date).length > 0
  return {
    'grid-cell': true,
    'cell-selected': selected,
    'cell-has-schedule': hasSchedule,
    'cell-today': isToday(date),
  }
}
</script>

<style scoped>
.schedule-grid-wrapper {
  flex: 1;
  overflow: auto;
}
.schedule-grid {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.schedule-grid th,
.schedule-grid td {
  border: 1px solid #e4e7ed;
  padding: 6px 4px;
  font-size: 13px;
  text-align: center;
  vertical-align: middle;
}
.schedule-grid th {
  background: #f5f7fa;
  font-weight: 500;
  color: #606266;
}
.col-doctor {
  width: 80px;
  min-width: 80px;
}
.col-day {
  width: calc((100% - 80px - 44px) / 7);
}
.col-today {
  background: #ecf5ff !important;
  color: #409eff;
  font-weight: 600;
}
.col-template {
  width: 44px;
  min-width: 44px;
}
.grid-cell {
  min-height: 56px;
  cursor: pointer;
  transition: background 0.15s;
  vertical-align: middle;
}
.grid-cell:hover {
  background: #ecf5ff;
}
.cell-selected {
  background: #d9ecff !important;
}
.cell-has-schedule {
  background: #f0f9eb;
}
.cell-today {
  background: #ecf5ff;
}
.cell-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 48px;
}
.cell-tag {
  margin: 2px 1px;
}
.grid-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 40px 0;
  font-size: 14px;
}
</style>
