"""
王者之奕 - 回放系统模块

本模块提供回放系统的核心功能：
- 保存对局回放
- 播放回放（支持倍速、跳转）
- 分享和导入回放

主要组件：
- ReplayManager: 回放管理器
- Replay: 回放数据
- ReplayFrame: 回放帧
- ReplaySession: 播放会话
"""

from .manager import (
    MAX_REPLAYS_PER_PLAYER,
    ReplayManager,
    get_replay_manager,
    init_replay_manager,
)
from .models import (
    PlayerSnapshot,
    PlaySpeed,
    Replay,
    ReplayFrame,
    ReplayListItem,
    ReplayMetadata,
    ReplaySession,
    ReplayStatus,
)
from .ws_handler import (
    ReplayWSHandler,
    replay_ws_handler,
)

__all__ = [
    # 数据类
    "PlaySpeed",
    "PlayerSnapshot",
    "Replay",
    "ReplayFrame",
    "ReplayListItem",
    "ReplayMetadata",
    "ReplaySession",
    "ReplayStatus",
    # 管理器
    "ReplayManager",
    "get_replay_manager",
    "init_replay_manager",
    # WebSocket 处理器
    "ReplayWSHandler",
    "replay_ws_handler",
    # 常量
    "MAX_REPLAYS_PER_PLAYER",
]
