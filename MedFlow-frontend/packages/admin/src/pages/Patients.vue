<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openCreateDialog()">新增</el-button>
      <div style="display:flex;align-items:center;gap:12px">
        <el-select v-model="queryForm.gender" placeholder="性别" clearable style="width:120px" @change="search">
          <el-option label="未知" :value="0" />
          <el-option label="男" :value="1" />
          <el-option label="女" :value="2" />
        </el-select>
        <el-select v-model="queryForm.bloodType" placeholder="血型" clearable style="width:120px" @change="search">
          <el-option label="未知" value="" />
          <el-option label="A型" value="A" />
          <el-option label="B型" value="B" />
          <el-option label="AB型" value="AB" />
          <el-option label="O型" value="O" />
        </el-select>
        <el-input v-model="keyword" placeholder="姓名/地址" clearable style="width:180px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="name" label="姓名" width="80" sortable="custom" />
      <el-table-column prop="gender" label="性别" width="90" sortable="custom">
        <template #default="{ row }">{{ row.gender === 1 ? '男' : row.gender === 2 ? '女' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="birth_date" label="出生日期" width="120" sortable="custom" />
      <el-table-column prop="address" label="地址" />
      <el-table-column prop="blood_type" label="血型" width="80" sortable="custom" />
      <el-table-column prop="allergy_history" label="过敏史" />
      <el-table-column prop="deleted_at" label="状态" width="80" sortable="custom">
        <template #default="{ row }">
          <el-tag :type="row.deleted_at ? 'danger' : 'success'">{{ row.deleted_at ? '删除' : '正常' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button v-if="!row.deleted_at" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          <el-button v-else size="small" type="success" @click="handleRestore(row)">恢复</el-button>
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

    <el-dialog v-model="createVisible" title="新增病人" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="邮箱" required>
          <el-input v-model="createForm.email" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="createForm.confirmPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="createForm.gender" placeholder="请选择" style="width:100%">
            <el-option label="未知" :value="0" />
            <el-option label="男" :value="1" />
            <el-option label="女" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="血型">
          <el-select v-model="createForm.blood_type" clearable style="width:100%">
            <el-option label="A型" value="A" />
            <el-option label="B型" value="B" />
            <el-option label="AB型" value="AB" />
            <el-option label="O型" value="O" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="createForm.birth_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="createForm.address" type="textarea" />
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input v-model="createForm.allergy_history" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" title="编辑病人" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名">
          <el-input v-model="form.name" disabled />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" style="width:100%">
            <el-option label="未知" :value="0" />
            <el-option label="男" :value="1" />
            <el-option label="女" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birth_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" type="textarea" />
        </el-form-item>
        <el-form-item label="血型">
          <el-select v-model="form.blood_type" clearable style="width:100%">
            <el-option label="A型" value="A" />
            <el-option label="B型" value="B" />
            <el-option label="AB型" value="AB" />
            <el-option label="O型" value="O" />
          </el-select>
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input v-model="form.allergy_history" type="textarea" />
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
import { patientsApi, formatDateTime } from '@medflow/shared'
import type { Patient } from '@medflow/shared'

const list = ref<Patient[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const queryForm = reactive<{ gender: number | undefined; bloodType: string | undefined }>({ gender: undefined, bloodType: undefined })
const sortBy = ref('')
const sortOrder = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '', gender: 0, birth_date: '', address: '', blood_type: '', allergy_history: '',
})
const createVisible = ref(false)
const createForm = reactive({
  email: '', password: '', confirmPassword: '', name: '', gender: null as number | null, birth_date: '', address: '', blood_type: '', allergy_history: '',
})

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await patientsApi.listPatients({
      page: page.value, page_size: pageSize.value,
      keyword: keyword.value || undefined,
      gender: queryForm.gender,
      blood_type: queryForm.bloodType,
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

function openDialog(row: Patient) {
  editingId.value = row.id
  form.name = row.name
  form.gender = row.gender
  form.birth_date = row.birth_date || ''
  form.address = row.address || ''
  form.blood_type = row.blood_type || ''
  form.allergy_history = row.allergy_history || ''
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await patientsApi.updatePatient(editingId.value!, {
      gender: form.gender,
      birth_date: form.birth_date || null,
      address: form.address || null,
      blood_type: form.blood_type || null,
      allergy_history: form.allergy_history || null,
    })
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleDelete(row: Patient) {
  try {
    await ElMessageBox.confirm(`确定要删除病人「${row.name}」吗？`)
    await patientsApi.deletePatient(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleRestore(row: Patient) {
  try {
    await patientsApi.restorePatient(row.id)
    ElMessage.success('已恢复')
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '恢复失败') }
}

function openCreateDialog() {
  createForm.email = ''; createForm.password = ''; createForm.confirmPassword = ''; createForm.name = ''
  createForm.gender = null; createForm.birth_date = ''; createForm.address = ''
  createForm.blood_type = ''; createForm.allergy_history = ''
  createVisible.value = true
}

async function handleCreate() {
  if (!createForm.email || !createForm.password || !createForm.name) {
    ElMessage.warning('请填写邮箱、密码和姓名')
    return
  }
  if (createForm.password !== createForm.confirmPassword) {
    ElMessage.warning('两次密码输入不一致')
    return
  }
  try {
    await patientsApi.createPatient({
      email: createForm.email,
      password: createForm.password,
      name: createForm.name,
      gender: createForm.gender ?? undefined,
      birth_date: createForm.birth_date || undefined,
      address: createForm.address || undefined,
      blood_type: createForm.blood_type || undefined,
      allergy_history: createForm.allergy_history || undefined,
    })
    ElMessage.success('创建成功')
    createVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '创建失败') }
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
