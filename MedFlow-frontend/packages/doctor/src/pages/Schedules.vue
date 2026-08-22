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
      <el-table-column prop="start_time" label="开始时间" width="100" />
      <el-table-column prop="end_time" label="结束时间" width="100" />
      <el-table-column prop="max_patients" label="最大挂号数" width="110" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">
            {{ row.status === 1 ? '正常' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore, doctorSchedulesApi } from '@medflow/shared'
import type { DoctorSchedule } from '@medflow/shared'

const authStore = useAuthStore()
const list = ref<DoctorSchedule[]>([])
const loading = ref(false)
const query = reactive({
  work_date_from: undefined as string | undefined,
  work_date_to: undefined as string | undefined,
})

async function fetchData() {
  loading.value = true
  try {
    const res = await doctorSchedulesApi.listSchedules({
      doctor_id: authStore.user?.id,
      work_date_from: query.work_date_from,
      work_date_to: query.work_date_to,
    })
    list.value = res.data
  } finally { loading.value = false }
}

function resetQuery() {
  query.work_date_from = undefined
  query.work_date_to = undefined
  fetchData()
}

onMounted(fetchData)
</script>
