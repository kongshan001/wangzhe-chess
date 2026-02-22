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
    
    # ========== 阵容预设 ==========
    # 客户端 -> 服务器
    LINEUP_SAVE = "lineup_save"       # 保存阵容预设
    LINEUP_LOAD = "lineup_load"       # 加载阵容预设
    LINEUP_DELETE = "lineup_delete"   # 删除阵容预设
    LINEUP_RENAME = "lineup_rename"   # 重命名阵容预设
    LINEUP_LIST = "lineup_list"       # 获取预设列表
    LINEUP_APPLY = "lineup_apply"     # 应用预设到对局
    
    # 服务器 -> 客户端
    LINEUP_SAVED = "lineup_saved"     # 预设保存成功
    LINEUP_LOADED = "lineup_loaded"   # 预设加载成功
    LINEUP_DELETED = "lineup_deleted" # 预设删除成功
    LINEUP_RENAMED = "lineup_renamed" # 预设重命名成功
    LINEUP_LIST_RESULT = "lineup_list_result"  # 预设列表结果
    LINEUP_APPLIED = "lineup_applied" # 预设应用成功
    
    # ========== 好友系统 ==========
    # 客户端 -> 服务器
    FRIEND_REQUEST = "friend_request"           # 发送好友请求
    FRIEND_ACCEPT = "friend_accept"             # 接受好友请求
    FRIEND_REJECT = "friend_reject"             # 拒绝好友请求
    FRIEND_REMOVE = "friend_remove"             # 删除好友
    FRIEND_BLOCK = "friend_block"               # 拉黑玩家
    FRIEND_UNBLOCK = "friend_unblock"           # 取消拉黑
    GET_FRIEND_LIST = "get_friend_list"         # 获取好友列表
    GET_PENDING_REQUESTS = "get_pending_requests"  # 获取待处理请求
    SEARCH_PLAYER = "search_player"             # 搜索玩家
    
    # 服务器 -> 客户端
    FRIEND_REQUEST_RECEIVED = "friend_request_received"  # 收到好友请求
    FRIEND_REQUEST_SENT = "friend_request_sent"          # 好友请求已发送
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"  # 好友请求已接受
    FRIEND_REQUEST_REJECTED = "friend_request_rejected"  # 好友请求已拒绝
    FRIEND_LIST = "friend_list"                          # 好友列表
    PENDING_REQUESTS = "pending_requests"                # 待处理请求列表
    FRIEND_REMOVED = "friend_removed"                    # 好友已删除
    FRIEND_BLOCKED = "friend_blocked"                    # 玩家已拉黑
    FRIEND_UNBLOCKED = "friend_unblocked"                # 玩家已取消拉黑
    FRIEND_STATUS_UPDATE = "friend_status_update"        # 好友状态更新
    PLAYER_SEARCH_RESULT = "player_search_result"        # 玩家搜索结果
    
    # ========== 私聊系统 ==========
    # 客户端 -> 服务器
    PRIVATE_MESSAGE = "private_message"         # 发送私聊消息
    GET_CHAT_HISTORY = "get_chat_history"       # 获取聊天记录
    MARK_MESSAGES_READ = "mark_messages_read"   # 标记消息已读
    
    # 服务器 -> 客户端
    PRIVATE_MESSAGE_RECEIVED = "private_message_received"  # 收到私聊消息
    CHAT_HISTORY = "chat_history"                          # 聊天记录
    MESSAGES_READ = "messages_read"                        # 消息已读确认
    UNREAD_COUNT = "unread_count"                          # 未读消息数
    
    # ========== 组队系统 ==========
    # 客户端 -> 服务器
    CREATE_TEAM = "create_team"             # 创建队伍
    JOIN_TEAM = "join_team"                 # 加入队伍
    LEAVE_TEAM = "leave_team"               # 离开队伍
    KICK_TEAM_MEMBER = "kick_team_member"   # 踢出成员
    INVITE_TEAM = "invite_team"             # 邀请加入队伍
    ACCEPT_TEAM_INVITE = "accept_team_invite"  # 接受队伍邀请
    REJECT_TEAM_INVITE = "reject_team_invite"  # 拒绝队伍邀请
    GET_TEAM_INFO = "get_team_info"         # 获取队伍信息
    
    # 服务器 -> 客户端
    TEAM_CREATED = "team_created"               # 队伍创建成功
    TEAM_JOINED = "team_joined"                 # 加入队伍成功
    TEAM_LEFT = "team_left"                     # 离开队伍成功
    TEAM_MEMBER_KICKED = "team_member_kicked"   # 成员被踢出
    TEAM_INVITE_RECEIVED = "team_invite_received"  # 收到队伍邀请
    TEAM_INVITE_SENT = "team_invite_sent"       # 队伍邀请已发送
    TEAM_INFO = "team_info"                     # 队伍信息
    TEAM_DISBANDED = "team_disbanded"           # 队伍已解散
    TEAM_MEMBER_JOINED = "team_member_joined"   # 成员加入队伍
    TEAM_MEMBER_LEFT = "team_member_left"       # 成员离开队伍
    
    # ========== 排行榜系统 ==========
    # 客户端 -> 服务器
    GET_LEADERBOARD = "get_leaderboard"               # 获取排行榜
    GET_PLAYER_RANK = "get_player_rank"               # 获取玩家排名
    LEADERBOARD_LIST = "leaderboard_list"             # 获取排行榜列表
    CLAIM_LEADERBOARD_REWARD = "claim_leaderboard_reward"  # 领取排行榜奖励
    
    # 服务器 -> 客户端
    LEADERBOARD_DATA = "leaderboard_data"             # 排行榜数据
    PLAYER_RANK_INFO = "player_rank_info"             # 玩家排名信息
    LEADERBOARD_LIST_RESULT = "leaderboard_list_result"  # 排行榜列表结果
    LEADERBOARD_REWARD_CLAIMED = "leaderboard_reward_claimed"  # 排行榜奖励已领取
    
    # ========== 签到系统 ==========
    # 客户端 -> 服务器
    CHECKIN = "checkin"                         # 每日签到
    GET_CHECKIN_INFO = "get_checkin_info"       # 获取签到信息
    SUPPLEMENT_CHECKIN = "supplement_checkin"   # 补签
    GET_CHECKIN_RECORDS = "get_checkin_records" # 获取签到记录
    GET_CHECKIN_REWARDS = "get_checkin_rewards" # 获取签到奖励配置
    
    # 服务器 -> 客户端
    CHECKIN_SUCCESS = "checkin_success"         # 签到成功
    CHECKIN_INFO = "checkin_info"               # 签到信息
    CHECKIN_RECORDS = "checkin_records"         # 签到记录列表
    CHECKIN_REWARDS = "checkin_rewards"         # 签到奖励配置
    SUPPLEMENT_SUCCESS = "supplement_success"   # 补签成功
    
    # ========== 羁绊图鉴系统 ==========
    # 客户端 -> 服务器
    GET_SYNERGY_PEDIA = "get_synergy_pedia"           # 获取羁绊图鉴
    SYNERGY_PEDIA_INFO = "synergy_pedia_info"         # 获取单个羁绊详情
    SIMULATE_SYNERGY = "simulate_synergy"             # 羁绊模拟器
    GET_SYNERGY_RECOMMENDATIONS = "get_synergy_recommendations"  # 获取阵容推荐
    GET_SYNERGY_ACHIEVEMENTS = "get_synergy_achievements"  # 获取羁绊成就
    
    # 服务器 -> 客户端
    SYNERGY_PEDIA_LIST = "synergy_pedia_list"         # 羁绊图鉴列表
    SYNERGY_PEDIA_DETAIL = "synergy_pedia_detail"     # 羁绊详情
    SYNERGY_SIMULATION_RESULT = "synergy_simulation_result"  # 模拟结果
    SYNERGY_RECOMMENDATIONS_RESULT = "synergy_recommendations_result"  # 推荐结果
    SYNERGY_ACHIEVEMENTS_RESULT = "synergy_achievements_result"  # 成就列表
    SYNERGY_ACHIEVEMENT_UNLOCKED = "synergy_achievement_unlocked"  # 成就解锁通知
    
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
# 阵容预设消息
# ============================================================================

