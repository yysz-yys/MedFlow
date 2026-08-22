<template>
  <div class="page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索患者姓名"
        clearable
        :prefix-icon="Search"
        style="width: 240px"
      />
      <el-select
        v-model="statusFilter"
        placeholder="状态"
        clearable
        style="width: 100px"
        @change="fetchData"
      >
        <el-option label="待就诊" :value="1" />
        <el-option label="已完成" :value="2" />
      </el-select>
      <span class="status-count">{{ statusText }}</span>
    </div>

    <!-- 卡片网格 -->
    <div v-loading="loading" class="card-grid">
      <el-empty v-if="!loading && sortedList.length === 0" :description="emptyText" />
      <div
        v-for="item in sortedList"
        :key="item.id"
        class="appointment-card"
        :class="{ 'is-today': isToday(item.appointment_time) }"
      >
        <div class="card-date">{{ formatDate(item.appointment_time) }}</div>
        <div class="card-patient">{{ item.patient_name }}</div>
        <div class="card-schedule">
          <template v-if="item.schedule_start_time && item.schedule_end_time">
            {{ item.schedule_start_time }} ~ {{ item.schedule_end_time }}
          </template>
          <template v-else>-</template>
        </div>
        <div class="card-time">挂号: {{ formatTime(item.appointment_time) }}</div>
        <div class="card-status">
          <el-tag :type="statusTagType(item.status)" size="small">{{ statusLabel(item.status) }}</el-tag>
        </div>
        <div class="card-action">
          <el-button
            size="small"
            type="primary"
            @click.stop="openDiagnosis(item)"
          >诊断</el-button>
          <el-button
            v-if="item.status === 1"
            size="small"
            type="success"
            @click.stop="doComplete(item)"
          >完成</el-button>
          <el-button
            v-if="item.status === 2"
            size="small"
            @click.stop="doUncomplete(item)"
          >撤销</el-button>
        </div>
      </div>
    </div>
    <!-- 诊断弹窗 -->
    <el-dialog
      v-model="diagVisible"
      :title="diagEditing ? `编辑诊断 · ${diagPatientName}` : `新增诊断 · ${diagPatientName}`"
      width="860px"
    >
      <el-form label-width="80px">
        <el-form-item label="挂号时间">
          <el-input :model-value="diagAppointmentTime" disabled />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <div class="col-title">诊断信息</div>

            <el-form-item label="主诉">
              <el-input v-model="diagForm.chief_complaint" type="textarea" :rows="3" placeholder="患者主诉" />
            </el-form-item>
            <el-form-item label="诊断结果">
              <el-input v-model="diagForm.diagnosis_result" type="textarea" :rows="4" placeholder="诊断结果" />
            </el-form-item>
            <el-form-item label="处方建议">
              <el-input v-model="diagForm.prescription_advice" type="textarea" :rows="3" placeholder="处方建议" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <div class="col-title">处方用药</div>

            <div style="margin-bottom:8px">
              <el-button size="small" type="primary" @click="addRxItem">+ 添加药品</el-button>
            </div>
            <div class="rx-scroll">
              <div
                v-for="(item, idx) in rxItems"
                :key="idx"
                style="border:1px solid #ebeef5;border-radius:4px;padding:8px 10px;margin-bottom:8px"
              >
                <el-row :gutter="6" align="middle" style="margin-bottom:6px">
                  <el-col :span="4" style="font-size:13px;color:#606266;line-height:24px">药品</el-col>
                  <el-col :span="16">
                    <el-select
                      v-model="item.drug_id"
                      placeholder="选择药品"
                      clearable
                      style="width:100%"
                      size="small"
                      @change="onDrugSelect(idx)"
                    >
                      <el-option
                        v-for="d in drugList"
                        :key="d.id"
                        :label="`${d.name} · ${d.specification || '-'} · ${d.unit || '-'} (库存:${d.stock})`"
                        :value="d.id"
                      />
                    </el-select>
                  </el-col>
                  <el-col :span="4" style="text-align:right">
                    <el-button size="small" type="danger" @click="removeRxItem(idx)" :disabled="rxItems.length === 1" text>删除</el-button>
                  </el-col>
                </el-row>
                <el-row :gutter="6" align="middle" style="margin-bottom:6px">
                  <el-col :span="4" style="font-size:13px;color:#606266;line-height:24px">数量</el-col>
                  <el-col :span="20">
                    <el-input-number v-model="item.quantity" :min="1" :max="drugMaxStock(idx)" size="small" style="width:100%" />
                  </el-col>
                </el-row>
                <el-row :gutter="6" align="middle" style="margin-bottom:6px">
                  <el-col :span="4" style="font-size:13px;color:#606266;line-height:24px">天数</el-col>
                  <el-col :span="20">
                    <el-input-number v-model="item.days" :min="1" size="small" style="width:100%" />
                  </el-col>
                </el-row>
                <el-row :gutter="6" align="middle">
                  <el-col :span="4" style="font-size:13px;color:#606266;line-height:24px">用法</el-col>
                  <el-col :span="20">
                    <el-input v-model="item.usage_method" placeholder="限100字" maxlength="100" size="small" />
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="diagVisible = false">取消</el-button>
        <el-button type="primary" :loading="diagSubmitting" @click="handleDiagSubmit">
          {{ diagEditing ? '保存修改' : '提交诊断并开处方' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appointmentsApi, diagnosisRecordsApi, drugsApi, prescriptionsApi } from '@medflow/shared'
import type { Appointment, DiagnosisRecord, Drug, Prescription } from '@medflow/shared'

const list = ref<Appointment[]>([])
const loading = ref(true)
const keyword = ref('')
const statusFilter = ref<number | undefined>(undefined)

// ===== 诊断弹窗 =====
const diagVisible = ref(false)
const diagEditing = ref(false)  // true=编辑已有, false=新增
const diagSubmitting = ref(false)
const diagAppointmentId = ref<number | null>(null)
const diagPatientName = ref('')
const diagAppointmentTime = ref('')
const diagForm = reactive({
  id: null as number | null,
  chief_complaint: '',
  diagnosis_result: '',
  prescription_advice: '',
})

// ===== 处方用药 =====
const drugList = ref<Drug[]>([])
interface RxItem {
  drug_id: number | null
  quantity: number
  days: number
  usage_method: string
}
const rxItems = ref<RxItem[]>([{ drug_id: null, quantity: 1, days: 1, usage_method: '' }])
const existingPrescriptionId = ref<number | null>(null)

// ===== 日期工具 =====
function parseDate(dateStr: string): Date {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d)
}

