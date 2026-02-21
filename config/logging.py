"""
王者之奕 - 日志配置模块
=======================

提供结构化日志配置，支持：
- JSON 格式输出（生产环境）
- 彩色文本输出（开发环境）
- 日志轮转
- 多目标输出（文件、控制台）
- 请求追踪
- 性能日志

使用方式：
    from config.logging import setup_logging, get_logger
    
    # 初始化日志
    setup_logging()
    
    # 获取 logger
    logger = get_logger(__name__)
    logger.info("服务启动", extra={"port": 8000})
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, Processor, WrappedLogger

from config.settings import settings


# =============================================================================
# 上下文变量（请求追踪）
# =============================================================================
# 请求 ID 上下文变量，用于追踪单个请求
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


# =============================================================================
# 自定义处理器
# =============================================================================
def add_request_id(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    添加请求 ID 到日志记录
    
    如果当前上下文中存在请求 ID，将其添加到日志记录中，
    便于追踪单个请求的完整生命周期。
    """
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def add_timestamp(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    添加 ISO 格式时间戳
    
    使用 UTC 时间，确保日志时间在不同时区间一致。
    """
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_service_info(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    添加服务信息
    
    包括服务名称、版本、环境等元数据。
    """
    event_dict["service"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.APP_ENV
    return event_dict


def drop_color_message_key(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    移除颜色消息键
    
    在 JSON 输出中移除颜色代码，避免日志污染。
    """
    event_dict.pop("color_message", None)
    return event_dict


def rename_event_to_message(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    将 'event' 字段重命名为 'message'
    
    保持与标准日志格式的兼容性。
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def extract_from_record(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    从标准 logging 记录中提取额外信息
    
    包括文件名、行号、函数名等调试信息。
    """
    # 获取底层 logging 记录
    record = event_dict.get("_record")
    if record:
        event_dict["file"] = record.filename
        event_dict["line"] = record.lineno
        event_dict["function"] = record.funcName
        event_dict["module"] = record.module
    return event_dict


# =============================================================================
# 日志格式化器
# =============================================================================
class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器
    
    将日志记录格式化为 JSON，便于日志收集系统（如 ELK）解析。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # 使用 structlog 的 JSON 渲染
        import json
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """
    彩色文本格式化器
    
    在终端中输出带颜色的日志，便于开发调试。
    """
    
    # 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为彩色文本"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # 构建消息
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = f"{color}{record.levelname:8}{self.RESET}"
        message = record.getMessage()
        
        # 基础格式
        formatted = f"{timestamp} | {level} | {record.name} | {message}"
        
        # 添加请求 ID
        request_id = request_id_var.get()
        if request_id:
            formatted = f"[{request_id[:8]}] {formatted}"
        
        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


# =============================================================================
# 日志配置
# =============================================================================
def get_processors(json_format: bool = False) -> list[Processor]:
    """
    获取日志处理器链
    
    Args:
        json_format: 是否使用 JSON 格式
    
    Returns:
        处理器列表
    """
    processors: list[Processor] = [
        # 添加上下文信息
        structlog.contextvars.merge_contextvars,
        add_request_id,
        add_timestamp,
        add_service_info,
        # 标准化日志级别
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # 提取记录信息
        structlog.stdlib.PositionalArgumentsFormatter(),
        # 处理异常
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        # JSON 输出处理器
        processors.extend([
            rename_event_to_message,
            drop_color_message_key,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ])
    else:
        # 控制台输出处理器
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    return processors


def setup_logging() -> None:
    """
    配置应用日志
    
    根据运行环境配置不同的日志格式：
    - 生产环境：JSON 格式，输出到文件和控制台
    - 开发环境：彩色文本，输出到控制台
    """
    # 获取日志配置
    log_level = getattr(logging, settings.logging.LEVEL.upper(), logging.INFO)
    json_format = settings.logging.FORMAT.lower() == "json" or settings.is_production
    
    # 配置 structlog
    structlog.configure(
        processors=get_processors(json_format=json_format),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准 logging
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果配置了日志文件）
    if settings.logging.FILE and not settings.is_development:
        log_file = Path(settings.logging.FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 RotatingFileHandler 实现日志轮转
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=settings.logging.MAX_SIZE * 1024 * 1024,  # MB to bytes
            backupCount=settings.logging.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())  # 文件始终使用 JSON 格式
        root_logger.addHandler(file_handler)
    
    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.database.ECHO else logging.WARNING
    )
    logging.getLogger("aiomysql").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 记录日志配置完成
    logger = get_logger(__name__)
    logger.info(
        "日志系统初始化完成",
        extra={
            "level": settings.logging.LEVEL,
            "format": settings.logging.FORMAT,
            "file": settings.logging.FILE,
        }
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    获取 structlog 日志器
    
    Args:
        name: 日志器名称（通常使用 __name__）
    
    Returns:
        配置好的 structlog 日志器
    
    使用示例：
        logger = get_logger(__name__)
        logger.info("消息", extra={"key": "value"})
    """
    return structlog.get_logger(name)


# =============================================================================
# 性能日志装饰器
# =============================================================================
import functools
import time
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def log_performance(
    logger: structlog.stdlib.BoundLogger | None = None,
    level: str = "debug",
) -> Callable[[F], F]:
    """
    性能日志装饰器
    
    记录函数执行时间，用于性能分析。
    
    Args:
        logger: 日志器实例
        level: 日志级别
    
    使用示例：
        @log_performance()
        def slow_function():
            time.sleep(1)
        
        @log_performance(level="info")
        def important_function():
            return "result"
    """
    def decorator(func: F) -> F:
        _logger = logger or get_logger(func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                getattr(_logger, level)(
                    "函数执行完成",
                    extra={
                        "function": func.__qualname__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success",
                    }
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.error(
                    "函数执行失败",
                    extra={
                        "function": func.__qualname__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "error": str(e),
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                getattr(_logger, level)(
                    "函数执行完成",
                    extra={
                        "function": func.__qualname__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success",
                    }
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.error(
                    "函数执行失败",
                    extra={
                        "function": func.__qualname__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "error": str(e),
                    }
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


# =============================================================================
# 请求日志中间件工具
# =============================================================================
def set_request_id(request_id: str) -> None:
    """
    设置当前请求 ID
    
    在请求开始时调用，用于追踪请求。
    """
    request_id_var.set(request_id)


def clear_request_id() -> None:
    """
    清除当前请求 ID
    
    在请求结束时调用。
    """
    request_id_var.set(None)


def get_request_id() -> str | None:
    """
    获取当前请求 ID
    """
    return request_id_var.get()


# =============================================================================
# 日志上下文管理
# =============================================================================
class LogContext:
    """
    日志上下文管理器
    
    绑定额外的上下文信息到日志记录中。
    
    使用示例：
        with LogContext(user_id="123", action="login"):
            logger.info("用户登录")
    """
    
    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs
        self._token: Any = None
    
    def __enter__(self) -> "LogContext":
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, *args: Any) -> None:
        if self._token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


# =============================================================================
# 导出
# =============================================================================
__all__ = [
    "setup_logging",
    "get_logger",
    "log_performance",
    "set_request_id",
    "clear_request_id",
    "get_request_id",
    "LogContext",
    "request_id_var",
]