class LineupSlotData(BaseModel):
    """阵容槽位数据"""
    
    hero_id: str = Field(..., description="英雄ID")
    row: int = Field(..., ge=0, le=7, description="行位置")
    col: int = Field(..., ge=0, le=6, description="列位置")
    equipment: list[str] = Field(default_factory=list, description="装备ID列表")
    star_level: int = Field(default=1, ge=1, le=3, description="星级")


class LineupSynergyData(BaseModel):
    """目标羁绊数据"""
    
    synergy_id: str = Field(..., description="羁绊ID")
    target_count: int = Field(default=1, description="目标数量")
    priority: int = Field(default=3, ge=1, le=5, description="优先级")


class LineupPresetData(BaseModel):
    """阵容预设数据"""
    
    preset_id: str = Field(..., description="预设ID")
    name: str = Field(..., description="预设名称")
    description: str = Field(default="", description="预设描述")
    slots: list[LineupSlotData] = Field(default_factory=list, description="槽位列表")
    target_synergies: list[LineupSynergyData] = Field(default_factory=list, description="目标羁绊")
    notes: str = Field(default="", description="策略备注")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class LineupSaveMessage(BaseMessage):
    """
    保存阵容预设请求
    
    Attributes:
        name: 预设名称
        description: 预设描述
        slots: 英雄槽位列表
        target_synergies: 目标羁绊列表
        notes: 策略备注
    """
    
    type: MessageType = MessageType.LINEUP_SAVE
    name: str = Field(..., min_length=1, max_length=100, description="预设名称")
    description: str = Field(default="", max_length=500, description="预设描述")
    slots: list[LineupSlotData] = Field(default_factory=list, description="槽位列表")
    target_synergies: list[LineupSynergyData] = Field(default_factory=list, description="目标羁绊")
    notes: str = Field(default="", description="策略备注")


class LineupSavedMessage(BaseMessage):
    """
    预设保存成功响应
    
    Attributes:
        preset: 保存的预设数据
    """
    
    type: MessageType = MessageType.LINEUP_SAVED
    preset: LineupPresetData = Field(..., description="预设数据")


class LineupLoadMessage(BaseMessage):
    """
    加载阵容预设请求
    
    Attributes:
        preset_id: 预设ID
    """
    
    type: MessageType = MessageType.LINEUP_LOAD
    preset_id: str = Field(..., description="预设ID")


class LineupLoadedMessage(BaseMessage):
    """
    预设加载成功响应
    
    Attributes:
        preset: 加载的预设数据
    """
    
    type: MessageType = MessageType.LINEUP_LOADED
    preset: LineupPresetData = Field(..., description="预设数据")


class LineupDeleteMessage(BaseMessage):
    """
    删除阵容预设请求
    
    Attributes:
        preset_id: 预设ID
    """
    
    type: MessageType = MessageType.LINEUP_DELETE
    preset_id: str = Field(..., description="预设ID")


class LineupDeletedMessage(BaseMessage):
    """
    预设删除成功响应
    
    Attributes:
        preset_id: 被删除的预设ID
    """
    
    type: MessageType = MessageType.LINEUP_DELETED
    preset_id: str = Field(..., description="预设ID")


class LineupRenameMessage(BaseMessage):
    """
    重命名阵容预设请求
    
    Attributes:
        preset_id: 预设ID
        new_name: 新名称
    """
    
    type: MessageType = MessageType.LINEUP_RENAME
    preset_id: str = Field(..., description="预设ID")
    new_name: str = Field(..., min_length=1, max_length=100, description="新名称")


class LineupRenamedMessage(BaseMessage):
    """
    预设重命名成功响应
    
    Attributes:
        preset_id: 预设ID
        new_name: 新名称
    """
    
    type: MessageType = MessageType.LINEUP_RENAMED
    preset_id: str = Field(..., description="预设ID")
    new_name: str = Field(..., description="新名称")


class LineupListMessage(BaseMessage):
    """获取预设列表请求"""
    
    type: MessageType = MessageType.LINEUP_LIST


class LineupListResultMessage(BaseMessage):
    """
    预设列表响应
    
    Attributes:
        presets: 预设列表
        max_presets: 最大预设数量
    """
    
    type: MessageType = MessageType.LINEUP_LIST_RESULT
    presets: list[LineupPresetData] = Field(default_factory=list, description="预设列表")
    max_presets: int = Field(default=5, description="最大预设数量")


class LineupApplyMessage(BaseMessage):
    """
    应用预设到对局请求
    
    Attributes:
        preset_id: 预设ID
    """
    
    type: MessageType = MessageType.LINEUP_APPLY
    preset_id: str = Field(..., description="预设ID")


class LineupAppliedMessage(BaseMessage):
    """
    预设应用成功响应
    
    Attributes:
        preset_id: 预设ID
        preset_name: 预设名称
        heroes_to_buy: 需要购买的英雄ID列表
        slots: 槽位建议
    """
    
    type: MessageType = MessageType.LINEUP_APPLIED
    preset_id: str = Field(..., description="预设ID")
    preset_name: str = Field(..., description="预设名称")
    heroes_to_buy: list[str] = Field(default_factory=list, description="需要购买的英雄")
    slots: list[LineupSlotData] = Field(default_factory=list, description="槽位建议")


# ============================================================================
# 好友系统消息
# ============================================================================

class FriendRequestMessage(BaseMessage):
    """
    发送好友请求
    
    Attributes:
        to_player_id: 目标玩家ID
        message: 附带消息
    """
    
    type: MessageType = MessageType.FRIEND_REQUEST
    to_player_id: str = Field(..., description="目标玩家ID")
    message: str = Field(default="", max_length=200, description="附带消息")


