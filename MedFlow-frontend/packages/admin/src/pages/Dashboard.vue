<template>
  <div class="dashboard">
    <!-- ===== 统计卡片行 ===== -->
    <el-row :gutter="12" v-loading="cardsLoading" class="stat-row">
      <el-col :span="4" v-for="card in statCards" :key="card.label">
        <el-card
          shadow="hover"
          :body-style="{ padding: '16px 12px', cursor: card.link ? 'pointer' : 'default', textAlign: 'center' }"
          @click="card.link && $router.push(card.link)"
        >
          <div class="stat-value" :style="card.warning && card.value > 0 ? 'color:#f56c6c' : ''">
            {{ card.value }}
          </div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ===== 图表行 ===== -->
    <el-row :gutter="12">
      <el-col :span="12">
        <el-card header="近7天挂号趋势">
          <div ref="trendChartRef" class="chart-box"></div>
          <div v-if="!trendData.length" class="chart-empty">暂无数据</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="今日科室挂号">
          <div ref="deptChartRef" class="chart-box"></div>
          <div v-if="!deptData.length" class="chart-empty">暂无数据</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ===== 最新动态 ===== -->
    <el-card header="最新动态" body-style="padding: 0 20px 8px">
      <div v-if="activities.length === 0" class="chart-empty chart-empty-sm">暂无动态</div>
      <div v-else>
        <div
          v-for="(item, i) in activities"
          :key="i"
          :class="['activity-item', { 'activity-warn': item.type === 'warn' }]"
        >
          <span class="activity-content">
            <el-tag v-if="item.type === 'warn'" type="danger" size="small">预警</el-tag>
            <el-tag v-else-if="item.type === 'register'" type="primary" size="small">挂号</el-tag>
            <el-tag v-else type="success" size="small">就诊</el-tag>
            <span class="activity-text">{{ item.text }}</span>
          </span>
          <span class="activity-time">{{ item.time }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  appointmentsApi, doctorSchedulesApi, drugsApi, drugOrdersApi, getToken,
} from '@medflow/shared'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// ===== 统计卡片 =====
const cardsLoading = ref(false)

interface StatCard {
  label: string
  value: number
  link?: string
  warning?: boolean
}

const statCards = ref<StatCard[]>([
  { label: '今日挂号', value: 0, link: '/admin/schedules' },
  { label: '已就诊', value: 0, link: '/admin/schedules' },
  { label: '待就诊', value: 0, link: '/admin/schedules' },
  { label: '今日收入', value: 0, link: '/admin/orders' },
  { label: '在岗医生', value: 0, link: '/admin/schedules' },
  { label: '库存预警', value: 0, link: '/admin/drugs', warning: true },
])

async function fetchCards() {
  cardsLoading.value = true
  const today = new Date().toISOString().slice(0, 10)
  try {
    const [appts1, appts2, schedules, lowStock, orders] = await Promise.all([
      appointmentsApi.listAppointments({ status: 1, date: today }),
      appointmentsApi.listAppointments({ status: 2, date: today }),
      doctorSchedulesApi.listSchedules({ date: today }),
      drugsApi.listDrugs({ stock_lte: 20, page_size: 1 }),
      drugOrdersApi.listDrugOrders({ date: today }),
    ])
    const todayTotal = appts1.data.length + appts2.data.length
    statCards.value = [
      { label: '今日挂号', value: todayTotal, link: '/admin/schedules' },
      { label: '已就诊', value: appts2.data.length, link: '/admin/schedules' },
      { label: '待就诊', value: appts1.data.length, link: '/admin/schedules' },
      {
        label: '今日收入',
        value: orders.data
          .filter((o: any) => o.status !== 0)
          .reduce((sum: number, o: any) => sum + (Number(o.total_amount) || 0), 0),
        link: '/admin/orders',
      },
      {
        label: '在岗医生',
        value: new Set(schedules.data.map((s: any) => s.doctor_id)).size,
        link: '/admin/schedules',
      },
      {
        label: '库存预警',
        value: lowStock.data.total,
        link: '/admin/drugs',
        warning: true,
      },
    ]
  } catch { /* 静默降级，卡片保持 0 */ }
  finally { cardsLoading.value = false }
}

// ===== 图表 =====
const trendChartRef = ref<HTMLDivElement>()
const deptChartRef = ref<HTMLDivElement>()
let trendChart: echarts.ECharts | null = null
let deptChart: echarts.ECharts | null = null
let trendObserver: ResizeObserver | null = null
let deptObserver: ResizeObserver | null = null

