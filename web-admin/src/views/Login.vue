<template>
  <div class="login-wrap">
    <!-- 装饰光斑 -->
    <div class="blob blob-pink"></div>
    <div class="blob blob-coffee"></div>
    <div class="blob blob-cream"></div>

    <div class="login-card">
      <div class="login-brand">
        <div class="brand-mark">y</div>
        <div class="login-title">yinyu</div>
      </div>
      <div class="login-sub">温暖治愈的精神角落 · 治愈书房</div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="onSubmit"
        >
          登 录
        </el-button>
      </el-form>

      <div class="login-footer">yinyu · 一个安放思绪的角落</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  await formRef.value.validate().catch(() => {})
  if (!form.username || !form.password) return
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.replace(redirect)
  } catch {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #faf3ea 0%, #f5e6d3 50%, #efd8c1 100%);
  overflow: hidden;
}

/* 装饰浮动光斑 */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  pointer-events: none;
  animation: float 12s ease-in-out infinite;
}

.blob-pink {
  width: 320px;
  height: 320px;
  background: #f5d4d4;
  top: -80px;
  left: -80px;
}

.blob-coffee {
  width: 380px;
  height: 380px;
  background: #e2c4a4;
  bottom: -100px;
  right: -100px;
  animation-delay: -4s;
}

.blob-cream {
  width: 260px;
  height: 260px;
  background: #fbeedd;
  top: 50%;
  left: 60%;
  animation-delay: -8s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%      { transform: translate(30px, -20px) scale(1.05); }
  66%      { transform: translate(-20px, 30px) scale(0.95); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  padding: 44px 38px 32px;
  box-shadow:
    0 20px 60px rgba(120, 80, 40, 0.12),
    0 4px 12px rgba(120, 80, 40, 0.06);
}

.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 6px;
}

.brand-mark {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #b8825a 0%, #d4a373 100%);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(184, 130, 90, 0.3);
  margin-bottom: 14px;
}

.login-title {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 6px;
  text-align: center;
}

.login-sub {
  text-align: center;
  color: var(--text-tertiary);
  margin: 8px 0 30px;
  font-size: 13px;
  font-style: italic;
  letter-spacing: 1px;
}

.login-btn {
  width: 100%;
  margin-top: 6px;
  height: 44px;
  font-size: 15px;
  letter-spacing: 4px;
  font-weight: 500;
}

.login-footer {
  margin-top: 26px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 1px;
}
</style>