class FriendRequestSentMessage(BaseMessage):
    """
    好友请求已发送
    
    Attributes:
        request_id: 请求ID
        to_player_id: 目标玩家ID
    """
    
    type: MessageType = MessageType.FRIEND_REQUEST_SENT
    request_id: str = Field(..., description="请求ID")
    to_player_id: str = Field(..., description="目标玩家ID")


class FriendRequestReceivedMessage(BaseMessage):
    """
    收到好友请求
    
    Attributes:
        request: 请求数据
    """
    
    type: MessageType = MessageType.FRIEND_REQUEST_RECEIVED
    request: FriendRequestData = Field(..., description="请求数据")


class FriendAcceptMessage(BaseMessage):
    """
    接受好友请求
    
    Attributes:
        request_id: 请求ID
    """
    
    type: MessageType = MessageType.FRIEND_ACCEPT
    request_id: str = Field(..., description="请求ID")


class FriendRequestAcceptedMessage(BaseMessage):
    """
    好友请求已接受
    
    Attributes:
        request_id: 请求ID
        friend: 新好友信息
    """
    
    type: MessageType = MessageType.FRIEND_REQUEST_ACCEPTED
    request_id: str = Field(..., description="请求ID")
    friend: FriendInfoData = Field(..., description="新好友信息")


class FriendRejectMessage(BaseMessage):
    """
    拒绝好友请求
    
    Attributes:
        request_id: 请求ID
    """
    
    type: MessageType = MessageType.FRIEND_REJECT
    request_id: str = Field(..., description="请求ID")


class FriendRequestRejectedMessage(BaseMessage):
    """
    好友请求已拒绝
    
    Attributes:
        request_id: 请求ID
        player_id: 拒绝者ID
    """
    
    type: MessageType = MessageType.FRIEND_REQUEST_REJECTED
    request_id: str = Field(..., description="请求ID")
    player_id: str = Field(..., description="拒绝者ID")


class FriendRemoveMessage(BaseMessage):
    """
    删除好友
    
    Attributes:
        friend_id: 好友ID
    """
    
    type: MessageType = MessageType.FRIEND_REMOVE
    friend_id: str = Field(..., description="好友ID")


class FriendRemovedMessage(BaseMessage):
    """
    好友已删除
    
    Attributes:
        friend_id: 好友ID
    """
    
    type: MessageType = MessageType.FRIEND_REMOVED
    friend_id: str = Field(..., description="好友ID")


class FriendBlockMessage(BaseMessage):
    """
    拉黑玩家
    
    Attributes:
        player_id: 玩家ID
        reason: 拉黑原因
    """
    
    type: MessageType = MessageType.FRIEND_BLOCK
    player_id: str = Field(..., description="玩家ID")
    reason: str = Field(default="", description="拉黑原因")


class FriendBlockedMessage(BaseMessage):
    """
    玩家已拉黑
    
    Attributes:
        player_id: 被拉黑的玩家ID
    """
    
    type: MessageType = MessageType.FRIEND_BLOCKED
    player_id: str = Field(..., description="被拉黑的玩家ID")


class FriendUnblockMessage(BaseMessage):
    """
    取消拉黑
    
    Attributes:
        player_id: 玩家ID
    """
    
    type: MessageType = MessageType.FRIEND_UNBLOCK
    player_id: str = Field(..., description="玩家ID")


class FriendUnblockedMessage(BaseMessage):
    """
    玩家已取消拉黑
    
    Attributes:
        player_id: 玩家ID
    """
    
    type: MessageType = MessageType.FRIEND_UNBLOCKED
    player_id: str = Field(..., description="玩家ID")


class GetFriendListMessage(BaseMessage):
    """获取好友列表请求"""
    
    type: MessageType = MessageType.GET_FRIEND_LIST


class FriendListMessage(BaseMessage):
    """
    好友列表响应
    
    Attributes:
        friends: 好友列表
        total: 总数
    """
    
    type: MessageType = MessageType.FRIEND_LIST
    friends: list[FriendInfoData] = Field(default_factory=list, description="好友列表")
    total: int = Field(default=0, description="总数")


class GetPendingRequestsMessage(BaseMessage):
    """获取待处理好友请求"""
    
    type: MessageType = MessageType.GET_PENDING_REQUESTS


class PendingRequestsMessage(BaseMessage):
    """
    待处理请求列表
    
    Attributes:
        requests: 请求列表
    """
    
    type: MessageType = MessageType.PENDING_REQUESTS
    requests: list[FriendRequestData] = Field(default_factory=list, description="请求列表")


class SearchPlayerMessage(BaseMessage):
    """
    搜索玩家
    
    Attributes:
        query: 搜索关键词
        limit: 返回数量
    """
    
    type: MessageType = MessageType.SEARCH_PLAYER
    query: str = Field(..., min_length=1, max_length=50, description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=50, description="返回数量")


class PlayerSearchResultMessage(BaseMessage):
    """
    玩家搜索结果
    
    Attributes:
        query: 搜索关键词
        results: 搜索结果
    """
    
    type: MessageType = MessageType.PLAYER_SEARCH_RESULT
    query: str = Field(..., description="搜索关键词")
    results: list[PlayerSearchInfoData] = Field(default_factory=list, description="搜索结果")


class FriendStatusUpdateMessage(BaseMessage):
    """
    好友状态更新
    
    Attributes:
        friend_id: 好友ID
        status: 新状态
        in_game_info: 游戏中信息（可选）
    """
    
    type: MessageType = MessageType.FRIEND_STATUS_UPDATE
    friend_id: str = Field(..., description="好友ID")
    status: str = Field(..., description="新状态")
    in_game_info: Optional[dict[str, Any]] = Field(default=None, description="游戏中信息")


# ============================================================================
# 私聊系统消息
# ============================================================================

class PrivateMessage(BaseMessage):
    """
    发送私聊消息
    
    Attributes:
        to_player_id: 接收者ID
        content: 消息内容
        message_type: 消息类型
    """
    
    type: MessageType = MessageType.PRIVATE_MESSAGE
    to_player_id: str = Field(..., description="接收者ID")
    content: str = Field(..., min_length=1, max_length=500, description="消息内容")
    message_type: str = Field(default="text", description="消息类型")


class PrivateMessageReceivedMessage(BaseMessage):
    """
    收到私聊消息
    
    Attributes:
        message: 消息数据
    """
    
    type: MessageType = MessageType.PRIVATE_MESSAGE_RECEIVED
    message: PrivateMessageData = Field(..., description="消息数据")


class GetChatHistoryMessage(BaseMessage):
    """
    获取聊天记录
    
    Attributes:
        friend_id: 好友ID
        limit: 返回数量
        before_id: 此消息ID之前的记录
    """
    
    type: MessageType = MessageType.GET_CHAT_HISTORY
    friend_id: str = Field(..., description="好友ID")
    limit: int = Field(default=50, ge=1, le=100, description="返回数量")
    before_id: Optional[str] = Field(default=None, description="此消息ID之前的记录")


