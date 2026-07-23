<template>
  <div class="profile-wrap">
    <div class="page-card">
      <h2 class="title">个人资料</h2>
      <el-form :model="form" label-width="100px" v-loading="loading" style="max-width: 560px">
        <el-form-item label="头像">
          <div class="avatar-row upload-zone" ref="avatarZoneRef" :class="{ 'is-dragover': avatarDrag }">
            <el-avatar :size="72" :src="form.avatar_url">
              {{ (form.nickname || '?').slice(0, 1) }}
            </el-avatar>
            <el-upload :show-file-list="false" :before-upload="onAvatar" accept="image/*">
              <el-button :loading="avatarUploading" size="small">更换头像</el-button>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input :model-value="auth.user?.username" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="40" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="可留空" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.bio" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="onSaveProfile">保存资料</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card" style="margin-top: 18px">
      <h2 class="title">修改密码</h2>
      <el-form :model="pwd" label-width="100px" style="max-width: 560px">
        <el-form-item label="原密码">
          <el-input v-model="pwd.old" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwd.new1" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwd.new2" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useImageDropPaste } from '@/composables/useImageDropPaste'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const avatarUploading = ref(false)
const avatarZoneRef = ref()

const form = reactive({ nickname: '', email: '', bio: '', avatar_url: '' })
const pwd = reactive({ old: '', new1: '', new2: '' })

async function loadProfile() {
  loading.value = true
  try {
    const data = await api.me.get()
    form.nickname = data.nickname || ''
    form.email = data.email || ''
    form.bio = data.bio || ''
    form.avatar_url = data.avatar_url || ''
  } finally {
    loading.value = false
  }
}

async function onAvatar(file) {
  avatarUploading.value = true
  try {
    const data = await api.upload(file)
    form.avatar_url = data.url
  } catch {
    ElMessage.error('头像上传失败')
  } finally {
    avatarUploading.value = false
  }
  return false
}

// 支持拖拽 / 粘贴上传头像
const { isDragover: avatarDrag } = useImageDropPaste(avatarZoneRef, onAvatar)

async function onSaveProfile() {
  saving.value = true
  try {
    const data = await api.me.update({
      nickname: form.nickname,
      email: form.email || null,
      bio: form.bio || null,
      avatar_url: form.avatar_url || null
    })
    auth.setUser(data)
    ElMessage.success('资料已保存')
  } finally {
    saving.value = false
  }
}

async function onChangePassword() {
  if (!pwd.old || !pwd.new1) return ElMessage.warning('请填写完整')
  if (pwd.new1 !== pwd.new2) return ElMessage.warning('两次新密码不一致')
  if (pwd.new1.length < 6) return ElMessage.warning('新密码至少 6 位')
  await api.auth.changePassword(pwd.old, pwd.new1)
  ElMessage.success('密码已修改')
  pwd.old = ''
  pwd.new1 = ''
  pwd.new2 = ''
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-wrap {
  max-width: 900px;
}
.title {
  margin: 0 0 18px;
  font-size: 18px;
}
.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s, box-shadow 0.15s;
}
.avatar-row.is-dragover {
  background: #fff8fb;
  box-shadow: 0 0 0 2px rgba(230, 122, 163, 0.25);
}
</style>
