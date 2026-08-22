<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:13px;color:#606266">日志记录</span>
        <el-switch v-model="auditOn" @change="handleToggle" />
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <el-select v-model="query.role" placeholder="角色" clearable style="width:100px" @change="search">
          <el-option label="管理员" :value="0" />
          <el-option label="医生" :value="1" />
          <el-option label="病人" :value="2" />
        </el-select>
        <el-date-picker v-model="query.date_from" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width:140px" />
        <el-date-picker v-model="query.date_to" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width:140px" />
        <el-input v-model="query.keyword" placeholder="搜索操作/IP" clearable style="width:180px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="user_name" label="操作人" width="100" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">{{ row.role === 0 ? '管理员' : row.role === 1 ? '医生' : '病人' }}</template>
      </el-table-column>
      <el-table-column prop="action" label="操作" width="150" sortable="custom" />
      <el-table-column prop="target_type" label="目标类型" width="120" />
      <el-table-column prop="target_id" label="目标ID" width="80" />
      <el-table-column prop="detail" label="详情" />
      <el-table-column prop="ip_address" label="IP" width="140" />
      <el-table-column prop="created_at" label="时间" width="170" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="query.page"
      v-model:page-size="query.page_size"
      :total="total"
      :page-sizes="[10, 20, 50]"
      background
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="fetchData"
      @size-change="fetchData"
      style="margin-top:20px;justify-content:flex-end"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { auditLogsApi, formatDateTime } from '@medflow/shared'
import { ElMessage } from 'element-plus'
import type { AuditLog } from '@medflow/shared'

const auditOn = ref(true)
const list = ref<AuditLog[]>([])
const total = ref(0)
const loading = ref(false)
const sortBy = ref('')
const sortOrder = ref('')
const query = reactive({
  role: undefined as number | undefined,
  keyword: '',
  date_from: undefined as string | undefined,
  date_to: undefined as string | undefined,
  page: 1,
  page_size: 10,
})

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await auditLogsApi.listAuditLogs({
      role: query.role,
      keyword: query.keyword || undefined,
      date_from: query.date_from,
      date_to: query.date_to,
      page: query.page,
      page_size: query.page_size,
      sort_by: sortBy.value || undefined,
      sort_order: sortOrder.value || undefined,
    })
    list.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function search() {
  query.page = 1
  fetchData()
}

async function loadStatus() {
  try {
    const res = await auditLogsApi.getAuditStatus()
    auditOn.value = res.data.enabled
  } catch { /* ignore */ }
}

async function handleToggle() {
  try {
    const res = await auditLogsApi.toggleAudit()
    auditOn.value = res.data.enabled
    ElMessage.success(res.data.enabled ? '日志记录已开启' : '日志记录已关闭')
  } catch { /* ignore */ }
}

onMounted(async () => {
  await loadStatus()
  fetchData()
})
</script>

<style scoped>
:deep(.el-table__body-wrapper .el-table__cell .cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
