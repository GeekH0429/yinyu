# web-admin 前端约定

> 改动 `web-admin/` 前先通读。

- `src/api/request.js`:axios 实例,注入 Bearer token,401 时自动用 refresh token 续期并重放,失败跳登录。**响应拦截器直接返回 `resp.data`**,所以 API 封装拿到的是业务对象。
- `src/api/index.js`:按模块组织的 API 封装(注意 `auth.me` → `/me`,后端无 `/auth/me`)。
- `src/components/RichEditor.vue`:TipTap 编辑器。`src/components/tiptap/Audio.js`、`Video.js` 是自定义原子节点(`renderHTML` 输出真实 `<audio controls>`/`<video controls>`,编辑器内可见可播放;`parseHTML` 反解析保证回显)。图片走 `@tiptap/extension-image`。