class ChatHistoryMessage(BaseMessage):
    """
    聊天记录响应
    
    Attributes:
        friend_id: 好友ID
        messages: 消息列表
    """
    
    type: MessageType = MessageType.CHAT_HISTORY
    friend_id: str = Field(..., description="好友ID")
    messages: list[PrivateMessageData] = Field(default_factory=list, description="消息列表")


class MarkMessagesReadMessage(BaseMessage):
    """
    标记消息已读
    
    Attributes:
        friend_id: 好友ID
    """
    
    type: MessageType = MessageType.MARK_MESSAGES_READ
    friend_id: str = Field(..., description="好友ID")


class MessagesReadMessage(BaseMessage):
    """
    消息已读确认
    
    Attributes:
        friend_id: 好友ID
        count: 标记数量
    """
    
    type: MessageType = MessageType.MESSAGES_READ
    friend_id: str = Field(..., description="好友ID")
    count: int = Field(..., description="标记数量")


class UnreadCountMessage(BaseMessage):
    """
    未读消息数
    
    Attributes:
        count: 未读消息总数
    """
    
    type: MessageType = MessageType.UNREAD_COUNT
    count: int = Field(..., description="未读消息总数")


# ============================================================================
# 组队系统消息
# ============================================================================

class CreateTeamMessage(BaseMessage):
    """
    创建队伍
    
    Attributes:
        max_members: 最大成员数
    """
    
    type: MessageType = MessageType.CREATE_TEAM
    max_members: int = Field(default=3, ge=2, le=3, description="最大成员数")


class TeamCreatedMessage(BaseMessage):
    """
    队伍创建成功
    
    Attributes:
        team: 队伍信息
    """
    
    type: MessageType = MessageType.TEAM_CREATED
    team: TeamInfoData = Field(..., description="队伍信息")


class JoinTeamMessage(BaseMessage):
    """
    加入队伍
    
    Attributes:
        team_id: 队伍ID
    """
    
    type: MessageType = MessageType.JOIN_TEAM
    team_id: str = Field(..., description="队伍ID")


class TeamJoinedMessage(BaseMessage):
    """
    加入队伍成功
    
    Attributes:
        team: 队伍信息
    """
    
    type: MessageType = MessageType.TEAM_JOINED
    team: TeamInfoData = Field(..., description="队伍信息")


class LeaveTeamMessage(BaseMessage):
    """离开队伍"""
    
    type: MessageType = MessageType.LEAVE_TEAM


class TeamLeftMessage(BaseMessage):
    """
    离开队伍成功
    
    Attributes:
        team_id: 队伍ID
    """
    
    type: MessageType = MessageType.TEAM_LEFT
    team_id: str = Field(..., description="队伍ID")


class KickTeamMemberMessage(BaseMessage):
    """
    踢出队伍成员
    
    Attributes:
        player_id: 要踢出的玩家ID
    """
    
    type: MessageType = MessageType.KICK_TEAM_MEMBER
    player_id: str = Field(..., description="要踢出的玩家ID")


class TeamMemberKickedMessage(BaseMessage):
    """
    成员被踢出
    
    Attributes:
        team_id: 队伍ID
        player_id: 被踢出的玩家ID
    """
    
    type: MessageType = MessageType.TEAM_MEMBER_KICKED
    team_id: str = Field(..., description="队伍ID")
    player_id: str = Field(..., description="被踢出的玩家ID")


class InviteTeamMessage(BaseMessage):
    """
    邀请加入队伍
    
    Attributes:
        player_id: 被邀请者ID
    """
    
    type: MessageType = MessageType.INVITE_TEAM
    player_id: str = Field(..., description="被邀请者ID")


class TeamInviteSentMessage(BaseMessage):
    """
    队伍邀请已发送
    
    Attributes:
        team_id: 队伍ID
        player_id: 被邀请者ID
    """
    
    type: MessageType = MessageType.TEAM_INVITE_SENT
    team_id: str = Field(..., description="队伍ID")
    player_id: str = Field(..., description="被邀请者ID")


class TeamInviteReceivedMessage(BaseMessage):
    """
    收到队伍邀请
    
    Attributes:
        invite: 邀请数据
    """
    
    type: MessageType = MessageType.TEAM_INVITE_RECEIVED
    invite: TeamInviteData = Field(..., description="邀请数据")


class AcceptTeamInviteMessage(BaseMessage):
    """
    接受队伍邀请
    
    Attributes:
        invite_id: 邀请ID
    """
    
    type: MessageType = MessageType.ACCEPT_TEAM_INVITE
    invite_id: str = Field(..., description="邀请ID")


class RejectTeamInviteMessage(BaseMessage):
    """
    拒绝队伍邀请
    
    Attributes:
        invite_id: 邀请ID
    """
    
    type: MessageType = MessageType.REJECT_TEAM_INVITE
    invite_id: str = Field(..., description="邀请ID")


class GetTeamInfoMessage(BaseMessage):
    """获取队伍信息"""
    
    type: MessageType = MessageType.GET_TEAM_INFO


class TeamInfoMessage(BaseMessage):
    """
    队伍信息响应
    
    Attributes:
        team: 队伍信息（None表示不在队伍中）
    """
    
    type: MessageType = MessageType.TEAM_INFO
    team: Optional[TeamInfoData] = Field(default=None, description="队伍信息")


class TeamDisbandedMessage(BaseMessage):
    """
    队伍已解散
    
    Attributes:
        team_id: 队伍ID
    """
    
    type: MessageType = MessageType.TEAM_DISBANDED
    team_id: str = Field(..., description="队伍ID")


class TeamMemberJoinedMessage(BaseMessage):
    """
    成员加入队伍广播
    
    Attributes:
        team_id: 队伍ID
        player_id: 加入的玩家ID
        player_info: 玩家信息
    """
    
    type: MessageType = MessageType.TEAM_MEMBER_JOINED
    team_id: str = Field(..., description="队伍ID")
    player_id: str = Field(..., description="加入的玩家ID")
    player_info: PlayerInfoData = Field(..., description="玩家信息")


class TeamMemberLeftMessage(BaseMessage):
    """
    成员离开队伍广播
    
    Attributes:
        team_id: 队伍ID
        player_id: 离开的玩家ID
    """
    
    type: MessageType = MessageType.TEAM_MEMBER_LEFT
    team_id: str = Field(..., description="队伍ID")
    player_id: str = Field(..., description="离开的玩家ID")


# ============================================================================
# 好友系统数据模型
# ============================================================================

class FriendInfoData(BaseModel):
    """好友信息数据"""
    
    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str = Field(default="", description="头像")
    status: str = Field(default="offline", description="在线状态")
    status_text: str = Field(default="离线", description="状态文本")
    tier: str = Field(default="bronze", description="段位")
    stars: int = Field(default=0, description="星数")
    display_rank: str = Field(default="", description="段位显示")
    relation: str = Field(default="friend", description="关系")
    last_online_at: Optional[str] = Field(default=None, description="最后在线时间")
    is_online: bool = Field(default=False, description="是否在线")
    in_game_info: Optional[dict[str, Any]] = Field(default=None, description="游戏中信息")


