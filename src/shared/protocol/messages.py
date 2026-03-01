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
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# 消息类型枚举
# ============================================================================


class MessageType(str, Enum):
    """消息类型枚举"""

    # ========== 连接相关 ==========
    # 客户端 -> 服务器
    CONNECT = "connect"  # 连接请求
    DISCONNECT = "disconnect"  # 断开连接
    HEARTBEAT = "heartbeat"  # 心跳
    RECONNECT = "reconnect"  # 断线重连

    # 服务器 -> 客户端
    CONNECTED = "connected"  # 连接成功
    RECONNECTED = "reconnected"  # 重连成功
    HEARTBEAT_ACK = "heartbeat_ack"  # 心跳响应

    # ========== 房间相关 ==========
    # 客户端 -> 服务器
    CREATE_ROOM = "create_room"  # 创建房间
    JOIN_ROOM = "join_room"  # 加入房间
    LEAVE_ROOM = "leave_room"  # 离开房间
    READY = "ready"  # 准备
    CANCEL_READY = "cancel_ready"  # 取消准备
    GET_ROOM_INFO = "get_room_info"  # 获取房间信息
    GET_ROOM_LIST = "get_room_list"  # 获取房间列表

    # 服务器 -> 客户端
    ROOM_CREATED = "room_created"  # 房间创建成功
    ROOM_JOINED = "room_joined"  # 加入房间成功
    ROOM_LEFT = "room_left"  # 离开房间
    ROOM_INFO = "room_info"  # 房间信息
    ROOM_LIST = "room_list"  # 房间列表
    PLAYER_JOINED = "player_joined"  # 玩家加入广播
    PLAYER_LEFT = "player_left"  # 玩家离开广播
    PLAYER_READY_CHANGED = "player_ready_changed"  # 玩家准备状态变化

    # ========== 商店操作 ==========
    # 客户端 -> 服务器
    SHOP_REFRESH = "shop_refresh"  # 刷新商店
    SHOP_BUY = "shop_buy"  # 购买英雄
    HERO_SELL = "hero_sell"  # 出售英雄
    SHOP_LOCK = "shop_lock"  # 锁定商店
    SHOP_UNLOCK = "shop_unlock"  # 解锁商店

    # 服务器 -> 客户端
    SHOP_REFRESHED = "shop_refreshed"  # 商店已刷新
    SHOP_BUY_SUCCESS = "shop_buy_success"  # 购买成功
    HERO_SOLD = "hero_sold"  # 英雄已出售
    SHOP_LOCKED = "shop_locked"  # 商店已锁定
    SHOP_UNLOCKED = "shop_unlocked"  # 商店已解锁

    # ========== 英雄操作 ==========
    # 客户端 -> 服务器
    HERO_PLACE = "hero_place"  # 放置英雄到棋盘
    HERO_MOVE = "hero_move"  # 移动英雄
    HERO_REMOVE = "hero_remove"  # 移除英雄（放回备战席）
    HERO_UPGRADE = "hero_upgrade"  # 合成升级英雄

    # 服务器 -> 客户端
    HERO_PLACED = "hero_placed"  # 英雄已放置
    HERO_MOVED = "hero_moved"  # 英雄已移动
    HERO_REMOVED = "hero_removed"  # 英雄已移除
    HERO_UPGRADED = "hero_upgraded"  # 英雄已升级

    # ========== 回合状态 ==========
    # 服务器 -> 客户端（广播）
    ROUND_START = "round_start"  # 回合开始
    PREPARATION_START = "preparation_start"  # 准备阶段开始
    BATTLE_START = "battle_start"  # 战斗阶段开始
    ROUND_END = "round_end"  # 回合结束

    # ========== 战斗同步 ==========
    # 服务器 -> 客户端（广播）
    BATTLE_SYNC = "battle_sync"  # 战斗状态同步
    BATTLE_EVENT = "battle_event"  # 战斗事件（伤害、死亡、技能等）
    BATTLE_RESULT = "battle_result"  # 战斗结果

    # ========== 玩家状态 ==========
    # 服务器 -> 客户端
    PLAYER_STATE_UPDATE = "player_state_update"  # 玩家状态更新
    PLAYER_HP_UPDATE = "player_hp_update"  # 玩家血量更新
    PLAYER_GOLD_UPDATE = "player_gold_update"  # 玩家金币更新
    PLAYER_LEVEL_UPDATE = "player_level_update"  # 玩家等级更新
    PLAYER_ELIMINATED = "player_eliminated"  # 玩家被淘汰

    # ========== 游戏流程 ==========
    # 服务器 -> 客户端
    GAME_START = "game_start"  # 游戏开始
    GAME_OVER = "game_over"  # 游戏结束
    GAME_PAUSE = "game_pause"  # 游戏暂停
    GAME_RESUME = "game_resume"  # 游戏恢复

    # ========== 羁绊/阵容 ==========
    # 服务器 -> 客户端
    SYNERGY_UPDATE = "synergy_update"  # 羁绊状态更新

    # ========== 经验/升级 ==========
    # 客户端 -> 服务器
    BUY_EXP = "buy_exp"  # 购买经验

    # 服务器 -> 客户端
    EXP_GAINED = "exp_gained"  # 获得经验
    LEVEL_UP = "level_up"  # 等级提升

    # ========== 阵容预设 ==========
    # 客户端 -> 服务器
    LINEUP_SAVE = "lineup_save"  # 保存阵容预设
    LINEUP_LOAD = "lineup_load"  # 加载阵容预设
    LINEUP_DELETE = "lineup_delete"  # 删除阵容预设
    LINEUP_RENAME = "lineup_rename"  # 重命名阵容预设
    LINEUP_LIST = "lineup_list"  # 获取预设列表
    LINEUP_APPLY = "lineup_apply"  # 应用预设到对局

    # 服务器 -> 客户端
    LINEUP_SAVED = "lineup_saved"  # 预设保存成功
    LINEUP_LOADED = "lineup_loaded"  # 预设加载成功
    LINEUP_DELETED = "lineup_deleted"  # 预设删除成功
    LINEUP_RENAMED = "lineup_renamed"  # 预设重命名成功
    LINEUP_LIST_RESULT = "lineup_list_result"  # 预设列表结果
    LINEUP_APPLIED = "lineup_applied"  # 预设应用成功

    # ========== 好友系统 ==========
    # 客户端 -> 服务器
    FRIEND_REQUEST = "friend_request"  # 发送好友请求
    FRIEND_ACCEPT = "friend_accept"  # 接受好友请求
    FRIEND_REJECT = "friend_reject"  # 拒绝好友请求
    FRIEND_REMOVE = "friend_remove"  # 删除好友
    FRIEND_BLOCK = "friend_block"  # 拉黑玩家
    FRIEND_UNBLOCK = "friend_unblock"  # 取消拉黑
    GET_FRIEND_LIST = "get_friend_list"  # 获取好友列表
    GET_PENDING_REQUESTS = "get_pending_requests"  # 获取待处理请求
    SEARCH_PLAYER = "search_player"  # 搜索玩家

    # 服务器 -> 客户端
    FRIEND_REQUEST_RECEIVED = "friend_request_received"  # 收到好友请求
    FRIEND_REQUEST_SENT = "friend_request_sent"  # 好友请求已发送
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"  # 好友请求已接受
    FRIEND_REQUEST_REJECTED = "friend_request_rejected"  # 好友请求已拒绝
    FRIEND_LIST = "friend_list"  # 好友列表
    PENDING_REQUESTS = "pending_requests"  # 待处理请求列表
    FRIEND_REMOVED = "friend_removed"  # 好友已删除
    FRIEND_BLOCKED = "friend_blocked"  # 玩家已拉黑
    FRIEND_UNBLOCKED = "friend_unblocked"  # 玩家已取消拉黑
    FRIEND_STATUS_UPDATE = "friend_status_update"  # 好友状态更新
    PLAYER_SEARCH_RESULT = "player_search_result"  # 玩家搜索结果

    # ========== 私聊系统 ==========
    # 客户端 -> 服务器
    PRIVATE_MESSAGE = "private_message"  # 发送私聊消息
    GET_CHAT_HISTORY = "get_chat_history"  # 获取聊天记录
    MARK_MESSAGES_READ = "mark_messages_read"  # 标记消息已读

    # 服务器 -> 客户端
    PRIVATE_MESSAGE_RECEIVED = "private_message_received"  # 收到私聊消息
    CHAT_HISTORY = "chat_history"  # 聊天记录
    MESSAGES_READ = "messages_read"  # 消息已读确认
    UNREAD_COUNT = "unread_count"  # 未读消息数

    # ========== 组队系统 ==========
    # 客户端 -> 服务器
    CREATE_TEAM = "create_team"  # 创建队伍
    JOIN_TEAM = "join_team"  # 加入队伍
    LEAVE_TEAM = "leave_team"  # 离开队伍
    KICK_TEAM_MEMBER = "kick_team_member"  # 踢出成员
    INVITE_TEAM = "invite_team"  # 邀请加入队伍
    ACCEPT_TEAM_INVITE = "accept_team_invite"  # 接受队伍邀请
    REJECT_TEAM_INVITE = "reject_team_invite"  # 拒绝队伍邀请
    GET_TEAM_INFO = "get_team_info"  # 获取队伍信息

    # 服务器 -> 客户端
    TEAM_CREATED = "team_created"  # 队伍创建成功
    TEAM_JOINED = "team_joined"  # 加入队伍成功
    TEAM_LEFT = "team_left"  # 离开队伍成功
    TEAM_MEMBER_KICKED = "team_member_kicked"  # 成员被踢出
    TEAM_INVITE_RECEIVED = "team_invite_received"  # 收到队伍邀请
    TEAM_INVITE_SENT = "team_invite_sent"  # 队伍邀请已发送
    TEAM_INFO = "team_info"  # 队伍信息
    TEAM_DISBANDED = "team_disbanded"  # 队伍已解散
    TEAM_MEMBER_JOINED = "team_member_joined"  # 成员加入队伍
    TEAM_MEMBER_LEFT = "team_member_left"  # 成员离开队伍

    # ========== 排行榜系统 ==========
    # 客户端 -> 服务器
    GET_LEADERBOARD = "get_leaderboard"  # 获取排行榜
    GET_PLAYER_RANK = "get_player_rank"  # 获取玩家排名
    LEADERBOARD_LIST = "leaderboard_list"  # 获取排行榜列表
    CLAIM_LEADERBOARD_REWARD = "claim_leaderboard_reward"  # 领取排行榜奖励

    # 服务器 -> 客户端
    LEADERBOARD_DATA = "leaderboard_data"  # 排行榜数据
    PLAYER_RANK_INFO = "player_rank_info"  # 玩家排名信息
    LEADERBOARD_LIST_RESULT = "leaderboard_list_result"  # 排行榜列表结果
    LEADERBOARD_REWARD_CLAIMED = "leaderboard_reward_claimed"  # 排行榜奖励已领取

    # ========== 签到系统 ==========
    # 客户端 -> 服务器
    CHECKIN = "checkin"  # 每日签到
    GET_CHECKIN_INFO = "get_checkin_info"  # 获取签到信息
    SUPPLEMENT_CHECKIN = "supplement_checkin"  # 补签
    GET_CHECKIN_RECORDS = "get_checkin_records"  # 获取签到记录
    GET_CHECKIN_REWARDS = "get_checkin_rewards"  # 获取签到奖励配置

    # 服务器 -> 客户端
    CHECKIN_SUCCESS = "checkin_success"  # 签到成功
    CHECKIN_INFO = "checkin_info"  # 签到信息
    CHECKIN_RECORDS = "checkin_records"  # 签到记录列表
    CHECKIN_REWARDS = "checkin_rewards"  # 签到奖励配置
    SUPPLEMENT_SUCCESS = "supplement_success"  # 补签成功

    # ========== 羁绊图鉴系统 ==========
    # 客户端 -> 服务器
    GET_SYNERGY_PEDIA = "get_synergy_pedia"  # 获取羁绊图鉴
    SYNERGY_PEDIA_INFO = "synergy_pedia_info"  # 获取单个羁绊详情
    SIMULATE_SYNERGY = "simulate_synergy"  # 羁绊模拟器
    GET_SYNERGY_RECOMMENDATIONS = "get_synergy_recommendations"  # 获取阵容推荐
    GET_SYNERGY_ACHIEVEMENTS = "get_synergy_achievements"  # 获取羁绊成就

    # 服务器 -> 客户端
    SYNERGY_PEDIA_LIST = "synergy_pedia_list"  # 羁绊图鉴列表
    SYNERGY_PEDIA_DETAIL = "synergy_pedia_detail"  # 羁绊详情
    SYNERGY_SIMULATION_RESULT = "synergy_simulation_result"  # 模拟结果
    SYNERGY_RECOMMENDATIONS_RESULT = "synergy_recommendations_result"  # 推荐结果
    SYNERGY_ACHIEVEMENTS_RESULT = "synergy_achievements_result"  # 成就列表
    SYNERGY_ACHIEVEMENT_UNLOCKED = "synergy_achievement_unlocked"  # 成就解锁通知

    # ========== 皮肤系统 ==========
    # 客户端 -> 服务器
    GET_SKINS = "get_skins"  # 获取皮肤列表
    GET_HERO_SKINS = "get_hero_skins"  # 获取英雄皮肤列表
    GET_OWNED_SKINS = "get_owned_skins"  # 获取已拥有皮肤
    EQUIP_SKIN = "equip_skin"  # 装备皮肤
    UNEQUIP_SKIN = "unequip_skin"  # 卸下皮肤
    BUY_SKIN = "buy_skin"  # 购买皮肤
    SET_FAVORITE_SKIN = "set_favorite_skin"  # 设置收藏皮肤

    # 服务器 -> 客户端
    SKINS_LIST = "skins_list"  # 皮肤列表
    HERO_SKINS_LIST = "hero_skins_list"  # 英雄皮肤列表
    OWNED_SKINS_LIST = "owned_skins_list"  # 已拥有皮肤列表
    SKIN_EQUIPPED = "skin_equipped"  # 皮肤已装备
    SKIN_UNEQUIPPED = "skin_unequipped"  # 皮肤已卸下
    SKIN_BOUGHT = "skin_bought"  # 皮肤已购买
    SKIN_UNLOCKED = "skin_unlocked"  # 皮肤已解锁
    SKIN_FAVORITE_SET = "skin_favorite_set"  # 收藏设置成功

    # ========== 英雄碎片系统 ==========
    # 客户端 -> 服务器
    GET_SHARD_BACKPACK = "get_shard_backpack"  # 获取碎片背包
    COMPOSE_HERO = "compose_hero"  # 合成英雄
    DECOMPOSE_HERO = "decompose_hero"  # 分解英雄
    BATCH_COMPOSE = "batch_compose"  # 批量合成
    BATCH_DECOMPOSE = "batch_decompose"  # 批量分解
    ONE_KEY_COMPOSE = "one_key_compose"  # 一键合成
    GET_COMPOSE_REQUIREMENTS = "get_compose_requirements"  # 获取合成要求
    GET_DECOMPOSE_REWARDS = "get_decompose_rewards"  # 获取分解奖励

    # 服务器 -> 客户端
    SHARD_BACKPACK = "shard_backpack"  # 碎片背包响应
    HERO_COMPOSED = "hero_composed"  # 英雄合成成功
    HERO_DECOMPOSED = "hero_decomposed"  # 英雄分解成功
    BATCH_COMPOSE_RESULT = "batch_compose_result"  # 批量合成结果
    BATCH_DECOMPOSE_RESULT = "batch_decompose_result"  # 批量分解结果
    COMPOSE_REQUIREMENTS = "compose_requirements"  # 合成要求响应
    DECOMPOSE_REWARDS = "decompose_rewards"  # 分解奖励响应
    SHARD_UPDATED = "shard_updated"  # 碎片更新通知
    CAN_COMPOSE_NOTIFY = "can_compose_notify"  # 可合成通知

    # ========== 错误消息 ==========
    # ========== 观战系统 ==========
    # 客户端 -> 服务器
    GET_SPECTATABLE_GAMES = "get_spectatable_games"  # 获取可观战对局列表
    JOIN_SPECTATE = "join_spectate"  # 加入观战
    LEAVE_SPECTATE = "leave_spectate"  # 离开观战
    SPECTATE_SWITCH = "spectate_switch"  # 切换观战对象
    SPECTATE_SYNC = "spectate_sync"  # 请求同步状态
    SPECTATE_CHAT = "spectate_chat"  # 发送弹幕

    # 服务器 -> 客户端
    SPECTATABLE_GAMES_LIST = "spectatable_games_list"  # 可观战对局列表
    SPECTATE_JOINED = "spectate_joined"  # 加入观战成功
    SPECTATE_LEFT = "spectate_left"  # 离开观战成功
    SPECTATE_STATE = "spectate_state"  # 观战状态同步
    SPECTATE_CHAT_RECEIVED = "spectate_chat_received"  # 收到弹幕
    SPECTATE_ENDED = "spectate_ended"  # 观战结束通知

    # ========== 随机事件系统 ==========
    # 客户端 -> 服务器
    GET_EVENT_HISTORY = "get_event_history"  # 获取事件历史
    GET_ACTIVE_EVENTS = "get_active_events"  # 获取当前活跃事件

    # 服务器 -> 客户端
    RANDOM_EVENT_TRIGGERED = "random_event_triggered"  # 事件触发广播
    EVENT_HISTORY = "event_history"  # 事件历史响应
    ACTIVE_EVENTS = "active_events"  # 活跃事件响应

    # ========== 投票系统 ==========
    # 客户端 -> 服务器
    GET_VOTING_LIST = "get_voting_list"  # 获取投票列表
    GET_VOTING_DETAILS = "get_voting_details"  # 获取投票详情
    VOTE = "vote"  # 投票
    GET_VOTING_RESULTS = "get_voting_results"  # 获取投票结果
    CLAIM_VOTING_REWARDS = "claim_voting_rewards"  # 领取投票奖励

    # 服务器 -> 客户端
    VOTING_LIST = "voting_list"  # 投票列表响应
    VOTING_DETAILS = "voting_details"  # 投票详情响应
    VOTE_CASTED = "vote_casted"  # 投票成功
    VOTING_RESULTS = "voting_results"  # 投票结果响应
    VOTING_REWARDS_CLAIMED = "voting_rewards_claimed"  # 奖励领取成功

    # ========== 回放系统 ==========
    # 客户端 -> 服务器
    SAVE_REPLAY = "save_replay"  # 保存回放
    GET_REPLAY_LIST = "get_replay_list"  # 获取回放列表
    LOAD_REPLAY = "load_replay"  # 加载回放
    DELETE_REPLAY = "delete_replay"  # 删除回放
    REPLAY_CONTROL = "replay_control"  # 回放控制（播放/暂停/停止/倍速/跳转）
    EXPORT_REPLAY = "export_replay"  # 导出回放
    IMPORT_REPLAY = "import_replay"  # 导入回放

    # 服务器 -> 客户端
    REPLAY_SAVED = "replay_saved"  # 回放保存成功
    REPLAY_LIST = "replay_list"  # 回放列表响应
    REPLAY_LOADED = "replay_loaded"  # 回放加载成功
    REPLAY_DELETED = "replay_deleted"  # 回放删除成功
    REPLAY_EXPORTED = "replay_exported"  # 回放导出成功
    REPLAY_IMPORTED = "replay_imported"  # 回放导入成功
    REPLAY_STATE_UPDATE = "replay_state_update"  # 回放状态更新

    # ========== 表情系统 ==========
    # 客户端 -> 服务器
    GET_EMOTES = "get_emotes"  # 获取表情列表
    GET_OWNED_EMOTES = "get_owned_emotes"  # 获取已拥有表情
    SEND_EMOTE = "send_emote"  # 发送表情
    SET_EMOTE_HOTKEY = "set_emote_hotkey"  # 设置表情快捷键
    GET_EMOTE_HISTORY = "get_emote_history"  # 获取表情历史

    # 服务器 -> 客户端
    EMOTES_LIST = "emotes_list"  # 表情列表响应
    OWNED_EMOTES_LIST = "owned_emotes_list"  # 已拥有表情列表
    EMOTE_SENT = "emote_sent"  # 表情发送成功
    EMOTE_RECEIVED = "emote_received"  # 收到表情（广播）
    EMOTE_HOTKEY_SET = "emote_hotkey_set"  # 快捷键设置成功
    EMOTE_HISTORY = "emote_history"  # 表情历史响应
    EMOTE_UNLOCKED = "emote_unlocked"  # 表情解锁通知

    # ========== 道具系统 ==========
    # 客户端 -> 服务器
    GET_CONSUMABLES = "get_consumables"  # 获取道具列表
    GET_PLAYER_CONSUMABLES = "get_player_consumables"  # 获取玩家道具
    USE_CONSUMABLE = "use_consumable"  # 使用道具
    BUY_CONSUMABLE = "buy_consumable"  # 购买道具
    GET_CONSUMABLE_HISTORY = "get_consumable_history"  # 获取道具使用历史

    # 服务器 -> 客户端
    CONSUMABLES_LIST = "consumables_list"  # 道具列表响应
    PLAYER_CONSUMABLES_LIST = "player_consumables_list"  # 玩家道具列表
    CONSUMABLE_USED = "consumable_used"  # 道具已使用
    CONSUMABLE_BOUGHT = "consumable_bought"  # 道具已购买
    CONSUMABLE_HISTORY = "consumable_history"  # 道具使用历史
    CONSUMABLE_ADDED = "consumable_added"  # 道具获得通知
    CONSUMABLE_EFFECT_APPLIED = "consumable_effect_applied"  # 道具效果生效

    # ========== 交易系统 ==========
    # 客户端 -> 服务器
    SEND_TRADE_REQUEST = "send_trade_request"  # 发送交易请求
    ACCEPT_TRADE_REQUEST = "accept_trade_request"  # 接受交易请求
    REJECT_TRADE_REQUEST = "reject_trade_request"  # 拒绝交易请求
    CANCEL_TRADE = "cancel_trade"  # 取消交易
    CONFIRM_TRADE = "confirm_trade"  # 确认交易
    EXECUTE_TRADE = "execute_trade"  # 执行交易
    GET_TRADE_HISTORY = "get_trade_history"  # 获取交易历史
    GET_PENDING_TRADES = "get_pending_trades"  # 获取待处理交易
    GET_TRADE_STATUS = "get_trade_status"  # 获取交易状态

    # 服务器 -> 客户端
    TRADE_REQUEST_SENT = "trade_request_sent"  # 交易请求已发送
    TRADE_REQUEST_ACCEPTED = "trade_request_accepted"  # 交易请求已接受
    TRADE_REQUEST_REJECTED = "trade_request_rejected"  # 交易请求已拒绝
    TRADE_CANCELLED = "trade_cancelled"  # 交易已取消
    TRADE_CONFIRMED = "trade_confirmed"  # 交易已确认
    TRADE_EXECUTED = "trade_executed"  # 交易已执行
    TRADE_HISTORY = "trade_history"  # 交易历史响应
    PENDING_TRADES = "pending_trades"  # 待处理交易响应
    TRADE_STATUS = "trade_status"  # 交易状态响应
    TRADE_RECEIVED = "trade_received"  # 收到交易请求通知

    # ========== AI教练系统 ==========
    # 客户端 -> 服务器
    GET_COACH_SUGGESTIONS = "get_coach_suggestions"  # 获取教练建议
    ANALYZE_LINEUP = "analyze_lineup"  # 分析阵容
    GET_LINEUP_RECOMMENDATIONS = "get_lineup_recommendations"  # 获取阵容推荐
    GET_MATCH_HISTORY = "get_match_history"  # 获取对局历史
    GET_EQUIPMENT_ADVICE = "get_equipment_advice"  # 获取装备建议
    GET_POSITION_ADVICE = "get_position_advice"  # 获取站位建议
    GET_ROUND_STRATEGY = "get_round_strategy"  # 获取回合策略
    GET_WIN_RATE_PREDICTION = "get_win_rate_prediction"  # 获取胜率预测

    # 服务器 -> 客户端
    COACH_SUGGESTIONS = "coach_suggestions"  # 教练建议响应
    LINEUP_ANALYSIS = "lineup_analysis"  # 阵容分析结果
    LINEUP_RECOMMENDATIONS = "lineup_recommendations"  # 阵容推荐响应
    MATCH_HISTORY = "match_history"  # 对局历史响应
    EQUIPMENT_ADVICE = "equipment_advice"  # 装备建议响应
    POSITION_ADVICE = "position_advice"  # 站位建议响应
    ROUND_STRATEGY = "round_strategy"  # 回合策略响应
    WIN_RATE_PREDICTION = "win_rate_prediction"  # 胜率预测响应

    # ========== 装备系统 ==========
    # 客户端 -> 服务器
    EQUIP_ITEM = "equip_item"  # 穿戴装备
    UNEQUIP_ITEM = "unequip_item"  # 卸下装备
    CRAFT_EQUIPMENT = "craft_equipment"  # 合成装备
    GET_EQUIPMENT_BAG = "get_equipment_bag"  # 获取装备背包

    # 服务器 -> 客户端
    ITEM_EQUIPPED = "item_equipped"  # 装备穿戴成功
    ITEM_UNEQUIPPED = "item_unequipped"  # 装备卸下成功
    EQUIPMENT_CRAFTED = "equipment_crafted"  # 装备合成成功
    EQUIPMENT_BAG_DATA = "equipment_bag_data"  # 装备背包响应

    # ========== 错误消息 ==========
    ERROR = "error"  # 错误消息


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
    seq: int | None = Field(default=None, description="消息序列号")
    timestamp: int | None = Field(default=None, description="消息时间戳（毫秒）")

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
    reason: str | None = Field(default=None, description="断开原因")


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
    room_id: str | None = Field(default=None, description="当前房间ID")
    game_state: dict[str, Any] | None = Field(default=None, description="游戏状态")


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
    password: str | None = Field(default=None, description="房间密码")
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
    password: str | None = Field(default=None, description="房间密码")


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
    damage: int | None = Field(default=None, description="本次受到的伤害")


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
    details: dict[str, Any] | None = Field(default=None, description="错误详情")


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
    position: PositionData | None = Field(default=None, description="位置")


