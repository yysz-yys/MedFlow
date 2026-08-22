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
      <!-- 左栏：患者档案 -->
      <el-card class="profile-card">
        <template #header>
          <span class="card-title">患者档案</span>
        </template>
        <el-form :model="form" label-width="80px" class="card-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="性别">
                <el-select v-model="form.gender" clearable placeholder="请选择" style="width:100%">
                  <el-option label="未知" :value="0" />
                  <el-option label="男" :value="1" />
                  <el-option label="女" :value="2" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="血型">
                <el-select v-model="form.blood_type" clearable placeholder="请选择" style="width:100%">
                  <el-option label="A型" value="A" />
                  <el-option label="B型" value="B" />
                  <el-option label="AB型" value="AB" />
                  <el-option label="O型" value="O" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="出生日期">
            <el-date-picker v-model="form.birth_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="地址">
            <el-input v-model="form.address" type="textarea" :rows="2" placeholder="请输入地址" />
          </el-form-item>
          <el-form-item label="过敏史">
            <el-input v-model="form.allergy_history" type="textarea" :rows="3" placeholder="请输入过敏史" />
          </el-form-item>
          <el-form-item class="card-actions">
            <el-button type="primary" @click="handleSavePatient" style="width:100%">保存</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 右栏：账号信息 -->
      <el-card class="profile-card">
        <template #header>
          <span class="card-title">账号信息</span>
        </template>
        <el-form :model="form" label-width="80px" class="card-form" style="padding-top:20px">
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
        <el-form-item label="邮箱">
          <el-input :model-value="authStore.user?.email" disabled />
        </el-form-item>
        <el-form-item label="验证码">
          <div style="display:flex;gap:10px">
            <el-input v-model="pwdForm.code" placeholder="请输入验证码" style="flex:1" />
            <el-button :disabled="codeCd > 0" @click="handleSendCode" style="width:120px;flex-shrink:0">
              {{ codeCd > 0 ? `${codeCd}s` : '发送验证码' }}
            </el-button>
          </div>
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
import { useAuthStore, authApi, patientsApi } from '@medflow/shared'

const authStore = useAuthStore()

const form = reactive({
  name: '', phone: '', gender: 0, birth_date: '', address: '', blood_type: '', allergy_history: '',
})
const pwdForm = reactive({ code: '', newPassword: '', confirmPassword: '' })
const codeCd = ref(0)
let codeTimer: ReturnType<typeof setInterval> | null = null
const showPwdDialog = ref(false)

function resetPwdForm() {
  pwdForm.code = ''
  pwdForm.newPassword = ''
  pwdForm.confirmPassword = ''
  if (codeTimer) { clearInterval(codeTimer); codeTimer = null }
  codeCd.value = 0
}

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
    const res = await patientsApi.listPatients({ page_size: 1 })
    const patient = res.data.items[0]
    if (patient) {
      form.gender = patient.gender
      form.birth_date = patient.birth_date || ''
      form.address = patient.address || ''
      form.blood_type = patient.blood_type || ''
      form.allergy_history = patient.allergy_history || ''
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

async function handleSavePatient() {
  try {
    const res = await patientsApi.listPatients({ page_size: 1 })
    const patient = res.data.items[0]
    if (patient) {
      await patientsApi.updatePatient(patient.id, {
        gender: form.gender,
        birth_date: form.birth_date || null,
        address: form.address || null,
        blood_type: form.blood_type || null,
        allergy_history: form.allergy_history || null,
      })
    }
    ElMessage.success('患者档案已保存')
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleSendCode() {
  const email = authStore.user?.email
  if (!email) { ElMessage.warning('未获取到邮箱'); return }
  try {
    await authApi.sendCode({ email, scene: 'RESET_PASSWORD' })
    ElMessage.success('验证码已发送')
    codeCd.value = 60
    if (codeTimer) clearInterval(codeTimer)
    codeTimer = setInterval(() => {
      codeCd.value--
      if (codeCd.value <= 0) {
        if (codeTimer) { clearInterval(codeTimer); codeTimer = null }
      }
    }, 1000)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  }
}

async function handleChangePassword() {
  if (!pwdForm.code) { ElMessage.warning('请输入验证码'); return }
  if (!pwdForm.newPassword) { ElMessage.warning('请输入新密码'); return }
  if (pwdForm.newPassword.length < 6) { ElMessage.warning('新密码至少6位'); return }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) { ElMessage.warning('两次输入的密码不一致'); return }
  try {
    await authApi.resetPasswordByCode({
      email: authStore.user!.email,
      code: pwdForm.code,
      new_password: pwdForm.newPassword,
    })
    ElMessage.success('密码修改成功')
    showPwdDialog.value = false
    resetPwdForm()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  }
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
  background: #f0a0b0;
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
