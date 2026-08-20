<template>
  <div class="profile-wrap">
    <div class="page-card">
      <h2 class="title">个人资料</h2>
      <el-form :model="form" label-width="100px" v-loading="loading" style="max-width: 560px">
        <el-form-item label="头像">
          <div class="avatar-wrap">
            <div
              class="avatar-row upload-zone img-uploader img-uploader--square"
              ref="avatarZoneRef"
              :class="{ 'is-dragover': avatarDrag }"
            >
              <el-upload :show-file-list="false" :before-upload="onAvatar" accept="image/*">
                <div v-if="form.avatar_url" class="img-uploader__filled">
                  <img :src="form.avatar_url" alt="avatar" />
                  <div class="img-uploader__mask">
                    <el-icon><Refresh /></el-icon>
                    <span>更换</span>
                  </div>
                </div>
                <div v-else class="img-uploader__empty">
                  <el-icon class="img-uploader__icon"><Picture /></el-icon>
                  <div class="img-uploader__title">上传头像</div>
                  <div class="img-uploader__hint">点击 / 拖拽 / 粘贴</div>
                </div>
              </el-upload>
            </div>
            <div class="avatar-side">
              <div class="avatar-hint">支持 JPG / PNG,推荐方形</div>
              <el-button
                v-if="form.avatar_url"
                link
                type="danger"
                size="small"
                @click="form.avatar_url = ''"
              >移除头像</el-button>
            </div>
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
        <el-form-item label="新文章邮件订阅">
          <div class="notify-wrap">
            <el-switch v-model="form.article_notify_enabled" :disabled="!form.email" />
            <span class="notify-hint">
              {{ form.email ? '有新文章发布时发送邮件提醒' : '请先填写邮箱后再开启订阅' }}
            </span>
          </div>
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
import { Picture, Refresh } from '@element-plus/icons-vue'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useImageDropPaste } from '@/composables/useImageDropPaste'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const avatarUploading = ref(false)
const avatarZoneRef = ref()

const form = reactive({
  nickname: '',
  email: '',
  bio: '',
  avatar_url: '',
  article_notify_enabled: false
})
const pwd = reactive({ old: '', new1: '', new2: '' })

async function loadProfile() {
  loading.value = true
  try {
    const data = await api.me.get()
    form.nickname = data.nickname || ''
    form.email = data.email || ''
    form.bio = data.bio || ''
    form.avatar_url = data.avatar_url || ''
    form.article_notify_enabled = !!data.article_notify_enabled
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
      avatar_url: form.avatar_url || null,
      article_notify_enabled: form.article_notify_enabled
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
.avatar-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar-row {
  /* 尺寸/dragover 由全局 .img-uploader 控制 */
}
.avatar-side {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.avatar-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.3px;
}
.notify-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.notify-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
