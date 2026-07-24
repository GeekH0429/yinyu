"""自定义异常与统一错误响应。"""
import logging

from fastapi import HTTPException, status

_logger = logging.getLogger("yinyu.exceptions")


class AppException(HTTPException):
    """业务异常基类,携带可读 code。

    抛出时记录 WARNING 级日志(4xx 量大,不上 ERROR,避免噪音)。
    子类调用 super().__init__ 即可受益,无需重复 logging。
    """

    def __init__(self, status_code: int, detail: str, code: str = "error"):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        _logger.warning(
            "app_exception",
            extra={
                "status_code": status_code,
                "code": code,
                "detail": detail,
            },
        )


class BadRequest(AppException):
    def __init__(self, detail: str, code: str = "bad_request"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, code)


class Unauthorized(AppException):
    def __init__(self, detail: str = "未授权", code: str = "unauthorized"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, code)


class Forbidden(AppException):
    def __init__(self, detail: str = "无权限", code: str = "forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail, code)


class NotFound(AppException):
    def __init__(self, detail: str = "资源不存在", code: str = "not_found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail, code)


class Conflict(AppException):
    def __init__(self, detail: str, code: str = "conflict"):
        super().__init__(status.HTTP_409_CONFLICT, detail, code)


class TooManyRequests(AppException):
    def __init__(self, detail: str = "请求过于频繁,请稍后再试", code: str = "rate_limited"):
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, detail, code)
