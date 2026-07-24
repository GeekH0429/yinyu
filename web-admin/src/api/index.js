import request from './request'

export const api = {
  auth: {
    login: (username, password) =>
      request.post('/auth/login', { username, password }),
    register: (payload) => request.post('/auth/register', payload),
    me: () => request.get('/me'),
    changePassword: (old_password, new_password) =>
      request.put('/auth/password', { old_password, new_password })
  },

  articles: {
    list: (params) => request.get('/articles', { params }),
    adminList: (params) => request.get('/admin/articles', { params }),
    tags: () => request.get('/articles/tags'),
    get: (id) => request.get(`/articles/${id}`),
    create: (data) => request.post('/articles', data),
    update: (id, data) => request.put(`/articles/${id}`, data),
    remove: (id) => request.delete(`/articles/${id}`)
  },

  treeholes: {
    create: (data) => request.post('/treeholes', data),
    update: (id, data) => request.put(`/treeholes/${id}`, data),
    changeCode: (id, code) => request.put(`/treeholes/${id}/code`, { code }),
    remove: (id) => request.delete(`/treeholes/${id}`),
    adminList: (params) => request.get('/admin/treeholes', { params }),
    mine: (params) => request.get('/me/treeholes', { params })
  },

  me: {
    get: () => request.get('/me'),
    update: (data) => request.put('/me', data),
    myArticles: (params) => request.get('/me/articles', { params })
  },

  admin: {
    inviteCreate: (data) => request.post('/admin/invite-codes', data),
    inviteList: (params) => request.get('/admin/invite-codes', { params }),
    users: (params) => request.get('/admin/users', { params }),
    patchUser: (id, data) => request.patch(`/admin/users/${id}`, data),
    dailyList: (params) => request.get('/admin/daily-images', { params }),
    dailyCreate: (data) => request.post('/admin/daily-images', data),
    dailyUpdate: (id, data) => request.put(`/admin/daily-images/${id}`, data),
    dailyRemove: (id) => request.delete(`/admin/daily-images/${id}`),
    commentList: (params) => request.get('/admin/comments', { params }),
    commentRemove: (id) => request.delete(`/admin/comments/${id}`),
    statsOverview: (params) => request.get('/stats/overview', { params }),
    statsTrends: (params) => request.get('/stats/trends', { params }),
    statsTopArticles: (params) => request.get('/stats/top-articles', { params }),
    statsActiveUsers: (params) => request.get('/stats/active-users', { params })
  },

  upload: (file, { onProgress } = {}) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
        ? (e) => {
            // e.loaded / e.total(字节);axios 不直接给百分比
            const percent = e.total ? Math.round((e.loaded / e.total) * 100) : 0
            onProgress(percent, e)
          }
        : undefined
    })
  }
}

export default api
