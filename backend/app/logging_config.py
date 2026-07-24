"""结构化日志配置。

简单 KV 格式,不引入第三方依赖(python-json-logger 暂不必要):

    2024-01-01T12:00:00+08:00 level=INFO logger=yinyu.xxx msg="..."
    2024-01-01T12:00:01+08:00 level=ERROR logger=yinyu.view_flusher msg="..." exc="..."

所有业务日志统一走 `yinyu` 命名空间,使用方式:

    import logging
    logger = logging.getLogger("yinyu.<module>")
"""
import logging
from datetime import datetime

from app.config import settings

LOG_NAMESPACE = "yinyu"


class KVFormatter(logging.Formatter):
    """单行 KV 格式化器。

    特殊字段:level / logger / msg / exc。其余通过 `extra=` 传入的字段
    会被附加到日志记录的 custom_attrs 中,顺序输出。
    """

    # 排除 logging 默认注入但本格式化器不关心的字段
    _RESERVED = {"name", "msg", "args", "levelname", "levelno", "pathname",
                 "filename", "module", "exc_info", "exc_text", "stack_info",
                 "lineno", "funcName", "created", "msecs", "relativeCreated",
                 "thread", "threadName", "processName", "process", "message",
                 "asctime", "taskName"}

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).isoformat(timespec="seconds")
        parts = [
            f"time={ts}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f'msg={self._quote(record.getMessage())}',
        ]
        # 附加 extra 字段
        for key, value in record.__dict__.items():
            if key in self._RESERVED or key.startswith("_"):
                continue
            parts.append(f"{key}={self._quote(value)}")
        if record.exc_info:
            parts.append(f"exc={self._quote(self.formatException(record.exc_info))}")
        return " ".join(parts)

    @staticmethod
    def _quote(value) -> str:
        """空格、=、引号、中文等多字节字符均加引号转义。"""
        text = str(value)
        if text == "":
            return '""'
        needs_quote = any(c in text for c in (" ", "=", '"', "\n", "\r", "\t"))
        if needs_quote:
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return text


def setup_logging() -> None:
    """配置 yinyu 命名空间日志。

    - dev: DEBUG
    - 其他: INFO
    幂等:重复调用不会重复添加 handler。
    """
    level = logging.DEBUG if settings.is_dev else logging.INFO
    root_logger = logging.getLogger(LOG_NAMESPACE)
    root_logger.setLevel(level)
    # 幂等保护
    if getattr(root_logger, "_yinyu_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(KVFormatter())
    root_logger.addHandler(handler)
    root_logger.propagate = False  # 避免 root logger 重复打印
    root_logger._yinyu_configured = True  # type: ignore[attr-defined]