class ShopSlotData(BaseModel):
    """商店槽位数据"""

    slot_index: int = Field(..., description="槽位索引")
    hero_template_id: str | None = Field(default=None, description="英雄模板ID")
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
    created_at: str | None = Field(default=None, description="创建时间")
    updated_at: str | None = Field(default=None, description="更新时间")


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
    in_game_info: dict[str, Any] | None = Field(default=None, description="游戏中信息")


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
    before_id: str | None = Field(default=None, description="此消息ID之前的记录")


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
    team: TeamInfoData | None = Field(default=None, description="队伍信息")


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
    last_online_at: str | None = Field(default=None, description="最后在线时间")
    is_online: bool = Field(default=False, description="是否在线")
    in_game_info: dict[str, Any] | None = Field(default=None, description="游戏中信息")


class FriendRequestData(BaseModel):
    """好友请求数据"""

    request_id: str = Field(..., description="请求ID")
    from_player_id: str = Field(..., description="发送者ID")
    to_player_id: str = Field(..., description="接收者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    from_avatar: str = Field(default="", description="发送者头像")
    message: str = Field(default="", description="附带消息")
    created_at: str | None = Field(default=None, description="创建时间")


class PrivateMessageData(BaseModel):
    """私聊消息数据"""

    message_id: str = Field(..., description="消息ID")
    from_player_id: str = Field(..., description="发送者ID")
    to_player_id: str = Field(..., description="接收者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    from_avatar: str = Field(default="", description="发送者头像")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")
    created_at: str | None = Field(default=None, description="创建时间")


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
    created_at: str | None = Field(default=None, description="创建时间")


class TeamInviteData(BaseModel):
    """队伍邀请数据"""

    invite_id: str = Field(..., description="邀请ID")
    team_id: str = Field(..., description="队伍ID")
    inviter_id: str = Field(..., description="邀请者ID")
    inviter_nickname: str = Field(default="", description="邀请者昵称")
    team_member_count: int = Field(default=1, description="队伍成员数")
    created_at: str | None = Field(default=None, description="创建时间")


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
    updated_at: str | None = Field(default=None, description="更新时间")
    period_start: str | None = Field(default=None, description="周期开始时间")
    period_end: str | None = Field(default=None, description="周期结束时间")


class GetPlayerRankMessage(BaseMessage):
    """
    获取玩家排名请求

    Attributes:
        leaderboard_type: 排行榜类型（可选，不传则返回所有类型）
        period: 排行榜周期（可选，不传则返回所有周期）
    """

    type: MessageType = MessageType.GET_PLAYER_RANK
    leaderboard_type: str | None = Field(default=None, description="排行榜类型")
    period: str | None = Field(default=None, description="排行榜周期")


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
    updated_at: str | None = Field(default=None, description="更新时间")


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
    leaderboards: list[LeaderboardOverviewData] = Field(
        default_factory=list, description="排行榜列表"
    )
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
    title: str | None = Field(default=None, description="称号")
    avatar_frame: str | None = Field(default=None, description="头像框")
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
    item_id: str | None = Field(default=None, description="物品ID")
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
    daily_rewards: list[DailyRewardConfigData] = Field(
        default_factory=list, description="7天循环奖励"
    )
    monthly_rewards: list[DailyRewardConfigData] = Field(
        default_factory=list, description="月度累计奖励"
    )
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
    progress: dict[str, Any] | None = Field(default=None, description="玩家进度")


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
    progress: dict[str, Any] | None = Field(default=None, description="玩家进度")
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
    inactive_synergies: list[dict[str, Any]] = Field(
        default_factory=list, description="未激活的羁绊"
    )
    synergy_progress: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="羁绊进度"
    )
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
    synergy_name: str | None = Field(default=None, description="羁绊名称")
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
    synergy_name: str | None = Field(default=None, description="羁绊名称")


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
# 随机事件系统消息
# ============================================================================


