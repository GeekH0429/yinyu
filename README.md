# yinyu · 治愈系图文 App

> 一个极致私密、温暖治愈的精神角落。图文阅读 + 树洞(暗号解锁)+ 我的,配套 Web 写作后台。

## 整体架构

```
yinyu/
├── backend/        # FastAPI 后端(Python 3.12 / miniconda: blogPigV312)
│   ├── app/        # 配置 / 模型 / schema / 路由 / 服务
│   ├── alembic/    # 数据库迁移
│   ├── requirements.txt
│   └── .env.example
├── web-admin/      # Web 管理后台(Vue 3 + Vite + Element Plus + TipTap)
├── app/            # uni-app 客户端(阅读为主 + 轻量写作,暖色治愈 UI)
├── nginx/          # 部署用 Nginx 配置
├── CLAUDE.md       # 给 Claude Code 的工程指引
└── README.md
```

技术栈:PostgreSQL + Redis + FastAPI(异步 SQLAlchemy + asyncpg),本地文件存储 `/data/uploads/`,Nginx 直接代理静态文件。三个前端共用同一套后端 API:Web 后台(TipTap 富文本写作)、App(uni-app 阅读 + 轻量写作)。

## 三大模块

| 模块 | 说明 |
|------|------|
| 图文阅读 | 多用户共创:登录用户均可发布;支持图片/音频/视频混排;公共 feed + 标签筛选 |
| 树洞 | 无列表、无标签、全量隐匿;仅凭 **6 位数字暗号**解锁单篇;暗号默认系统生成,可刷新、可自定义;Redis 限流防爆破 |
| 我的 | 个人资料、我发布的图文、我的树洞、我点赞的图文、改密 |

写作主力在 **Web 管理后台**(富文本编辑器,支持图/音/视频);App 端以**阅读**为主,保留**轻量写作**(纯文本+图片/音频)。

---

## 后端本地启动

### 1. 准备依赖(PostgreSQL / Redis)

```bash
# PostgreSQL: 创建库与用户
sudo -u postgres psql -c "CREATE USER yinyu WITH PASSWORD 'yinyu';"
sudo -u postgres psql -c "CREATE DATABASE yinyu OWNER yinyu;"

# Redis: 启动即可(默认 6379)
redis-server
```

### 2. 激活 conda 环境并安装依赖

```bash
conda activate blogPigV312
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env:数据库连接、JWT_SECRET_KEY、初始超管账号密码等
# 生成强随机密钥: openssl rand -hex 32
```

### 4. 初始化数据库

```bash
# 执行迁移(创建全部表)
alembic upgrade head
```

### 5. 启动

```bash
uvicorn app.main:app --reload --port 8000
```

- 启动时自动初始化:超管账号(见 `.env`)、首个引导邀请码(打印到控制台,`max_uses=10`)
- Swagger 文档:http://localhost:8000/docs
- 健康检查:http://localhost:8000/health

---

## API 概览(前缀 `/api/v1`)

### 认证
- `POST /auth/register` 注册(**需邀请码**)
- `POST /auth/login` 登录 → 返回 access/refresh token
- `POST /auth/refresh` 刷新 token
- `PUT  /auth/password` 改密

### 图文阅读
- `GET  /articles` 公共 feed(已发布,支持 `tag`、`keyword`、分页)
- `GET  /articles/tags` 所有标签
- `GET  /articles/{id}` 详情(浏览量自增)
- `POST /articles` 新建(登录)
- `PUT  /articles/{id}` 更新(作者/管理员)
- `DELETE /articles/{id}` 删除(作者/管理员)
- `POST /articles/{id}/like` 点赞/取消

### 树洞
- `POST /treeholes/unlock` 凭 6 位暗号解锁单篇(**限流**)
- `POST /treeholes` 创建(默认随机暗号;传 `code` 则自定义)
- `PUT  /treeholes/{id}` 编辑内容/标题/启用状态
- `PUT  /treeholes/{id}/code` 刷新随机 / 自定义暗号(`code=null` 刷新)
- `DELETE /treeholes/{id}` 删除

### 我的(`/me`)
- `GET /me` 个人资料 · `PUT /me` 更新资料
- `GET /me/articles` 我的图文(可按 `status` 过滤)
- `GET /me/treeholes` 我的树洞(含暗号)
- `GET /me/likes` 我点赞的图文

### 上传
- `POST /upload` 上传图片/音频/视频,返回 `/uploads/...` URL

### 管理后台(`/admin`,需管理员)
- `POST /admin/invite-codes` 批量生成邀请码
- `GET  /admin/invite-codes` · `GET /admin/users` · `PATCH /admin/users/{id}`
- `GET  /admin/articles` · `GET /admin/treeholes` · `DELETE /admin/treeholes/{id}`

> 鉴权:除注册/登录/刷新/解锁外,所有接口需在请求头携带 `Authorization: Bearer <access_token>`。

---

## Web 管理后台启动

```bash
cd web-admin
npm install
npm run dev      # 开发:http://localhost:5173 (自动代理 /api、/uploads 到后端 8000)
npm run build    # 生产构建到 dist/ (部署时拷到 Nginx 的 /www/wwwroot/yinyu-admin)
```

