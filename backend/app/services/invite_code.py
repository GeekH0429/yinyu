"""邀请码生成(admin 后台 + 首启引导共用)。"""
import secrets
import string

# 大写字母 + 数字,避开易混淆字符(0/O、1/I)可后续精简;此处保持简单
_ALPHABET = string.ascii_uppercase + string.digits
INVITE_CODE_LENGTH = 8


def generate_invite_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(INVITE_CODE_LENGTH))