class EventEffectData(BaseModel):
    """事件效果数据"""

    effect_type: str = Field(..., description="效果类型")
    value: int = Field(default=0, description="效果数值")
    target: str = Field(default="", description="目标")
    affected_players: list[int] = Field(default_factory=list, description="受影响玩家")
    details: dict[str, Any] = Field(default_factory=dict, description="详情")


class RandomEventData(BaseModel):
    """随机事件数据"""

    event_id: str = Field(..., description="事件ID")
    name: str = Field(..., description="事件名称")
    description: str = Field(default="", description="事件描述")
    event_type: str = Field(..., description="事件类型")
    event_type_name: str = Field(default="", description="事件类型名称")
    rarity: str = Field(default="common", description="稀有度")
    rarity_name: str = Field(default="普通", description="稀有度名称")
    icon: str = Field(default="", description="图标")
    animation: str = Field(default="", description="动画")
    announcement: str = Field(default="", description="广播文本")


class EventHistoryEntryData(BaseModel):
    """事件历史条目数据"""

    entry_id: str = Field(..., description="记录ID")
    room_id: str = Field(..., description="房间ID")
    event: RandomEventData = Field(..., description="事件信息")
    round_number: int = Field(default=1, description="触发回合")
    trigger_time: str = Field(default="", description="触发时间")
    affected_players: list[int] = Field(default_factory=list, description="受影响玩家")
    effect_results: list[EventEffectData] = Field(default_factory=list, description="效果结果")


class ActiveEventData(BaseModel):
    """活跃事件数据"""

    event: RandomEventData = Field(..., description="事件信息")
    start_round: int = Field(default=1, description="开始回合")
    remaining_duration: int = Field(default=1, description="剩余持续回合")
    affected_players: list[int] = Field(default_factory=list, description="受影响玩家")


class GetEventHistoryMessage(BaseMessage):
    """
    获取事件历史请求

    Attributes:
        room_id: 房间ID
        limit: 返回数量限制
    """

    type: MessageType = MessageType.GET_EVENT_HISTORY
    room_id: str | None = Field(default=None, description="房间ID")
    limit: int = Field(default=50, description="返回数量限制")


class EventHistoryMessage(BaseMessage):
    """
    事件历史响应

    Attributes:
        room_id: 房间ID
        events: 事件历史列表
        total_count: 总数量
    """

    type: MessageType = MessageType.EVENT_HISTORY
    room_id: str = Field(..., description="房间ID")
    events: list[EventHistoryEntryData] = Field(default_factory=list, description="事件历史")
    total_count: int = Field(default=0, description="总数量")


class GetActiveEventsMessage(BaseMessage):
    """
    获取活跃事件请求

    Attributes:
        room_id: 房间ID
    """

    type: MessageType = MessageType.GET_ACTIVE_EVENTS
    room_id: str = Field(..., description="房间ID")


class ActiveEventsMessage(BaseMessage):
    """
    活跃事件响应

    Attributes:
        room_id: 房间ID
        events: 活跃事件列表
    """

    type: MessageType = MessageType.ACTIVE_EVENTS
    room_id: str = Field(..., description="房间ID")
    events: list[ActiveEventData] = Field(default_factory=list, description="活跃事件")


class RandomEventTriggeredMessage(BaseMessage):
    """
    事件触发广播

    当随机事件触发时，向房间内所有玩家广播。

    Attributes:
        room_id: 房间ID
        event: 触发的事件
        round_number: 触发回合
        effects: 效果执行结果
        affected_players: 受影响玩家列表
    """

    type: MessageType = MessageType.RANDOM_EVENT_TRIGGERED
    room_id: str = Field(..., description="房间ID")
    event: RandomEventData = Field(..., description="触发的事件")
    round_number: int = Field(..., description="触发回合")
    effects: list[EventEffectData] = Field(default_factory=list, description="效果结果")
    affected_players: list[int] = Field(default_factory=list, description="受影响玩家")


# ============================================================================
# 投票系统数据模型
# ============================================================================


class VotingOptionData(BaseModel):
    """投票选项数据"""

    option_id: str = Field(..., description="选项ID")
    title: str = Field(..., description="选项标题")
    description: str = Field(default="", description="选项描述")
    icon: str | None = Field(default=None, description="选项图标")
    vote_count: int = Field(default=0, description="当前票数")
    percentage: float = Field(default=0.0, description="得票百分比")


class VotingRewardData(BaseModel):
    """投票奖励数据"""

    reward_id: str = Field(..., description="奖励ID")
    reward_type: str = Field(..., description="奖励类型")
    item_id: str | None = Field(default=None, description="物品ID")
    quantity: int = Field(default=1, description="数量")
    is_bonus: bool = Field(default=False, description="是否为投中额外奖励")


class VotingPollData(BaseModel):
    """投票主题数据"""

    poll_id: str = Field(..., description="投票ID")
    title: str = Field(..., description="投票标题")
    description: str = Field(default="", description="投票描述")
    voting_type: str = Field(..., description="投票类型")
    status: str = Field(..., description="投票状态")
    options: list[VotingOptionData] = Field(default_factory=list, description="投票选项")
    start_time: str | None = Field(default=None, description="开始时间")
    end_time: str | None = Field(default=None, description="结束时间")
    total_votes: int = Field(default=0, description="总票数")
    total_voters: int = Field(default=0, description="参与人数")
    min_vip_level: int = Field(default=0, description="最低VIP等级要求")
    tags: list[str] = Field(default_factory=list, description="标签")


class VotingInfoData(BaseModel):
    """投票信息数据（包含玩家投票状态）"""

    poll: VotingPollData = Field(..., description="投票详情")
    player_voted: bool = Field(default=False, description="玩家是否已投票")
    player_option_id: str | None = Field(default=None, description="玩家投票选项ID")
    player_vote_weight: int = Field(default=1, description="玩家投票权重")
    can_vote: bool = Field(default=True, description="是否可以投票")
    reason: str = Field(default="", description="不能投票的原因")


class VotingResultData(BaseModel):
    """投票结果数据"""

    poll_id: str = Field(..., description="投票ID")
    winning_option_id: str | None = Field(default=None, description="获胜选项ID")
    winning_option: VotingOptionData | None = Field(default=None, description="获胜选项")
    total_votes: int = Field(default=0, description="总票数")
    total_voters: int = Field(default=0, description="参与人数")
    results: list[VotingOptionData] = Field(default_factory=list, description="各选项结果")
    ended_at: str | None = Field(default=None, description="结束时间")


# ============================================================================
# 投票系统消息
# ============================================================================


class GetVotingListMessage(BaseMessage):
    """
    获取投票列表请求

    Attributes:
        status: 状态过滤 (ongoing/ended)
        voting_type: 类型过滤
        limit: 返回数量限制
        offset: 偏移量
    """

    type: MessageType = MessageType.GET_VOTING_LIST
    status: str | None = Field(default=None, description="状态过滤")
    voting_type: str | None = Field(default=None, description="类型过滤")
    limit: int = Field(default=20, description="返回数量限制")
    offset: int = Field(default=0, description="偏移量")


class VotingListMessage(BaseMessage):
    """
    投票列表响应

    Attributes:
        polls: 投票列表
        total_count: 总数量
    """

    type: MessageType = MessageType.VOTING_LIST
    polls: list[VotingPollData] = Field(default_factory=list, description="投票列表")
    total_count: int = Field(default=0, description="总数量")


class GetVotingDetailsMessage(BaseMessage):
    """
    获取投票详情请求

    Attributes:
        poll_id: 投票ID
    """

    type: MessageType = MessageType.GET_VOTING_DETAILS
    poll_id: str = Field(..., description="投票ID")


class VotingDetailsMessage(BaseMessage):
    """
    投票详情响应

    Attributes:
        info: 投票信息（包含玩家投票状态）
    """

    type: MessageType = MessageType.VOTING_DETAILS
    info: VotingInfoData = Field(..., description="投票信息")


class VoteMessage(BaseMessage):
    """
    投票请求

    Attributes:
        poll_id: 投票ID
        option_id: 选项ID
    """

    type: MessageType = MessageType.VOTE
    poll_id: str = Field(..., description="投票ID")
    option_id: str = Field(..., description="选项ID")


class VoteCastedMessage(BaseMessage):
    """
    投票成功响应

    Attributes:
        poll_id: 投票ID
        option_id: 选择的选项ID
        vote_weight: 投票权重
        updated_poll: 更新后的投票信息
    """

    type: MessageType = MessageType.VOTE_CASTED
    poll_id: str = Field(..., description="投票ID")
    option_id: str = Field(..., description="选择的选项ID")
    vote_weight: int = Field(default=1, description="投票权重")
    updated_poll: VotingPollData = Field(..., description="更新后的投票信息")


class GetVotingResultsMessage(BaseMessage):
    """
    获取投票结果请求

    Attributes:
        poll_id: 投票ID
    """

    type: MessageType = MessageType.GET_VOTING_RESULTS
    poll_id: str = Field(..., description="投票ID")


class VotingResultsMessage(BaseMessage):
    """
    投票结果响应

    Attributes:
        result: 投票结果
    """

    type: MessageType = MessageType.VOTING_RESULTS
    result: VotingResultData = Field(..., description="投票结果")


class ClaimVotingRewardsMessage(BaseMessage):
    """
    领取投票奖励请求

    Attributes:
        poll_id: 投票ID
    """

    type: MessageType = MessageType.CLAIM_VOTING_REWARDS
    poll_id: str = Field(..., description="投票ID")


class VotingRewardsClaimedMessage(BaseMessage):
    """
    奖励领取成功响应

    Attributes:
        poll_id: 投票ID
        rewards: 领取的奖励列表
        is_winner: 是否投中获胜选项
    """

    type: MessageType = MessageType.VOTING_REWARDS_CLAIMED
    poll_id: str = Field(..., description="投票ID")
    rewards: list[VotingRewardData] = Field(default_factory=list, description="奖励列表")
    is_winner: bool = Field(default=False, description="是否投中获胜选项")


# ============================================================================
# 观战系统消息
# ============================================================================


class SpectatableGameData(BaseModel):
    """
    可观战对局数据

    Attributes:
        game_id: 对局ID
        players: 玩家列表
        created_at: 创建时间
        current_round: 当前回合
        spectator_count: 观众数量
        visibility: 可见性
        is_featured: 是否精选
    """

    game_id: str = Field(..., description="对局ID")
    players: list[dict[str, Any]] = Field(default_factory=list, description="玩家列表")
    created_at: int = Field(..., description="创建时间")
    current_round: int = Field(default=0, description="当前回合")
    spectator_count: int = Field(default=0, description="观众数量")
    visibility: str = Field(default="public", description="可见性")
    is_featured: bool = Field(default=False, description="是否精选")


class SpectatorPlayerStateData(BaseModel):
    """
    观战玩家状态数据

    Attributes:
        player_id: 玩家ID
        nickname: 昵称
        avatar: 头像
        tier: 段位
        hp: 生命值
        gold: 金币
        level: 等级
        board: 棋盘状态
        bench: 备战席状态
        synergies: 羁绊状态
    """

    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str | None = Field(default=None, description="头像")
    tier: str | None = Field(default=None, description="段位")
    hp: int = Field(default=100, description="生命值")
    gold: int = Field(default=0, description="金币")
    level: int = Field(default=1, description="等级")
    board: list[Any] = Field(default_factory=list, description="棋盘状态")
    bench: list[Any] = Field(default_factory=list, description="备战席状态")
    synergies: dict[str, Any] = Field(default_factory=dict, description="羁绊状态")


class SpectatorChatData(BaseModel):
    """
    观战弹幕数据

    Attributes:
        chat_id: 聊天ID
        sender_id: 发送者ID
        sender_name: 发送者昵称
        content: 消息内容
        sent_at: 发送时间
        message_type: 消息类型
        avatar: 头像
        tier: 段位
    """

    chat_id: str = Field(..., description="聊天ID")
    sender_id: str = Field(..., description="发送者ID")
    sender_name: str = Field(..., description="发送者昵称")
    content: str = Field(..., description="消息内容")
    sent_at: int = Field(..., description="发送时间")
    message_type: str = Field(default="text", description="消息类型")
    avatar: str | None = Field(default=None, description="头像")
    tier: str | None = Field(default=None, description="段位")


# 观战请求消息