class FriendRequestData(BaseModel):
    """好友请求数据"""
    
    request_id: str = Field(..., description="请求ID")
    from_player_id: str = Field(..., description="发送者ID")
    to_player_id: str = Field(..., description="接收者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    from_avatar: str = Field(default="", description="发送者头像")
    message: str = Field(default="", description="附带消息")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class PrivateMessageData(BaseModel):
    """私聊消息数据"""
    
    message_id: str = Field(..., description="消息ID")
    from_player_id: str = Field(..., description="发送者ID")
    to_player_id: str = Field(..., description="接收者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    from_avatar: str = Field(default="", description="发送者头像")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class PlayerSearchInfoData(BaseModel):
    """玩家搜索结果数据"""
    
    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str = Field(default="", description="头像")
    tier: str = Field(default="bronze", description="段位")
    stars: int = Field(default=0, description="星数")
    is_friend: bool = Field(default=False, description="是否已是好友")
    has_pending_request: bool = Field(default=False, description="是否有待处理请求")


class TeamInfoData(BaseModel):
    """队伍信息数据"""
    
    team_id: str = Field(..., description="队伍ID")
    leader_id: str = Field(..., description="队长ID")
    members: list[PlayerInfoData] = Field(default_factory=list, description="成员列表")
    member_count: int = Field(default=0, description="成员数")
    max_members: int = Field(default=3, description="最大成员数")
    is_full: bool = Field(default=False, description="是否已满")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class TeamInviteData(BaseModel):
    """队伍邀请数据"""
    
    invite_id: str = Field(..., description="邀请ID")
    team_id: str = Field(..., description="队伍ID")
    inviter_id: str = Field(..., description="邀请者ID")
    inviter_nickname: str = Field(default="", description="邀请者昵称")
    team_member_count: int = Field(default=1, description="队伍成员数")
    created_at: Optional[str] = Field(default=None, description="创建时间")


# ============================================================================
# 排行榜系统消息
# ============================================================================

class GetLeaderboardMessage(BaseMessage):
    """
    获取排行榜请求
    
    Attributes:
        leaderboard_type: 排行榜类型 (tier/win_rate/first_place/damage/wealth)
        period: 排行榜周期 (weekly/monthly/season)
        page: 页码（从1开始）
        page_size: 每页大小
    """
    
    type: MessageType = MessageType.GET_LEADERBOARD
    leaderboard_type: str = Field(default="tier", description="排行榜类型")
    period: str = Field(default="weekly", description="排行榜周期")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=100, description="每页大小")


class LeaderboardEntryData(BaseModel):
    """排行榜条目数据"""
    
    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str = Field(default="", description="头像")
    rank: int = Field(default=0, description="排名")
    score: float = Field(default=0.0, description="分数")
    tier: str = Field(default="bronze", description="段位")
    stars: int = Field(default=0, description="星数")
    display_rank: str = Field(default="", description="段位显示")
    extra_data: dict[str, Any] = Field(default_factory=dict, description="额外数据")


class LeaderboardDataMessage(BaseMessage):
    """
    排行榜数据响应
    
    Attributes:
        leaderboard_type: 排行榜类型
        leaderboard_type_name: 排行榜类型名称
        period: 排行榜周期
        period_name: 周期名称
        entries: 排行榜条目列表
        total_count: 总记录数
        page: 当前页码
        page_size: 每页大小
        total_pages: 总页数
        updated_at: 更新时间
        period_start: 周期开始时间
        period_end: 周期结束时间
    """
    
    type: MessageType = MessageType.LEADERBOARD_DATA
    leaderboard_type: str = Field(..., description="排行榜类型")
    leaderboard_type_name: str = Field(default="", description="排行榜类型名称")
    period: str = Field(..., description="排行榜周期")
    period_name: str = Field(default="", description="周期名称")
    entries: list[LeaderboardEntryData] = Field(default_factory=list, description="条目列表")
    total_count: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=50, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")
    updated_at: Optional[str] = Field(default=None, description="更新时间")
    period_start: Optional[str] = Field(default=None, description="周期开始时间")
    period_end: Optional[str] = Field(default=None, description="周期结束时间")


class GetPlayerRankMessage(BaseMessage):
    """
    获取玩家排名请求
    
    Attributes:
        leaderboard_type: 排行榜类型（可选，不传则返回所有类型）
        period: 排行榜周期（可选，不传则返回所有周期）
    """
    
    type: MessageType = MessageType.GET_PLAYER_RANK
    leaderboard_type: Optional[str] = Field(default=None, description="排行榜类型")
    period: Optional[str] = Field(default=None, description="排行榜周期")


class PlayerRankInfoData(BaseModel):
    """玩家排名信息数据"""
    
    player_id: str = Field(..., description="玩家ID")
    leaderboard_type: str = Field(..., description="排行榜类型")
    leaderboard_type_name: str = Field(default="", description="排行榜类型名称")
    period: str = Field(..., description="排行榜周期")
    period_name: str = Field(default="", description="周期名称")
    rank: int = Field(default=0, description="排名")
    score: float = Field(default=0.0, description="分数")
    total_players: int = Field(default=0, description="总参与人数")
    percentile: float = Field(default=100.0, description="百分位排名")
    history_rank: int = Field(default=0, description="排名变化")
    rank_change_text: str = Field(default="", description="排名变化文本")
    rewards_claimed: bool = Field(default=False, description="是否已领取奖励")
    best_rank: int = Field(default=0, description="历史最佳排名")
    is_ranked: bool = Field(default=False, description="是否上榜")


class PlayerRankInfoMessage(BaseMessage):
    """
    玩家排名信息响应
    
    Attributes:
        ranks: 玩家排名信息列表（可能有多个类型/周期）
    """
    
    type: MessageType = MessageType.PLAYER_RANK_INFO
    ranks: list[PlayerRankInfoData] = Field(default_factory=list, description="排名信息列表")


class LeaderboardListMessage(BaseMessage):
    """获取排行榜列表请求"""
    
    type: MessageType = MessageType.LEADERBOARD_LIST


class LeaderboardOverviewData(BaseModel):
    """排行榜概览数据"""
    
    type: str = Field(..., description="排行榜类型")
    type_name: str = Field(default="", description="类型名称")
    period: str = Field(..., description="排行榜周期")
    period_name: str = Field(default="", description="周期名称")
    total_count: int = Field(default=0, description="总参与人数")
    top_players: list[dict[str, Any]] = Field(default_factory=list, description="前三名")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class LeaderboardListResultMessage(BaseMessage):
    """
    排行榜列表响应
    
    Attributes:
        leaderboards: 排行榜概览列表
        page: 页码
        page_size: 每页大小
        total_count: 总数
    """
    
    type: MessageType = MessageType.LEADERBOARD_LIST_RESULT
    leaderboards: list[LeaderboardOverviewData] = Field(default_factory=list, description="排行榜列表")
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页大小")
    total_count: int = Field(default=0, description="总数")


class ClaimLeaderboardRewardMessage(BaseMessage):
    """
    领取排行榜奖励请求
    
    Attributes:
        leaderboard_type: 排行榜类型
        period: 排行榜周期
    """
    
    type: MessageType = MessageType.CLAIM_LEADERBOARD_REWARD
    leaderboard_type: str = Field(..., description="排行榜类型")
    period: str = Field(..., description="排行榜周期")


class LeaderboardRewardData(BaseModel):
    """排行榜奖励数据"""
    
    gold: int = Field(default=0, description="金币")
    exp: int = Field(default=0, description="经验值")
    title: Optional[str] = Field(default=None, description="称号")
    avatar_frame: Optional[str] = Field(default=None, description="头像框")
    items: list[dict[str, Any]] = Field(default_factory=list, description="其他物品")


class LeaderboardRewardClaimedMessage(BaseMessage):
    """
    排行榜奖励已领取响应
    
    Attributes:
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        rank: 排名
        reward: 奖励内容
    """
    
    type: MessageType = MessageType.LEADERBOARD_REWARD_CLAIMED
    leaderboard_type: str = Field(..., description="排行榜类型")
    period: str = Field(..., description="排行榜周期")
    rank: int = Field(..., description="排名")
    reward: LeaderboardRewardData = Field(..., description="奖励内容")


# ============================================================================
# 签到系统消息
# ============================================================================

class CheckinRewardData(BaseModel):
    """签到奖励数据"""
    
    reward_id: str = Field(..., description="奖励ID")
    reward_type: str = Field(..., description="奖励类型")
    item_id: Optional[str] = Field(default=None, description="物品ID")
    quantity: int = Field(default=1, description="数量")


class CheckinStreakData(BaseModel):
    """连续签到数据"""
    
    current_streak: int = Field(default=0, description="当前连续签到天数")
    max_streak: int = Field(default=0, description="历史最大连续签到天数")
    monthly_count: int = Field(default=0, description="本月签到天数")
    total_count: int = Field(default=0, description="总签到天数")


class CheckinMessage(BaseMessage):
    """每日签到请求"""
    
    type: MessageType = MessageType.CHECKIN


class CheckinSuccessMessage(BaseMessage):
    """
    签到成功响应
    
    Attributes:
        rewards: 获得的奖励列表
        day_in_cycle: 周期天数
        streak_days: 连续签到天数
        streak_info: 连续签到信息
    """
    
    type: MessageType = MessageType.CHECKIN_SUCCESS
    rewards: list[CheckinRewardData] = Field(default_factory=list, description="奖励列表")
    day_in_cycle: int = Field(..., description="周期天数(1-7)")
    streak_days: int = Field(..., description="连续签到天数")
    streak_info: CheckinStreakData = Field(..., description="连续签到信息")


class GetCheckinInfoMessage(BaseMessage):
    """获取签到信息请求"""
    
    type: MessageType = MessageType.GET_CHECKIN_INFO


class CheckinInfoMessage(BaseMessage):
    """
    签到信息响应
    
    Attributes:
        can_checkin: 今日是否可签到
        today_checked: 今日是否已签到
        streak_info: 连续签到信息
        today_rewards: 今日签到奖励预览
        cycle_day: 当前周期天数
        monthly_count: 本月签到次数
        supplement_days: 可补签天数
    """
    
    type: MessageType = MessageType.CHECKIN_INFO
    can_checkin: bool = Field(..., description="今日是否可签到")
    today_checked: bool = Field(..., description="今日是否已签到")
    streak_info: CheckinStreakData = Field(..., description="连续签到信息")
    today_rewards: list[CheckinRewardData] = Field(default_factory=list, description="今日奖励预览")
    cycle_day: int = Field(default=1, description="周期天数")
    monthly_count: int = Field(default=0, description="本月签到次数")
    supplement_days: int = Field(default=0, description="可补签天数")


class SupplementCheckinMessage(BaseMessage):
    """
    补签请求
    
    Attributes:
        target_date: 补签日期 (YYYY-MM-DD)
    """
    
    type: MessageType = MessageType.SUPPLEMENT_CHECKIN
    target_date: str = Field(..., description="补签日期")


class SupplementSuccessMessage(BaseMessage):
    """
    补签成功响应
    
    Attributes:
        target_date: 补签日期
        rewards: 获得的奖励
        cost_diamond: 消耗钻石
    """
    
    type: MessageType = MessageType.SUPPLEMENT_SUCCESS
    target_date: str = Field(..., description="补签日期")
    rewards: list[CheckinRewardData] = Field(default_factory=list, description="奖励列表")
    cost_diamond: int = Field(..., description="消耗钻石")


class GetCheckinRecordsMessage(BaseMessage):
    """
    获取签到记录请求
    
    Attributes:
        limit: 返回数量限制
    """
    
    type: MessageType = MessageType.GET_CHECKIN_RECORDS
    limit: int = Field(default=30, description="返回数量限制")


class CheckinRecordData(BaseModel):
    """签到记录数据"""
    
    record_id: str = Field(..., description="记录ID")
    checkin_date: str = Field(..., description="签到日期")
    day_in_cycle: int = Field(default=1, description="周期天数")
    streak_days: int = Field(default=1, description="连续签到天数")
    rewards: list[CheckinRewardData] = Field(default_factory=list, description="奖励列表")
    is_supplement: bool = Field(default=False, description="是否补签")


class CheckinRecordsMessage(BaseMessage):
    """
    签到记录响应
    
    Attributes:
        records: 签到记录列表
    """
    
    type: MessageType = MessageType.CHECKIN_RECORDS
    records: list[CheckinRecordData] = Field(default_factory=list, description="签到记录列表")


class GetCheckinRewardsMessage(BaseMessage):
    """获取签到奖励配置请求"""
    
    type: MessageType = MessageType.GET_CHECKIN_REWARDS


class DailyRewardConfigData(BaseModel):
    """每日奖励配置数据"""
    
    day: int = Field(..., description="天数")
    base_rewards: list[CheckinRewardData] = Field(default_factory=list, description="基础奖励")
    bonus_rewards: list[CheckinRewardData] = Field(default_factory=list, description="额外奖励")


class CheckinRewardsMessage(BaseMessage):
    """
    签到奖励配置响应
    
    Attributes:
        daily_rewards: 7天循环奖励配置
        monthly_rewards: 月度累计奖励配置
        max_supplement_days: 最大补签天数
        supplement_base_cost: 补签基础消耗
    """
    
    type: MessageType = MessageType.CHECKIN_REWARDS
    daily_rewards: list[DailyRewardConfigData] = Field(default_factory=list, description="7天循环奖励")
    monthly_rewards: list[DailyRewardConfigData] = Field(default_factory=list, description="月度累计奖励")
    max_supplement_days: int = Field(default=3, description="最大补签天数")
    supplement_base_cost: int = Field(default=50, description="补签基础消耗")


# ============================================================================
# 羁绊图鉴系统消息
# ============================================================================

class GetSynergypediaMessage(BaseMessage):
    """获取羁绊图鉴请求"""
    
    type: MessageType = MessageType.GET_SYNERGY_PEDIA


class SynergyPediaEntryData(BaseModel):
    """羁绊图鉴条目数据"""
    
    name: str = Field(..., description="羁绊名称")
    synergy_type: str = Field(..., description="羁绊类型")
    description: str = Field(..., description="羁绊描述")
    levels: list[dict[str, Any]] = Field(default_factory=list, description="羁绊等级")
    related_heroes: list[str] = Field(default_factory=list, description="关联英雄")
    icon: str = Field(default="", description="羁绊图标")
    tips: str = Field(default="", description="使用技巧")
    progress: Optional[dict[str, Any]] = Field(default=None, description="玩家进度")


class SynergyPediaListMessage(BaseMessage):
    """
    羁绊图鉴列表响应
    
    Attributes:
        races: 种族羁绊列表
        professions: 职业羁绊列表
        total_count: 总羁绊数量
    """
    
    type: MessageType = MessageType.SYNERGY_PEDIA_LIST
    races: list[SynergyPediaEntryData] = Field(default_factory=list, description="种族羁绊")
    professions: list[SynergyPediaEntryData] = Field(default_factory=list, description="职业羁绊")
    total_count: int = Field(default=0, description="总羁绊数量")


class SynergypediaInfoMessage(BaseMessage):
    """
    获取单个羁绊详情请求
    
    Attributes:
        synergy_name: 羁绊名称
    """
    
    type: MessageType = MessageType.SYNERGY_PEDIA_INFO
    synergy_name: str = Field(..., description="羁绊名称")


class SynergyPediaDetailMessage(BaseMessage):
    """
    羁绊详情响应
    
    Attributes:
        entry: 羁绊详情
        progress: 玩家进度
        recommended_lineups: 相关推荐阵容
    """
    
    type: MessageType = MessageType.SYNERGY_PEDIA_DETAIL
    entry: SynergyPediaEntryData = Field(..., description="羁绊详情")
    progress: Optional[dict[str, Any]] = Field(default=None, description="玩家进度")
    recommended_lineups: list[dict[str, Any]] = Field(default_factory=list, description="推荐阵容")


class SimulateSynergyMessage(BaseMessage):
    """
    羁绊模拟器请求
    
    Attributes:
        hero_ids: 选中的英雄ID列表
    """
    
    type: MessageType = MessageType.SIMULATE_SYNERGY
    hero_ids: list[str] = Field(..., description="英雄ID列表")


class SynergySimulationResultMessage(BaseMessage):
    """
    模拟结果响应
    
    Attributes:
        selected_heroes: 选中的英雄
        active_synergies: 激活的羁绊
        inactive_synergies: 未激活的羁绊
        synergy_progress: 羁绊进度
        recommendations: 推荐补充英雄
        total_bonuses: 总属性加成
    """
    
    type: MessageType = MessageType.SYNERGY_SIMULATION_RESULT
    selected_heroes: list[str] = Field(default_factory=list, description="选中的英雄")
    active_synergies: list[dict[str, Any]] = Field(default_factory=list, description="激活的羁绊")
    inactive_synergies: list[dict[str, Any]] = Field(default_factory=list, description="未激活的羁绊")
    synergy_progress: dict[str, dict[str, Any]] = Field(default_factory=dict, description="羁绊进度")
    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="推荐补充英雄")
    total_bonuses: dict[str, float] = Field(default_factory=dict, description="总属性加成")


