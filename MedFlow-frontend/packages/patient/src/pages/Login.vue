<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>云诊易 · 患者服务</h2>

      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 密码登录 -->
        <el-tab-pane label="密码登录" name="password">
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
        </el-tab-pane>

        <!-- 验证码登录 -->
        <el-tab-pane label="验证码登录" name="code">
          <el-form @submit.prevent="handleCodeLogin">
            <el-form-item>
              <el-input v-model="codeForm.email" placeholder="邮箱" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="codeForm.code" placeholder="邮箱验证码">
                <template #suffix>
                  <el-button :disabled="countdown > 0" @click="sendCode" link size="small">
                    {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" native-type="submit" style="width:100%">
                登 录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div style="text-align:center;margin-top:16px">
        没有账号？<router-link to="/patient/register">去注册</router-link>
      </div>
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
const countdown = ref(0)
const activeTab = ref('password')
const captchaId = ref('')
const captchaImage = ref('')
const captchaText = ref('')

const form = reactive({ email: '', password: '' })
const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const codeForm = reactive({ email: '', code: '' })

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
    router.push('/patient/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

async function sendCode() {
  if (!codeForm.email) { ElMessage.warning('请先输入邮箱'); return }
  try {
    await authApi.sendCode({ email: codeForm.email, scene: 'LOGIN', captcha_id: '', captcha_text: '' })
    ElMessage.success('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  }
}

async function handleCodeLogin() {
  if (!codeForm.email || !codeForm.code) { ElMessage.warning('请输入邮箱和验证码'); return }
  loading.value = true
  try {
    await authStore.login({ email: codeForm.email, code: codeForm.code })
    ElMessage.success('登录成功')
    router.push('/patient/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
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
  height: 100vh;
  background: #f0f2f5;
  overflow: hidden;
}
.login-card {
  width: 420px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 10px;
}
.login-tabs {
  margin-top: 10px;
}
.login-tabs :deep(.el-tabs__nav) {
  display: flex;
  justify-content: center;
  width: 100%;
}
</style>