class GetSpectatableGamesMessage(BaseMessage):
    """
    获取可观战对局列表请求

    Attributes:
        page: 页码
        page_size: 每页大小
    """

    type: MessageType = MessageType.GET_SPECTATABLE_GAMES
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页大小")


class JoinSpectateMessage(BaseMessage):
    """
    加入观战请求

    Attributes:
        game_id: 对局ID
        watching_player_id: 观看的玩家ID
    """

    type: MessageType = MessageType.JOIN_SPECTATE
    game_id: str = Field(..., description="对局ID")
    watching_player_id: str = Field(..., description="观看的玩家ID")


class LeaveSpectateMessage(BaseMessage):
    """
    离开观战请求

    Attributes:
        game_id: 对局ID
    """

    type: MessageType = MessageType.LEAVE_SPECTATE
    game_id: str = Field(..., description="对局ID")


class SpectateSwitchMessage(BaseMessage):
    """
    切换观战对象请求

    Attributes:
        game_id: 对局ID
        new_player_id: 新的观看玩家ID
    """

    type: MessageType = MessageType.SPECTATE_SWITCH
    game_id: str = Field(..., description="对局ID")
    new_player_id: str = Field(..., description="新的观看玩家ID")


class SpectateSyncMessage(BaseMessage):
    """
    请求同步观战状态

    Attributes:
        game_id: 对局ID
    """

    type: MessageType = MessageType.SPECTATE_SYNC
    game_id: str = Field(..., description="对局ID")


class SpectateChatMessage(BaseMessage):
    """
    发送观战弹幕

    Attributes:
        game_id: 对局ID
        content: 消息内容
        message_type: 消息类型
    """

    type: MessageType = MessageType.SPECTATE_CHAT
    game_id: str = Field(..., description="对局ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")


# 观战响应消息


class SpectatableGamesListMessage(BaseMessage):
    """
    可观战对局列表响应

    Attributes:
        games: 对局列表
        page: 当前页码
        page_size: 每页大小
        total_count: 总数量
    """

    type: MessageType = MessageType.SPECTATABLE_GAMES_LIST
    games: list[SpectatableGameData] = Field(default_factory=list, description="对局列表")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    total_count: int = Field(default=0, description="总数量")


class SpectateJoinedMessage(BaseMessage):
    """
    加入观战成功响应

    Attributes:
        game_id: 对局ID
        session_id: 观战会话ID
        watching_player_id: 观看的玩家ID
        delay_seconds: 延迟秒数
        spectator_count: 当前观众数量
    """

    type: MessageType = MessageType.SPECTATE_JOINED
    game_id: str = Field(..., description="对局ID")
    session_id: str = Field(..., description="观战会话ID")
    watching_player_id: str = Field(..., description="观看的玩家ID")
    delay_seconds: int = Field(default=30, description="延迟秒数")
    spectator_count: int = Field(default=0, description="当前观众数量")


class SpectateLeftMessage(BaseMessage):
    """
    离开观战成功响应

    Attributes:
        game_id: 对局ID
        session_id: 观战会话ID
    """

    type: MessageType = MessageType.SPECTATE_LEFT
    game_id: str = Field(..., description="对局ID")
    session_id: str | None = Field(default=None, description="观战会话ID")


class SpectateStateMessage(BaseMessage):
    """
    观战状态同步消息

    Attributes:
        game_id: 对局ID
        round_num: 当前回合
        phase: 当前阶段
        player_states: 所有玩家状态
        snapshot_time: 快照时间
        delay_seconds: 延迟秒数
    """

    type: MessageType = MessageType.SPECTATE_STATE
    game_id: str = Field(..., description="对局ID")
    round_num: int = Field(default=0, description="当前回合")
    phase: str = Field(default="", description="当前阶段")
    player_states: list[SpectatorPlayerStateData] = Field(
        default_factory=list, description="所有玩家状态"
    )
    snapshot_time: int = Field(..., description="快照时间")
    delay_seconds: int = Field(default=30, description="延迟秒数")


class SpectateChatReceivedMessage(BaseMessage):
    """
    收到观战弹幕消息

    Attributes:
        game_id: 对局ID
        chat: 弹幕数据
    """

    type: MessageType = MessageType.SPECTATE_CHAT_RECEIVED
    game_id: str = Field(..., description="对局ID")
    chat: SpectatorChatData = Field(..., description="弹幕数据")


class SpectateEndedMessage(BaseMessage):
    """
    观战结束通知

    Attributes:
        game_id: 对局ID
        reason: 结束原因
    """

    type: MessageType = MessageType.SPECTATE_ENDED
    game_id: str = Field(..., description="对局ID")
    reason: str = Field(default="game_ended", description="结束原因")


# ============================================================================
# 皮肤系统数据模型
# ============================================================================


class SkinData(BaseModel):
    """皮肤数据"""

    skin_id: str = Field(..., description="皮肤ID")
    hero_id: str = Field(..., description="英雄ID")
    name: str = Field(..., description="皮肤名称")
    description: str = Field(default="", description="皮肤描述")
    rarity: str = Field(..., description="稀有度")
    rarity_name: str = Field(default="", description="稀有度名称")
    skin_type: str = Field(default="shop", description="皮肤类型")
    price: dict[str, Any] | None = Field(default=None, description="价格")
    stat_bonuses: list[dict[str, Any]] = Field(default_factory=list, description="属性加成")
    effects: list[dict[str, Any]] = Field(default_factory=list, description="特效列表")
    preview_image: str = Field(default="", description="预览图")
    is_available: bool = Field(default=True, description="是否可获取")
    is_owned: bool = Field(default=False, description="是否已拥有")
    is_equipped: bool = Field(default=False, description="是否已装备")
    is_favorite: bool = Field(default=False, description="是否收藏")


class PlayerSkinData(BaseModel):
    """玩家拥有的皮肤数据"""

    skin_id: str = Field(..., description="皮肤ID")
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    skin_name: str = Field(default="", description="皮肤名称")
    rarity: str = Field(default="normal", description="稀有度")
    is_equipped: bool = Field(default=False, description="是否已装备")
    is_favorite: bool = Field(default=False, description="是否收藏")
    acquired_at: str | None = Field(default=None, description="获得时间")
    acquire_type: str = Field(default="buy", description="获得方式")


# ============================================================================
# 皮肤系统消息
# ============================================================================


class GetSkinsMessage(BaseMessage):
    """
    获取皮肤列表请求

    Attributes:
        rarity_filter: 稀有度筛选（可选）
        page: 页码
        page_size: 每页大小
    """

    type: MessageType = MessageType.GET_SKINS
    rarity_filter: str | None = Field(default=None, description="稀有度筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")


class GetHeroSkinsMessage(BaseMessage):
    """
    获取英雄皮肤列表请求

    Attributes:
        hero_id: 英雄ID
    """

    type: MessageType = MessageType.GET_HERO_SKINS
    hero_id: str = Field(..., description="英雄ID")


class GetOwnedSkinsMessage(BaseMessage):
    """
    获取已拥有皮肤请求

    Attributes:
        hero_id: 英雄ID（可选，不传则返回所有）
    """

    type: MessageType = MessageType.GET_OWNED_SKINS
    hero_id: str | None = Field(default=None, description="英雄ID")


class EquipSkinMessage(BaseMessage):
    """
    装备皮肤请求

    Attributes:
        skin_id: 皮肤ID
    """

    type: MessageType = MessageType.EQUIP_SKIN
    skin_id: str = Field(..., description="皮肤ID")


class UnequipSkinMessage(BaseMessage):
    """
    卸下皮肤请求

    Attributes:
        hero_id: 英雄ID
    """

    type: MessageType = MessageType.UNEQUIP_SKIN
    hero_id: str = Field(..., description="英雄ID")


class BuySkinMessage(BaseMessage):
    """
    购买皮肤请求

    Attributes:
        skin_id: 皮肤ID
        currency: 货币类型（gold/diamond/auto）
    """

    type: MessageType = MessageType.BUY_SKIN
    skin_id: str = Field(..., description="皮肤ID")
    currency: str = Field(default="auto", description="货币类型")


class SetFavoriteSkinMessage(BaseMessage):
    """
    设置收藏皮肤请求

    Attributes:
        skin_id: 皮肤ID
        is_favorite: 是否收藏
    """

    type: MessageType = MessageType.SET_FAVORITE_SKIN
    skin_id: str = Field(..., description="皮肤ID")
    is_favorite: bool = Field(default=True, description="是否收藏")


# 皮肤系统响应消息


class SkinsListMessage(BaseMessage):
    """
    皮肤列表响应

    Attributes:
        skins: 皮肤列表
        total_count: 总数量
        page: 当前页码
        page_size: 每页大小
        total_pages: 总页数
    """

    type: MessageType = MessageType.SKINS_LIST
    skins: list[SkinData] = Field(default_factory=list, description="皮肤列表")
    total_count: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")


class HeroSkinsListMessage(BaseMessage):
    """
    英雄皮肤列表响应

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        skins: 皮肤列表
        equipped_skin_id: 当前装备的皮肤ID
    """

    type: MessageType = MessageType.HERO_SKINS_LIST
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    skins: list[SkinData] = Field(default_factory=list, description="皮肤列表")
    equipped_skin_id: str | None = Field(default=None, description="当前装备的皮肤ID")


class OwnedSkinsListMessage(BaseMessage):
    """
    已拥有皮肤列表响应

    Attributes:
        skins: 皮肤列表
        total_count: 总数量
    """

    type: MessageType = MessageType.OWNED_SKINS_LIST
    skins: list[PlayerSkinData] = Field(default_factory=list, description="皮肤列表")
    total_count: int = Field(default=0, description="总数量")


class SkinEquippedMessage(BaseMessage):
    """
    皮肤已装备响应

    Attributes:
        skin_id: 皮肤ID
        hero_id: 英雄ID
        skin_name: 皮肤名称
        stat_bonuses: 属性加成说明
        effects: 特效说明
    """

    type: MessageType = MessageType.SKIN_EQUIPPED
    skin_id: str = Field(..., description="皮肤ID")
    hero_id: str = Field(..., description="英雄ID")
    skin_name: str = Field(..., description="皮肤名称")
    stat_bonuses: str = Field(default="", description="属性加成说明")
    effects: str = Field(default="", description="特效说明")


class SkinUnequippedMessage(BaseMessage):
    """
    皮肤已卸下响应

    Attributes:
        hero_id: 英雄ID
        previous_skin_id: 之前装备的皮肤ID
    """

    type: MessageType = MessageType.SKIN_UNEQUIPPED
    hero_id: str = Field(..., description="英雄ID")
    previous_skin_id: str | None = Field(default=None, description="之前装备的皮肤ID")


class SkinBoughtMessage(BaseMessage):
    """
    皮肤已购买响应

    Attributes:
        skin_id: 皮肤ID
        hero_id: 英雄ID
        skin_name: 皮肤名称
        currency: 消耗货币类型
        cost: 消耗数量
        remaining_balance: 剩余余额
    """

    type: MessageType = MessageType.SKIN_BOUGHT
    skin_id: str = Field(..., description="皮肤ID")
    hero_id: str = Field(..., description="英雄ID")
    skin_name: str = Field(..., description="皮肤名称")
    currency: str = Field(..., description="消耗货币类型")
    cost: int = Field(..., description="消耗数量")
    remaining_balance: int = Field(..., description="剩余余额")


class SkinUnlockedMessage(BaseMessage):
    """
    皮肤已解锁响应（奖励/成就/活动）

    Attributes:
        skin_id: 皮肤ID
        hero_id: 英雄ID
        skin_name: 皮肤名称
        unlock_type: 解锁类型
    """

    type: MessageType = MessageType.SKIN_UNLOCKED
    skin_id: str = Field(..., description="皮肤ID")
    hero_id: str = Field(..., description="英雄ID")
    skin_name: str = Field(..., description="皮肤名称")
    unlock_type: str = Field(default="reward", description="解锁类型")


class SkinFavoriteSetMessage(BaseMessage):
    """
    收藏设置成功响应

    Attributes:
        skin_id: 皮肤ID
        is_favorite: 是否收藏
    """

    type: MessageType = MessageType.SKIN_FAVORITE_SET
    skin_id: str = Field(..., description="皮肤ID")
    is_favorite: bool = Field(..., description="是否收藏")


# ============================================================================
# 英雄碎片系统数据模型
# ============================================================================


class HeroShardData(BaseModel):
    """英雄碎片数据"""

    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    quantity: int = Field(default=0, description="碎片数量")
    hero_cost: int = Field(default=1, description="英雄费用")
    last_acquired_at: str | None = Field(default=None, description="最后获得时间")
    can_compose: bool = Field(default=False, description="是否可合成")


class ComposeRequirementData(BaseModel):
    """合成要求数据"""

    target_star: int = Field(..., description="目标星级")
    shards_required: int = Field(default=100, description="需要碎片数")
    same_star_heroes: int = Field(default=0, description="需要同星级英雄数")
    hero_star_required: int = Field(default=1, description="需要的英雄星级")


class DecomposeRewardData(BaseModel):
    """分解奖励数据"""

    star_level: int = Field(..., description="星级")
    shards_gained: int = Field(default=30, description="获得碎片数")


# ============================================================================
# 英雄碎片系统消息
# ============================================================================


class GetShardBackpackMessage(BaseMessage):
    """
    获取碎片背包请求

    Attributes:
        hero_id: 英雄ID（可选，不传则返回所有）
    """

    type: MessageType = MessageType.GET_SHARD_BACKPACK
    hero_id: str | None = Field(default=None, description="英雄ID")


class ComposeHeroMessage(BaseMessage):
    """
    合成英雄请求

    Attributes:
        hero_id: 英雄ID
        target_star: 目标星级
        hero_name: 英雄名称
    """

    type: MessageType = MessageType.COMPOSE_HERO
    hero_id: str = Field(..., description="英雄ID")
    target_star: int = Field(default=1, ge=1, le=3, description="目标星级")
    hero_name: str = Field(default="", description="英雄名称")


class DecomposeHeroMessage(BaseMessage):
    """
    分解英雄请求

    Attributes:
        hero_id: 英雄ID
        star_level: 英雄星级
        hero_name: 英雄名称
        hero_cost: 英雄费用
    """

    type: MessageType = MessageType.DECOMPOSE_HERO
    hero_id: str = Field(..., description="英雄ID")
    star_level: int = Field(default=1, ge=1, le=3, description="英雄星级")
    hero_name: str = Field(default="", description="英雄名称")
    hero_cost: int = Field(default=1, description="英雄费用")