class GetSynergyRecommendationsMessage(BaseMessage):
    """
    获取阵容推荐请求
    
    Attributes:
        synergy_name: 羁绊名称（可选，用于筛选）
        limit: 返回数量限制
    """
    
    type: MessageType = MessageType.GET_SYNERGY_RECOMMENDATIONS
    synergy_name: Optional[str] = Field(default=None, description="羁绊名称")
    limit: int = Field(default=10, description="返回数量限制")


class SynergyRecommendationsResultMessage(BaseMessage):
    """
    推荐结果响应
    
    Attributes:
        recommendations: 推荐阵容列表
        total_count: 总数量
    """
    
    type: MessageType = MessageType.SYNERGY_RECOMMENDATIONS_RESULT
    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="推荐阵容")
    total_count: int = Field(default=0, description="总数量")


class GetSynergyAchievementsMessage(BaseMessage):
    """
    获取羁绊成就请求
    
    Attributes:
        synergy_name: 羁绊名称（可选，不提供则返回所有）
    """
    
    type: MessageType = MessageType.GET_SYNERGY_ACHIEVEMENTS
    synergy_name: Optional[str] = Field(default=None, description="羁绊名称")


class SynergyAchievementData(BaseModel):
    """羁绊成就数据"""
    
    achievement_id: str = Field(..., description="成就ID")
    name: str = Field(..., description="成就名称")
    description: str = Field(..., description="成就描述")
    synergy_name: str = Field(..., description="羁绊名称")
    requirement_type: str = Field(..., description="需求类型")
    requirement_value: int = Field(..., description="需求值")
    reward: dict[str, Any] = Field(default_factory=dict, description="奖励")
    is_unlocked: bool = Field(default=False, description="是否已解锁")
    progress: int = Field(default=0, description="当前进度")


