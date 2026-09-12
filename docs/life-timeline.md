# 人生时光轴:实现约定与已踩坑

> 改动 `app/src/utils/lifeTimeline.js` / `app/src/pages/life/index.vue` / `/me/life*` 接口前,先通读本文件。

- 移植自 lifetime-visualization:「我的」入口,纯个人私密页(无他人可见入口,同树洞理念)。
- `users.birthday/lifespan_years` + `life_milestones`(label/color/start/end/site/images);**默认学制节点(童年→大学,9 月入学推算)不入库**——App 端 `utils/lifeTimeline.js` 按生日纯函数推算,改生日零成本重算;仅自定义节点走 `/me/life/milestones` CRUD。
- `GET /me/life` 一次聚合:设置 + 节点 + 胶囊落点(只回 unlock_at/title,**content 服务端强制不下发**)+ 写作足迹(published_at+标题)。
- 格子墙**必须 canvas 窗口化渲染**(`utils/lifeTimeline.js` + `pages/life/index.vue`):日粒度 2.9 万格,view 循环必卡且画布高度受限;canvas 固定可视高,透明 scroll-view(占位 view 撑总高)叠在上层接管滚动手势,scroll 事件节流重绘窗口;tap 命中用 e.detail 坐标反算格子索引。定位今天用独立的 `jumpTop` 绑 `:scroll-top`(**不能**直接绑滚动状态 scrollTop——滚动回写绑定量会在 iOS 打断惯性滚动)。单位/视角偏好存本地 storage(`life_unit` / `life_view_mode`)。
- drawGrid 是性能敏感路径(日粒度窗口约 5-6 千格),优化手段缺一不可:①节点覆盖**预转 int 索引区间**(`cellIndexOf`),绘制时不做 Date 区间过滤;②**行内同色段合并**(连续同色格一个 fillRect,命令数降一个数量级);③段合并会盖掉格间 gap,需**贯穿式补线恢复点阵视觉**——已过区在每列 gap 中心画背景色宽线(窗口顶→今天行底,一条 path),未来区画淡棕细线(今天行→窗口底,从 todayCol+1 起防穿色),月/年大格子(cellPx≥10)未来格保持逐格描边不合并;④标记点遍历 Map(条目=胶囊/文章数)而非全窗口扫描;⑤**位移不足一行且数据未变跳过重绘**(`lastDrawnTop`/`gridDirty`,这两个状态在 `pages/life/index.vue`,layout 后置 dirty)。日/周 gap 占比要足够(cell 4/gap 2、cell 8/gap 3),太小点阵感不可见。若真机(老 canvas API 跨层通信)仍卡,下一步方案是 renderjs + `type="2d"` canvas 在视图层本地绘制。
- 两个已踩的绘制坑:**`setFillStyle(undefined)` 会画出黑色**(非标准 canvas 忽略无效值的行为,uni 老 API 模拟层直接落成黑)——两节点叠加分半绘制时 `colors[1]` 可能 undefined,必须先判长度;**格子墙容器不能自带 border**——`boundingClientRect` 含边框,canvas 按它定尺寸会溢出内容区 ~1px,H5 下 scroll-view 底部冒横向滚动条(黑线),边框放外层 `.grid-frame`、`#gridArea` 做纯测量层。另:uni-canvas **首帧异步初始化**(loading 态挂载/尺寸 0→W 变化/display:none 恢复)时立即 `draw()` 会落空——首屏空白、滚动才出格子;measure 与切回总览后都要 `gridDirty=true` 立即画一次 + 120ms 延时补画一次,canvas 隐藏(日历视角)时 drawGrid 直接 return。
- 日粒度双视角:**总览**(canvas 格子墙)与**日历**(月历 view 渲染,一次一个月,周一开头,箭头/左右滑动翻页,clamp 在 [生日月, 寿命终点月],「回到今天」);月历每月仅 42 格故用 view 即可,与总览互斥时 canvas 用 v-show 藏(不销毁画布)。滑动翻页用 **swiper 三页循环**([上月,当月,下月],change 后内容移位+归位中间页):归位必须**两步赋值**——先把 `current` 同步成 `e.detail.current`(1→0/2 产生变化),nextTick 内容移位后再赋回 1;直接赋 1 是同值赋值,Vue 不触发更新,swiper 不归位。
- 人生进度卡:`utils/lifeCard.js` 平行实现同款 canvas 绘制(不 import quoteCard),保存/分享直接用 quoteCard 的 `saveQuoteCard`/`shareQuoteCard`。