class BatchComposeMessage(BaseMessage):
    """
    批量合成请求

    Attributes:
        compose_list: 合成列表
    """

    type: MessageType = MessageType.BATCH_COMPOSE
    compose_list: list[dict[str, Any]] = Field(default_factory=list, description="合成列表")


class BatchDecomposeMessage(BaseMessage):
    """
    批量分解请求

    Attributes:
        decompose_list: 分解列表
    """

    type: MessageType = MessageType.BATCH_DECOMPOSE
    decompose_list: list[dict[str, Any]] = Field(default_factory=list, description="分解列表")


class OneKeyComposeMessage(BaseMessage):
    """
    一键合成请求（合成所有可合成的1星英雄）
    """

    type: MessageType = MessageType.ONE_KEY_COMPOSE


class GetComposeRequirementsMessage(BaseMessage):
    """
    获取合成要求请求

    Attributes:
        target_star: 目标星级
    """

    type: MessageType = MessageType.GET_COMPOSE_REQUIREMENTS
    target_star: int = Field(default=1, ge=1, le=3, description="目标星级")


class GetDecomposeRewardsMessage(BaseMessage):
    """
    获取分解奖励请求

    Attributes:
        star_level: 星级
    """

    type: MessageType = MessageType.GET_DECOMPOSE_REWARDS
    star_level: int = Field(default=1, ge=1, le=3, description="星级")


# 英雄碎片系统响应消息


class ShardBackpackMessage(BaseMessage):
    """
    碎片背包响应

    Attributes:
        shards: 碎片列表
        total_shards: 总碎片数
        total_heroes: 总英雄数
    """

    type: MessageType = MessageType.SHARD_BACKPACK
    shards: list[HeroShardData] = Field(default_factory=list, description="碎片列表")
    total_shards: int = Field(default=0, description="总碎片数")
    total_heroes: int = Field(default=0, description="总英雄数")


class HeroComposedMessage(BaseMessage):
    """
    英雄合成成功响应

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        star_level: 星级
        shards_used: 消耗碎片数
        heroes_used: 消耗英雄数
        success: 是否成功
        error_message: 错误信息
    """

    type: MessageType = MessageType.HERO_COMPOSED
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    star_level: int = Field(default=1, description="星级")
    shards_used: int = Field(default=0, description="消耗碎片数")
    heroes_used: int = Field(default=0, description="消耗英雄数")
    success: bool = Field(default=True, description="是否成功")
    error_message: str | None = Field(default=None, description="错误信息")


class HeroDecomposedMessage(BaseMessage):
    """
    英雄分解成功响应

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        star_level: 星级
        shards_gained: 获得碎片数
        success: 是否成功
        error_message: 错误信息
    """

    type: MessageType = MessageType.HERO_DECOMPOSED
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    star_level: int = Field(default=1, description="星级")
    shards_gained: int = Field(default=0, description="获得碎片数")
    success: bool = Field(default=True, description="是否成功")
    error_message: str | None = Field(default=None, description="错误信息")


class BatchComposeResultMessage(BaseMessage):
    """
    批量合成结果响应

    Attributes:
        success_count: 成功数量
        fail_count: 失败数量
        total_shards_used: 总消耗碎片
        results: 合成结果列表
    """

    type: MessageType = MessageType.BATCH_COMPOSE_RESULT
    success_count: int = Field(default=0, description="成功数量")
    fail_count: int = Field(default=0, description="失败数量")
    total_shards_used: int = Field(default=0, description="总消耗碎片")
    results: list[dict[str, Any]] = Field(default_factory=list, description="合成结果列表")


class BatchDecomposeResultMessage(BaseMessage):
    """
    批量分解结果响应

    Attributes:
        success_count: 成功数量
        fail_count: 失败数量
        total_shards_gained: 总获得碎片
        results: 分解结果列表
    """

    type: MessageType = MessageType.BATCH_DECOMPOSE_RESULT
    success_count: int = Field(default=0, description="成功数量")
    fail_count: int = Field(default=0, description="失败数量")
    total_shards_gained: int = Field(default=0, description="总获得碎片")
    results: list[dict[str, Any]] = Field(default_factory=list, description="分解结果列表")


class ComposeRequirementsMessage(BaseMessage):
    """
    合成要求响应

    Attributes:
        target_star: 目标星级
        shards_required: 需要碎片数
        same_star_heroes: 需要同星级英雄数
        hero_star_required: 需要的英雄星级
    """

    type: MessageType = MessageType.COMPOSE_REQUIREMENTS
    target_star: int = Field(default=1, description="目标星级")
    shards_required: int = Field(default=100, description="需要碎片数")
    same_star_heroes: int = Field(default=0, description="需要同星级英雄数")
    hero_star_required: int = Field(default=1, description="需要的英雄星级")


class DecomposeRewardsMessage(BaseMessage):
    """
    分解奖励响应

    Attributes:
        star_level: 星级
        shards_gained: 获得碎片数
    """

    type: MessageType = MessageType.DECOMPOSE_REWARDS
    star_level: int = Field(default=1, description="星级")
    shards_gained: int = Field(default=30, description="获得碎片数")


class ShardUpdatedMessage(BaseMessage):
    """
    碎片更新通知

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        quantity: 当前数量
        change: 变动数量
        source: 变动来源
    """

    type: MessageType = MessageType.SHARD_UPDATED
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    quantity: int = Field(default=0, description="当前数量")
    change: int = Field(default=0, description="变动数量")
    source: str = Field(default="", description="变动来源")


class CanComposeNotifyMessage(BaseMessage):
    """
    可合成通知

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        shard_quantity: 当前碎片数
    """

    type: MessageType = MessageType.CAN_COMPOSE_NOTIFY
    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(default="", description="英雄名称")
    shard_quantity: int = Field(default=0, description="当前碎片数")


# ============================================================================
# 回放系统数据模型
# ============================================================================


class ReplayPlayerSnapshotData(BaseModel):
    """回放玩家快照数据"""

    player_id: int = Field(..., description="玩家ID")
    nickname: str = Field(default="", description="昵称")
    avatar: str | None = Field(default=None, description="头像")
    tier: str | None = Field(default=None, description="段位")
    hp: int = Field(default=100, description="生命值")
    gold: int = Field(default=0, description="金币")
    level: int = Field(default=1, description="等级")
    exp: int = Field(default=0, description="经验值")
    board: list[Any] = Field(default_factory=list, description="棋盘状态")
    bench: list[Any] = Field(default_factory=list, description="备战席状态")
    synergies: dict[str, int] = Field(default_factory=dict, description="羁绊状态")
    equipment: list[Any] = Field(default_factory=list, description="装备信息")


class ReplayFrameData(BaseModel):
    """回放帧数据"""

    round_num: int = Field(..., description="回合数")
    phase: str = Field(default="", description="阶段")
    timestamp: int = Field(default=0, description="时间戳")
    player_snapshots: dict[str, ReplayPlayerSnapshotData] = Field(
        default_factory=dict, description="玩家快照"
    )
    shop_data: dict[str, Any] | None = Field(default=None, description="商店数据")
    battle_data: dict[str, Any] | None = Field(default=None, description="战斗数据")
    events: list[dict[str, Any]] = Field(default_factory=list, description="事件列表")


class ReplayMetadataData(BaseModel):
    """回放元数据"""

    match_id: str = Field(..., description="对局ID")
    player_id: int = Field(..., description="玩家ID")
    player_nickname: str = Field(default="", description="玩家昵称")
    final_rank: int = Field(default=0, description="最终排名")
    total_rounds: int = Field(default=0, description="总回合数")
    duration_seconds: int = Field(default=0, description="对局时长（秒）")
    player_count: int = Field(default=8, description="参与人数")
    created_at: int = Field(default=0, description="创建时间")
    game_version: str = Field(default="1.0.0", description="游戏版本")
    is_shared: bool = Field(default=False, description="是否已分享")
    share_code: str | None = Field(default=None, description="分享码")
    tags: list[str] = Field(default_factory=list, description="标签")


class ReplayListItemData(BaseModel):
    """回放列表项数据"""

    replay_id: str = Field(..., description="回放ID")
    match_id: str = Field(..., description="对局ID")
    player_nickname: str = Field(default="", description="玩家昵称")
    final_rank: int = Field(default=0, description="最终排名")
    total_rounds: int = Field(default=0, description="总回合数")
    duration_seconds: int = Field(default=0, description="对局时长（秒）")
    duration_minutes: float = Field(default=0.0, description="对局时长（分钟）")
    created_at: int = Field(default=0, description="创建时间")
    is_shared: bool = Field(default=False, description="是否已分享")
    share_code: str | None = Field(default=None, description="分享码")


class ReplayData(BaseModel):
    """完整回放数据"""

    replay_id: str = Field(..., description="回放ID")
    metadata: ReplayMetadataData | None = Field(default=None, description="元数据")
    frames: list[ReplayFrameData] = Field(default_factory=list, description="帧列表")
    initial_state: dict[str, Any] | None = Field(default=None, description="初始状态")
    final_rankings: list[dict[str, Any]] = Field(default_factory=list, description="最终排名")


# ============================================================================
# 回放系统消息
# ============================================================================


class SaveReplayMessage(BaseMessage):
    """
    保存回放请求

    Attributes:
        match_id: 对局ID
        match_data: 对局数据（包含帧数据等）
    """

    type: MessageType = MessageType.SAVE_REPLAY
    match_id: str = Field(..., description="对局ID")
    match_data: dict[str, Any] = Field(default_factory=dict, description="对局数据")


class ReplaySavedMessage(BaseMessage):
    """
    回放保存成功响应

    Attributes:
        replay_id: 回放ID
        match_id: 对局ID
        message: 成功消息
    """

    type: MessageType = MessageType.REPLAY_SAVED
    replay_id: str = Field(..., description="回放ID")
    match_id: str = Field(..., description="对局ID")
    message: str = Field(default="回放保存成功", description="成功消息")


class GetReplayListMessage(BaseMessage):
    """
    获取回放列表请求

    Attributes:
        page: 页码（从1开始）
        page_size: 每页数量
    """

    type: MessageType = MessageType.GET_REPLAY_LIST
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class ReplayListMessage(BaseMessage):
    """
    回放列表响应

    Attributes:
        replays: 回放列表
        page: 当前页码
        page_size: 每页数量
        total_count: 总数量
        max_replays: 最大回放数量
    """

    type: MessageType = MessageType.REPLAY_LIST
    replays: list[ReplayListItemData] = Field(default_factory=list, description="回放列表")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_count: int = Field(default=0, description="总数量")
    max_replays: int = Field(default=20, description="最大回放数量")


class LoadReplayMessage(BaseMessage):
    """
    加载回放请求

    Attributes:
        replay_id: 回放ID
    """

    type: MessageType = MessageType.LOAD_REPLAY
    replay_id: str = Field(..., description="回放ID")


class ReplayLoadedMessage(BaseMessage):
    """
    回放加载成功响应

    Attributes:
        replay: 回放数据
    """

    type: MessageType = MessageType.REPLAY_LOADED
    replay: ReplayData = Field(..., description="回放数据")


class DeleteReplayMessage(BaseMessage):
    """
    删除回放请求

    Attributes:
        replay_id: 回放ID
    """

    type: MessageType = MessageType.DELETE_REPLAY
    replay_id: str = Field(..., description="回放ID")


class ReplayDeletedMessage(BaseMessage):
    """
    回放删除成功响应

    Attributes:
        replay_id: 被删除的回放ID
    """

    type: MessageType = MessageType.REPLAY_DELETED
    replay_id: str = Field(..., description="回放ID")


class ReplayControlMessage(BaseMessage):
    """
    回放控制请求

    Attributes:
        session_id: 播放会话ID
        action: 控制动作 (play/pause/stop/speed/seek)
        speed: 播放速度 (0.5/1/2/4)
        round_num: 跳转回合（仅 seek 时需要）
    """

    type: MessageType = MessageType.REPLAY_CONTROL
    session_id: str = Field(..., description="播放会话ID")
    action: str = Field(..., description="控制动作")
    speed: float | None = Field(default=None, description="播放速度")
    round_num: int | None = Field(default=None, description="跳转回合")


class ReplayStateUpdateMessage(BaseMessage):
    """
    回放状态更新消息

    Attributes:
        session_id: 播放会话ID
        status: 播放状态 (idle/playing/paused/ended)
        current_round: 当前回合
        current_frame_index: 当前帧索引
        total_frames: 总帧数
        speed: 播放速度
        current_frame: 当前帧数据
    """

    type: MessageType = MessageType.REPLAY_STATE_UPDATE
    session_id: str = Field(..., description="播放会话ID")
    status: str = Field(default="idle", description="播放状态")
    current_round: int = Field(default=1, description="当前回合")
    current_frame_index: int = Field(default=0, description="当前帧索引")
    total_frames: int = Field(default=0, description="总帧数")
    speed: float = Field(default=1.0, description="播放速度")
    current_frame: ReplayFrameData | None = Field(default=None, description="当前帧数据")


class ExportReplayMessage(BaseMessage):
    """
    导出回放请求

    Attributes:
        replay_id: 回放ID
    """

    type: MessageType = MessageType.EXPORT_REPLAY
    replay_id: str = Field(..., description="回放ID")


class ReplayExportedMessage(BaseMessage):
    """
    回放导出成功响应

    Attributes:
        replay_id: 回放ID
        share_code: 分享码
        export_data: 导出数据（JSON字符串）
    """

    type: MessageType = MessageType.REPLAY_EXPORTED
    replay_id: str = Field(..., description="回放ID")
    share_code: str = Field(..., description="分享码")
    export_data: str | None = Field(default=None, description="导出数据")


class ImportReplayMessage(BaseMessage):
    """
    导入回放请求

    Attributes:
        share_code: 分享码
        import_data: 导入数据（JSON字符串，可选）
    """

    type: MessageType = MessageType.IMPORT_REPLAY
    share_code: str | None = Field(default=None, description="分享码")
    import_data: str | None = Field(default=None, description="导入数据")


