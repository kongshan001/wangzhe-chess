"""
王者之奕 - 观战系统

本模块提供观战功能的完整实现：
- 观战会话管理
- 延迟同步机制（30秒防作弊）
- 弹幕/聊天系统
- 可观战对局列表

主要组件：
- SpectatorManager: 观战管理器
- SpectatorSession: 观战会话
- SpectatorData: 观战数据
- SpectatorChat: 弹幕/聊天

使用示例:
    from src.server.spectator import (
        SpectatorManager,
        get_spectator_manager,
    )
    
    # 获取管理器
    manager = get_spectator_manager()
    
    # 创建可观战对局
    manager.create_spectatable_game("game_123")
    
    # 加入观战
    session = manager.create_session("player_456", "game_123", "player_789")
    
    # 获取延迟状态
    state = manager.get_delayed_state("game_123")
    
    # 发送弹幕
    chat = manager.send_chat("game_123", "player_456", "观众", "666")
"""

from .models import (
    GameVisibility,
    SpectatableGame,
    SpectatorChat,
    SpectatorData,
    SpectatorGameState,
    SpectatorSession,
    SpectatorStatus,
)
from .manager import (
    SpectatorManager,
    get_spectator_manager,
)

__all__ = [
    # 数据模型
    "GameVisibility",
    "SpectatableGame",
    "SpectatorChat",
    "SpectatorData",
    "SpectatorGameState",
    "SpectatorSession",
    "SpectatorStatus",
    
    # 管理器
    "SpectatorManager",
    "get_spectator_manager",
]
