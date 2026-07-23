<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '210px'" class="aside">
      <div class="logo">
        <span v-if="!collapsed">yinyu</span>
        <span v-else>Y</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        background-color="#2b2b3c"
        text-color="#cfcfe0"
        active-text-color="#ffd6e7"
      >
        <el-menu-item index="/articles" :icon="Document">
          <span>图文管理</span>
        </el-menu-item>
        <template v-if="auth.isAdmin">
          <el-menu-item index="/treeholes" :icon="ChatDotRound">
            <span>树洞管理</span>
          </el-menu-item>
          <el-menu-item index="/users" :icon="User">
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/invites" :icon="Ticket">
            <span>邀请码</span>
          </el-menu-item>
          <el-menu-item index="/daily-images" :icon="Picture">
            <span>每日一图</span>
          </el-menu-item>
        </template>
        <el-menu-item index="/profile" :icon="Setting">
          <span>个人资料</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <el-icon class="collapse-btn" @click="collapsed = !collapsed">
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
        <div class="grow"></div>
        <el-dropdown @command="onCommand">
          <span class="user-chip">
            <el-avatar :size="28" :src="auth.user?.avatar_url">
              {{ (auth.user?.nickname || auth.user?.username || '?').slice(0, 1) }}
            </el-avatar>
            <span class="uname">{{ auth.user?.nickname || auth.user?.username }}</span>
            <el-tag v-if="auth.isAdmin" size="small" type="warning" effect="plain">管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人资料</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  ChatDotRound,
  User,
  Ticket,
  Picture,
  Setting,
  Fold,
  Expand
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const activeMenu = computed(() => {
  // 文章编辑页高亮"图文管理"
  if (route.path.startsWith('/articles')) return '/articles'
  return route.path
})

function onCommand(cmd) {
  if (cmd === 'profile') router.push('/profile')
  else if (cmd === 'logout') {
    auth.logout()
    router.replace('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #2b2b3c;
  transition: width 0.2s;
  overflow: hidden;
}
.logo {
  height: 56px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  font-family: 'Georgia', serif;
}
.aside :deep(.el-menu) {
  border-right: none;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #eee;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #666;
}
.grow {
  flex: 1;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.uname {
  font-size: 14px;
  color: #333;
}
.main {
  padding: 18px;
  overflow-y: auto;
}
</style>