const weekNames = ['日', '一', '二', '三', '四', '五', '六']

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const d = parseDate(iso.slice(0, 10))
  return `${d.getMonth() + 1}月${d.getDate()}日 周${weekNames[d.getDay()]}`
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  return iso.slice(11, 16)
}

function isToday(iso: string | null): boolean {
  if (!iso) return false
  const today = new Date()
  const date = parseDate(iso.slice(0, 10))
  return date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
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

// ===== 过滤 & 排序 =====
const filteredList = computed(() => {
  // 排除已取消
  let items = list.value.filter(a => a.status !== 0)
  // 按患者姓名搜索
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    items = items.filter(a => a.patient_name.toLowerCase().includes(kw))
  }
  return items
})

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

    if (isFutureA && !isFutureB) return -1
    if (!isFutureA && isFutureB) return 1

    if (isFutureA && isFutureB) {
      if (tsA !== tsB) return tsA - tsB
    } else {
      if (tsA !== tsB) return tsB - tsA
    }

    const ta = a.schedule_start_time || '99:99'
    const tb = b.schedule_start_time || '99:99'
    return ta.localeCompare(tb)
  })

  return sorted
})

// ===== 状态文字 =====
const statusText = computed(() => {
  const count = sortedList.value.length
  if (statusFilter.value === 1) return `待就诊 ${count}`
  if (statusFilter.value === 2) return `已完成 ${count}`
  return `全部 ${count}`
})

const emptyText = computed(() => {
  if (keyword.value) return '未找到匹配的患者'
  if (statusFilter.value === 1) return '暂无待就诊病人'
  if (statusFilter.value === 2) return '暂无已完成挂号'
  return '暂无挂号记录'
})

// ===== 数据加载 =====
async function fetchData() {
  loading.value = true
  try {
    const res = await appointmentsApi.listAppointments({ status: statusFilter.value })
    list.value = res.data
  } finally {
    loading.value = false
  }
}

// ===== 操作 =====
async function doComplete(item: Appointment) {
  try {
    await ElMessageBox.confirm(`确定标记患者「${item.patient_name}」就诊完成吗？`)
    await appointmentsApi.completeAppointment(item.id)
    item.status = 2
    ElMessage.success('就诊已完成')
  } catch { /* 取消 */ }
}

async function doUncomplete(item: Appointment) {
  try {
    await ElMessageBox.confirm(`确定撤销「${item.patient_name}」的就诊完成状态吗？`)
    await appointmentsApi.uncompleteAppointment(item.id)
    item.status = 1
    ElMessage.success('已撤销')
  } catch { /* 取消 */ }
}

// ===== 诊断操作 =====
function resetRxItems() {
  rxItems.value = [{ drug_id: null, quantity: 1, days: 1, usage_method: '' }]
  existingPrescriptionId.value = null
}

function addRxItem() {
  rxItems.value.push({ drug_id: null, quantity: 1, days: 1, usage_method: '' })
}

function removeRxItem(idx: number) {
  if (rxItems.value.length > 1) rxItems.value.splice(idx, 1)
}

