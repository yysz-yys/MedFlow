<template>
  <div class="page">
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索医生、科室、主诉、诊断结果"
        clearable
        :prefix-icon="Search"
        style="width:320px"
        @input="page = 1"
      />
    </div>

    <el-table :data="pagedList" border stripe v-loading="loading" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="doctor_name" label="医生" width="100" />
      <el-table-column prop="department_name" label="科室" width="140" />
      <el-table-column prop="chief_complaint" label="主诉" />
      <el-table-column prop="diagnosis_result" label="诊断结果" />
      <el-table-column prop="created_at" label="诊断时间" width="180" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :total="total"
      :page-size="pageSize"
      background
      layout="total, prev, pager, next"
      style="margin-top:20px;justify-content:flex-end"
    />

    <el-dialog v-model="dialogVisible" :title="''" width="700px" top="8vh">
      <div class="diagnosis-report">
        <div class="report-title">诊断详情</div>
        <div class="report-info-grid">
          <div class="info-item">
            <span class="info-label">姓名：</span>
            <span class="info-value">{{ detail.patient_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">医生：</span>
            <span class="info-value">{{ detail.doctor_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">科室：</span>
            <span class="info-value">{{ detail.department_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">日期：</span>
            <span class="info-value">{{ formatDate(detail.created_at) || '-' }}</span>
          </div>
        </div>
        <div class="report-section">
          <div class="section-label">主诉</div>
          <div class="section-content">{{ detail.chief_complaint || '-' }}</div>
        </div>
        <div class="report-section">
          <div class="section-label">诊断结果</div>
          <div class="section-content">{{ detail.diagnosis_result || '-' }}</div>
        </div>
        <div class="report-section">
          <div class="section-label">医嘱</div>
          <div class="section-content">{{ detail.prescription_advice || '-' }}</div>
        </div>
        <div v-if="detailItems.length > 0" class="report-section">
          <div class="section-label">处方明细</div>
          <el-table :data="detailItems" border stripe size="small">
            <el-table-column prop="drug_name" label="药品名称" />
            <el-table-column prop="specification" label="规格" width="100" />
            <el-table-column prop="unit" label="单位" width="60" />
            <el-table-column prop="quantity" label="数量" width="60" />
            <el-table-column prop="days" label="天数" width="60">
              <template #default="{ row }">{{ row.days ?? '-' }}</template>
            </el-table-column>
            <el-table-column prop="usage_method" label="用法">
              <template #default="{ row }">{{ row.usage_method || '-' }}</template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { diagnosisRecordsApi, prescriptionsApi, formatDateTime } from '@medflow/shared'
import type { DiagnosisRecord, PrescriptionItem } from '@medflow/shared'

const allList = ref<DiagnosisRecord[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = 10
const sortBy = ref('')
const sortOrder = ref('')

const filteredList = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return allList.value
  return allList.value.filter(r =>
    (r.doctor_name || '').toLowerCase().includes(kw) ||
    (r.department_name || '').toLowerCase().includes(kw) ||
    (r.chief_complaint || '').toLowerCase().includes(kw) ||
    (r.diagnosis_result || '').toLowerCase().includes(kw)
  )
})

const sortedList = computed(() => {
  const result = [...filteredList.value]
  if (!sortBy.value) return result
  result.sort((a: any, b: any) => {
    const va = a[sortBy.value]
    const vb = b[sortBy.value]
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    if (typeof va === 'string') {
      return sortOrder.value === 'desc' ? vb.localeCompare(va) : va.localeCompare(vb)
    }
    return sortOrder.value === 'desc' ? vb - va : va - vb
  })
  return result
})

const total = computed(() => sortedList.value.length)

const pagedList = computed(() => {
  const start = (page.value - 1) * pageSize
  return sortedList.value.slice(start, start + pageSize)
})

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
}
const detail = reactive({
  patient_name: '',
  doctor_name: '',
  department_name: '',
  created_at: '',
  chief_complaint: '',
  diagnosis_result: '',
  prescription_advice: '',
})
const detailItems = ref<PrescriptionItem[]>([])

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function fetchData() {
  loading.value = true
  try {
    const res = await diagnosisRecordsApi.listDiagnosisRecords()
    allList.value = res.data
  } finally { loading.value = false }
}

async function openDetail(row: DiagnosisRecord) {
  detail.patient_name = row.patient_name || ''
  detail.doctor_name = row.doctor_name || ''
  detail.department_name = row.department_name || ''
  detail.created_at = row.created_at || ''
  detail.chief_complaint = row.chief_complaint || ''
  detail.diagnosis_result = row.diagnosis_result || ''
  detail.prescription_advice = row.prescription_advice || ''
  dialogVisible.value = true
  try {
    const res = await prescriptionsApi.listPrescriptions()
    const items = res.data.flatMap(p => p.diagnosis_id === row.id ? (p.items || []) : [])
    detailItems.value = items
  } catch { detailItems.value = [] }
}

onMounted(fetchData)
</script>

<style scoped>
.search-bar {
  margin-bottom: 16px;
}

.diagnosis-report {
  padding: 20px;
}

.report-title {
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e4e7ed;
}

.report-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  min-width: 60px;
}

.info-value {
  font-size: 14px;
  color: #303133;
}

.report-section {
  margin-bottom: 20px;
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #ebeef5;
}

.section-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  padding: 8px 0;
  min-height: 40px;
  white-space: pre-wrap;
}
</style>
