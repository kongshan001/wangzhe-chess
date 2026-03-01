"""
王者之奕 - 消息编解码器

本模块提供 WebSocket 消息的编解码功能：
- JSON 序列化/反序列化
- 消息类型注册
- 消息验证
- 消息压缩（可选）
"""

from __future__ import annotations

import json
import time
from typing import Any, TypeVar, cast

from pydantic import ValidationError

from .messages import (
    MESSAGE_CLASS_MAP,
    BaseMessage,
    ErrorMessage,
    MessageType,
)

# 泛型类型变量
T = TypeVar("T", bound=BaseMessage)


class MessageCodecError(Exception):
    """消息编解码错误"""

    def __init__(self, message: str, code: int = 0, details: dict[str, Any] | None = None) -> None:
        """
        初始化错误

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}


class MessageEncoder:
    """
    消息编码器

    负责将消息对象序列化为 JSON 字符串。

    使用方式:
        encoder = MessageEncoder()
        json_str = encoder.encode(message)
    """

    def __init__(self, *, indent: int | None = None, ensure_ascii: bool = False) -> None:
        """
        初始化编码器

        Args:
            indent: JSON 缩进（None 表示紧凑格式）
            ensure_ascii: 是否转义非 ASCII 字符
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def encode(self, message: BaseMessage) -> str:
        """
        编码消息为 JSON 字符串

        Args:
            message: 消息对象

        Returns:
            JSON 字符串

        Raises:
            MessageCodecError: 编码失败
        """
        try:
            # 自动设置时间戳
            if message.timestamp is None:
                message.timestamp = int(time.time() * 1000)

            # 使用 Pydantic 的 model_dump 转换为字典
            data = message.model_dump(mode="json", exclude_none=True)

            # 序列化为 JSON
            return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)

        except Exception as e:
            raise MessageCodecError(
                f"编码消息失败: {e}",
                code=1001,
                details={"message_type": str(message.type) if message else None},
            ) from e

    def encode_to_bytes(self, message: BaseMessage) -> bytes:
        """
        编码消息为字节

        Args:
            message: 消息对象

        Returns:
            UTF-8 编码的字节
        """
        return self.encode(message).encode("utf-8")


class MessageDecoder:
    """
    消息解码器

    负责将 JSON 字符串反序列化为消息对象。

    使用方式:
        decoder = MessageDecoder()
        message = decoder.decode(json_str)
    """

    def __init__(self, *, strict: bool = True) -> None:
        """
        初始化解码器

        Args:
            strict: 是否严格模式（严格模式下会验证所有字段）
        """
        self.strict = strict

    def decode(self, data: str | bytes | dict[str, Any]) -> BaseMessage:
        """
        解码 JSON 数据为消息对象

        Args:
            data: JSON 字符串、字节或字典

        Returns:
            消息对象

        Raises:
            MessageCodecError: 解码失败
        """
        try:
            # 处理不同输入类型
            if isinstance(data, bytes):
                data = data.decode("utf-8")

            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                raise MessageCodecError("消息数据必须是字典或 JSON 字符串", code=1002)

            # 获取消息类型
            type_value = data.get("type")
            if type_value is None:
                raise MessageCodecError("消息缺少 type 字段", code=1003)

            # 解析消息类型
            try:
                message_type = MessageType(type_value)
            except ValueError:
                raise MessageCodecError(
                    f"未知的消息类型: {type_value}", code=1004, details={"type": type_value}
                ) from None

            # 获取对应的消息类
            message_class = MESSAGE_CLASS_MAP.get(message_type)
            if message_class is None:
                raise MessageCodecError(
                    f"消息类型未注册: {message_type}", code=1005, details={"type": type_value}
                ) from None

            # 使用 Pydantic 解析
            return message_class.model_validate(data)

        except MessageCodecError:
            raise
        except ValidationError as e:
            raise MessageCodecError(
                f"消息验证失败: {e}", code=1006, details={"validation_errors": e.errors()}
            ) from e
        except json.JSONDecodeError as e:
            raise MessageCodecError(
                f"JSON 解析失败: {e}", code=1007, details={"position": e.pos, "message": e.msg}
            ) from e
        except Exception as e:
            raise MessageCodecError(f"解码消息失败: {e}", code=1000) from e

    def decode_as(self, data: str | bytes | dict[str, Any], message_class: type[T]) -> T:
        """
        解码为指定类型的消息

        Args:
            data: JSON 数据
            message_class: 目标消息类

        Returns:
            指定类型的消息对象

        Raises:
            MessageCodecError: 解码失败
        """
        message = self.decode(data)
        if not isinstance(message, message_class):
            raise MessageCodecError(
                f"消息类型不匹配: 期望 {message_class.__name__}, 实际 {type(message).__name__}",
                code=1008,
            )
        return cast(T, message)


