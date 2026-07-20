# 隐语 App(uni-app 客户端)

治愈系图文 + 树洞的移动端,基于 **uni-app (Vue 3 + Vite)**。UI 审美参考自 pig-blog(暖白 `#FDFBF7` + 木褐 `#C4A882` + 苔绿 `#88A07A` + 落日粉 `#E8C4C4`,大圆角卡片 + 柔阴影)。

## 模块
- **阅读**(首页):图文 feed,标签筛选,下拉加载,点进详情(mp-html 渲染图/音/视频)
- **树洞**:6 位暗号解锁单篇(无列表/全量隐匿);限流 429 友好提示
- **写作**(轻量):图文 / 树洞切换;纯文本 + 插入图片/音频(上传到 `/upload`);树洞发布后展示并复制暗号
- **我的**:资料、我的图文、我的树洞(含暗号,可复制/换暗号)、退出登录

## 运行

```bash
cd app
npm install

# 1. 改后端地址(关键)
#    编辑 src/config/index.js 的 SERVER_ORIGIN
#    H5 调试:http://127.0.0.1:8000
#    真机/小程序:改成电脑局域网 IP,如 http://192.168.x.x:8000,且手机与电脑同网段
#    生产:https://你的域名

# 2. 启动(H5,默认端口 8080)
npm run dev:h5
# 微信小程序:HBuilderX 打开或 npm run dev:mp-weixin
# App:HBuilderX 运行到模拟器/真机

# 构建
npm run build:h5
npm run build:mp-weixin
```

> 后端必须先跑起来(`../backend`,见根 README),且数据库里有账号(超管或用邀请码注册)。

## 关键点
- **鉴权**:JWT access + refresh。`utils/request.js` 在 401 时自动用 refresh_token 续期并重放,失败则跳登录页。token 存 `uni.storage`。
- **富文本阅读**:`<mp-html>` 渲染后端返回的 `content_html`(图片/音频/视频均支持),已在 `pages.json` easycom 注册。
- **资源 URL**:`config/resourceUrl()` 把后端的 `/uploads/xxx` 补成完整地址。
- **TabBar**:自定义组件 `components/TabBar.vue`(内联 SVG,暖色高亮),通过 `uni.reLaunch` 切换三个主页面。
- **登录守卫**:`App.vue` onLaunch 未登录即 `reLaunch` 到登录页;`mine` 页 onShow 复核。

## 与 pig-blog 的差异(重要)
pig-blog 后端用 `{code:0,data}` 信封;**yinyu 后端是 FastAPI 直接返回对象,错误为 `{code,detail}`**。所以 `utils/request.js` 是按 yinyu 重写的(2xx 直接 resolve `res.data`),不要照搬 pig-blog 的解析。
