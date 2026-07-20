# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

yinyu 是一个治愈系图文 App,提供极致私密、温暖治愈的精神角落。技术栈由用户敲定:
- **后端**:`backend/` — FastAPI(Python 3.12)+ PostgreSQL(async SQLAlchemy / asyncpg)+ Redis
- **Web 管理后台**:`web-admin/` — Vue 3 + Vite + Element Plus + **TipTap v3** 富文本(主力写作,图/音/视频)
- **App 客户端**:`app/` — uni-app (Vue3 + Vite),暖色治愈 UI(审美参考 `D:\code\pig-blog`)。阅读为主 + 轻量写作(图文/树洞)。已通过 `build:h5`。
- **文件存储**:本地 `/data/uploads/`,生产由 Nginx 直接代理 `/uploads/`
- **登录**:账号密码 + JWT(access + refresh)+ **邀请码注册**(封闭社区)
- **部署目标**:**宝塔面板(BT Panel)Linux 服务器**,**坚决不用 Docker**(PG/Redis/Nginx/Python 项目都走宝塔)

三大模块:
- **图文阅读**:多用户共创平台,任何登录用户均可发布;支持图/音/视频混排、标签筛选、点赞
- **树洞**:无列表、无标签、全量隐匿;仅凭 **6 位数字暗号**解锁单篇;暗号默认系统生成、可刷新、可自定义(全局唯一);Redis 限流防爆破
- **我的**:个人资料、我的图文、我的树洞、我点赞的图文

## 常用命令

后端在 conda 环境 `blogPigV312`(路径 `C:\Users\geekdx\.conda\envs\blogPigV312`)。bash 里用绝对路径调用(bash 命令的 cwd 不跨调用保留):

```bash
PY="/c/Users/geekdx/.conda/envs/blogPigV312/python.exe"

# 后端(必须先 cd 到 backend,否则找不到 app 包 / .env)
cd /d/code/yinyu/backend
cp .env.example .env            # 首次:填 DB / JWT_SECRET_KEY / 超管账密
"$PY" -m pip install -r requirements.txt
"$PY" -m alembic upgrade head   # 建表 / 迁移
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload   # 开发

# 语法/import 自检(不需要 DB)
"$PY" -m compileall -q app
DATABASE_URL="postgresql+asyncpg://u:p@127.0.0.1/db" DATABASE_URL_SYNC="postgresql://u:p@127.0.0.1/db" JWT_SECRET_KEY=x "$PY" -c "import app.main"

# 前端(web 后台)
cd /d/code/yinyu/web-admin
npm install
npm run dev      # :5173,自动代理 /api 与 /uploads 到后端 :8000
npm run build    # 生产构建到 dist/(部署到宝塔 /www/wwwroot/yinyu-admin)

# App 客户端(uni-app)
cd /d/code/yinyu/app
npm install
# 先改 src/config/index.js 的 SERVER_ORIGIN(H5 调试 127.0.0.1:8000;真机改局域网 IP;生产改域名)
npm run dev:h5       # H5,默认 :8080
npm run build:h5     # 编译验证;产物 dist/build/h5
# 小程序 / App 用 HBuilderX 或 npm run dev:mp-weixin / dev:app-android
```

- 后端启动会自动 bootstrap:建超管(见 `.env` 的 `SUPERADMIN_*`)+ 打印一个引导邀请码到控制台。
- 手动测 API:启动后访问 `http://localhost:8000/docs`(Swagger)。默认本地凭据:`yinyu/yinyu/yinyu`(user/pass/db),超管 `admin/admin123`。
- 没有 pytest 测试套件;端到端验证靠走通真实 PG+Redis 后调接口(参见本文件「关键坑」理解 async 用法)。

## 架构(大图景)

### Monorepo 分层
- `backend/app/`:`config.py`(pydantic-settings,读 `.env`)、`database.py`(async engine/session)、`redis_client.py`、`security.py`(pwdlib bcrypt + JWT)、`deps.py`(`get_current_user` / `require_admin`)、`startup.py`(首启 bootstrap)、`main.py`(装配 + dev 静态挂载)
- `backend/app/models/`:SQLAlchemy 2.0 `Mapped` 风格;`models/__init__.py` 集中导出(Alembic autogenerate 与应用都从这里感知全部表)
- `backend/app/schemas/`:Pydantic v2 入参/出参。**文章→ArticleBrief 的序列化集中在 `schemas/article.py` 的 `to_brief()` / `to_out()`**,所有路由复用,不要在新路由里重写映射
- `backend/app/api/`:`auth` / `articles` / `treehole` / `me` / `admin` / `upload`,在 `api/router.py` 聚合,统一挂 `/api/v1` 前缀
- `backend/app/core/`:`exceptions.py`(业务异常基类 `AppException` + 子类)、`ownership.py`(**通用 `get_owned(db, model, id, user, ...)`** —— 加载→404→作者或管理员放行,文章/树洞共用)
- `backend/app/services/`:`treehole_code.py`(暗号生成/校验/解锁限流)、`invite_code.py`(邀请码生成,admin+startup 共用)
- `backend/alembic/`:迁移。首版 `0001_initial.py` 手写 baseline(匹配模型);`env.py` 是 async 版,从 `settings.database_url` 取连接

