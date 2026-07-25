<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="logo">
        <span v-if="!collapsed" class="logo-text">yinyu</span>
        <span v-else class="logo-mark">y</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="aside-menu"
      >
        <el-menu-item index="/articles" :icon="Document">
          <span>图文管理</span>
        </el-menu-item>
        <template v-if="auth.isAdmin">
          <el-menu-item index="/stats" :icon="DataAnalysis">
            <span>数据统计</span>
          </el-menu-item>
          <el-menu-item index="/treeholes" :icon="ChatDotRound">
            <span>树洞管理</span>
          </el-menu-item>
          <el-menu-item index="/comments" :icon="ChatLineSquare">
            <span>评论管理</span>
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
      <div v-if="!collapsed" class="aside-footer">
        <span class="aside-footer-text">温暖治愈的精神角落</span>
      </div>
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
            <el-avatar :size="30" :src="auth.user?.avatar_url">
              {{ (auth.user?.nickname || auth.user?.username || '?').slice(0, 1) }}
            </el-avatar>
            <span class="uname">{{ auth.user?.nickname || auth.user?.username }}</span>
            <span v-if="auth.isAdmin" class="admin-chip">管理员</span>
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
  ChatLineSquare,
  User,
  Ticket,
  Picture,
  Setting,
  Fold,
  Expand,
  DataAnalysis
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

/* ============================================================
 * 侧边栏:浅杏奶油底,告别深紫黑
 * ============================================================ */
.aside {
  background: var(--bg-aside);
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-soft);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-soft);
  padding: 0 16px;
}

.logo-text {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 4px;
  color: var(--text-primary);
  position: relative;
}

.logo-text::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -6px;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: var(--brand-primary);
  border-radius: 2px;
}

.logo-mark {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 700;
  color: var(--brand-primary);
}

.aside-menu {
  flex: 1;
  border-right: none;
  background: transparent !important;
  padding: 10px 10px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* el-menu-item 浅色暖调样式覆盖 */
.aside-menu :deep(.el-menu-item) {
  color: var(--text-secondary);
  background: transparent !important;
  border-radius: 8px;
  margin-bottom: 2px;
  height: 44px;
  line-height: 44px;
  transition: all 0.15s ease;
  position: relative;
}

.aside-menu :deep(.el-menu-item:hover) {
  background: var(--brand-primary-mist) !important;
  color: var(--text-primary);
}

.aside-menu :deep(.el-menu-item.is-active) {
  background: var(--bg-aside-active) !important;
  color: var(--brand-primary) !important;
  font-weight: 500;
}

.aside-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  background: var(--brand-primary);
  border-radius: 0 3px 3px 0;
}

/* 折叠态菜单图标居中 */
.aside-menu :deep(.el-menu--collapse .el-menu-item) {
  text-align: center;
}

.aside-footer {
  padding: 14px 16px 18px;
  border-top: 1px solid var(--border-soft);
  text-align: center;
}

.aside-footer-text {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 1px;
}

/* ============================================================
 * 头部:奶油白 + 微妙下边框
 * ============================================================ */
.header {
  background: var(--bg-card);
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-soft);
  height: 56px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.15s ease;
  padding: 6px;
  border-radius: 6px;
}

.collapse-btn:hover {
  color: var(--brand-primary);
  background: var(--brand-primary-mist);
}

.grow {
  flex: 1;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  outline: none;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  transition: background 0.15s ease;
}

.user-chip:hover {
  background: var(--brand-primary-mist);
}

.uname {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.admin-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--brand-primary-soft);
  color: var(--brand-primary-hover);
  letter-spacing: 0.5px;
}

.main {
  padding: 22px;
  overflow-y: auto;
}
</style>
