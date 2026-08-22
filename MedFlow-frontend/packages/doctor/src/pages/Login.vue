<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>云诊易 · 医生工作站</h2>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <!-- 图形验证码 -->
        <el-form-item>
          <div style="display:flex;align-items:center;gap:8px">
            <el-input v-model="captchaText" placeholder="图片中的数字" maxlength="4" style="flex:1" />
            <img
              :src="captchaImage"
              @click="refreshCaptcha"
              style="height:44px;cursor:pointer;border:1px solid #dcdfe6;border-radius:4px"
              alt="图形验证码"
            />
            <el-button @click="refreshCaptcha" link size="small">换一张</el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" native-type="submit" style="width:100%">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore, authApi } from '@medflow/shared'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)
const captchaId = ref('')
const captchaImage = ref('')
const captchaText = ref('')

const form = reactive({ email: '', password: '' })
const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function refreshCaptcha() {
  try {
    const res = await authApi.getCaptcha()
    captchaId.value = res.data.captcha_id
    captchaImage.value = res.data.image
    captchaText.value = ''
  } catch (e: any) {
    ElMessage.error('获取图形验证码失败')
  }
}

async function handleLogin() {
  await formRef.value?.validate()
  if (!captchaText.value) { ElMessage.warning('请输入图形验证码'); return }
  loading.value = true
  try {
    await authStore.login({ email: form.email, password: form.password, captcha_id: captchaId.value, captcha_text: captchaText.value })
    ElMessage.success('登录成功')
    router.push('/doctor/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 420px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 30px;
}
</style>