### 数据模型(6 张业务表)
`users` / `invite_codes`(邀请码,max_uses 计数,注册时消耗)/ `articles`(含 `tags` PG ARRAY、status draft/published、view/like 计数)/ `article_likes`(user×article 唯一)/ `treeholes`(6 位 `code` 全局唯一、`author_id` 仅作者/管理员可见)/ `media`(上传记录)。计数(view/like)用原子 `UPDATE ... SET x = x + 1`,不读改写。

### 鉴权与权限
- 除 `register`/`login`/`refresh`/`treeholes/unlock` 外,所有接口需 `Authorization: Bearer <access_token>`。`get_current_user` 解 JWT;`require_admin` 加角色校验。
- **admin 路由**用 `APIRouter(dependencies=[Depends(require_admin)])` 路由级守卫;handler 内只取 `get_current_user`,**不要**再 `Depends(require_admin)`(会双重校验)。
- 资源归属:`get_owned(db, Model, id, user, not_found=, forbidden=)` 统一处理「作者本人或管理员」。

### 树洞(核心安全设计)
- **读者侧无任何集合接口**(无列表、无标签)。唯一入口 `POST /treeholes/unlock {code}`。
- 解锁返回 `TreeHolePublicOut`:**不含 author、不含 code**(全量隐匿);暗号无效与不存在回包一致(统一 `NotFound("暗号无效")`)。
- 限流在 `services/treehole_code.assert_unlock_allowed`:Redis 滑动窗口(默认 60s 内 10 次,超限锁 30min),**对错都计数**,防 6 位枚举。
- 作者可在 `me/treeholes` 看到自己写的(含 code)。

### 前端(web-admin)
- `src/api/request.js`:axios 实例,注入 Bearer token,401 时自动用 refresh token 续期并重放,失败跳登录。**响应拦截器直接返回 `resp.data`**,所以 API 封装拿到的是业务对象。
- `src/api/index.js`:按模块组织的 API 封装(注意 `auth.me` → `/me`,后端无 `/auth/me`)。
- `src/components/RichEditor.vue`:TipTap 编辑器。`src/components/tiptap/Audio.js`、`Video.js` 是自定义原子节点(`renderHTML` 输出真实 `<audio controls>`/`<video controls>`,编辑器内可见可播放;`parseHTML` 反解析保证回显)。图片走 `@tiptap/extension-image`。

## 关键坑(踩过、已修,务必遵守)

**后端(async SQLAlchemy + asyncpg)**
- ORM 批量自增 `update(Model).values(x = Model.x + 1)` **必须**加 `.execution_options(synchronize_session=False)`,然后**内存校正** `obj.x = (obj.x or 0) + 1` 再返回。否则默认 `synchronize_session='auto'` 会把会话内对象属性标记过期,async 下后续属性访问触发懒加载 → `MissingGreenlet`。
- **不要**开 `pool_pre_ping`(asyncpg 的 `do_ping` 同样触发 `MissingGreenlet`)。需要连接健康用 `pool_recycle`。
- PG 数组(ARRAY)按元素筛选用 `Column.any(value)`(生成 `value = ANY(col)`),**不要**用 `.contains([...])`(基础 ARRAY 未实现,会 500)。
- pydantic-settings 的 `List[str]` 字段若想接受逗号分隔或 `*`,必须用 `Annotated[List[str], NoDecode]` + `@field_validator(mode="before")` 切分;否则会被当 JSON 解析报错。
- `alembic.ini` 等 `.ini` **必须纯 ASCII**(Windows 中文系统 configparser 用 GBK 读,中文注释会炸)。

**前端(TipTap v3)**
- 很多扩展是**命名导出**(无 default),例如 `@tiptap/extension-text-style` 只能 `import { TextStyle }`。`@tiptap/starter-kit` **已内置 underline + link**(不要再单独装/导入,会重复注册)。

**App 客户端(uni-app)**
- `app/src/utils/request.js` 按 **yinyu 后端**重写:2xx 直接 `resolve(res.data)`(FastAPI 直返对象),**不要**照搬 pig-blog 的 `{code:0,data}` 信封解析。401 用 refresh_token 续期并重放一次,失败跳登录。
- 后端地址在 `app/src/config/index.js` 的 `SERVER_ORIGIN`(H5=127.0.0.1:8000;真机/小程序必须改局域网 IP 且同网段;生产改域名)。换环境只改这一处。
- 富文本阅读用 `<mp-html>`(`pages.json` easycom 已注册),渲染 `content_html` 里的图/音/视频。
- TabBar 是自定义组件 `components/TabBar.vue`(内联 SVG),三主页用 `uni.reLaunch` 切换;写作经首页 FAB 进入 `pages/write`。
- @dcloudio 包用固定 alpha 版本 `3.0.0-5000720260410001`(与 pig-blog 对齐,已知可装可编译)。

## dev 与生产差异
- 开发期 `main.py` 在 `APP_ENV=dev` 时挂 `/uploads` 静态(`StaticFiles`),前端能直接预览上传文件;**生产由 Nginx 直接 alias `/data/uploads/`**,不走 Python。`.env` 的 `UPLOAD_DIR` 在 Windows dev 下用相对路径(如 `./_uploads`)避开 `/data/uploads` 在 Windows 的路径问题。

## 详细部署
见 `README.md`(宝塔面板:软件商店装 PG/Redis/Nginx/Python 项目管理器 → 建 `yinyu` 库 → 上传代码 → Python 项目管理器跑 `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4` → `alembic upgrade head` → `web-admin/dist` 上传到 `/www/wwwroot/yinyu-admin` → Nginx 三段:`/api/` 反代、`/uploads/` 直连磁盘、`/` 指向前端)。
