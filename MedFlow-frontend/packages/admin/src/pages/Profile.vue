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

    <!-- 基本信息 -->
    <div class="profile-cards">
      <el-card header="基本信息" class="profile-card">
        <el-form :model="form" label-width="80px" class="card-form">
          <el-form-item label="姓名">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input :model-value="authStore.user?.email" disabled />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSave">保存</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码 -->
      <el-card header="修改密码" class="profile-card">
      <el-form :model="pwdForm" label-width="80px" class="card-form pwd-form">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore, authApi } from '@medflow/shared'

const authStore = useAuthStore()
const form = reactive({ name: '', phone: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '' })
const avatarPath = ref<string | null>(null)

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const avatarUrl = computed(() => {
  if (!avatarPath.value) return ''
  return API_BASE.replace('/api/v1', '') + '/uploads/' + avatarPath.value
})
const userInitial = computed(() => (form.name || '?')[0])

async function fetchAvatar() {
  try {
    const res = await authApi.getAvatar()
    avatarPath.value = res.data.avatar
  } catch { /* ignore */ }
}

function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('请选择图片文件')
    return false
  }
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

async function handleAvatarUpload(options: { file: File }) {
  try {
    const res = await authApi.uploadAvatar(options.file)
    avatarPath.value = res.data.avatar
    ElMessage.success('头像更新成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  }
}

onMounted(async () => {
  await authStore.fetchMe()
  if (authStore.user) {
    form.name = authStore.user.name
    form.phone = authStore.user.phone || ''
  }
  fetchAvatar()
})

async function handleSave() {
  try {
    await authApi.updateMe({ name: form.name, phone: form.phone || undefined })
    ElMessage.success('保存成功')
    authStore.fetchMe()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleChangePassword() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword) { ElMessage.warning('请填写旧密码和新密码'); return }
  try {
    await authApi.changePassword({ old_password: pwdForm.oldPassword, new_password: pwdForm.newPassword })
    ElMessage.success('密码修改成功')
    pwdForm.oldPassword = ''; pwdForm.newPassword = ''
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
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: #fff;
  overflow: hidden;
  background-size: cover;
  background-position: center;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 96px;
  height: 96px;
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
  justify-content: center;
}
.profile-card {
  width: 380px;
  display: flex;
  flex-direction: column;
}
.profile-card :deep(.el-card__header) {
  text-align: center;
}
.profile-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.card-form {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.card-form .el-form-item:last-child {
  margin-top: auto;
  margin-bottom: 0;
}
.card-form .el-form-item:last-child :deep(.el-form-item__content) {
  justify-content: center;
  margin-left: 0 !important;
}
.pwd-form {
  justify-content: center;
  padding-top: 20px;
}
.pwd-form :deep(.el-form-item) {
  justify-content: center;
}
</style>