- 用超管账号或任意有邀请码注册的账号登录
- 富文本编辑器(**TipTap**):工具栏支持图片 / 音频 / 视频上传(自定义 Audio/Video 节点 + Image 扩展),正文以 HTML 存库,App 端用 mp-html 渲染
- 管理员可见额外菜单:树洞管理 / 用户管理 / 邀请码

## App 客户端启动(uni-app)

详见 [`app/README.md`](app/README.md)。要点:

```bash
cd app
npm install
# 改 src/config/index.js 的 SERVER_ORIGIN:
#   H5 调试 -> http://127.0.0.1:8000
#   真机/小程序 -> 电脑局域网 IP(如 http://192.168.x.x:8000),且手机同网段
#   生产 -> https://你的域名
npm run dev:h5     # H5:http://localhost:8080
npm run build:h5   # 编译验证;微信小程序/App 用 HBuilderX 或 dev:mp-weixin / dev:app-android
```

- 页面:登录注册 / 图文 feed / 详情(mp-html)/ 树洞暗号解锁 / 轻量写作(图文/树洞 + 图音上传)/ 我的
- 自定义 TabBar(暖色 SVG),JWT 自动 refresh,`utils/request.js` 按 yinyu FastAPI 直返重写

## 安全要点

- **邀请码注册**:封闭社区,无邀请码不可注册
- **树洞暗号防爆破**:6 位共 100 万种;Redis 滑动窗口限流(默认 60s 内 10 次,超限锁定 30min),见 `.env` 中 `TREEHOLE_*`
- **暗号读者全量隐匿**:解锁返回内容不含作者、不含暗号;暗号无效与不存在的回包一致
- **JWT**:access(默认 60min)+ refresh(默认 30 天),密钥务必随机

---

## 部署(宝塔面板 Linux 服务器)

> 不使用 Docker。以下面向**宝塔面板(BT Panel)**流程,PostgreSQL / Redis / Nginx / Python 项目均在宝塔中安装管理。

### 1. 软件商店安装依赖
在宝塔「软件商店」安装:
- **PostgreSQL**(用宝塔的 PostgreSQL 管理器插件)
- **Redis**
- **Nginx**(通常自带)
- **Python 项目管理器**(用于托管 FastAPI)

### 2. 创建数据库
宝塔 → PostgreSQL 管理器 → 添加数据库:
- 库名 / 用户名 / 密码:`yinyu`(记下密码,稍后写进 `.env`)

### 3. 上传代码
把项目上传到 `/www/wwwroot/yinyu/`(后端代码即 `/www/wwwroot/yinyu/backend/`)。

### 4. 后端运行(Python 项目管理器)
宝塔 → Python 项目管理器 → 添加项目:
- 项目目录:`/www/wwwroot/yinyu/backend`
- Python 版本:`3.12`
- 框架:`FastAPI`(或通用)
- 启动命令:
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
  ```
- 安装依赖:`pip install -r requirements.txt`

随后在该项目目录里:
```bash
cp .env.example .env      # 编辑:DATABASE_URL/REDIS_URL/JWT_SECRET_KEY/超管账密
# 生成密钥:openssl rand -hex 32
alembic upgrade head      # 建表
```
> 首启会自动建超管并打印一个引导邀请码(看项目日志)。

### 5. 上传文件目录
```bash
mkdir -p /data/uploads && chown -R www:www /data/uploads
```
(若想放在网站目录,改 `.env` 的 `UPLOAD_DIR=/www/wwwroot/yinyu/uploads` 并同步改 Nginx。)

### 6. 前端构建与上传
- **Web 管理后台**:本地 `cd web-admin && npm run build`,把 `dist/` 上传到服务器 `/www/wwwroot/yinyu-admin/`。
- **App**:微信小程序 / App 用 HBuilderX 打包后发布;若出 H5 版,`cd app && npm run build:h5`,把 `dist/build/h5/` 上传到站点目录(记得先把 `app/src/config/index.js` 的 `SERVER_ORIGIN` 改成线上域名)。

### 7. Nginx 配置
宝塔 → 网站 → 添加站点(绑定域名)→ 设置 → 配置文件,参考 `nginx/yinyu.conf` 改写,关键三段:
- `/api/` 反代到 `http://127.0.0.1:8000`
- `/uploads/` 直接 `alias /data/uploads/`(不走 Python)
- `/` 指向 `/www/wwwroot/yinyu-admin`(`try_files $uri $uri/ /index.html`)
- `client_max_body_size 60m;`(允许上传)

Nginx 将 `/uploads/` 直接映射到磁盘目录,后端只负责写入,不参与静态下载。

---

## 后续路线

- [x] `backend/`:FastAPI 后端(已完成并通过验证)
- [x] `web-admin/`:Vue 3 + Vite + Element Plus + TipTap 写作后台(图/音/视频)
- [x] `app/`:uni-app 客户端(图文阅读 + 树洞暗号解锁 + 我的 + 轻量写作,暖色治愈 UI)
- [ ] 评论 / 收藏 / 搜索(全文)
- [ ] 定时清理孤立上传文件
