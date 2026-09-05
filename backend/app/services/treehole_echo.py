"""树洞回音:预设短句白名单 + 解锁回音令牌。

安全模型:
    - 回音接口只认 echo_token(解锁成功时签发,Redis 短时效绑定树洞 id),
      不接受裸 treehole_id —— 否则登录用户可枚举 id 给任意树洞塞回音/通知。
    - message 必须命中预设白名单:无自由文本,从源头杜绝骚扰与身份推理。
"""
import secrets

from redis.asyncio import Redis

# 预设回音短句(前后端各自维护同一份;新增时两边同步)
ECHO_PRESETS = ["我听见了", "抱抱你", "我也曾这样", "会好的", "陪你到天亮"]

_TOKEN_TTL = 30 * 60  # 解锁后 30 分钟内可回音
_TOKEN_PREFIX = "th:echo:"


async def grant_echo_token(redis: Redis, treehole_id: int) -> str:
    """解锁成功时签发回音令牌(随机,Redis 绑定树洞 id,30 分钟有效)。"""
    token = secrets.token_hex(16)
    await redis.setex(_TOKEN_PREFIX + token, _TOKEN_TTL, str(treehole_id))
    return token


async def resolve_echo_token(redis: Redis, token: str) -> int | None:
    """校验回音令牌,返回树洞 id;无效/过期返回 None。"""
    raw = await redis.get(_TOKEN_PREFIX + token)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None
