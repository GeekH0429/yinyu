<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
onMounted(() => {
  // 已登录则刷新一次用户信息(token 失效会自动登出)
  if (auth.isLoggedIn) auth.refreshUser()
})
</script>