class SynergyAchievementsResultMessage(BaseMessage):
    """
    成就列表响应
    
    Attributes:
        achievements: 成就列表
        total_count: 总数量
        unlocked_count: 已解锁数量
    """
    
    type: MessageType = MessageType.SYNERGY_ACHIEVEMENTS_RESULT
    achievements: list[SynergyAchievementData] = Field(default_factory=list, description="成就列表")
    total_count: int = Field(default=0, description="总数量")
    unlocked_count: int = Field(default=0, description="已解锁数量")


class SynergyAchievementUnlockedMessage(BaseMessage):
    """
    成就解锁通知
    
    Attributes:
        achievement: 解锁的成就
        rewards: 获得的奖励
    """
    
    type: MessageType = MessageType.SYNERGY_ACHIEVEMENT_UNLOCKED
    achievement: SynergyAchievementData = Field(..., description="解锁的成就")
    rewards: dict[str, Any] = Field(default_factory=dict, description="获得的奖励")


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
    
    # 阵容预设
    MessageType.LINEUP_SAVE: LineupSaveMessage,
    MessageType.LINEUP_SAVED: LineupSavedMessage,
    MessageType.LINEUP_LOAD: LineupLoadMessage,
    MessageType.LINEUP_LOADED: LineupLoadedMessage,
    MessageType.LINEUP_DELETE: LineupDeleteMessage,
    MessageType.LINEUP_DELETED: LineupDeletedMessage,
    MessageType.LINEUP_RENAME: LineupRenameMessage,
    MessageType.LINEUP_RENAMED: LineupRenamedMessage,
    MessageType.LINEUP_LIST: LineupListMessage,
    MessageType.LINEUP_LIST_RESULT: LineupListResultMessage,
    MessageType.LINEUP_APPLY: LineupApplyMessage,
    MessageType.LINEUP_APPLIED: LineupAppliedMessage,
    
    # 好友系统
    MessageType.FRIEND_REQUEST: FriendRequestMessage,
    MessageType.FRIEND_ACCEPT: FriendAcceptMessage,
    MessageType.FRIEND_REJECT: FriendRejectMessage,
    MessageType.FRIEND_REMOVE: FriendRemoveMessage,
    MessageType.FRIEND_BLOCK: FriendBlockMessage,
    MessageType.FRIEND_UNBLOCK: FriendUnblockMessage,
    MessageType.GET_FRIEND_LIST: GetFriendListMessage,
    MessageType.GET_PENDING_REQUESTS: GetPendingRequestsMessage,
    MessageType.SEARCH_PLAYER: SearchPlayerMessage,
    MessageType.FRIEND_REQUEST_RECEIVED: FriendRequestReceivedMessage,
    MessageType.FRIEND_REQUEST_SENT: FriendRequestSentMessage,
    MessageType.FRIEND_REQUEST_ACCEPTED: FriendRequestAcceptedMessage,
    MessageType.FRIEND_REQUEST_REJECTED: FriendRequestRejectedMessage,
    MessageType.FRIEND_LIST: FriendListMessage,
    MessageType.PENDING_REQUESTS: PendingRequestsMessage,
    MessageType.FRIEND_REMOVED: FriendRemovedMessage,
    MessageType.FRIEND_BLOCKED: FriendBlockedMessage,
    MessageType.FRIEND_UNBLOCKED: FriendUnblockedMessage,
    MessageType.FRIEND_STATUS_UPDATE: FriendStatusUpdateMessage,
    MessageType.PLAYER_SEARCH_RESULT: PlayerSearchResultMessage,
    
    # 私聊系统
    MessageType.PRIVATE_MESSAGE: PrivateMessage,
    MessageType.GET_CHAT_HISTORY: GetChatHistoryMessage,
    MessageType.MARK_MESSAGES_READ: MarkMessagesReadMessage,
    MessageType.PRIVATE_MESSAGE_RECEIVED: PrivateMessageReceivedMessage,
    MessageType.CHAT_HISTORY: ChatHistoryMessage,
    MessageType.MESSAGES_READ: MessagesReadMessage,
    MessageType.UNREAD_COUNT: UnreadCountMessage,
    
    # 组队系统
    MessageType.CREATE_TEAM: CreateTeamMessage,
    MessageType.JOIN_TEAM: JoinTeamMessage,
    MessageType.LEAVE_TEAM: LeaveTeamMessage,
    MessageType.KICK_TEAM_MEMBER: KickTeamMemberMessage,
    MessageType.INVITE_TEAM: InviteTeamMessage,
    MessageType.ACCEPT_TEAM_INVITE: AcceptTeamInviteMessage,
    MessageType.REJECT_TEAM_INVITE: RejectTeamInviteMessage,
    MessageType.GET_TEAM_INFO: GetTeamInfoMessage,
    MessageType.TEAM_CREATED: TeamCreatedMessage,
    MessageType.TEAM_JOINED: TeamJoinedMessage,
    MessageType.TEAM_LEFT: TeamLeftMessage,
    MessageType.TEAM_MEMBER_KICKED: TeamMemberKickedMessage,
    MessageType.TEAM_INVITE_RECEIVED: TeamInviteReceivedMessage,
    MessageType.TEAM_INVITE_SENT: TeamInviteSentMessage,
    MessageType.TEAM_INFO: TeamInfoMessage,
    MessageType.TEAM_DISBANDED: TeamDisbandedMessage,
    MessageType.TEAM_MEMBER_JOINED: TeamMemberJoinedMessage,
    MessageType.TEAM_MEMBER_LEFT: TeamMemberLeftMessage,
    
    # 排行榜系统
    MessageType.GET_LEADERBOARD: GetLeaderboardMessage,
    MessageType.LEADERBOARD_DATA: LeaderboardDataMessage,
    MessageType.GET_PLAYER_RANK: GetPlayerRankMessage,
    MessageType.PLAYER_RANK_INFO: PlayerRankInfoMessage,
    MessageType.LEADERBOARD_LIST: LeaderboardListMessage,
    MessageType.LEADERBOARD_LIST_RESULT: LeaderboardListResultMessage,
    MessageType.CLAIM_LEADERBOARD_REWARD: ClaimLeaderboardRewardMessage,
    MessageType.LEADERBOARD_REWARD_CLAIMED: LeaderboardRewardClaimedMessage,
    
    # 签到系统
    MessageType.CHECKIN: CheckinMessage,
    MessageType.CHECKIN_SUCCESS: CheckinSuccessMessage,
    MessageType.GET_CHECKIN_INFO: GetCheckinInfoMessage,
    MessageType.CHECKIN_INFO: CheckinInfoMessage,
    MessageType.SUPPLEMENT_CHECKIN: SupplementCheckinMessage,
    MessageType.SUPPLEMENT_SUCCESS: SupplementSuccessMessage,
    MessageType.GET_CHECKIN_RECORDS: GetCheckinRecordsMessage,
    MessageType.CHECKIN_RECORDS: CheckinRecordsMessage,
    MessageType.GET_CHECKIN_REWARDS: GetCheckinRewardsMessage,
    MessageType.CHECKIN_REWARDS: CheckinRewardsMessage,
    
    # 羁绊图鉴系统
    MessageType.GET_SYNERGY_PEDIA: GetSynergypediaMessage,
    MessageType.SYNERGY_PEDIA_LIST: SynergyPediaListMessage,
    MessageType.SYNERGY_PEDIA_INFO: SynergypediaInfoMessage,
    MessageType.SYNERGY_PEDIA_DETAIL: SynergyPediaDetailMessage,
    MessageType.SIMULATE_SYNERGY: SimulateSynergyMessage,
    MessageType.SYNERGY_SIMULATION_RESULT: SynergySimulationResultMessage,
    MessageType.GET_SYNERGY_RECOMMENDATIONS: GetSynergyRecommendationsMessage,
    MessageType.SYNERGY_RECOMMENDATIONS_RESULT: SynergyRecommendationsResultMessage,
    MessageType.GET_SYNERGY_ACHIEVEMENTS: GetSynergyAchievementsMessage,
    MessageType.SYNERGY_ACHIEVEMENTS_RESULT: SynergyAchievementsResultMessage,
    MessageType.SYNERGY_ACHIEVEMENT_UNLOCKED: SynergyAchievementUnlockedMessage,
    
    # 错误
    MessageType.ERROR: ErrorMessage,
}
