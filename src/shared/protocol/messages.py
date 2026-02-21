"""
王者之奕 - WebSocket 消息协议定义

本模块定义所有 WebSocket 消息类型，使用 Pydantic 实现类型安全的消息格式。
包括：
- 基础消息类型
- 请求/响应消息
- 广播消息
- 错误消息
- 游戏操作消息（连接、商店、英雄、回合、战斗等）
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# 消息类型枚举
# ============================================================================

class MessageType(str, Enum):
    """消息类型枚举"""
    
    # ========== 连接相关 ==========
    # 客户端 -> 服务器
    CONNECT = "connect"               # 连接请求
    DISCONNECT = "disconnect"         # 断开连接
    HEARTBEAT = "heartbeat"           # 心跳
    RECONNECT = "reconnect"           # 断线重连
    
    # 服务器 -> 客户端
    CONNECTED = "connected"           # 连接成功
    RECONNECTED = "reconnected"       # 重连成功
    HEARTBEAT_ACK = "heartbeat_ack"   # 心跳响应
    
    # ========== 房间相关 ==========
    # 客户端 -> 服务器
    CREATE_ROOM = "create_room"       # 创建房间
    JOIN_ROOM = "join_room"           # 加入房间
    LEAVE_ROOM = "leave_room"         # 离开房间
    READY = "ready"                   # 准备
    CANCEL_READY = "cancel_ready"     # 取消准备
    GET_ROOM_INFO = "get_room_info"   # 获取房间信息
    GET_ROOM_LIST = "get_room_list"   # 获取房间列表
    
    # 服务器 -> 客户端
    ROOM_CREATED = "room_created"           # 房间创建成功
    ROOM_JOINED = "room_joined"             # 加入房间成功
    ROOM_LEFT = "room_left"                 # 离开房间
    ROOM_INFO = "room_info"                 # 房间信息
    ROOM_LIST = "room_list"                 # 房间列表
    PLAYER_JOINED = "player_joined"         # 玩家加入广播
    PLAYER_LEFT = "player_left"             # 玩家离开广播
    PLAYER_READY_CHANGED = "player_ready_changed"  # 玩家准备状态变化
    
    # ========== 商店操作 ==========
    # 客户端 -> 服务器
    SHOP_REFRESH = "shop_refresh"     # 刷新商店
    SHOP_BUY = "shop_buy"             # 购买英雄
    HERO_SELL = "hero_sell"           # 出售英雄
    SHOP_LOCK = "shop_lock"           # 锁定商店
    SHOP_UNLOCK = "shop_unlock"       # 解锁商店
    
    # 服务器 -> 客户端
    SHOP_REFRESHED = "shop_refreshed"       # 商店已刷新
    SHOP_BUY_SUCCESS = "shop_buy_success"   # 购买成功
    HERO_SOLD = "hero_sold"                 # 英雄已出售
    SHOP_LOCKED = "shop_locked"             # 商店已锁定
    SHOP_UNLOCKED = "shop_unlocked"         # 商店已解锁
    
    # ========== 英雄操作 ==========
    # 客户端 -> 服务器
    HERO_PLACE = "hero_place"         # 放置英雄到棋盘
    HERO_MOVE = "hero_move"           # 移动英雄
    HERO_REMOVE = "hero_remove"       # 移除英雄（放回备战席）
    HERO_UPGRADE = "hero_upgrade"     # 合成升级英雄
    
    # 服务器 -> 客户端
    HERO_PLACED = "hero_placed"       # 英雄已放置
    HERO_MOVED = "hero_moved"         # 英雄已移动
    HERO_REMOVED = "hero_removed"     # 英雄已移除
    HERO_UPGRADED = "hero_upgraded"   # 英雄已升级
    
    # ========== 回合状态 ==========
    # 服务器 -> 客户端（广播）
    ROUND_START = "round_start"       # 回合开始
    PREPARATION_START = "preparation_start"  # 准备阶段开始
    BATTLE_START = "battle_start"     # 战斗阶段开始
    ROUND_END = "round_end"           # 回合结束
    
    # ========== 战斗同步 ==========
    # 服务器 -> 客户端（广播）
    BATTLE_SYNC = "battle_sync"       # 战斗状态同步
    BATTLE_EVENT = "battle_event"     # 战斗事件（伤害、死亡、技能等）
    BATTLE_RESULT = "battle_result"   # 战斗结果
    
    # ========== 玩家状态 ==========
    # 服务器 -> 客户端
    PLAYER_STATE_UPDATE = "player_state_update"  # 玩家状态更新
    PLAYER_HP_UPDATE = "player_hp_update"        # 玩家血量更新
    PLAYER_GOLD_UPDATE = "player_gold_update"    # 玩家金币更新
    PLAYER_LEVEL_UPDATE = "player_level_update"  # 玩家等级更新
    PLAYER_ELIMINATED = "player_eliminated"      # 玩家被淘汰
    
    # ========== 游戏流程 ==========
    # 服务器 -> 客户端
    GAME_START = "game_start"         # 游戏开始
    GAME_OVER = "game_over"           # 游戏结束
    GAME_PAUSE = "game_pause"         # 游戏暂停
    GAME_RESUME = "game_resume"       # 游戏恢复
    
    # ========== 羁绊/阵容 ==========
    # 服务器 -> 客户端
    SYNERGY_UPDATE = "synergy_update"  # 羁绊状态更新
    
    # ========== 经验/升级 ==========
    # 客户端 -> 服务器
    BUY_EXP = "buy_exp"               # 购买经验
    
    # 服务器 -> 客户端
    EXP_GAINED = "exp_gained"         # 获得经验
    LEVEL_UP = "level_up"             # 等级提升
    
    # ========== 错误消息 ==========
    ERROR = "error"                   # 错误消息


# ============================================================================
# 基础消息模型
# ============================================================================

class BaseMessage(BaseModel):
    """
    基础消息模型
    
    所有消息的基类，包含公共字段。
    
    Attributes:
        type: 消息类型
        seq: 消息序列号（用于请求-响应匹配）
        timestamp: 消息时间戳（毫秒）
    """
    
    type: MessageType = Field(..., description="消息类型")
    seq: Optional[int] = Field(default=None, description="消息序列号")
    timestamp: Optional[int] = Field(default=None, description="消息时间戳（毫秒）")
    
    class Config:
        use_enum_values = True


# ============================================================================
# 连接相关消息
# ============================================================================

class ConnectMessage(BaseMessage):
    """
    连接请求消息
    
    客户端发送以建立连接。
    
    Attributes:
        player_id: 玩家ID
        token: 认证令牌
        version: 客户端版本
    """
    
    type: MessageType = MessageType.CONNECT
    player_id: str = Field(..., description="玩家ID")
    token: str = Field(..., description="认证令牌")
    version: str = Field(default="1.0.0", description="客户端版本")


class ConnectedMessage(BaseMessage):
    """
    连接成功消息
    
    服务器响应连接请求。
    
    Attributes:
        player_id: 玩家ID
        session_id: 会话ID
        server_time: 服务器时间戳
    """
    
    type: MessageType = MessageType.CONNECTED
    player_id: str = Field(..., description="玩家ID")
    session_id: str = Field(..., description="会话ID")
    server_time: int = Field(..., description="服务器时间戳")


class DisconnectMessage(BaseMessage):
    """
    断开连接消息
    
    Attributes:
        reason: 断开原因
    """
    
    type: MessageType = MessageType.DISCONNECT
    reason: Optional[str] = Field(default=None, description="断开原因")


class HeartbeatMessage(BaseMessage):
    """心跳消息"""
    
    type: MessageType = MessageType.HEARTBEAT


class HeartbeatAckMessage(BaseMessage):
    """心跳响应消息"""
    
    type: MessageType = MessageType.HEARTBEAT_ACK
    server_time: int = Field(..., description="服务器时间戳")


class ReconnectMessage(BaseMessage):
    """
    断线重连请求
    
    Attributes:
        session_id: 原会话ID
        player_id: 玩家ID
    """
    
    type: MessageType = MessageType.RECONNECT
    session_id: str = Field(..., description="原会话ID")
    player_id: str = Field(..., description="玩家ID")


class ReconnectedMessage(BaseMessage):
    """
    重连成功消息
    
    Attributes:
        player_id: 玩家ID
        room_id: 当前所在房间ID（如果有）
        game_state: 当前游戏状态（如果游戏中）
    """
    
    type: MessageType = MessageType.RECONNECTED
    player_id: str = Field(..., description="玩家ID")
    room_id: Optional[str] = Field(default=None, description="当前房间ID")
    game_state: Optional[dict[str, Any]] = Field(default=None, description="游戏状态")


# ============================================================================
# 房间相关消息
# ============================================================================

class CreateRoomMessage(BaseMessage):
    """
    创建房间请求
    
    Attributes:
        room_name: 房间名称
        password: 房间密码（可选）
        max_players: 最大玩家数（默认8）
    """
    
    type: MessageType = MessageType.CREATE_ROOM
    room_name: str = Field(..., description="房间名称")
    password: Optional[str] = Field(default=None, description="房间密码")
    max_players: int = Field(default=8, ge=2, le=8, description="最大玩家数")


class RoomCreatedMessage(BaseMessage):
    """
    房间创建成功
    
    Attributes:
        room_id: 房间ID
        room_name: 房间名称
    """
    
    type: MessageType = MessageType.ROOM_CREATED
    room_id: str = Field(..., description="房间ID")
    room_name: str = Field(..., description="房间名称")


class JoinRoomMessage(BaseMessage):
    """
    加入房间请求
    
    Attributes:
        room_id: 房间ID
        password: 房间密码（如果需要）
    """
    
    type: MessageType = MessageType.JOIN_ROOM
    room_id: str = Field(..., description="房间ID")
    password: Optional[str] = Field(default=None, description="房间密码")


class RoomJoinedMessage(BaseMessage):
    """
    加入房间成功
    
    Attributes:
        room_id: 房间ID
        room_info: 房间信息
    """
    
    type: MessageType = MessageType.ROOM_JOINED
    room_id: str = Field(..., description="房间ID")
    room_info: RoomInfoData = Field(..., description="房间信息")


class LeaveRoomMessage(BaseMessage):
    """离开房间请求"""
    
    type: MessageType = MessageType.LEAVE_ROOM


class RoomLeftMessage(BaseMessage):
    """
    离开房间成功
    
    Attributes:
        room_id: 房间ID
    """
    
    type: MessageType = MessageType.ROOM_LEFT
    room_id: str = Field(..., description="房间ID")


class ReadyMessage(BaseMessage):
    """准备请求"""
    
    type: MessageType = MessageType.READY


class CancelReadyMessage(BaseMessage):
    """取消准备请求"""
    
    type: MessageType = MessageType.CANCEL_READY


class PlayerJoinedMessage(BaseMessage):
    """
    玩家加入房间广播
    
    Attributes:
        player: 加入的玩家信息
    """
    
    type: MessageType = MessageType.PLAYER_JOINED
    player: PlayerInfoData = Field(..., description="玩家信息")


class PlayerLeftMessage(BaseMessage):
    """
    玩家离开房间广播
    
    Attributes:
        player_id: 离开的玩家ID
    """
    
    type: MessageType = MessageType.PLAYER_LEFT
    player_id: str = Field(..., description="玩家ID")


class PlayerReadyChangedMessage(BaseMessage):
    """
    玩家准备状态变化广播
    
    Attributes:
        player_id: 玩家ID
        is_ready: 是否已准备
    """
    
    type: MessageType = MessageType.PLAYER_READY_CHANGED
    player_id: str = Field(..., description="玩家ID")
    is_ready: bool = Field(..., description="是否已准备")


class GetRoomInfoMessage(BaseMessage):
    """获取房间信息请求"""
    
    type: MessageType = MessageType.GET_ROOM_INFO


class RoomInfoMessage(BaseMessage):
    """
    房间信息响应
    
    Attributes:
        room_info: 房间信息
    """
    
    type: MessageType = MessageType.ROOM_INFO
    room_info: RoomInfoData = Field(..., description="房间信息")


class GetRoomListMessage(BaseMessage):
    """获取房间列表请求"""
    
    type: MessageType = MessageType.GET_ROOM_LIST


class RoomListMessage(BaseMessage):
    """
    房间列表响应
    
    Attributes:
        rooms: 房间列表
    """
    
    type: MessageType = MessageType.ROOM_LIST
    rooms: list[RoomInfoData] = Field(default_factory=list, description="房间列表")


# ============================================================================
# 商店操作消息
# ============================================================================

class ShopRefreshMessage(BaseMessage):
    """刷新商店请求"""
    
    type: MessageType = MessageType.SHOP_REFRESH


class ShopRefreshedMessage(BaseMessage):
    """
    商店刷新成功
    
    Attributes:
        slots: 新的商店槽位列表
        gold: 剩余金币
    """
    
    type: MessageType = MessageType.SHOP_REFRESHED
    slots: list[ShopSlotData] = Field(..., description="商店槽位列表")
    gold: int = Field(..., description="剩余金币")


class ShopBuyMessage(BaseMessage):
    """
    购买英雄请求
    
    Attributes:
        slot_index: 商店槽位索引
    """
    
    type: MessageType = MessageType.SHOP_BUY
    slot_index: int = Field(..., ge=0, le=4, description="槽位索引")


class ShopBuySuccessMessage(BaseMessage):
    """
    购买成功响应
    
    Attributes:
        hero: 购买的英雄信息
        gold: 剩余金币
        slot_index: 购买的槽位索引
    """
    
    type: MessageType = MessageType.SHOP_BUY_SUCCESS
    hero: HeroData = Field(..., description="购买的英雄")
    gold: int = Field(..., description="剩余金币")
    slot_index: int = Field(..., description="槽位索引")


class HeroSellMessage(BaseMessage):
    """
    出售英雄请求
    
    Attributes:
        instance_id: 英雄实例ID
    """
    
    type: MessageType = MessageType.HERO_SELL
    instance_id: str = Field(..., description="英雄实例ID")


class HeroSoldMessage(BaseMessage):
    """
    出售英雄成功
    
    Attributes:
        instance_id: 出售的英雄实例ID
        gold: 获得金币
        total_gold: 当前总金币
    """
    
    type: MessageType = MessageType.HERO_SOLD
    instance_id: str = Field(..., description="英雄实例ID")
    gold: int = Field(..., description="获得金币")
    total_gold: int = Field(..., description="当前总金币")


class ShopLockMessage(BaseMessage):
    """锁定商店请求"""
    
    type: MessageType = MessageType.SHOP_LOCK


class ShopLockedMessage(BaseMessage):
    """商店已锁定"""
    
    type: MessageType = MessageType.SHOP_LOCKED


class ShopUnlockMessage(BaseMessage):
    """解锁商店请求"""
    
    type: MessageType = MessageType.SHOP_UNLOCK


class ShopUnlockedMessage(BaseMessage):
    """商店已解锁"""
    
    type: MessageType = MessageType.SHOP_UNLOCKED


# ============================================================================
# 英雄操作消息
# ============================================================================

class HeroPlaceMessage(BaseMessage):
    """
    放置英雄请求
    
    Attributes:
        instance_id: 英雄实例ID
        position: 目标位置
    """
    
    type: MessageType = MessageType.HERO_PLACE
    instance_id: str = Field(..., description="英雄实例ID")
    position: PositionData = Field(..., description="目标位置")


class HeroPlacedMessage(BaseMessage):
    """
    英雄放置成功
    
    Attributes:
        instance_id: 英雄实例ID
        position: 放置位置
    """
    
    type: MessageType = MessageType.HERO_PLACED
    instance_id: str = Field(..., description="英雄实例ID")
    position: PositionData = Field(..., description="放置位置")


class HeroMoveMessage(BaseMessage):
    """
    移动英雄请求
    
    Attributes:
        instance_id: 英雄实例ID
        from_pos: 原位置
        to_pos: 目标位置
    """
    
    type: MessageType = MessageType.HERO_MOVE
    instance_id: str = Field(..., description="英雄实例ID")
    from_pos: PositionData = Field(..., description="原位置")
    to_pos: PositionData = Field(..., description="目标位置")


class HeroMovedMessage(BaseMessage):
    """
    英雄移动成功
    
    Attributes:
        instance_id: 英雄实例ID
        from_pos: 原位置
        to_pos: 目标位置
    """
    
    type: MessageType = MessageType.HERO_MOVED
    instance_id: str = Field(..., description="英雄实例ID")
    from_pos: PositionData = Field(..., description="原位置")
    to_pos: PositionData = Field(..., description="目标位置")


class HeroRemoveMessage(BaseMessage):
    """
    移除英雄请求（放回备战席）
    
    Attributes:
        instance_id: 英雄实例ID
    """
    
    type: MessageType = MessageType.HERO_REMOVE
    instance_id: str = Field(..., description="英雄实例ID")


class HeroRemovedMessage(BaseMessage):
    """
    英雄移除成功
    
    Attributes:
        instance_id: 英雄实例ID
    """
    
    type: MessageType = MessageType.HERO_REMOVED
    instance_id: str = Field(..., description="英雄实例ID")


class HeroUpgradeMessage(BaseMessage):
    """
    合成升级英雄请求
    
    Attributes:
        instance_ids: 要合成的英雄实例ID列表（3个）
    """
    
    type: MessageType = MessageType.HERO_UPGRADE
    instance_ids: list[str] = Field(..., min_length=3, max_length=3, description="英雄实例ID列表")


class HeroUpgradedMessage(BaseMessage):
    """
    英雄升级成功
    
    Attributes:
        old_ids: 合成消耗的英雄ID列表
        new_hero: 升级后的英雄
    """
    
    type: MessageType = MessageType.HERO_UPGRADED
    old_ids: list[str] = Field(..., description="消耗的英雄ID列表")
    new_hero: HeroData = Field(..., description="升级后的英雄")


# ============================================================================
# 回合状态消息
# ============================================================================

class RoundStartMessage(BaseMessage):
    """
    回合开始广播
    
    Attributes:
        round_number: 回合数
        phase: 当前阶段（preparation/battle）
        duration: 阶段时长（秒）
    """
    
    type: MessageType = MessageType.ROUND_START
    round_number: int = Field(..., description="回合数")
    phase: str = Field(..., description="当前阶段")
    duration: int = Field(..., description="阶段时长（秒）")


class PreparationStartMessage(BaseMessage):
    """
    准备阶段开始广播
    
    Attributes:
        round_number: 回合数
        duration: 准备时长（秒）
        income: 本回合收入
    """
    
    type: MessageType = MessageType.PREPARATION_START
    round_number: int = Field(..., description="回合数")
    duration: int = Field(..., description="准备时长（秒）")
    income: IncomeData = Field(..., description="本回合收入详情")


class BattleStartMessage(BaseMessage):
    """
    战斗阶段开始广播
    
    Attributes:
        round_number: 回合数
        matchups: 对阵信息列表
    """
    
    type: MessageType = MessageType.BATTLE_START
    round_number: int = Field(..., description="回合数")
    matchups: list[MatchupData] = Field(..., description="对阵信息")


class RoundEndMessage(BaseMessage):
    """
    回合结束广播
    
    Attributes:
        round_number: 回合数
        results: 各玩家战斗结果
    """
    
    type: MessageType = MessageType.ROUND_END
    round_number: int = Field(..., description="回合数")
    results: list[PlayerRoundResultData] = Field(..., description="战斗结果")


# ============================================================================
# 战斗同步消息
# ============================================================================

class BattleSyncMessage(BaseMessage):
    """
    战斗状态同步
    
    Attributes:
        battle_id: 战斗ID
        time_ms: 战斗时间（毫秒）
        board_a: 玩家A棋盘状态
        board_b: 玩家B棋盘状态
    """
    
    type: MessageType = MessageType.BATTLE_SYNC
    battle_id: str = Field(..., description="战斗ID")
    time_ms: int = Field(..., description="战斗时间（毫秒）")
    board_a: BoardData = Field(..., description="玩家A棋盘状态")
    board_b: BoardData = Field(..., description="玩家B棋盘状态")


class BattleEventMessage(BaseMessage):
    """
    战斗事件
    
    Attributes:
        battle_id: 战斗ID
        time_ms: 事件时间（毫秒）
        event_type: 事件类型（damage/death/skill/mana）
        event_data: 事件详情
    """
    
    type: MessageType = MessageType.BATTLE_EVENT
    battle_id: str = Field(..., description="战斗ID")
    time_ms: int = Field(..., description="事件时间（毫秒）")
    event_type: str = Field(..., description="事件类型")
    event_data: dict[str, Any] = Field(..., description="事件详情")


class BattleResultMessage(BaseMessage):
    """
    战斗结果
    
    Attributes:
        battle_id: 战斗ID
        winner_id: 获胜方玩家ID
        loser_id: 失败方玩家ID
        damage: 失败方受到的伤害
        duration_ms: 战斗时长（毫秒）
    """
    
    type: MessageType = MessageType.BATTLE_RESULT
    battle_id: str = Field(..., description="战斗ID")
    winner_id: str = Field(..., description="获胜方玩家ID")
    loser_id: str = Field(..., description="失败方玩家ID")
    damage: int = Field(..., description="失败方受到的伤害")
    duration_ms: int = Field(..., description="战斗时长（毫秒）")


# ============================================================================
# 玩家状态消息
# ============================================================================

class PlayerStateUpdateMessage(BaseMessage):
    """
    玩家状态更新
    
    Attributes:
        player_id: 玩家ID
        state: 完整玩家状态
    """
    
    type: MessageType = MessageType.PLAYER_STATE_UPDATE
    player_id: str = Field(..., description="玩家ID")
    state: PlayerStateData = Field(..., description="玩家状态")


class PlayerHpUpdateMessage(BaseMessage):
    """
    玩家血量更新
    
    Attributes:
        player_id: 玩家ID
        hp: 当前血量
        max_hp: 最大血量
        damage: 本次受到的伤害（可选）
    """
    
    type: MessageType = MessageType.PLAYER_HP_UPDATE
    player_id: str = Field(..., description="玩家ID")
    hp: int = Field(..., ge=0, description="当前血量")
    max_hp: int = Field(default=100, description="最大血量")
    damage: Optional[int] = Field(default=None, description="本次受到的伤害")


class PlayerGoldUpdateMessage(BaseMessage):
    """
    玩家金币更新
    
    Attributes:
        player_id: 玩家ID
        gold: 当前金币
        change: 金币变化量（正为获得，负为消耗）
    """
    
    type: MessageType = MessageType.PLAYER_GOLD_UPDATE
    player_id: str = Field(..., description="玩家ID")
    gold: int = Field(..., ge=0, description="当前金币")
    change: int = Field(default=0, description="金币变化量")


class PlayerLevelUpdateMessage(BaseMessage):
    """
    玩家等级更新
    
    Attributes:
        player_id: 玩家ID
        level: 当前等级
        exp: 当前经验值
        exp_to_next: 升级所需经验
    """
    
    type: MessageType = MessageType.PLAYER_LEVEL_UPDATE
    player_id: str = Field(..., description="玩家ID")
    level: int = Field(..., ge=1, le=10, description="当前等级")
    exp: int = Field(..., ge=0, description="当前经验值")
    exp_to_next: int = Field(..., ge=0, description="升级所需经验")


class PlayerEliminatedMessage(BaseMessage):
    """
    玩家被淘汰广播
    
    Attributes:
        player_id: 被淘汰的玩家ID
        rank: 最终排名
    """
    
    type: MessageType = MessageType.PLAYER_ELIMINATED
    player_id: str = Field(..., description="玩家ID")
    rank: int = Field(..., description="最终排名")


# ============================================================================
# 游戏流程消息
# ============================================================================

class GameStartMessage(BaseMessage):
    """
    游戏开始广播
    
    Attributes:
        room_id: 房间ID
        players: 所有玩家初始状态
        seed: 随机种子（用于确定性模拟）
    """
    
    type: MessageType = MessageType.GAME_START
    room_id: str = Field(..., description="房间ID")
    players: list[PlayerInfoData] = Field(..., description="玩家列表")
    seed: int = Field(..., description="随机种子")


class GameOverMessage(BaseMessage):
    """
    游戏结束广播
    
    Attributes:
        room_id: 房间ID
        winner_id: 获胜玩家ID
        rankings: 最终排名列表
    """
    
    type: MessageType = MessageType.GAME_OVER
    room_id: str = Field(..., description="房间ID")
    winner_id: str = Field(..., description="获胜玩家ID")
    rankings: list[RankingData] = Field(..., description="最终排名")


class GamePauseMessage(BaseMessage):
    """游戏暂停广播"""
    
    type: MessageType = MessageType.GAME_PAUSE


class GameResumeMessage(BaseMessage):
    """游戏恢复广播"""
    
    type: MessageType = MessageType.GAME_RESUME


# ============================================================================
# 羁绊更新消息
# ============================================================================

class SynergyUpdateMessage(BaseMessage):
    """
    羁绊状态更新
    
    Attributes:
        player_id: 玩家ID
        synergies: 激活的羁绊列表
    """
    
    type: MessageType = MessageType.SYNERGY_UPDATE
    player_id: str = Field(..., description="玩家ID")
    synergies: list[ActiveSynergyData] = Field(..., description="羁绊列表")


# ============================================================================
# 经验/升级消息
# ============================================================================

class BuyExpMessage(BaseMessage):
    """购买经验请求"""
    
    type: MessageType = MessageType.BUY_EXP


class ExpGainedMessage(BaseMessage):
    """
    获得经验响应
    
    Attributes:
        exp: 获得的经验值
        total_exp: 当前总经验
    """
    
    type: MessageType = MessageType.EXP_GAINED
    exp: int = Field(..., description="获得的经验值")
    total_exp: int = Field(..., description="当前总经验")


class LevelUpMessage(BaseMessage):
    """
    等级提升广播
    
    Attributes:
        player_id: 玩家ID
        new_level: 新等级
        max_heroes: 可上场英雄数量
    """
    
    type: MessageType = MessageType.LEVEL_UP
    player_id: str = Field(..., description="玩家ID")
    new_level: int = Field(..., description="新等级")
    max_heroes: int = Field(..., description="可上场英雄数量")


# ============================================================================
# 错误消息
# ============================================================================

class ErrorMessage(BaseMessage):
    """
    错误消息
    
    Attributes:
        code: 错误码
        message: 错误描述
        details: 错误详情
    """
    
    type: MessageType = MessageType.ERROR
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误描述")
    details: Optional[dict[str, Any]] = Field(default=None, description="错误详情")


# ============================================================================
# 数据模型（嵌入到消息中的数据结构）
# ============================================================================

class PositionData(BaseModel):
    """位置数据"""
    
    x: int = Field(..., ge=0, le=7, description="X坐标")
    y: int = Field(..., ge=0, le=7, description="Y坐标")


class HeroData(BaseModel):
    """英雄数据"""
    
    instance_id: str = Field(..., description="实例ID")
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="名称")
    cost: int = Field(..., ge=1, le=5, description="费用")
    star: int = Field(..., ge=1, le=3, description="星级")
    race: str = Field(..., description="种族")
    profession: str = Field(..., description="职业")
    max_hp: int = Field(..., description="最大生命值")
    hp: int = Field(..., description="当前生命值")
    attack: int = Field(..., description="攻击力")
    defense: int = Field(..., description="防御力")
    attack_speed: float = Field(..., description="攻击速度")
    mana: int = Field(default=0, description="当前蓝量")
    position: Optional[PositionData] = Field(default=None, description="位置")


class ShopSlotData(BaseModel):
    """商店槽位数据"""
    
    slot_index: int = Field(..., description="槽位索引")
    hero_template_id: Optional[str] = Field(default=None, description="英雄模板ID")
    is_locked: bool = Field(default=False, description="是否锁定")
    is_sold: bool = Field(default=False, description="是否已售出")


class PlayerInfoData(BaseModel):
    """玩家基本信息"""
    
    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str = Field(default="", description="头像")
    is_ready: bool = Field(default=False, description="是否准备")
    is_host: bool = Field(default=False, description="是否房主")


class PlayerStateData(BaseModel):
    """玩家完整状态数据"""
    
    player_id: str = Field(..., description="玩家ID")
    hp: int = Field(..., description="当前血量")
    gold: int = Field(..., description="当前金币")
    level: int = Field(..., description="当前等级")
    exp: int = Field(..., description="当前经验")
    board: list[HeroData] = Field(default_factory=list, description="场上英雄")
    bench: list[HeroData] = Field(default_factory=list, description="备战席英雄")
    shop_slots: list[ShopSlotData] = Field(default_factory=list, description="商店槽位")
    win_streak: int = Field(default=0, description="连胜")
    lose_streak: int = Field(default=0, description="连败")


class RoomInfoData(BaseModel):
    """房间信息数据"""
    
    room_id: str = Field(..., description="房间ID")
    room_name: str = Field(..., description="房间名称")
    host_id: str = Field(..., description="房主ID")
    max_players: int = Field(default=8, description="最大玩家数")
    current_players: int = Field(default=0, description="当前玩家数")
    players: list[PlayerInfoData] = Field(default_factory=list, description="玩家列表")
    status: str = Field(default="waiting", description="房间状态")
    has_password: bool = Field(default=False, description="是否有密码")


class BoardData(BaseModel):
    """棋盘数据"""
    
    owner_id: str = Field(..., description="所有者ID")
    heroes: list[HeroData] = Field(default_factory=list, description="英雄列表")


class IncomeData(BaseModel):
    """收入详情数据"""
    
    base: int = Field(default=5, description="基础收入")
    interest: int = Field(default=0, description="利息")
    win_streak: int = Field(default=0, description="连胜奖励")
    lose_streak: int = Field(default=0, description="连败奖励")
    total: int = Field(..., description="总收入")


class MatchupData(BaseModel):
    """对阵数据"""
    
    player_a_id: str = Field(..., description="玩家A ID")
    player_b_id: str = Field(..., description="玩家B ID")
    battle_id: str = Field(..., description="战斗ID")


class PlayerRoundResultData(BaseModel):
    """玩家回合结果数据"""
    
    player_id: str = Field(..., description="玩家ID")
    opponent_id: str = Field(..., description="对手ID")
    is_winner: bool = Field(..., description="是否获胜")
    damage_dealt: int = Field(default=0, description="造成伤害")
    damage_taken: int = Field(default=0, description="受到伤害")
    survivors: int = Field(default=0, description="存活英雄数")


class ActiveSynergyData(BaseModel):
    """激活的羁绊数据"""
    
    name: str = Field(..., description="羁绊名称")
    synergy_type: str = Field(..., description="羁绊类型")
    count: int = Field(..., description="当前数量")
    level: int = Field(..., description="当前等级")
    effect: str = Field(default="", description="效果描述")


class RankingData(BaseModel):
    """排名数据"""
    
    player_id: str = Field(..., description="玩家ID")
    rank: int = Field(..., description="排名")
    nickname: str = Field(default="", description="昵称")


# ============================================================================
# 消息类型映射（用于反序列化）
# ============================================================================

MESSAGE_CLASS_MAP: dict[MessageType, type[BaseMessage]] = {
    # 连接相关
    MessageType.CONNECT: ConnectMessage,
    MessageType.CONNECTED: ConnectedMessage,
    MessageType.DISCONNECT: DisconnectMessage,
    MessageType.HEARTBEAT: HeartbeatMessage,
    MessageType.HEARTBEAT_ACK: HeartbeatAckMessage,
    MessageType.RECONNECT: ReconnectMessage,
    MessageType.RECONNECTED: ReconnectedMessage,
    
    # 房间相关
    MessageType.CREATE_ROOM: CreateRoomMessage,
    MessageType.ROOM_CREATED: RoomCreatedMessage,
    MessageType.JOIN_ROOM: JoinRoomMessage,
    MessageType.ROOM_JOINED: RoomJoinedMessage,
    MessageType.LEAVE_ROOM: LeaveRoomMessage,
    MessageType.ROOM_LEFT: RoomLeftMessage,
    MessageType.READY: ReadyMessage,
    MessageType.CANCEL_READY: CancelReadyMessage,
    MessageType.PLAYER_JOINED: PlayerJoinedMessage,
    MessageType.PLAYER_LEFT: PlayerLeftMessage,
    MessageType.PLAYER_READY_CHANGED: PlayerReadyChangedMessage,
    MessageType.GET_ROOM_INFO: GetRoomInfoMessage,
    MessageType.ROOM_INFO: RoomInfoMessage,
    MessageType.GET_ROOM_LIST: GetRoomListMessage,
    MessageType.ROOM_LIST: RoomListMessage,
    
    # 商店操作
    MessageType.SHOP_REFRESH: ShopRefreshMessage,
    MessageType.SHOP_REFRESHED: ShopRefreshedMessage,
    MessageType.SHOP_BUY: ShopBuyMessage,
    MessageType.SHOP_BUY_SUCCESS: ShopBuySuccessMessage,
    MessageType.HERO_SELL: HeroSellMessage,
    MessageType.HERO_SOLD: HeroSoldMessage,
    MessageType.SHOP_LOCK: ShopLockMessage,
    MessageType.SHOP_LOCKED: ShopLockedMessage,
    MessageType.SHOP_UNLOCK: ShopUnlockMessage,
    MessageType.SHOP_UNLOCKED: ShopUnlockedMessage,
    
    # 英雄操作
    MessageType.HERO_PLACE: HeroPlaceMessage,
    MessageType.HERO_PLACED: HeroPlacedMessage,
    MessageType.HERO_MOVE: HeroMoveMessage,
    MessageType.HERO_MOVED: HeroMovedMessage,
    MessageType.HERO_REMOVE: HeroRemoveMessage,
    MessageType.HERO_REMOVED: HeroRemovedMessage,
    MessageType.HERO_UPGRADE: HeroUpgradeMessage,
    MessageType.HERO_UPGRADED: HeroUpgradedMessage,
    
    # 回合状态
    MessageType.ROUND_START: RoundStartMessage,
    MessageType.PREPARATION_START: PreparationStartMessage,
    MessageType.BATTLE_START: BattleStartMessage,
    MessageType.ROUND_END: RoundEndMessage,
    
    # 战斗同步
    MessageType.BATTLE_SYNC: BattleSyncMessage,
    MessageType.BATTLE_EVENT: BattleEventMessage,
    MessageType.BATTLE_RESULT: BattleResultMessage,
    
    # 玩家状态
    MessageType.PLAYER_STATE_UPDATE: PlayerStateUpdateMessage,
    MessageType.PLAYER_HP_UPDATE: PlayerHpUpdateMessage,
    MessageType.PLAYER_GOLD_UPDATE: PlayerGoldUpdateMessage,
    MessageType.PLAYER_LEVEL_UPDATE: PlayerLevelUpdateMessage,
    MessageType.PLAYER_ELIMINATED: PlayerEliminatedMessage,
    
    # 游戏流程
    MessageType.GAME_START: GameStartMessage,
    MessageType.GAME_OVER: GameOverMessage,
    MessageType.GAME_PAUSE: GamePauseMessage,
    MessageType.GAME_RESUME: GameResumeMessage,
    
    # 羁绊
    MessageType.SYNERGY_UPDATE: SynergyUpdateMessage,
    
    # 经验/升级
    MessageType.BUY_EXP: BuyExpMessage,
    MessageType.EXP_GAINED: ExpGainedMessage,
    MessageType.LEVEL_UP: LevelUpMessage,
    
    # 错误
    MessageType.ERROR: ErrorMessage,
}
