import http from '../utils/request'

export const api = {
  auth: {
    register: (p) => http.post('/auth/register', p),
    changePassword: (old_password, new_password) =>
      http.put('/auth/password', { old_password, new_password })
  },

  articles: {
    list: (params) => http.get('/articles', params),
    get: (id) => http.get('/articles/' + id),
    like: (id) => http.post('/articles/' + id + '/like')
  },

  comments: {
    list: (articleId, params) => http.get('/articles/' + articleId + '/comments', params),
    create: (articleId, data) => http.post('/articles/' + articleId + '/comments', data),
    like: (commentId) => http.post('/comments/' + commentId + '/like'),
    remove: (commentId) => http.delete('/comments/' + commentId)
  },

  notifications: {
    list: (params) => http.get('/notifications', params),
    unreadCount: () => http.get('/notifications/unread-count'),
    markRead: (id) => http.post('/notifications/' + id + '/read'),
    markAllRead: () => http.post('/notifications/read-all')
  },

  users: {
    search: (q) => http.get('/users/search', { q })
  },

  treeholes: {
    unlock: (code) => http.post('/treeholes/unlock', { code }),
    echo: (echoToken, message) =>
      http.post('/treeholes/echo', { echo_token: echoToken, message }),
    create: (data) => http.post('/treeholes', data),
    changeCode: (id, code) => http.put('/treeholes/' + id + '/code', { code })
  },

  me: {
    get: () => http.get('/me'),
    update: (data) => http.put('/me', data),
    myArticles: (params) => http.get('/me/articles', params),
    myTreeholes: (params) => http.get('/me/treeholes', params),
    treeholeEchoes: (id) => http.get('/me/treeholes/' + id + '/echoes')
  },

  capsules: {
    list: (params) => http.get('/capsules', params),
    get: (id) => http.get('/capsules/' + id),
    create: (data) => http.post('/capsules', data),
    remove: (id) => http.delete('/capsules/' + id)
  },

  daily: {
    today: () => http.get('/daily-images/today'),
    history: (params) => http.get('/daily-images/history', params)
  },

  warmWords: {
    scenes: () => http.get('/warm_words/scenes'),
    random: (scene) => http.get('/warm_words/random', { scene }),
    favorites: (params) => http.get('/warm_words/favorites', params),
    favorite: (id) => http.post('/warm_words/' + id + '/favorite'),
    unfavorite: (id) => http.delete('/warm_words/' + id + '/favorite')
  },

  write: {
    createArticle: (data) => http.post('/articles', data),
    updateArticle: (id, data) => http.put('/articles/' + id, data),
    createTreehole: (data) => http.post('/treeholes', data),
    updateTreehole: (id, data) => http.put('/treeholes/' + id, data)
  },

  upload: (filePath) => http.upload(filePath, '/upload'),
  // 录音产物:H5 是 File 走 fetch,App 是 path 走 uni.uploadFile
  uploadRecorded: (r) => (r.file ? http.uploadBlob(r.file, r.filename) : http.upload(r.path, '/upload'))
}

export default api
