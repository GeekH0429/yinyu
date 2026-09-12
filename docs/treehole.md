# 树洞:核心安全设计

> 改动树洞相关代码前后端/客户端任何一侧前,先通读本清单。

- **读者侧无任何集合接口**(无列表、无标签)。唯一入口 `POST /treeholes/unlock {code}`。
- 解锁返回 `TreeHolePublicOut`:**不含 author、不含 code**(全量隐匿);暗号无效与不存在回包一致(统一 `NotFound("暗号无效")`)。
- 限流在 `services/treehole_code.assert_unlock_allowed`:Redis 滑动窗口(默认 60s 内 10 次,超限锁 30min),**对错都计数**,防 6 位枚举。
- 作者可在 `me/treeholes` 看到自己写的(含 code)。
- **回音**:解锁响应带 30 分钟 `echo_token`(Redis 绑定树洞 id);`POST /treeholes/echo` 只认 token 不认裸 id(防枚举刷通知),message 必须命中 `services/treehole_echo.py` 的预设白名单;一人一洞一枚可改;作者收匿名通知(actor 空),`GET /me/treeholes/{id}/echoes` 查看。
