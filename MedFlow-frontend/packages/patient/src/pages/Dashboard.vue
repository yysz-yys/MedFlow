<template>
  <div class="dashboard">
    <!-- 快捷入口 -->
    <div class="quick-actions">
      <div class="action-card" @click="$router.push('/patient/book')">
        <div class="action-icon">📅</div>
        <div class="action-label">预约挂号</div>
        <div class="action-sub">去预约</div>
      </div>
      <div class="action-card" @click="$router.push('/patient/my-appointments')">
        <div class="action-icon">📋</div>
        <div class="action-label">我的挂号</div>
        <div class="action-sub">{{ upcomingCount }}个待就诊</div>
      </div>
      <div class="action-card" @click="$router.push('/patient/diagnosis')">
        <div class="action-icon">🩺</div>
        <div class="action-label">我的诊断</div>
        <div class="action-sub">{{ diagnosisCount }}条记录</div>
      </div>
      <div class="action-card" @click="$router.push('/patient/orders')">
        <div class="action-icon">📦</div>
        <div class="action-label">我的订单</div>
        <div class="action-sub">查看详情</div>
      </div>
    </div>

    <!-- 信息摘要 -->
    <el-row :gutter="20" class="info-row">
      <el-col :span="12">
        <el-card header="近期待就诊" shadow="hover">
          <div v-if="upcomingAppointments.length === 0" class="empty-hint">暂无待就诊</div>
          <div v-for="item in upcomingAppointments" :key="item.id" class="info-item">
            <div class="info-item__title">
              <span class="info-item__icon">👨‍⚕️</span>
              {{ item.doctor_name }} · {{ item.department_name || '-' }}
            </div>
            <div class="info-item__meta">
              <span>📅 {{ formatDate(item.appointment_time) }}</span>
              <template v-if="item.schedule_start_time">
                <span>🕐 {{ item.schedule_start_time }}-{{ item.schedule_end_time }}</span>
              </template>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="最近诊断" shadow="hover">
          <div v-if="recentDiagnoses.length === 0" class="empty-hint">暂无诊断记录</div>
          <div v-for="item in recentDiagnoses" :key="item.id" class="info-item">
            <div class="info-item__title">
              <span class="info-item__icon">🩺</span>
              {{ item.chief_complaint || '暂无主诉' }}
            </div>
            <div class="info-item__meta">
              <span style="margin-right:12px">📋 {{ item.diagnosis_result || '暂无诊断结果' }}</span>
              <span class="info-item__doctor">👨‍⚕️ {{ item.doctor_name }} · {{ formatDateTime(item.created_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { appointmentsApi, diagnosisRecordsApi, drugOrdersApi } from '@medflow/shared'
import type { Appointment, DiagnosisRecord } from '@medflow/shared'

const allAppointments = ref<Appointment[]>([])
const allDiagnoses = ref<DiagnosisRecord[]>([])
const pendingOrderCount = ref(0)

const upcomingCount = computed(() =>
  allAppointments.value.filter(a => a.status === 1).length
)

const upcomingAppointments = computed(() =>
  allAppointments.value
    .filter(a => a.status === 1)
    .sort((a, b) => (a.appointment_time || '').localeCompare(b.appointment_time || ''))
    .slice(0, 2)
)

const diagnosisCount = computed(() => allDiagnoses.value.length)

const recentDiagnoses = computed(() =>
  allDiagnoses.value.slice(0, 2)
)

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const [, m, d] = iso.slice(0, 10).split('-')
  return `${Number(m)}月${Number(d)}日`
}

function formatDateTime(iso: string | null): string {
  if (!iso) return '-'
  const [, m, d] = iso.slice(0, 10).split('-')
  const time = iso.slice(11, 16)
  return `${Number(m)}月${Number(d)}日 ${time}`
}

onMounted(async () => {
  try {
    const [appointments, diagnoses, orders] = await Promise.all([
      appointmentsApi.listAppointments(),
      diagnosisRecordsApi.listDiagnosisRecords(),
      drugOrdersApi.listDrugOrders(),
    ])
    allAppointments.value = appointments.data
    allDiagnoses.value = diagnoses.data
    pendingOrderCount.value = orders.data.filter((o: any) => o.status === 1).length
  } catch { /* ignore */ }
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.quick-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.action-card {
  flex: 1;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.action-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.action-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.action-label {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.action-sub {
  font-size: 12px;
  color: #909399;
}

.info-row {
  margin: 0 !important;
}

.empty-hint {
  text-align: center;
  color: #c0c4cc;
  padding: 24px 0;
  font-size: 14px;
}

.info-item {
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}
.info-item:last-child {
  border-bottom: none;
}

.info-item__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-item__icon {
  font-size: 16px;
  flex-shrink: 0;
}

.info-item__meta {
  font-size: 13px;
  color: #909399;
  display: flex;
  gap: 16px;
}

.info-item__doctor {
  color: #606266;
}
</style>
