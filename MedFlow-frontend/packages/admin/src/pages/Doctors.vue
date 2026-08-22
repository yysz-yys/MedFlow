<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openDialog()">新增</el-button>
      <div style="display:flex;align-items:center;gap:12px">
        <el-select v-model="departmentId" placeholder="科室" clearable style="width:140px" @change="search">
          <el-option v-for="d in deptList" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-input v-model="keyword" placeholder="姓名/职称" clearable style="width:180px" @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="name" label="姓名" width="80" sortable="custom" />
      <el-table-column prop="department_name" label="科室" width="100" sortable="custom" />
      <el-table-column prop="title" label="职称" width="100" sortable="custom" />
      <el-table-column prop="introduction" label="简介" />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑医生' : '新增医生'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item v-if="!editingId" label="邮箱" required>
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="密码" required>
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item v-if="!editingId" label="确认密码" required>
          <el-input v-model="form.confirmPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="科室">
          <el-select v-model="form.department_id" placeholder="选择科室" style="width:100%">
            <el-option v-for="d in deptList" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="form.title" placeholder="如：主任医师" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.introduction" type="textarea" />
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
import { doctorsApi, departmentsApi, formatDateTime } from '@medflow/shared'
import type { Doctor, Department } from '@medflow/shared'

const list = ref<Doctor[]>([])
const deptList = ref<Department[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const departmentId = ref<number | undefined>(undefined)
const sortBy = ref('')
const sortOrder = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  email: '', password: '', confirmPassword: '', name: '', department_id: null as number | null, title: '', introduction: '',
})

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const [doctors, depts] = await Promise.all([
      doctorsApi.listDoctors({ page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined, department_id: departmentId.value, sort_by: sortBy.value || undefined, sort_order: sortOrder.value || undefined }),
      departmentsApi.listDepartments({ page_size: 999 }),
    ])
    list.value = doctors.data.items
    total.value = doctors.data.total
    deptList.value = depts.data.items
  } finally { loading.value = false }
}

function search() {
  page.value = 1
  fetchData()
}

function openDialog(row?: Doctor) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.department_id = row.department_id
    form.title = row.title || ''
    form.introduction = row.introduction || ''
  } else {
    editingId.value = null
    form.email = ''; form.password = ''; form.confirmPassword = ''; form.name = ''; form.department_id = null
    form.title = ''; form.introduction = ''
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name) { ElMessage.warning('请输入姓名'); return }
  try {
    if (editingId.value) {
      await doctorsApi.updateDoctor(editingId.value, {
        name: form.name, department_id: form.department_id!, title: form.title, introduction: form.introduction,
      })
    } else {
      if (!form.email || !form.password || !form.name || !form.department_id) { ElMessage.warning('请填写完整信息'); return }
      if (form.password !== form.confirmPassword) { ElMessage.warning('两次密码输入不一致'); return }
      await doctorsApi.createDoctor({
        email: form.email, password: form.password, name: form.name,
        department_id: form.department_id, title: form.title, introduction: form.introduction,
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleDelete(row: Doctor) {
  try {
    await ElMessageBox.confirm(`确定要删除医生「${row.name}」吗？`)
    await doctorsApi.deleteDoctor(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleRestore(row: Doctor) {
  try {
    await doctorsApi.restoreDoctor(row.id)
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
