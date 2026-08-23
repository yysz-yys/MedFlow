<template>
  <div class="page">
    <el-form :inline="true" :model="query">
      <el-form-item label="开始日期">
        <el-date-picker v-model="query.work_date_from" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item label="结束日期">
        <el-date-picker v-model="query.work_date_to" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">搜索</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="work_date" label="日期" width="120" />
      <el-table-column label="时段" width="170">
        <template #default="{ row }">
          <el-tag :type="periodTagType(row)" size="small">{{ periodLabel(row) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="120">
        <template #default="{ row }">
          {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="max_patients" label="最大挂号数" width="100" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">
            {{ row.status === 1 ? '可预约' : '停诊' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { doctorSchedulesApi, parseScheduleConfig } from '@medflow/shared'
import type { DoctorSchedule } from '@medflow/shared'

const list = ref<DoctorSchedule[]>([])
const loading = ref(false)
const periods = parseScheduleConfig()

/** 获取本周一~周日的日期范围 */
function getThisWeek(): { start: string; end: string } {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - day + (day === 0 ? -6 : 1))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  const fmt = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { start: fmt(monday), end: fmt(sunday) }
}

const query = reactive({
  work_date_from: getThisWeek().start as string | undefined,
  work_date_to: getThisWeek().end as string | undefined,
})

async function fetchData() {
  loading.value = true
  try {
    // 不传 doctor_id，由后端根据当前登录用户自动解析为正确的 doctor.id
    const res = await doctorSchedulesApi.listSchedules({
      work_date_from: query.work_date_from,
      work_date_to: query.work_date_to,
    })
    list.value = res.data
  } finally { loading.value = false }
}

function resetQuery() {
  const w = getThisWeek()
  query.work_date_from = w.start
  query.work_date_to = w.end
  fetchData()
}

function formatTime(t: string): string {
  return t ? t.substring(0, 5) : ''
}

function periodLabel(row: DoctorSchedule): string {
  const start = formatTime(row.start_time)
  const end = formatTime(row.end_time)
  const p = periods
  if (start === p.morning.start && end === p.morning.end) return '上午'
  if (start === p.afternoon.start && end === p.afternoon.end) return '下午'
  if (start === p.evening.start && end === p.evening.end) return '晚上'
  return '自定义'
}

function periodTagType(row: DoctorSchedule): string {
  const start = formatTime(row.start_time)
  const end = formatTime(row.end_time)
  const p = periods
  if (start === p.morning.start && end === p.morning.end) return 'warning'
  if (start === p.afternoon.start && end === p.afternoon.end) return ''
  if (start === p.evening.start && end === p.evening.end) return 'info'
  return ''
}

onMounted(fetchData)
</script>
