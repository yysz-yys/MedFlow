<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openDialog()">新增配置</el-button>
      <div style="display:flex;align-items:center;gap:8px">
        <el-input v-model="keyword" placeholder="搜索键/描述" clearable style="width:220px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="config_key" label="键" width="270" sortable="custom" />
      <el-table-column prop="config_value" label="值" />
      <el-table-column prop="description" label="描述" width="200" />
      <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      background
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="fetchData"
      @size-change="fetchData"
      style="margin-top:20px;justify-content:flex-end"
    />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑配置' : '新增配置'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="键" required>
          <el-input v-model="form.config_key" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="form.config_value" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemConfigApi, formatDateTime } from '@medflow/shared'
import type { SystemConfig } from '@medflow/shared'

const list = ref<SystemConfig[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const sortBy = ref('')
const sortOrder = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ config_key: '', config_value: '', description: '' })

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await systemConfigApi.listSystemConfig({
      page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined,
      sort_by: sortBy.value || undefined, sort_order: sortOrder.value || undefined,
    })
    list.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function search() {
  page.value = 1
  fetchData()
}

function openDialog(row?: SystemConfig) {
  if (row) {
    editingId.value = row.id
    form.config_key = row.config_key
    form.config_value = row.config_value
    form.description = row.description || ''
  } else {
    editingId.value = null
    form.config_key = ''
    form.config_value = ''
    form.description = ''
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.config_key || !form.config_value) { ElMessage.warning('请填写键和值'); return }
  try {
    if (editingId.value) {
      await systemConfigApi.updateSystemConfig(editingId.value, {
        config_value: form.config_value, description: form.description,
      })
    } else {
      await systemConfigApi.createSystemConfig(form)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleDelete(row: SystemConfig) {
  try {
    await ElMessageBox.confirm(`确定要删除配置「${row.config_key}」吗？`)
    await systemConfigApi.deleteSystemConfig(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* 取消 */ }
}

onMounted(fetchData)
</script>

<style scoped>
:deep(.el-table__body-wrapper .el-table__cell .cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
