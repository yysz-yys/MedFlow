<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>云诊易 · 患者注册</h2>
      <el-form ref="formRef" :model="form" :rules="rules">
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item prop="code">
          <el-input v-model="form.code" placeholder="邮箱验证码">
            <template #suffix>
              <el-button :disabled="countdown > 0" @click="sendCode" link size="small">
                {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="name">
          <el-input v-model="form.name" placeholder="姓名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width:100%">注 册</el-button>
        </el-form-item>
      </el-form>
      <div style="text-align:center">
        已有账号？<router-link to="/patient/login">去登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@medflow/shared'

const router = useRouter()
const loading = ref(false)
const countdown = ref(0)
const form = reactive({ email: '', code: '', name: '', password: '' })
const rules = {
  email: [{ required: true, message: '请输入邮箱' }],
  code: [{ required: true, message: '请输入邮箱验证码' }],
  name: [{ required: true, message: '请输入姓名' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
}

async function sendCode() {
  if (!form.email) { ElMessage.warning('请先输入邮箱'); return }
  try {
    await authApi.sendCode({ email: form.email, scene: 'REGISTER', captcha_id: '', captcha_text: '' })
    ElMessage.success('验证码已发送')
    countdown.value = 60
    const t = setInterval(() => { if (--countdown.value <= 0) clearInterval(t) }, 1000)
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '发送失败') }
}

async function handleRegister() {
  loading.value = true
  try {
    await authApi.register({ email: form.email, code: form.code, name: form.name, password: form.password, role: 2 })
    ElMessage.success('注册成功，请登录')
    router.push('/patient/login')
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '注册失败') }
  finally { loading.value = false }
}
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