class ReplayImportedMessage(BaseMessage):
    """
    回放导入成功响应

    Attributes:
        replay: 导入的回放数据
        message: 成功消息
    """

    type: MessageType = MessageType.REPLAY_IMPORTED
    replay: ReplayData = Field(..., description="回放数据")
    message: str = Field(default="回放导入成功", description="成功消息")


# ============================================================================
# 表情系统数据模型
# ============================================================================


class EmoteData(BaseModel):
    """表情数据"""

    emote_id: str = Field(..., description="表情ID")
    name: str = Field(default="", description="表情名称")
    description: str = Field(default="", description="表情描述")
    category: str = Field(default="default", description="表情分类")
    emote_type: str = Field(default="static", description="表情类型")
    asset_url: str = Field(default="", description="表情资源URL")
    thumbnail_url: str = Field(default="", description="缩略图URL")
    sound_url: str | None = Field(default=None, description="音效URL")
    unlock_condition: dict[str, Any] | None = Field(default=None, description="解锁条件")
    is_free: bool = Field(default=True, description="是否免费")
    sort_order: int = Field(default=0, description="排序顺序")


class PlayerEmoteData(BaseModel):
    """玩家表情数据"""

    emote_id: str = Field(..., description="表情ID")
    name: str = Field(default="", description="表情名称")
    asset_url: str = Field(default="", description="表情资源URL")
    thumbnail_url: str = Field(default="", description="缩略图URL")
    category: str = Field(default="default", description="表情分类")
    emote_type: str = Field(default="static", description="表情类型")
    hotkey: str | None = Field(default=None, description="快捷键")
    use_count: int = Field(default=0, description="使用次数")


