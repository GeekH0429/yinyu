import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/articles' },
      {
        path: 'articles',
        name: 'articles',
        component: () => import('@/views/article/List.vue')
      },
      {
        path: 'articles/new',
        name: 'article-new',
        component: () => import('@/views/article/Edit.vue')
      },
      {
        path: 'articles/:id/edit',
        name: 'article-edit',
        component: () => import('@/views/article/Edit.vue')
      },
      {
        path: 'treeholes',
        name: 'treeholes',
        component: () => import('@/views/treehole/List.vue'),
        meta: { admin: true }
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/user/List.vue'),
        meta: { admin: true }
      },
      {
        path: 'invites',
        name: 'invites',
        component: () => import('@/views/invite/List.vue'),
        meta: { admin: true }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/Profile.vue')
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && auth.isLoggedIn) {
    return { path: '/' }
  }
  if (to.meta.admin && !auth.isAdmin) {
    return { path: '/' }
  }
})

export default router
