<template>
  <div class="page">
    <!-- 搜索栏 -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="openCreateDialog">新增</el-button>
      <div style="display:flex;align-items:center;gap:12px">
        <el-select v-model="query.role" placeholder="角色" clearable style="width:120px" @change="fetchData">
          <el-option label="管理员" :value="0" />
          <el-option label="医生" :value="1" />
          <el-option label="病人" :value="2" />
        </el-select>
        <el-select v-model="query.status" placeholder="状态" clearable style="width:120px" @change="fetchData">
          <el-option label="正常" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <el-input v-model="query.keyword" placeholder="姓名/邮箱" clearable style="width:180px" @keyup.enter="fetchData" />
        <el-button type="primary" @click="fetchData">搜索</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="list" border stripe v-loading="loading" :row-style="{ height: '44px' }" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="name" label="姓名" width="100" sortable="custom" />
      <el-table-column prop="email" label="邮箱" width="200" sortable="custom" />
      <el-table-column prop="phone" label="手机号" width="150" sortable="custom" align="center">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column prop="role" label="角色" sortable="custom">
        <template #default="{ row }">
          {{ row.role === 0 ? '管理员' : row.role === 1 ? '医生' : '病人' }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" sortable="custom">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">
            {{ row.status === 1 ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" :disabled="row.id === currentUserId" @click="toggleStatus(row)" :type="row.status === 1 ? 'danger' : 'success'">
            {{ row.status === 1 ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" @click="openResetDialog(row)">重置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="query.page"
      v-model:page-size="query.page_size"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      background
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="fetchData"
      @size-change="fetchData"
      style="margin-top:20px;justify-content:flex-end"
    />

    <el-dialog v-model="createVisible" title="新增用户" width="450px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="邮箱" prop="email" required>
          <el-input v-model="createForm.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" required>
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" required>
          <el-input v-model="createForm.confirmPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="name" required>
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-input value="管理员" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑用户" width="450px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="姓名" prop="name" required>
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width:100%" :disabled="editingUserId === currentUserId">
            <el-option label="管理员" :value="0" />
            <el-option label="医生" :value="1" />
            <el-option label="病人" :value="2" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置" width="450px">
      <el-tabs v-model="resetTab" @tab-change="onResetTabChange">
        <el-tab-pane label="更改邮箱" name="email">
          <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="80px">
            <el-form-item label="当前邮箱">
              <el-input :model-value="resetForm.oldEmail" disabled />
            </el-form-item>
            <el-form-item label="新邮箱" prop="newEmail" required>
              <el-input v-model="resetForm.newEmail" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="重置密码" name="password">
          <el-form :model="resetForm" label-width="80px">
            <el-form-item label="新密码" required>
              <el-input v-model="resetForm.newPassword" type="password" show-password />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReset">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi, formatDateTime, useAuthStore } from '@medflow/shared'
import type { UserListItem } from '@medflow/shared'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

const list = ref<UserListItem[]>([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ role: undefined as number | undefined, status: undefined as number | undefined, keyword: '', page: 1, page_size: 10 })
const sortBy = ref('')
const sortOrder = ref('')
const createVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({ email: '', password: '', confirmPassword: '', name: '', phone: '' })
const createRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}
const editVisible = ref(false)
const editFormRef = ref()
const editingUserId = ref<number | null>(null)
const editForm = reactive({ name: '', phone: '', role: 2 })
const editRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}
const resetVisible = ref(false)
const resetFormRef = ref()
const resetUserId = ref<number | null>(null)
const resetTab = ref('email')
const resetForm = reactive({ oldEmail: '', newEmail: '', newPassword: '' })
const resetRules = {
  newEmail: [
    { required: true, message: '请输入新邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
}

async function fetchData() {
  loading.value = true
  try {
    const res = await usersApi.listUsers({
      role: query.role,
      status: query.status,
      keyword: query.keyword || undefined,
      page: query.page,
      page_size: query.page_size,
      sort_by: sortBy.value || undefined,
      sort_order: sortOrder.value || undefined,
    })
    list.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
  fetchData()
}

async function toggleStatus(row: UserListItem) {
  const newStatus = row.status === 1 ? 0 : 1
  const action = newStatus === 0 ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户「${row.name}」吗？`)
    await usersApi.updateUserStatus(row.id, newStatus)
    row.status = newStatus
    ElMessage.success(`${action}成功`)
  } catch { /* 取消 */ }
}

function openResetDialog(row: UserListItem) {
  resetUserId.value = row.id
  resetTab.value = 'email'
  resetForm.oldEmail = row.email
  resetForm.newEmail = ''
  resetForm.newPassword = ''
  resetVisible.value = true
  setTimeout(() => resetFormRef.value?.clearValidate())
}

function onResetTabChange() {
  setTimeout(() => resetFormRef.value?.clearValidate())
}

async function handleReset() {
  try {
    if (resetTab.value === 'email') {
      try { await resetFormRef.value?.validate() } catch { return }
      await usersApi.resetPassword(resetUserId.value!, { email: resetForm.newEmail })
    } else {
      if (!resetForm.newPassword) { ElMessage.warning('请输入新密码'); return }
      await usersApi.resetPassword(resetUserId.value!, { new_password: resetForm.newPassword })
    }
    ElMessage.success('已保存')
    resetVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

function openCreateDialog() {
  createForm.email = ''; createForm.password = ''; createForm.confirmPassword = ''; createForm.name = ''; createForm.phone = ''
  createVisible.value = true
  setTimeout(() => createFormRef.value?.clearValidate())
}

async function handleCreate() {
  try { await createFormRef.value?.validate() } catch { return }
  if (createForm.password !== createForm.confirmPassword) {
    ElMessage.warning('两次密码输入不一致')
    return
  }
  try {
    await usersApi.createUser({
      email: createForm.email,
      password: createForm.password,
      name: createForm.name,
      role: 0,
      phone: createForm.phone || undefined,
    })
    ElMessage.success('创建成功')
    createVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '创建失败') }
}

function openEditDialog(row: UserListItem) {
  editingUserId.value = row.id
  editForm.name = row.name
  editForm.phone = row.phone || ''
  editForm.role = row.role
  editVisible.value = true
}

async function handleEdit() {
  try { await editFormRef.value?.validate() } catch { return }
  try {
    await usersApi.updateUser(editingUserId.value!, {
      name: editForm.name,
      phone: editForm.phone || null,
      role: editForm.role,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
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