const trendData = ref<{ date: string; count: number }[]>([])
const deptData = ref<{ department_name: string; count: number }[]>([])

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  trendObserver = new ResizeObserver(() => trendChart?.resize())
  trendObserver.observe(trendChartRef.value)
}

function initDeptChart() {
  if (!deptChartRef.value) return
  deptChart = echarts.init(deptChartRef.value)
  deptObserver = new ResizeObserver(() => deptChart?.resize())
  deptObserver.observe(deptChartRef.value)
}

async function fetchCharts() {
  const today = new Date().toISOString().slice(0, 10)
  try {
    const token = getToken()
    const headers: Record<string, string> = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const [trendRes, deptRes] = await Promise.all([
      fetch(`${API_BASE}/appointments/stats/daily?days=7`, { headers }),
      fetch(`${API_BASE}/appointments/stats/by-dept?date=${today}`, { headers }),
    ])
    if (trendRes.ok) trendData.value = await trendRes.json()
    if (deptRes.ok) deptData.value = await deptRes.json()
  } catch { /* 静默降级 */ }

  await nextTick()
  if (trendData.value.length) {
    if (!trendChart) initTrendChart()
    trendChart?.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trendData.value.map(d => d.date.slice(5)) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        type: 'line', data: trendData.value.map(d => d.count),
        smooth: true, lineStyle: { color: '#409eff' },
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.1)' },
      }],
      grid: { left: 45, right: 20, top: 15, bottom: 25 },
    })
  }
  if (deptData.value.length) {
    if (!deptChart) initDeptChart()
    const top10 = deptData.value.slice(0, 10)
    const otherCount = deptData.value.slice(10).reduce((s, d) => s + d.count, 0)
    const names = top10.map(d => d.department_name)
    const values = top10.map(d => d.count)
    if (otherCount > 0) { names.push('其他'); values.push(otherCount) }
    deptChart?.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: {
        type: 'category', data: names, inverse: true,
        axisLabel: { width: 70, overflow: 'truncate' },
      },
      series: [{
        type: 'bar', data: values, barMaxWidth: 14,
        itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] },
      }],
      grid: { left: 80, right: 30, top: 15, bottom: 25 },
    })
  }
}

// ===== 最新动态 =====
interface Activity {
  type: 'warn' | 'register' | 'complete'
  text: string
  time: string
}

const activities = ref<Activity[]>([])

async function fetchActivities() {
  const warnItems: Activity[] = []
  const flowItems: Activity[] = []

  try {
    const lowStockRes = await drugsApi.listDrugs({ stock_lte: 20, page_size: 5 })
    for (const d of lowStockRes.data.items) {
      warnItems.push({
        type: 'warn',
        text: `${d.name} 库存不足（仅剩 ${d.stock} ${d.unit || '个'}）`,
        time: d.updated_at ? d.updated_at.replace('T', ' ').slice(0, 16) : '',
      })
    }
  } catch { /* ignore */ }

  try {
    const appts = await appointmentsApi.listAppointments()
    for (const a of appts.data) {
      flowItems.push({
        type: a.status === 2 ? 'complete' : 'register',
        text: `${a.patient_name} ${a.status === 2 ? '完成就诊' : '挂号'} ${a.department_name || ''} · ${a.doctor_name}`,
        time: a.created_at ? a.created_at.replace('T', ' ').slice(0, 16) : '',
      })
    }
  } catch { /* ignore */ }

  activities.value = [...warnItems, ...flowItems].slice(0, 8)
}

// ===== 生命周期 =====
let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchCards()
  fetchCharts()
  fetchActivities()
  refreshTimer = setInterval(() => {
    fetchCards()
    fetchCharts()
    fetchActivities()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  trendObserver?.disconnect()
  deptObserver?.disconnect()
  trendChart?.dispose()
  deptChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row {
  margin-bottom: 0 !important;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.chart-box {
  height: 220px;
}

.chart-empty {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 14px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}
.activity-item:last-child {
  border-bottom: none;
}
.activity-warn {
  background: #fef0f0;
  margin: 0 -20px;
  padding: 6px 20px;
}
.activity-content {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  gap: 8px;
  font-size: 13px;
}
.activity-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.activity-time {
  flex-shrink: 0;
  margin-left: 16px;
  color: #c0c4cc;
  font-size: 12px;
}
</style>