function drugMaxStock(idx: number): number {
  const item = rxItems.value[idx]
  if (!item.drug_id) return 9999
  const drug = drugList.value.find(d => d.id === item.drug_id)
  return drug ? drug.stock : 9999
}

function onDrugSelect(idx: number) {
  const item = rxItems.value[idx]
  const drug = drugList.value.find(d => d.id === item.drug_id)
  if (drug && item.quantity > drug.stock) {
    item.quantity = drug.stock
  }
}

function openNewDiag(item: Appointment) {
  diagAppointmentId.value = item.id
  diagPatientName.value = item.patient_name
  diagAppointmentTime.value = item.appointment_time?.replace('T', ' ').slice(0, 16) || '-'
  diagEditing.value = false
  diagForm.id = null
  diagForm.chief_complaint = ''
  diagForm.diagnosis_result = ''
  diagForm.prescription_advice = ''
  resetRxItems()
  diagVisible.value = true
}

async function openDiagnosis(item: Appointment) {
  // 加载药品列表
  if (drugList.value.length === 0) {
    try {
      const res = await drugsApi.listDrugs({ page_size: 999, status: 0 })
      drugList.value = res.data.items
    } catch { /* ignore */ }
  }

  // 查询是否已有诊断记录
  try {
    const res = await diagnosisRecordsApi.listDiagnosisRecords()
    const records = (res.data as DiagnosisRecord[]).filter(
      r => r.appointment_id === item.id
    )
    if (records.length > 0) {
      // 编辑已有诊断
      diagAppointmentId.value = item.id
      diagPatientName.value = item.patient_name
      diagAppointmentTime.value = item.appointment_time?.replace('T', ' ').slice(0, 16) || '-'
      diagEditing.value = true
      diagForm.id = records[0].id
      diagForm.chief_complaint = records[0].chief_complaint || ''
      diagForm.diagnosis_result = records[0].diagnosis_result || ''
      diagForm.prescription_advice = records[0].prescription_advice || ''

      // 查询是否已有处方
      try {
        const rxRes = await prescriptionsApi.listPrescriptions()
        const rxList = (rxRes.data as Prescription[]).filter(
          p => p.diagnosis_id === records[0].id
        )
        if (rxList.length > 0) {
          existingPrescriptionId.value = rxList[0].id
          rxItems.value = rxList[0].items.map(i => ({
            drug_id: i.drug_id,
            quantity: i.quantity,
            days: i.days || 1,
            usage_method: i.usage_method || '',
          }))
        } else {
          resetRxItems()
        }
      } catch {
        resetRxItems()
      }
      diagVisible.value = true
    } else {
      openNewDiag(item)
    }
  } catch {
    openNewDiag(item)
  }
}

async function handleDiagSubmit() {
  diagSubmitting.value = true
  try {
    // 1. 保存诊断
    let diagnosisId: number | null = null
    if (diagEditing.value && diagForm.id) {
      await diagnosisRecordsApi.updateDiagnosisRecord(diagForm.id, {
        chief_complaint: diagForm.chief_complaint || undefined,
        diagnosis_result: diagForm.diagnosis_result || undefined,
        prescription_advice: diagForm.prescription_advice || undefined,
      })
      diagnosisId = diagForm.id
    } else {
      const diagRes = await diagnosisRecordsApi.createDiagnosisRecord({
        appointment_id: diagAppointmentId.value!,
        chief_complaint: diagForm.chief_complaint || undefined,
        diagnosis_result: diagForm.diagnosis_result || undefined,
        prescription_advice: diagForm.prescription_advice || undefined,
      })
      diagnosisId = (diagRes.data as any).id
    }

    // 2. 处方（仅填了药品才操作）
    const filled = rxItems.value.filter(i => i.drug_id)
    if (filled.length > 0 && diagnosisId) {
      if (existingPrescriptionId.value) {
        await prescriptionsApi.updatePrescription(existingPrescriptionId.value, filled.map(i => ({
          drug_id: i.drug_id!,
          quantity: i.quantity,
          usage_method: i.usage_method || undefined,
          days: i.days || undefined,
        })))
      } else {
        await prescriptionsApi.createPrescription({
          diagnosis_id: diagnosisId,
          items: filled.map(i => ({
            drug_id: i.drug_id!,
            quantity: i.quantity,
            usage_method: i.usage_method || undefined,
            days: i.days || undefined,
          })),
        })
      }
    }

    ElMessage.success(diagEditing.value ? '已保存' : '诊断及处方已提交')
    diagVisible.value = false
    fetchData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    diagSubmitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.search-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-count {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
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
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
  box-shadow: 0 0 0 1px #67c23a inset;
}

.card-date {
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}

.card-patient {
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
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.col-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.rx-scroll {
  max-height: 340px;
  overflow-y: auto;
}
</style>
