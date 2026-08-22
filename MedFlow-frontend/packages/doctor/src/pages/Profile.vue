<template>
  <div class="page profile-page">
    <!-- 头像区域 -->
    <div class="profile-avatar-section">
      <el-upload
        class="avatar-upload"
        :show-file-list="false"
        :before-upload="beforeAvatarUpload"
        :http-request="handleAvatarUpload"
        accept="image/*"
      >
        <div class="avatar-img" :style="avatarUrl ? { backgroundImage: `url(${avatarUrl})`, backgroundSize: 'cover' } : {}">
          <span v-if="!avatarUrl">{{ userInitial }}</span>
        </div>
        <div class="avatar-overlay">更换头像</div>
      </el-upload>
      <div class="profile-name">{{ form.name }}</div>
      <div class="profile-email">{{ authStore.user?.email }}</div>
    </div>

    <div class="profile-cards">
      <!-- 左栏：医生信息 -->
      <el-card class="profile-card">
        <template #header>
          <span class="card-title">医生信息</span>
        </template>
        <el-form :model="form" label-width="80px" class="card-form">
          <el-form-item label="科室">
            <el-input :model-value="departmentName" disabled />
          </el-form-item>
          <el-form-item label="职称">
            <el-input v-model="form.title" placeholder="请输入职称" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="form.introduction" type="textarea" :rows="5" placeholder="请输入个人简介" />
          </el-form-item>
          <el-form-item class="card-actions">
            <el-button type="primary" @click="handleSaveDoctor" style="width:100%">保存</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 右栏：账号信息 -->
      <el-card class="profile-card">
        <template #header>
          <span class="card-title">账号信息</span>
        </template>
        <el-form :model="form" label-width="80px" class="card-form" style="padding-top:30px">
          <el-form-item label="姓名">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input :model-value="authStore.user?.email" disabled />
          </el-form-item>
          <el-form-item class="card-actions">
            <el-button type="primary" @click="handleSaveAccount" style="width:100%">保存</el-button>
          </el-form-item>
          <el-form-item class="card-actions">
            <el-button @click="showPwdDialog = true" style="width:100%">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showPwdDialog" title="修改密码" width="460px" :close-on-click-modal="false" @closed="resetPwdForm">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore, authApi, doctorsApi, departmentsApi } from '@medflow/shared'
import type { Department } from '@medflow/shared'

const authStore = useAuthStore()

const doctorId = ref<number | null>(null)
const departments = ref<Department[]>([])

const form = reactive({
  name: '', phone: '', department_id: null as number | null, title: '', introduction: '',
})
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const showPwdDialog = ref(false)

function resetPwdForm() {
  pwdForm.oldPassword = ''
  pwdForm.newPassword = ''
  pwdForm.confirmPassword = ''
}

const avatarPath = ref<string | null>(null)

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const avatarUrl = computed(() => {
  if (!avatarPath.value) return ''
  return API_BASE.replace('/api/v1', '') + '/uploads/' + avatarPath.value
})
const userInitial = computed(() => (form.name || '?')[0])

const departmentName = computed(() => {
  const dept = departments.value.find(d => d.id === form.department_id)
  return dept?.name || '-'
})

async function fetchAvatar() {
  try {
    const res = await authApi.getAvatar()
    avatarPath.value = res.data.avatar
  } catch { /* ignore */ }
}

function beforeAvatarUpload(file: File) {
  if (!file.type.startsWith('image/')) { ElMessage.error('请选择图片文件'); return false }
  if (file.size / 1024 / 1024 > 5) { ElMessage.error('图片大小不能超过 5MB'); return false }
  return true
}

async function handleAvatarUpload(options: { file: File }) {
  try {
    const res = await authApi.uploadAvatar(options.file)
    avatarPath.value = res.data.avatar
    ElMessage.success('头像更新成功')
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '上传失败') }
}

onMounted(async () => {
  await authStore.fetchMe()
  if (authStore.user) {
    form.name = authStore.user.name
    form.phone = authStore.user.phone || ''
  }
  fetchAvatar()
  try {
    const [deptRes, docRes] = await Promise.all([
      departmentsApi.listDepartments({ page_size: 999 }),
      doctorsApi.listDoctors({ page_size: 999 }),
    ])
    departments.value = deptRes.data.items
    const doctor = docRes.data.items.find(d => d.user_id === authStore.user?.id)
    if (doctor) {
      doctorId.value = doctor.id
      form.department_id = doctor.department_id
      form.title = doctor.title || ''
      form.introduction = doctor.introduction || ''
    }
  } catch { /* ignore */ }
})

async function handleSaveAccount() {
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    ElMessage.warning('请输入正确的手机号'); return
  }
  try {
    await authApi.updateMe({ name: form.name, phone: form.phone || undefined })
    ElMessage.success('账号信息已保存')
    authStore.fetchMe()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleSaveDoctor() {
  if (!doctorId.value) { ElMessage.warning('未找到医生信息'); return }
  try {
    await doctorsApi.updateDoctor(doctorId.value, {
      department_id: form.department_id ?? undefined,
      title: form.title || undefined,
      introduction: form.introduction || undefined,
    })
    ElMessage.success('医生信息已保存')
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleChangePassword() {
  if (!pwdForm.oldPassword) { ElMessage.warning('请输入旧密码'); return }
  if (!pwdForm.newPassword) { ElMessage.warning('请输入新密码'); return }
  if (pwdForm.newPassword.length < 6) { ElMessage.warning('新密码至少6位'); return }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) { ElMessage.warning('两次输入的密码不一致'); return }
  try {
    await authApi.changePassword({ old_password: pwdForm.oldPassword, new_password: pwdForm.newPassword })
    ElMessage.success('密码修改成功')
    showPwdDialog.value = false
    resetPwdForm()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '修改失败') }
}
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.profile-avatar-section {
  text-align: center;
  padding: 32px 0 8px;
}
.avatar-upload {
  display: inline-block;
  position: relative;
  cursor: pointer;
}
.avatar-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #67c23a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #fff;
  overflow: hidden;
  background-size: cover;
  background-position: center;
}
.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}
.avatar-upload:hover .avatar-overlay {
  opacity: 1;
}
.profile-name {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.profile-email {
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}
.profile-cards {
  display: flex;
  gap: 20px;
  width: 800px;
  max-width: 100%;
  align-items: stretch;
}
.profile-card {
  flex: 1;
  min-width: 0;
}
.profile-card :deep(.el-card__header) {
  text-align: center;
  padding: 12px 20px;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.card-form {
  display: flex;
  flex-direction: column;
}
.card-actions {
  margin-top: 12px;
  margin-bottom: 0;
}
.card-actions :deep(.el-form-item__content) {
  justify-content: center;
  gap: 12px;
  margin-left: 0 !important;
}
</style>
