<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openDialog()">新增字典项</el-button>
      <div style="display:flex;align-items:center;gap:8px">
        <el-select v-model="typeFilter" placeholder="字典类型" clearable style="width:140px" @change="search">
          <el-option v-for="t in dictTypes" :key="t" :label="t" :value="t" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索标签/类型" clearable style="width:200px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="dict_type" label="字典类型" width="200" sortable="custom" />
      <el-table-column prop="dict_key" label="键" width="60" />
      <el-table-column prop="dict_label" label="标签" />
      <el-table-column prop="sort_order" label="排序" width="80" sortable="custom" />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑字典项' : '新增字典项'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="字典类型">
          <el-input v-model="form.dict_type" :disabled="!!editingId" placeholder="如：gender、blood_type" />
        </el-form-item>
        <el-form-item label="键">
          <el-input-number v-model="form.dict_key" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.dict_label" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" style="width:100%" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dataDictApi } from '@medflow/shared'
import type { DataDict } from '@medflow/shared'

const list = ref<DataDict[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const typeFilter = ref('')
const sortBy = ref('')
const sortOrder = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ dict_type: '', dict_key: 0, dict_label: '', sort_order: 0 })

const dictTypes = computed(() => {
  const types = new Set(list.value.map(item => item.dict_type))
  return Array.from(types)
})

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await dataDictApi.listDataDict({
      type: typeFilter.value || undefined,
      keyword: keyword.value || undefined,
      page: page.value, page_size: pageSize.value,
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

function openDialog(row?: DataDict) {
  if (row) {
    editingId.value = row.id
    form.dict_type = row.dict_type
    form.dict_key = row.dict_key
    form.dict_label = row.dict_label
    form.sort_order = row.sort_order
  } else {
    editingId.value = null
    form.dict_type = ''
    form.dict_key = 0
    form.dict_label = ''
    form.sort_order = 0
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.dict_type || !form.dict_label) { ElMessage.warning('请填写字典类型和标签'); return }
  try {
    if (editingId.value) {
      await dataDictApi.updateDataDict(editingId.value, {
        dict_label: form.dict_label, sort_order: form.sort_order,
      })
    } else {
      await dataDictApi.createDataDict(form)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleDelete(row: DataDict) {
  try {
    await ElMessageBox.confirm('确定要删除该字典项吗？')
    await dataDictApi.deleteDataDict(row.id)
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
