<template>
  <div class="page">
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="patient_name" label="病人" />
      <el-table-column prop="total_amount" label="金额(元)" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 2 ? 'success' : row.status === 0 ? 'danger' : 'warning'">
            {{ row.status === 0 ? '已取消' : row.status === 1 ? '待取药' : '已取药' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { drugOrdersApi } from '@medflow/shared'
import type { DrugOrder } from '@medflow/shared'

const list = ref<DrugOrder[]>([])
const loading = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const res = await drugOrdersApi.listDrugOrders()
    list.value = res.data
  } finally { loading.value = false }
}

onMounted(fetchData)
</script>
