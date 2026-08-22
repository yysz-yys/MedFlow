<template>
  <div class="page">
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索姓名/手机号"
        clearable
        :prefix-icon="Search"
        style="width: 260px"
        @input="onSearchInput"
        @keyup.enter="search"
      />
      <el-select
        v-model="genderFilter"
        placeholder="性别"
        clearable
        style="width: 100px"
        @change="search"
      >
        <el-option label="男" :value="1" />
        <el-option label="女" :value="2" />
      </el-select>
    </div>

    <div v-loading="loading" class="card-grid">
      <el-empty v-if="!loading && list.length === 0" :description="emptyText" />
      <div
        v-for="item in list"
        :key="item.id"
        class="patient-card"
        @click="openDetail(item)"
      >
        <div class="card-avatar">
          <img v-if="item.avatar" :src="avatarUrl(item.avatar)" class="avatar-img" />
          <span v-else class="avatar-text">{{ (item.name || '?')[0] }}</span>
        </div>
        <div class="card-name">{{ item.name }} · {{ item.gender === 1 ? '男' : item.gender === 2 ? '女' : '-' }}</div>
        <div class="card-phone">{{ item.phone || '-' }}</div>
      </div>
    </div>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :total="total"
      :page-size="pageSize"
      background
      layout="total, prev, pager, next"
      @current-change="fetchData"
      style="margin-top:20px;justify-content:flex-end"
    />

    <el-dialog v-model="dialogVisible" :title="`${currentPatient?.name} · 病人详情`" width="560px" center>
      <div v-if="currentPatient" class="dialog-content">
        <div class="info-section">
          <div class="info-row"><span class="info-label">出生日期</span><span>{{ currentPatient.birth_date || '-' }}</span></div>
          <div class="info-row"><span class="info-label">地址</span><span>{{ currentPatient.address || '-' }}</span></div>
          <div class="info-row"><span class="info-label">血型</span><span>{{ currentPatient.blood_type || '-' }}</span></div>
          <div class="info-row"><span class="info-label">过敏史</span><span>{{ currentPatient.allergy_history || '-' }}</span></div>
        </div>

        <div class="section-title">── 诊断记录 ──</div>

        <el-table
          v-if="currentPatient.diagnosis_records.length"
          :data="currentPatient.diagnosis_records"
          border
          stripe
          size="small"
        >
          <el-table-column prop="created_at" label="诊断时间" width="180">
            <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 19) || '-' }}</template>
          </el-table-column>
          <el-table-column prop="chief_complaint" label="主诉" />
          <el-table-column prop="diagnosis_result" label="诊断结果" />
        </el-table>
        <el-empty v-else description="暂无诊断记录" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { patientsApi } from '@medflow/shared'
import type { DoctorPatient } from '@medflow/shared'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function avatarUrl(path: string): string {
  return API_BASE.replace('/api/v1', '') + '/uploads/' + path
}

const list = ref<DoctorPatient[]>([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const genderFilter = ref<number | undefined>(undefined)
const dialogVisible = ref(false)
const currentPatient = ref<DoctorPatient | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => search(), 300)
}

function search() {
  page.value = 1
  fetchData()
}

const emptyText = computed(() => {
  if (keyword.value) return '未找到匹配的患者'
  return '暂无病人记录'
})

async function fetchData() {
  loading.value = true
  try {
    const res = await patientsApi.listMyPatients({
      keyword: keyword.value || undefined,
      gender: genderFilter.value,
      page: page.value,
      page_size: pageSize,
    })
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function openDetail(patient: DoctorPatient) {
  currentPatient.value = patient
  dialogVisible.value = true
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

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.patient-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px 16px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  aspect-ratio: 1 / 1;
}

.patient-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: #f0a0b0;
  color: #fff;
}
.avatar-text {
  font-size: 28px;
  font-weight: 600;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  text-align: center;
}

.card-phone {
  font-size: 13px;
  color: #909399;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  max-width: 360px;
}

.info-row {
  display: flex;
  justify-content: center;
  gap: 12px;
  font-size: 14px;
  color: #303133;
}

.info-label {
  color: #909399;
}

.section-title {
  margin: 24px 0 12px;
  font-size: 14px;
  color: #909399;
  text-align: center;
}
</style>
