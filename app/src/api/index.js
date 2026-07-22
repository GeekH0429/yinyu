import http from '../utils/request'

export const api = {
  auth: {
    register: (p) => http.post('/auth/register', p),
    changePassword: (old_password, new_password) =>
      http.put('/auth/password', { old_password, new_password })
  },

  articles: {
    list: (params) => http.get('/articles', params),
    tags: () => http.get('/articles/tags'),
    get: (id) => http.get('/articles/' + id),
    like: (id) => http.post('/articles/' + id + '/like')
  },

  treeholes: {
    unlock: (code) => http.post('/treeholes/unlock', { code }),
    create: (data) => http.post('/treeholes', data),
    changeCode: (id, code) => http.put('/treeholes/' + id + '/code', { code }),
    remove: (id) => http.delete('/treeholes/' + id)
  },

  me: {
    get: () => http.get('/me'),
    update: (data) => http.put('/me', data),
    myArticles: (params) => http.get('/me/articles', params),
    myTreeholes: (params) => http.get('/me/treeholes', params),
    myLikes: (params) => http.get('/me/likes', params)
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