class EmoteSentData(BaseModel):
    """已发送表情数据"""

    emote_id: str = Field(..., description="表情ID")
    name: str = Field(default="", description="表情名称")
    asset_url: str = Field(default="", description="表情资源URL")
    thumbnail_url: str = Field(default="", description="缩略图URL")
    emote_type: str = Field(default="static", description="表情类型")
    from_player_id: str = Field(..., description="发送者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    to_player_id: str | None = Field(default=None, description="目标玩家ID")
    room_id: str = Field(default="", description="房间ID")
    round_number: int = Field(default=0, description="回合数")
    timestamp: str = Field(default="", description="发送时间")


class EmoteHistoryItemData(BaseModel):
    """表情历史项数据"""

    history_id: str = Field(..., description="历史记录ID")
    emote_id: str = Field(..., description="表情ID")
    name: str = Field(default="", description="表情名称")
    asset_url: str = Field(default="", description="表情资源URL")
    from_player_id: str = Field(..., description="发送者ID")
    from_nickname: str = Field(default="", description="发送者昵称")
    to_player_id: str | None = Field(default=None, description="目标玩家ID")
    to_nickname: str = Field(default="", description="目标玩家昵称")
    room_id: str = Field(default="", description="房间ID")
    round_number: int = Field(default=0, description="回合数")
    created_at: str | None = Field(default=None, description="发送时间")


# ============================================================================
# 表情系统消息
# ============================================================================


class GetEmotesMessage(BaseMessage):
    """
    获取表情列表请求

    Attributes:
        category: 分类过滤（可选）
    """

    type: MessageType = MessageType.GET_EMOTES
    category: str | None = Field(default=None, description="分类过滤")


class EmotesListMessage(BaseMessage):
    """
    表情列表响应

    Attributes:
        emotes: 表情列表
        total_count: 总数量
    """

    type: MessageType = MessageType.EMOTES_LIST
    emotes: list[EmoteData] = Field(default_factory=list, description="表情列表")
    total_count: int = Field(default=0, description="总数量")


class GetOwnedEmotesMessage(BaseMessage):
    """
    获取已拥有表情请求
    """

    type: MessageType = MessageType.GET_OWNED_EMOTES


class OwnedEmotesListMessage(BaseMessage):
    """
    已拥有表情列表响应

    Attributes:
        emotes: 已拥有表情列表
        hotkeys: 快捷键映射
        total_count: 总数量
    """

    type: MessageType = MessageType.OWNED_EMOTES_LIST
    emotes: list[PlayerEmoteData] = Field(default_factory=list, description="表情列表")
    hotkeys: dict[str, str] = Field(default_factory=dict, description="快捷键映射")
    total_count: int = Field(default=0, description="总数量")


class SendEmoteMessage(BaseMessage):
    """
    发送表情请求

    Attributes:
        emote_id: 表情ID
        to_player_id: 目标玩家ID（可选，不传则发送给所有玩家）
        room_id: 房间ID
        round_number: 回合数
    """

    type: MessageType = MessageType.SEND_EMOTE
    emote_id: str = Field(..., description="表情ID")
    to_player_id: str | None = Field(default=None, description="目标玩家ID")
    room_id: str = Field(default="", description="房间ID")
    round_number: int = Field(default=0, description="回合数")


class EmoteSentMessage(BaseMessage):
    """
    表情发送成功响应

    Attributes:
        emote: 发送的表情数据
        cooldown_remaining: 剩余冷却时间（秒）
    """

    type: MessageType = MessageType.EMOTE_SENT
    emote: EmoteSentData = Field(..., description="表情数据")
    cooldown_remaining: float = Field(default=0.0, description="剩余冷却时间")


class EmoteReceivedMessage(BaseMessage):
    """
    收到表情广播

    Attributes:
        emote: 收到的表情数据
    """

    type: MessageType = MessageType.EMOTE_RECEIVED
    emote: EmoteSentData = Field(..., description="表情数据")


class SetEmoteHotkeyMessage(BaseMessage):
    """
    设置表情快捷键请求

    Attributes:
        emote_id: 表情ID
        hotkey: 快捷键（如 "1", "2", "ctrl+1" 等）
    """

    type: MessageType = MessageType.SET_EMOTE_HOTKEY
    emote_id: str = Field(..., description="表情ID")
    hotkey: str = Field(..., description="快捷键")


class EmoteHotkeySetMessage(BaseMessage):
    """
    快捷键设置成功响应

    Attributes:
        emote_id: 表情ID
        hotkey: 快捷键
        previous_hotkey: 之前的快捷键（如果有）
    """

    type: MessageType = MessageType.EMOTE_HOTKEY_SET
    emote_id: str = Field(..., description="表情ID")
    hotkey: str = Field(..., description="快捷键")
    previous_hotkey: str | None = Field(default=None, description="之前的快捷键")


class GetEmoteHistoryMessage(BaseMessage):
    """
    获取表情历史请求

    Attributes:
        room_id: 房间ID（可选）
        limit: 返回数量限制
    """

    type: MessageType = MessageType.GET_EMOTE_HISTORY
    room_id: str | None = Field(default=None, description="房间ID")
    limit: int = Field(default=50, ge=1, le=100, description="返回数量限制")


class EmoteHistoryMessage(BaseMessage):
    """
    表情历史响应

    Attributes:
        history: 历史记录列表
        room_id: 房间ID
        total_count: 总数量
    """

    type: MessageType = MessageType.EMOTE_HISTORY
    history: list[EmoteHistoryItemData] = Field(default_factory=list, description="历史记录")
    room_id: str | None = Field(default=None, description="房间ID")
    total_count: int = Field(default=0, description="总数量")


class EmoteUnlockedMessage(BaseMessage):
    """
    表情解锁通知

    Attributes:
        emote_id: 表情ID
        name: 表情名称
        unlock_type: 解锁类型
    """

    type: MessageType = MessageType.EMOTE_UNLOCKED
    emote_id: str = Field(..., description="表情ID")
    name: str = Field(default="", description="表情名称")
    unlock_type: str = Field(default="achievement", description="解锁类型")


# ============================================================================
# 道具系统消息
# ============================================================================


class ConsumableData(BaseModel):
    """
    道具数据

    Attributes:
        consumable_id: 道具ID
        name: 道具名称
        description: 道具描述
        consumable_type: 道具类型
        rarity: 道具稀有度
        effects: 效果列表
        price: 价格
        max_stack: 最大堆叠数
        icon: 图标路径
        auto_use: 是否自动使用
    """

    consumable_id: str = Field(..., description="道具ID")
    name: str = Field(..., description="道具名称")
    description: str = Field(default="", description="道具描述")
    consumable_type: str = Field(..., description="道具类型")
    rarity: str = Field(default="common", description="道具稀有度")
    effects: list[dict] = Field(default_factory=list, description="效果列表")
    price: dict | None = Field(default=None, description="价格")
    max_stack: int = Field(default=99, description="最大堆叠数")
    icon: str = Field(default="", description="图标路径")
    auto_use: bool = Field(default=False, description="是否自动使用")


class PlayerConsumableData(BaseModel):
    """
    玩家道具数据

    Attributes:
        consumable_id: 道具ID
        quantity: 数量
        acquired_at: 获得时间
        acquire_type: 获得方式
        expire_at: 过期时间
    """

    consumable_id: str = Field(..., description="道具ID")
    quantity: int = Field(..., description="数量")
    acquired_at: str = Field(..., description="获得时间")
    acquire_type: str = Field(default="buy", description="获得方式")
    expire_at: str | None = Field(default=None, description="过期时间")


class ConsumableUsageData(BaseModel):
    """
    道具使用记录数据

    Attributes:
        consumable_id: 道具ID
        used_at: 使用时间
        quantity: 使用数量
        context: 使用场景
        context_id: 场景ID
        effect_applied: 效果是否生效
    """

    consumable_id: str = Field(..., description="道具ID")
    used_at: str = Field(..., description="使用时间")
    quantity: int = Field(default=1, description="使用数量")
    context: str = Field(default="match", description="使用场景")
    context_id: str | None = Field(default=None, description="场景ID")
    effect_applied: bool = Field(default=True, description="效果是否生效")


class ConsumableEffectData(BaseModel):
    """
    道具效果数据

    Attributes:
        consumable_id: 道具ID
        effect_type: 效果类型
        value: 效果数值
        activated_at: 激活时间
        remaining_rounds: 剩余回合数
    """

    consumable_id: str = Field(..., description="道具ID")
    effect_type: str = Field(..., description="效果类型")
    value: float = Field(..., description="效果数值")
    activated_at: str = Field(..., description="激活时间")
    remaining_rounds: int = Field(default=-1, description="剩余回合数")


class GetConsumablesMessage(BaseMessage):
    """
    获取道具列表请求
    """

    type: MessageType = MessageType.GET_CONSUMABLES


class ConsumablesListMessage(BaseMessage):
    """
    道具列表响应

    Attributes:
        consumables: 道具列表
        total_count: 总数量
    """

    type: MessageType = MessageType.CONSUMABLES_LIST
    consumables: list[ConsumableData] = Field(default_factory=list, description="道具列表")
    total_count: int = Field(default=0, description="总数量")


class GetPlayerConsumablesMessage(BaseMessage):
    """
    获取玩家道具请求
    """

    type: MessageType = MessageType.GET_PLAYER_CONSUMABLES


class PlayerConsumablesListMessage(BaseMessage):
    """
    玩家道具列表响应

    Attributes:
        consumables: 玩家道具列表
        active_effects: 激活的效果列表
        total_count: 总数量
    """

    type: MessageType = MessageType.PLAYER_CONSUMABLES_LIST
    consumables: list[PlayerConsumableData] = Field(default_factory=list, description="道具列表")
    active_effects: list[ConsumableEffectData] = Field(default_factory=list, description="激活效果")
    total_count: int = Field(default=0, description="总数量")


class UseConsumableMessage(BaseMessage):
    """
    使用道具请求

    Attributes:
        consumable_id: 道具ID
        quantity: 使用数量
        context: 使用场景
        context_id: 场景ID
    """

    type: MessageType = MessageType.USE_CONSUMABLE
    consumable_id: str = Field(..., description="道具ID")
    quantity: int = Field(default=1, ge=1, description="使用数量")
    context: str = Field(default="match", description="使用场景")
    context_id: str | None = Field(default=None, description="场景ID")


class ConsumableUsedMessage(BaseMessage):
    """
    道具已使用响应

    Attributes:
        consumable_id: 道具ID
        quantity: 使用数量
        remaining: 剩余数量
        effect: 激活的效果（如果有）
    """

    type: MessageType = MessageType.CONSUMABLE_USED
    consumable_id: str = Field(..., description="道具ID")
    quantity: int = Field(..., description="使用数量")
    remaining: int = Field(default=0, description="剩余数量")
    effect: ConsumableEffectData | None = Field(default=None, description="激活效果")


class BuyConsumableMessage(BaseMessage):
    """
    购买道具请求

    Attributes:
        consumable_id: 道具ID
        quantity: 购买数量
        use_currency: 使用的货币类型
    """

    type: MessageType = MessageType.BUY_CONSUMABLE
    consumable_id: str = Field(..., description="道具ID")
    quantity: int = Field(default=1, ge=1, description="购买数量")
    use_currency: str = Field(default="auto", description="货币类型")


class ConsumableBoughtMessage(BaseMessage):
    """
    道具已购买响应

    Attributes:
        consumable_id: 道具ID
        quantity: 购买数量
        total_quantity: 总数量
        currency: 消耗的货币类型
        cost: 花费
    """

    type: MessageType = MessageType.CONSUMABLE_BOUGHT
    consumable_id: str = Field(..., description="道具ID")
    quantity: int = Field(..., description="购买数量")
    total_quantity: int = Field(..., description="总数量")
    currency: str = Field(..., description="货币类型")
    cost: int = Field(..., description="花费")


class GetConsumableHistoryMessage(BaseMessage):
    """
    获取道具使用历史请求

    Attributes:
        limit: 返回数量限制
    """

    type: MessageType = MessageType.GET_CONSUMABLE_HISTORY
    limit: int = Field(default=50, ge=1, le=100, description="返回数量限制")


class ConsumableHistoryMessage(BaseMessage):
    """
    道具使用历史响应

    Attributes:
        history: 历史记录列表
        total_count: 总数量
    """

    type: MessageType = MessageType.CONSUMABLE_HISTORY
    history: list[ConsumableUsageData] = Field(default_factory=list, description="历史记录")
    total_count: int = Field(default=0, description="总数量")


class ConsumableAddedMessage(BaseMessage):
    """
    道具获得通知

    Attributes:
        consumable_id: 道具ID
        name: 道具名称
        quantity: 获得数量
        acquire_type: 获得方式
    """

    type: MessageType = MessageType.CONSUMABLE_ADDED
    consumable_id: str = Field(..., description="道具ID")
    name: str = Field(default="", description="道具名称")
    quantity: int = Field(..., description="获得数量")
    acquire_type: str = Field(default="reward", description="获得方式")


class ConsumableEffectAppliedMessage(BaseMessage):
    """
    道具效果生效通知

    Attributes:
        consumable_id: 道具ID
        effect_type: 效果类型
        value: 效果数值
        duration_type: 持续类型
        duration_value: 持续值
    """

    type: MessageType = MessageType.CONSUMABLE_EFFECT_APPLIED
    consumable_id: str = Field(..., description="道具ID")
    effect_type: str = Field(..., description="效果类型")
    value: float = Field(..., description="效果数值")
    duration_type: str = Field(default="instant", description="持续类型")
    duration_value: int = Field(default=1, description="持续值")


# ============================================================================
# AI教练系统数据模型
# ============================================================================


class AISuggestionData(BaseModel):
    """
    AI建议数据

    Attributes:
        suggestion_id: 建议ID
        suggestion_type: 建议类型
        priority: 优先级
        title: 建议标题
        description: 建议详细描述
        reason: 建议原因
        action: 建议采取的行动
        expected_benefit: 预期收益
        confidence: 置信度
    """

    suggestion_id: str = Field(..., description="建议ID")
    suggestion_type: str = Field(..., description="建议类型")
    priority: str = Field(..., description="优先级")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议详细描述")
    reason: str = Field(..., description="建议原因")
    action: dict[str, Any] = Field(default_factory=dict, description="建议采取的行动")
    expected_benefit: str = Field(default="", description="预期收益")
    confidence: float = Field(default=0.8, ge=0, le=1, description="置信度")


class WinRatePredictionData(BaseModel):
    """
    胜率预测数据

    Attributes:
        predicted_win_rate: 预测胜率
        confidence: 置信度
        factors: 影响因素
        comparison_rank: 排名预测
        key_advantages: 关键优势
        key_weaknesses: 关键劣势
        improvement_suggestions: 改进建议
    """

    predicted_win_rate: float = Field(..., ge=0, le=1, description="预测胜率")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    factors: dict[str, float] = Field(default_factory=dict, description="影响因素")
    comparison_rank: int = Field(default=4, ge=1, le=8, description="排名预测")
    key_advantages: list[str] = Field(default_factory=list, description="关键优势")
    key_weaknesses: list[str] = Field(default_factory=list, description="关键劣势")
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")


class CoachAnalysisData(BaseModel):
    """
    对局分析数据

    Attributes:
        analysis_id: 分析ID
        player_id: 玩家ID
        game_id: 对局ID
        analysis_type: 分析类型
        round_num: 回合数
        lineup_score: 阵容评分
        economy_score: 经济评分
        synergy_score: 羁绊评分
        position_score: 站位评分
        overall_score: 综合评分
        strengths: 优势列表
        weaknesses: 劣势列表
        suggestions: 建议列表
        win_rate_prediction: 胜率预测
        created_at: 创建时间
    """

    analysis_id: str = Field(..., description="分析ID")
    player_id: int = Field(..., description="玩家ID")
    game_id: str = Field(..., description="对局ID")
    analysis_type: str = Field(..., description="分析类型")
    round_num: int = Field(..., description="回合数")
    lineup_score: float = Field(default=50.0, ge=0, le=100, description="阵容评分")
    economy_score: float = Field(default=50.0, ge=0, le=100, description="经济评分")
    synergy_score: float = Field(default=50.0, ge=0, le=100, description="羁绊评分")
    position_score: float = Field(default=50.0, ge=0, le=100, description="站位评分")
    overall_score: float = Field(default=50.0, ge=0, le=100, description="综合评分")
    strengths: list[str] = Field(default_factory=list, description="优势列表")
    weaknesses: list[str] = Field(default_factory=list, description="劣势列表")
    suggestions: list[AISuggestionData] = Field(default_factory=list, description="建议列表")
    win_rate_prediction: WinRatePredictionData | None = Field(default=None, description="胜率预测")
    created_at: int = Field(default=0, description="创建时间")


class LineupRecommendationData(BaseModel):
    """
    阵容推荐数据

    Attributes:
        lineup_id: 阵容ID
        name: 阵容名称
        description: 阵容描述
        difficulty: 难度等级
        core_heroes: 核心英雄
        optional_heroes: 可选英雄
        synergies: 激活的羁绊
        play_style: 玩法风格
        early_game: 前期阵容
        mid_game: 中期阵容
        late_game: 后期阵容
        key_items: 核心装备
        tips: 玩法提示
        win_rate: 胜率
        popularity: 流行度
    """

    lineup_id: str = Field(..., description="阵容ID")
    name: str = Field(..., description="阵容名称")
    description: str = Field(default="", description="阵容描述")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级")
    core_heroes: list[str] = Field(default_factory=list, description="核心英雄")
    optional_heroes: list[str] = Field(default_factory=list, description="可选英雄")
    synergies: dict[str, int] = Field(default_factory=dict, description="激活的羁绊")
    play_style: str = Field(default="balanced", description="玩法风格")
    early_game: list[str] = Field(default_factory=list, description="前期阵容")
    mid_game: list[str] = Field(default_factory=list, description="中期阵容")
    late_game: list[str] = Field(default_factory=list, description="后期阵容")
    key_items: list[str] = Field(default_factory=list, description="核心装备")
    tips: list[str] = Field(default_factory=list, description="玩法提示")
    win_rate: float = Field(default=0.5, ge=0, le=1, description="胜率")
    popularity: float = Field(default=0.5, ge=0, le=1, description="流行度")


class MatchHistoryItemData(BaseModel):
    """
    对局历史记录数据

    Attributes:
        match_id: 对局ID
        game_id: 游戏ID
        final_rank: 最终排名
        total_rounds: 总回合数
        duration_seconds: 对局时长
        final_lineup: 最终阵容
        final_synergies: 最终羁绊
        damage_dealt: 造成伤害
        damage_taken: 承受伤害
        gold_earned: 获得金币
        key_decisions: 关键决策
        analysis: 对局分析
        played_at: 对局时间
    """

    match_id: str = Field(..., description="对局ID")
    game_id: str = Field(..., description="游戏ID")
    final_rank: int = Field(..., ge=1, le=8, description="最终排名")
    total_rounds: int = Field(..., description="总回合数")
    duration_seconds: int = Field(..., description="对局时长（秒）")
    final_lineup: list[str] = Field(default_factory=list, description="最终阵容")
    final_synergies: dict[str, int] = Field(default_factory=dict, description="最终羁绊")
    damage_dealt: int = Field(default=0, description="造成伤害")
    damage_taken: int = Field(default=0, description="承受伤害")
    gold_earned: int = Field(default=0, description="获得金币")
    key_decisions: list[str] = Field(default_factory=list, description="关键决策")
    analysis: CoachAnalysisData | None = Field(default=None, description="对局分析")
    played_at: int = Field(default=0, description="对局时间")


class EquipmentAdviceData(BaseModel):
    """
    装备建议数据

    Attributes:
        equipment_id: 装备ID
        equipment_name: 装备名称
        target_hero_id: 目标英雄ID
        reason: 建议原因
        recipe: 合成配方
        priority: 优先级
        expected_stat_boost: 预期属性提升
    """

    equipment_id: str = Field(..., description="装备ID")
    equipment_name: str = Field(..., description="装备名称")
    target_hero_id: str | None = Field(default=None, description="目标英雄ID")
    reason: str = Field(..., description="建议原因")
    recipe: list[str] | None = Field(default=None, description="合成配方")
    priority: str = Field(default="medium", description="优先级")
    expected_stat_boost: dict[str, float] = Field(default_factory=dict, description="预期属性提升")


class PositionAdviceData(BaseModel):
    """
    站位建议数据

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        current_position: 当前位置
        recommended_position: 推荐位置
        reason: 建议原因
        priority: 优先级
        tactical_role: 战术角色
    """

    hero_id: str = Field(..., description="英雄ID")
    hero_name: str = Field(..., description="英雄名称")
    current_position: dict[str, int] | None = Field(default=None, description="当前位置")
    recommended_position: dict[str, int] = Field(..., description="推荐位置")
    reason: str = Field(..., description="建议原因")
    priority: str = Field(default="medium", description="优先级")
    tactical_role: str = Field(default="fighter", description="战术角色")


class RoundStrategyData(BaseModel):
    """
    回合策略数据

    Attributes:
        round_num: 回合数
        phase: 游戏阶段
        strategy_type: 策略类型
        description: 策略描述
        key_actions: 关键行动
        focus_synergies: 重点羁绊
        economy_advice: 经济建议
        risk_level: 风险等级
        win_condition: 获胜条件
    """

    round_num: int = Field(..., description="回合数")
    phase: str = Field(..., description="游戏阶段")
    strategy_type: str = Field(..., description="策略类型")
    description: str = Field(..., description="策略描述")
    key_actions: list[str] = Field(default_factory=list, description="关键行动")
    focus_synergies: list[str] = Field(default_factory=list, description="重点羁绊")
    economy_advice: str | None = Field(default=None, description="经济建议")
    risk_level: str = Field(default="medium", description="风险等级")
    win_condition: str | None = Field(default=None, description="获胜条件")


# ============================================================================
# AI教练系统消息
# ============================================================================


class GetCoachSuggestionsMessage(BaseMessage):
    """
    获取教练建议请求

    Attributes:
        game_state: 当前游戏状态
    """

    type: MessageType = MessageType.GET_COACH_SUGGESTIONS
    game_state: dict[str, Any] = Field(default_factory=dict, description="当前游戏状态")


class CoachSuggestionsMessage(BaseMessage):
    """
    教练建议响应

    Attributes:
        suggestions: 建议列表
        overall_score: 综合评分
    """

    type: MessageType = MessageType.COACH_SUGGESTIONS
    suggestions: list[AISuggestionData] = Field(default_factory=list, description="建议列表")
    overall_score: float = Field(default=50.0, description="综合评分")


class AnalyzeLineupMessage(BaseMessage):
    """
    分析阵容请求

    Attributes:
        game_state: 当前游戏状态
    """

    type: MessageType = MessageType.ANALYZE_LINEUP
    game_state: dict[str, Any] = Field(default_factory=dict, description="当前游戏状态")


class LineupAnalysisMessage(BaseMessage):
    """
    阵容分析结果

    Attributes:
        analysis: 分析结果
    """

    type: MessageType = MessageType.LINEUP_ANALYSIS
    analysis: CoachAnalysisData = Field(..., description="分析结果")


class GetLineupRecommendationsMessage(BaseMessage):
    """
    获取阵容推荐请求

    Attributes:
        current_heroes: 当前拥有的英雄
        limit: 返回数量限制
    """

    type: MessageType = MessageType.GET_LINEUP_RECOMMENDATIONS
    current_heroes: list[dict[str, Any]] = Field(default_factory=list, description="当前拥有的英雄")
    limit: int = Field(default=5, ge=1, le=10, description="返回数量限制")


class LineupRecommendationsMessage(BaseMessage):
    """
    阵容推荐响应

    Attributes:
        recommendations: 推荐阵容列表
    """

    type: MessageType = MessageType.LINEUP_RECOMMENDATIONS
    recommendations: list[LineupRecommendationData] = Field(
        default_factory=list, description="推荐阵容列表"
    )


class GetMatchHistoryMessage(BaseMessage):
    """
    获取对局历史请求

    Attributes:
        limit: 返回数量限制
    """

    type: MessageType = MessageType.GET_MATCH_HISTORY
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")


class MatchHistoryMessage(BaseMessage):
    """
    对局历史响应

    Attributes:
        matches: 对局历史列表
        total_matches: 总对局数
        win_rate: 胜率
        avg_rank: 平均排名
    """

    type: MessageType = MessageType.MATCH_HISTORY
    matches: list[MatchHistoryItemData] = Field(default_factory=list, description="对局历史列表")
    total_matches: int = Field(default=0, description="总对局数")
    win_rate: float = Field(default=0.0, description="胜率")
    avg_rank: float = Field(default=4.0, description="平均排名")


class GetEquipmentAdviceMessage(BaseMessage):
    """
    获取装备建议请求

    Attributes:
        equipment: 当前装备列表
        heroes: 当前英雄列表
    """

    type: MessageType = MessageType.GET_EQUIPMENT_ADVICE
    equipment: list[dict[str, Any]] = Field(default_factory=list, description="当前装备列表")
    heroes: list[dict[str, Any]] = Field(default_factory=list, description="当前英雄列表")


class EquipmentAdviceMessage(BaseMessage):
    """
    装备建议响应

    Attributes:
        advice: 装备建议列表
    """

    type: MessageType = MessageType.EQUIPMENT_ADVICE
    advice: list[EquipmentAdviceData] = Field(default_factory=list, description="装备建议列表")


class GetPositionAdviceMessage(BaseMessage):
    """
    获取站位建议请求

    Attributes:
        board: 当前棋盘状态
        heroes: 当前英雄列表
    """

    type: MessageType = MessageType.GET_POSITION_ADVICE
    board: dict[str, Any] = Field(default_factory=dict, description="当前棋盘状态")
    heroes: list[dict[str, Any]] = Field(default_factory=list, description="当前英雄列表")


class PositionAdviceMessage(BaseMessage):
    """
    站位建议响应

    Attributes:
        advice: 站位建议列表
    """

    type: MessageType = MessageType.POSITION_ADVICE
    advice: list[PositionAdviceData] = Field(default_factory=list, description="站位建议列表")


class GetRoundStrategyMessage(BaseMessage):
    """
    获取回合策略请求

    Attributes:
        round_num: 当前回合
        game_state: 当前游戏状态
    """

    type: MessageType = MessageType.GET_ROUND_STRATEGY
    round_num: int = Field(..., ge=1, description="当前回合")
    game_state: dict[str, Any] = Field(default_factory=dict, description="当前游戏状态")


class RoundStrategyMessage(BaseMessage):
    """
    回合策略响应

    Attributes:
        strategy: 回合策略
    """

    type: MessageType = MessageType.ROUND_STRATEGY
    strategy: RoundStrategyData = Field(..., description="回合策略")


class GetWinRatePredictionMessage(BaseMessage):
    """
    获取胜率预测请求

    Attributes:
        game_state: 当前游戏状态
    """

    type: MessageType = MessageType.GET_WIN_RATE_PREDICTION
    game_state: dict[str, Any] = Field(default_factory=dict, description="当前游戏状态")


class WinRatePredictionMessage(BaseMessage):
    """
    胜率预测响应

    Attributes:
        prediction: 胜率预测
    """

    type: MessageType = MessageType.WIN_RATE_PREDICTION
    prediction: WinRatePredictionData = Field(..., description="胜率预测")


# ============================================================================
# 装备系统消息
# ============================================================================


class EquipmentInstanceData(BaseModel):
    """装备实例数据"""

    instance_id: str = Field(..., description="装备实例ID")
    equipment_id: str = Field(..., description="装备配置ID")
    equipped_to: str | None = Field(default=None, description="穿戴的英雄ID")
    acquired_at: int = Field(default=0, description="获取时间戳")


class EquipItemMessage(BaseMessage):
    """
    穿戴装备请求

    Attributes:
        equipment_instance_id: 装备实例ID
        hero_instance_id: 英雄实例ID
    """

    type: MessageType = MessageType.EQUIP_ITEM
    equipment_instance_id: str = Field(..., description="装备实例ID")
    hero_instance_id: str = Field(..., description="英雄实例ID")


class ItemEquippedMessage(BaseMessage):
    """
    装备穿戴成功响应

    Attributes:
        equipment_instance_id: 装备实例ID
        hero_instance_id: 英雄实例ID
        hero: 更新后的英雄信息
    """

    type: MessageType = MessageType.ITEM_EQUIPPED
    equipment_instance_id: str = Field(..., description="装备实例ID")
    hero_instance_id: str = Field(..., description="英雄实例ID")
    hero: HeroData = Field(..., description="更新后的英雄信息")


class UnequipItemMessage(BaseMessage):
    """
    卸下装备请求

    Attributes:
        equipment_instance_id: 装备实例ID
    """

    type: MessageType = MessageType.UNEQUIP_ITEM
    equipment_instance_id: str = Field(..., description="装备实例ID")


class ItemUnequippedMessage(BaseMessage):
    """
    装备卸下成功响应

    Attributes:
        equipment_instance_id: 装备实例ID
        hero_instance_id: 英雄实例ID
        hero: 更新后的英雄信息
        equipment: 卸下的装备实例
    """

    type: MessageType = MessageType.ITEM_UNEQUIPPED
    equipment_instance_id: str = Field(..., description="装备实例ID")
    hero_instance_id: str = Field(..., description="英雄实例ID")
    hero: HeroData = Field(..., description="更新后的英雄信息")
    equipment: EquipmentInstanceData = Field(..., description="卸下的装备实例")


class CraftEquipmentMessage(BaseMessage):
    """
    合成装备请求

    Attributes:
        equipment_instance_ids: 要合成的装备实例ID列表
    """

    type: MessageType = MessageType.CRAFT_EQUIPMENT
    equipment_instance_ids: list[str] = Field(
        ..., min_length=2, description="要合成的装备实例ID列表"
    )


class EquipmentCraftedMessage(BaseMessage):
    """
    装备合成成功响应

    Attributes:
        consumed_ids: 消耗的装备ID列表
        new_equipment: 新获得的装备
    """

    type: MessageType = MessageType.EQUIPMENT_CRAFTED
    consumed_ids: list[str] = Field(..., description="消耗的装备ID列表")
    new_equipment: EquipmentInstanceData = Field(..., description="新获得的装备")


class GetEquipmentBagMessage(BaseMessage):
    """获取装备背包请求"""

    type: MessageType = MessageType.GET_EQUIPMENT_BAG


class EquipmentBagDataMessage(BaseMessage):
    """
    装备背包响应

    Attributes:
        equipment: 装备列表
    """

    type: MessageType = MessageType.EQUIPMENT_BAG_DATA
    equipment: list[EquipmentInstanceData] = Field(default_factory=list, description="装备列表")


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
    # 观战系统
    MessageType.GET_SPECTATABLE_GAMES: GetSpectatableGamesMessage,
    MessageType.SPECTATABLE_GAMES_LIST: SpectatableGamesListMessage,
    MessageType.JOIN_SPECTATE: JoinSpectateMessage,
    MessageType.SPECTATE_JOINED: SpectateJoinedMessage,
    MessageType.LEAVE_SPECTATE: LeaveSpectateMessage,
    MessageType.SPECTATE_LEFT: SpectateLeftMessage,
    MessageType.SPECTATE_SWITCH: SpectateSwitchMessage,
    MessageType.SPECTATE_SYNC: SpectateSyncMessage,
    MessageType.SPECTATE_STATE: SpectateStateMessage,
    MessageType.SPECTATE_CHAT: SpectateChatMessage,
    MessageType.SPECTATE_CHAT_RECEIVED: SpectateChatReceivedMessage,
    MessageType.SPECTATE_ENDED: SpectateEndedMessage,
    # 随机事件系统
    MessageType.GET_EVENT_HISTORY: GetEventHistoryMessage,
    MessageType.EVENT_HISTORY: EventHistoryMessage,
    MessageType.GET_ACTIVE_EVENTS: GetActiveEventsMessage,
    MessageType.ACTIVE_EVENTS: ActiveEventsMessage,
    MessageType.RANDOM_EVENT_TRIGGERED: RandomEventTriggeredMessage,
    # 皮肤系统
    MessageType.GET_SKINS: GetSkinsMessage,
    MessageType.GET_HERO_SKINS: GetHeroSkinsMessage,
    MessageType.GET_OWNED_SKINS: GetOwnedSkinsMessage,
    MessageType.EQUIP_SKIN: EquipSkinMessage,
    MessageType.UNEQUIP_SKIN: UnequipSkinMessage,
    MessageType.BUY_SKIN: BuySkinMessage,
    MessageType.SET_FAVORITE_SKIN: SetFavoriteSkinMessage,
    MessageType.SKINS_LIST: SkinsListMessage,
    MessageType.HERO_SKINS_LIST: HeroSkinsListMessage,
    MessageType.OWNED_SKINS_LIST: OwnedSkinsListMessage,
    MessageType.SKIN_EQUIPPED: SkinEquippedMessage,
    MessageType.SKIN_UNEQUIPPED: SkinUnequippedMessage,
    MessageType.SKIN_BOUGHT: SkinBoughtMessage,
    MessageType.SKIN_UNLOCKED: SkinUnlockedMessage,
    MessageType.SKIN_FAVORITE_SET: SkinFavoriteSetMessage,
    # 英雄碎片系统
    MessageType.GET_SHARD_BACKPACK: GetShardBackpackMessage,
    MessageType.SHARD_BACKPACK: ShardBackpackMessage,
    MessageType.COMPOSE_HERO: ComposeHeroMessage,
    MessageType.HERO_COMPOSED: HeroComposedMessage,
    MessageType.DECOMPOSE_HERO: DecomposeHeroMessage,
    MessageType.HERO_DECOMPOSED: HeroDecomposedMessage,
    MessageType.BATCH_COMPOSE: BatchComposeMessage,
    MessageType.BATCH_COMPOSE_RESULT: BatchComposeResultMessage,
    MessageType.BATCH_DECOMPOSE: BatchDecomposeMessage,
    MessageType.BATCH_DECOMPOSE_RESULT: BatchDecomposeResultMessage,
    MessageType.ONE_KEY_COMPOSE: OneKeyComposeMessage,
    MessageType.GET_COMPOSE_REQUIREMENTS: GetComposeRequirementsMessage,
    MessageType.COMPOSE_REQUIREMENTS: ComposeRequirementsMessage,
    MessageType.GET_DECOMPOSE_REWARDS: GetDecomposeRewardsMessage,
    MessageType.DECOMPOSE_REWARDS: DecomposeRewardsMessage,
    MessageType.SHARD_UPDATED: ShardUpdatedMessage,
    MessageType.CAN_COMPOSE_NOTIFY: CanComposeNotifyMessage,
    # 回放系统
    MessageType.SAVE_REPLAY: SaveReplayMessage,
    MessageType.REPLAY_SAVED: ReplaySavedMessage,
    MessageType.GET_REPLAY_LIST: GetReplayListMessage,
    MessageType.REPLAY_LIST: ReplayListMessage,
    MessageType.LOAD_REPLAY: LoadReplayMessage,
    MessageType.REPLAY_LOADED: ReplayLoadedMessage,
    MessageType.DELETE_REPLAY: DeleteReplayMessage,
    MessageType.REPLAY_DELETED: ReplayDeletedMessage,
    MessageType.REPLAY_CONTROL: ReplayControlMessage,
    MessageType.REPLAY_STATE_UPDATE: ReplayStateUpdateMessage,
    MessageType.EXPORT_REPLAY: ExportReplayMessage,
    MessageType.REPLAY_EXPORTED: ReplayExportedMessage,
    MessageType.IMPORT_REPLAY: ImportReplayMessage,
    MessageType.REPLAY_IMPORTED: ReplayImportedMessage,
    # 表情系统
    MessageType.GET_EMOTES: GetEmotesMessage,
    MessageType.EMOTES_LIST: EmotesListMessage,
    MessageType.GET_OWNED_EMOTES: GetOwnedEmotesMessage,
    MessageType.OWNED_EMOTES_LIST: OwnedEmotesListMessage,
    MessageType.SEND_EMOTE: SendEmoteMessage,
    MessageType.EMOTE_SENT: EmoteSentMessage,
    MessageType.EMOTE_RECEIVED: EmoteReceivedMessage,
    MessageType.SET_EMOTE_HOTKEY: SetEmoteHotkeyMessage,
    MessageType.EMOTE_HOTKEY_SET: EmoteHotkeySetMessage,
    MessageType.GET_EMOTE_HISTORY: GetEmoteHistoryMessage,
    MessageType.EMOTE_HISTORY: EmoteHistoryMessage,
    MessageType.EMOTE_UNLOCKED: EmoteUnlockedMessage,
    # 投票系统
    MessageType.GET_VOTING_LIST: GetVotingListMessage,
    MessageType.VOTING_LIST: VotingListMessage,
    MessageType.GET_VOTING_DETAILS: GetVotingDetailsMessage,
    MessageType.VOTING_DETAILS: VotingDetailsMessage,
    MessageType.VOTE: VoteMessage,
    MessageType.VOTE_CASTED: VoteCastedMessage,
    MessageType.GET_VOTING_RESULTS: GetVotingResultsMessage,
    MessageType.VOTING_RESULTS: VotingResultsMessage,
    MessageType.CLAIM_VOTING_REWARDS: ClaimVotingRewardsMessage,
    MessageType.VOTING_REWARDS_CLAIMED: VotingRewardsClaimedMessage,
    # 道具系统
    MessageType.GET_CONSUMABLES: GetConsumablesMessage,
    MessageType.CONSUMABLES_LIST: ConsumablesListMessage,
    MessageType.GET_PLAYER_CONSUMABLES: GetPlayerConsumablesMessage,
    MessageType.PLAYER_CONSUMABLES_LIST: PlayerConsumablesListMessage,
    MessageType.USE_CONSUMABLE: UseConsumableMessage,
    MessageType.CONSUMABLE_USED: ConsumableUsedMessage,
    MessageType.BUY_CONSUMABLE: BuyConsumableMessage,
    MessageType.CONSUMABLE_BOUGHT: ConsumableBoughtMessage,
    MessageType.GET_CONSUMABLE_HISTORY: GetConsumableHistoryMessage,
    MessageType.CONSUMABLE_HISTORY: ConsumableHistoryMessage,
    MessageType.CONSUMABLE_ADDED: ConsumableAddedMessage,
    MessageType.CONSUMABLE_EFFECT_APPLIED: ConsumableEffectAppliedMessage,
    # AI教练系统
    MessageType.GET_COACH_SUGGESTIONS: GetCoachSuggestionsMessage,
    MessageType.COACH_SUGGESTIONS: CoachSuggestionsMessage,
    MessageType.ANALYZE_LINEUP: AnalyzeLineupMessage,
    MessageType.LINEUP_ANALYSIS: LineupAnalysisMessage,
    MessageType.GET_LINEUP_RECOMMENDATIONS: GetLineupRecommendationsMessage,
    MessageType.LINEUP_RECOMMENDATIONS: LineupRecommendationsMessage,
    MessageType.GET_MATCH_HISTORY: GetMatchHistoryMessage,
    MessageType.MATCH_HISTORY: MatchHistoryMessage,
    MessageType.GET_EQUIPMENT_ADVICE: GetEquipmentAdviceMessage,
    MessageType.EQUIPMENT_ADVICE: EquipmentAdviceMessage,
    MessageType.GET_POSITION_ADVICE: GetPositionAdviceMessage,
    MessageType.POSITION_ADVICE: PositionAdviceMessage,
    MessageType.GET_ROUND_STRATEGY: GetRoundStrategyMessage,
    MessageType.ROUND_STRATEGY: RoundStrategyMessage,
    MessageType.GET_WIN_RATE_PREDICTION: GetWinRatePredictionMessage,
    MessageType.WIN_RATE_PREDICTION: WinRatePredictionMessage,
    # 装备系统
    MessageType.EQUIP_ITEM: EquipItemMessage,
    MessageType.ITEM_EQUIPPED: ItemEquippedMessage,
    MessageType.UNEQUIP_ITEM: UnequipItemMessage,
    MessageType.ITEM_UNEQUIPPED: ItemUnequippedMessage,
    MessageType.CRAFT_EQUIPMENT: CraftEquipmentMessage,
    MessageType.EQUIPMENT_CRAFTED: EquipmentCraftedMessage,
    MessageType.GET_EQUIPMENT_BAG: GetEquipmentBagMessage,
    MessageType.EQUIPMENT_BAG_DATA: EquipmentBagDataMessage,
    # 错误
    MessageType.ERROR: ErrorMessage,
}
