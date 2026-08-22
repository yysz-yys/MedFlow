<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openDialog()">新增药品</el-button>
      <div style="display:flex;align-items:center;gap:8px">
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width:100px" @change="search">
          <el-option label="正常" :value="0" />
          <el-option label="已删除" :value="1" />
        </el-select>
        <el-select v-model="unitFilter" placeholder="单位" clearable style="width:100px" @change="search">
          <el-option v-for="u in unitOptions" :key="u" :label="u" :value="u" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索名称/生产商" clearable style="width:200px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="70" sortable="custom" />
      <el-table-column prop="name" label="名称" width="160" sortable="custom" />
      <el-table-column prop="specification" label="规格" width="100" />
      <el-table-column prop="manufacturer" label="生产商" />
      <el-table-column prop="unit" label="单位" width="60" />
      <el-table-column prop="price" label="单价(元)" width="110" sortable="custom" />
      <el-table-column prop="stock" label="库存" width="80" sortable="custom" />
      <el-table-column prop="deleted_at" label="状态" width="80" sortable="custom">
        <template #default="{ row }">
          <el-tag :type="row.deleted_at ? 'danger' : 'success'">{{ row.deleted_at ? '删除' : '正常' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" :type="row.deleted_at ? 'success' : 'danger'" @click="row.deleted_at ? handleRestore(row) : handleDelete(row)">
            {{ row.deleted_at ? '恢复' : '删除' }}
          </el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑药品' : '新增药品'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" placeholder="如：0.25g*24片" />
        </el-form-item>
        <el-form-item label="生产商">
          <el-input v-model="form.manufacturer" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="如：盒、瓶" />
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="form.stock" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 调整库存弹窗 -->
    <el-dialog v-model="stockDialogVisible" title="调整库存" width="400px">
      <p style="margin-bottom:12px">当前库存：<strong>{{ currentStock }}</strong></p>
      <el-form :model="stockForm" label-width="80px">
        <el-form-item label="变化量">
          <el-input-number v-model="stockForm.change" placeholder="正数增加，负数减少" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveStock">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { drugsApi, formatDateTime } from '@medflow/shared'
import type { Drug } from '@medflow/shared'

const list = ref<Drug[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref<number | undefined>(undefined)
const unitFilter = ref('')
const unitOptions = ['盒', '瓶', '袋', '支', '片', '粒', '包', '板', '箱', '瓶/盒']
const sortBy = ref('')
const sortOrder = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '', specification: '', manufacturer: '', unit: '', price: 0, stock: 0,
})
const stockDialogVisible = ref(false)
const currentStock = ref(0)
const stockDrugId = ref<number | null>(null)
const stockForm = reactive({ change: 0 })

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await drugsApi.listDrugs({
      page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined,
      status: statusFilter.value, unit: unitFilter.value || undefined,
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

function openDialog(row?: Drug) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.specification = row.specification || ''
    form.manufacturer = row.manufacturer || ''
    form.unit = row.unit || ''
    form.price = row.price
    form.stock = row.stock
  } else {
    editingId.value = null
    form.name = ''; form.specification = ''; form.manufacturer = ''
    form.unit = ''; form.price = 0; form.stock = 0
  }
  dialogVisible.value = true
}

function handleAdjustStock(row: Drug) {
  stockDrugId.value = row.id
  currentStock.value = row.stock
  stockForm.change = 0
  stockDialogVisible.value = true
}

async function handleSave() {
  if (!form.name) { ElMessage.warning('请输入药品名称'); return }
  try {
    if (editingId.value) {
      await drugsApi.updateDrug(editingId.value, {
        name: form.name, specification: form.specification, manufacturer: form.manufacturer,
        unit: form.unit, price: form.price, stock: form.stock,
      })
    } else {
      await drugsApi.createDrug(form as any)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleSaveStock() {
  if (stockForm.change === 0) { ElMessage.warning('请输入变化量'); return }
  try {
    await drugsApi.adjustStock(stockDrugId.value!, stockForm.change)
    ElMessage.success('库存已调整')
    stockDialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '调整失败') }
}

async function handleDelete(row: Drug) {
  try {
    await ElMessageBox.confirm(`确定要删除药品「${row.name}」吗？`)
    await drugsApi.deleteDrug(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleRestore(row: Drug) {
  try {
    await drugsApi.restoreDrug(row.id)
    ElMessage.success('已恢复')
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '恢复失败') }
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