class MessageCodec:
    """
    消息编解码器

    组合编码器和解码器，提供完整的编解码功能。

    使用方式:
        codec = MessageCodec()

        # 编码
        json_str = codec.encode(message)

        # 解码
        message = codec.decode(json_str)
    """

    def __init__(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = False,
        strict: bool = True,
    ) -> None:
        """
        初始化编解码器

        Args:
            indent: JSON 缩进
            ensure_ascii: 是否转义非 ASCII 字符
            strict: 是否严格模式
        """
        self.encoder = MessageEncoder(indent=indent, ensure_ascii=ensure_ascii)
        self.decoder = MessageDecoder(strict=strict)

    def encode(self, message: BaseMessage) -> str:
        """
        编码消息

        Args:
            message: 消息对象

        Returns:
            JSON 字符串
        """
        return self.encoder.encode(message)

    def encode_to_bytes(self, message: BaseMessage) -> bytes:
        """
        编码消息为字节

        Args:
            message: 消息对象

        Returns:
            UTF-8 编码的字节
        """
        return self.encoder.encode_to_bytes(message)

    def decode(self, data: str | bytes | dict[str, Any]) -> BaseMessage:
        """
        解码消息

        Args:
            data: JSON 数据

        Returns:
            消息对象
        """
        return self.decoder.decode(data)

    def decode_as(self, data: str | bytes | dict[str, Any], message_class: type[T]) -> T:
        """
        解码为指定类型的消息

        Args:
            data: JSON 数据
            message_class: 目标消息类

        Returns:
            指定类型的消息对象
        """
        return self.decoder.decode_as(data, message_class)


# ============================================================================
# 全局编解码器实例
# ============================================================================

# 默认编解码器（紧凑格式）
default_codec = MessageCodec()

# 调试编解码器（带缩进，便于阅读）
debug_codec = MessageCodec(indent=2)


# ============================================================================
# 便捷函数
# ============================================================================


def encode_message(message: BaseMessage, *, debug: bool = False) -> str:
    """
    编码消息（便捷函数）

    Args:
        message: 消息对象
        debug: 是否使用调试模式（带缩进）

    Returns:
        JSON 字符串
    """
    codec = debug_codec if debug else default_codec
    return codec.encode(message)


def decode_message(data: str | bytes | dict[str, Any]) -> BaseMessage:
    """
    解码消息（便捷函数）

    Args:
        data: JSON 数据

    Returns:
        消息对象
    """
    return default_codec.decode(data)


def create_error_message(
    code: int,
    message: str,
    details: dict[str, Any] | None = None,
    seq: int | None = None,
) -> ErrorMessage:
    """
    创建错误消息（便捷函数）

    Args:
        code: 错误码
        message: 错误描述
        details: 错误详情
        seq: 消息序列号

    Returns:
        错误消息对象
    """
    return ErrorMessage(
        code=code,
        message=message,
        details=details,
        seq=seq,
    )


# ============================================================================
# 消息类型注册（扩展用）
# ============================================================================


def register_message_type(message_type: MessageType, message_class: type[BaseMessage]) -> None:
    """
    注册消息类型

    用于扩展自定义消息类型。

    Args:
        message_type: 消息类型
        message_class: 消息类

    Raises:
        MessageCodecError: 类型已注册
    """
    if message_type in MESSAGE_CLASS_MAP:
        raise MessageCodecError(f"消息类型已注册: {message_type}", code=1009)
    MESSAGE_CLASS_MAP[message_type] = message_class


def unregister_message_type(message_type: MessageType) -> bool:
    """
    注销消息类型

    Args:
        message_type: 消息类型

    Returns:
        是否成功注销
    """
    if message_type in MESSAGE_CLASS_MAP:
        del MESSAGE_CLASS_MAP[message_type]
        return True
    return False


def get_message_class(message_type: MessageType) -> type[BaseMessage] | None:
    """
    获取消息类型对应的类

    Args:
        message_type: 消息类型

    Returns:
        消息类，如果未注册返回 None
    """
    return MESSAGE_CLASS_MAP.get(message_type)


def is_message_type_registered(message_type: MessageType) -> bool:
    """
    检查消息类型是否已注册

    Args:
        message_type: 消息类型

    Returns:
        是否已注册
    """
    return message_type in MESSAGE_CLASS_MAP


# ============================================================================
# 消息验证工具
# ============================================================================


def validate_message_type(type_str: str) -> MessageType:
    """
    验证并转换消息类型字符串

    Args:
        type_str: 消息类型字符串

    Returns:
        消息类型枚举值

    Raises:
        MessageCodecError: 无效的消息类型
    """
    try:
        return MessageType(type_str)
    except ValueError:
        raise MessageCodecError(
            f"无效的消息类型: {type_str}", code=1004, details={"type": type_str}
        ) from None


def is_valid_message(data: dict[str, Any]) -> bool:
    """
    检查数据是否是有效的消息格式

    Args:
        data: 待检查的数据

    Returns:
        是否有效
    """
    if not isinstance(data, dict):
        return False

    if "type" not in data:
        return False

    try:
        message_type = MessageType(data["type"])
        message_class = MESSAGE_CLASS_MAP.get(message_type)
        if message_class is None:
            return False
        message_class.model_validate(data)
        return True
    except Exception:
        return False
