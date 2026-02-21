# 王者之奕 - 核心类职责说明

本文档详细说明项目中各个核心类的职责、属性和主要方法。

---

## 目录

1. [WebSocket 处理](#websocket-处理)
2. [房间管理](#房间管理)
3. [游戏核心](#游戏核心)
4. [匹配系统](#匹配系统)
5. [数据模型](#数据模型)
6. [通信协议](#通信协议)

---

## WebSocket 处理

### Session

**位置**: `src/server/ws/handler.py`

**职责**: 存储单个 WebSocket 连接的会话信息。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| session_id | str | 会话唯一ID |
| player_id | str | 玩家ID |
| websocket | WebSocket | WebSocket 连接对象 |
| connected_at | int | 连接时间戳（毫秒） |
| last_heartbeat | int | 最后心跳时间 |
| missed_heartbeats | int | 连续未响应心跳次数 |
| room_id | Optional[str] | 当前所在房间ID |
| is_authenticated | bool | 是否已认证 |
| metadata | dict | 额外元数据 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `update_heartbeat()` | 更新心跳时间，重置超时计数 |
| `is_heartbeat_timeout()` | 检查心跳是否超时 |
| `should_disconnect()` | 检查是否应该断开连接 |

---

### SessionManager

**位置**: `src/server/ws/handler.py`

**职责**: 管理所有活跃的 WebSocket 会话。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| _sessions | dict[str, Session] | session_id -> Session |
| _player_sessions | dict[str, str] | player_id -> session_id |
| _session_counter | int | 会话计数器 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `create_session(player_id, websocket)` | 创建新会话 |
| `get_session(session_id)` | 根据会话ID获取会话 |
| `get_session_by_player(player_id)` | 根据玩家ID获取会话 |
| `remove_session(session_id)` | 移除会话 |
| `get_all_sessions()` | 获取所有会话 |
| `get_sessions_in_room(room_id)` | 获取房间内的所有会话 |
| `set_player_room(player_id, room_id)` | 设置玩家所在房间 |

---

### WebSocketHandler

**位置**: `src/server/ws/handler.py`

**职责**: 管理 WebSocket 连接和消息处理。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| session_manager | SessionManager | 会话管理器 |
| _handlers | dict[MessageType, MessageHandler] | 消息处理器映射 |
| _heartbeat_task | Optional[Task] | 心跳检测任务 |
| _room_handler | Optional[RoomWSHandler] | 房间处理器 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `handle_connection(websocket)` | 处理 WebSocket 连接入口 |
| `on_message(message_type)` | 注册消息处理器装饰器 |
| `send_to_player(player_id, message)` | 向指定玩家发送消息 |
| `broadcast_to_players(player_ids, message)` | 向多个玩家广播消息 |
| `is_player_online(player_id)` | 检查玩家是否在线 |
| `get_online_players()` | 获取所有在线玩家ID |

**使用示例**:
```python
handler = WebSocketHandler()

@handler.on_message(MessageType.SHOP_REFRESH)
async def handle_shop_refresh(session: Session, message: ShopRefreshMessage):
    # 处理商店刷新
    pass
```

---

## 房间管理

### RoomState

**位置**: `src/server/room/game_room.py`

**职责**: 房间状态枚举。

**枚举值**:
| 值 | 说明 |
|------|------|
| WAITING | 等待玩家加入 |
| PREPARING | 准备阶段 |
| BATTLING | 战斗阶段 |
| SETTLING | 结算阶段 |
| FINISHED | 游戏结束 |

---

### PlayerState

**位置**: `src/server/room/game_room.py`

**职责**: 玩家状态枚举。

**枚举值**:
| 值 | 说明 |
|------|------|
| CONNECTED | 已连接但未准备 |
| READY | 已准备 |
| PLAYING | 游戏中 |
| DISCONNECTED | 已断开连接 |
| ELIMINATED | 已被淘汰 |

---

### PlayerInRoom

**位置**: `src/server/room/game_room.py`

**职责**: 存储玩家在当前房间/游戏中的所有状态信息。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| player_id | int | 玩家ID |
| nickname | str | 玩家昵称 |
| state | PlayerState | 玩家状态 |
| slot | int | 房间内位置(0-7) |
| hp | int | 当前生命值 |
| gold | int | 当前金币 |
| level | int | 当前等级 |
| exp | int | 当前经验值 |
| win_streak | int | 当前连胜 |
| lose_streak | int | 当前连败 |
| heroes | List[Dict] | 当前持有的英雄列表 |
| bench | List[Dict] | 备战席英雄 |
| board | List[Dict] | 棋盘上的英雄 |
| synergies | Dict[str, int] | 当前激活的羁绊 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `to_dict()` | 转换为字典 |
| `is_alive` | 检查玩家是否还活着 |
| `is_ready` | 检查玩家是否已准备 |
| `is_connected` | 检查玩家是否在线 |
| `set_ready()` | 设置玩家为已准备状态 |
| `set_playing()` | 设置玩家为游戏中状态 |
| `set_disconnected()` | 设置玩家为断开连接状态 |
| `eliminate()` | 淘汰玩家 |
| `take_damage(damage)` | 扣除生命值 |
| `heal(amount)` | 恢复生命值 |
| `add_gold(amount)` | 增加金币 |
| `spend_gold(amount)` | 消耗金币 |
| `add_exp(amount)` | 增加经验值并检查是否升级 |

---

### GameRoom

**位置**: `src/server/room/game_room.py`

**职责**: 管理8人自走棋游戏房间的所有逻辑。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| room_id | str | 房间唯一ID |
| name | str | 房间名称 |
| state | RoomState | 房间状态 |
| host_id | Optional[int] | 房主ID |
| players | Dict[int, PlayerInRoom] | 玩家字典 |
| spectators | Set[int] | 观战者集合 |
| max_players | int | 最大玩家数(8) |
| current_round | int | 当前回合 |
| phase_start_time | Optional[datetime] | 当前阶段开始时间 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `add_player(player_id, nickname, slot)` | 添加玩家到房间 |
| `remove_player(player_id)` | 从房间移除玩家 |
| `set_player_ready(player_id, ready)` | 设置玩家准备状态 |
| `get_player(player_id)` | 获取玩家实例 |
| `get_all_players()` | 获取所有玩家列表 |
| `get_alive_players()` | 获取存活玩家列表 |
| `start_game()` | 开始游戏 |
| `force_end()` | 强制结束游戏 |
| `get_room_state()` | 获取房间完整状态 |
| `get_player_state(player_id)` | 获取指定玩家的详细状态 |

**属性访问器**:
| 属性 | 说明 |
|------|------|
| player_count | 当前玩家数量 |
| alive_count | 存活玩家数量 |
| ready_count | 已准备玩家数量 |
| is_full | 房间是否已满 |
| is_empty | 房间是否为空 |
| can_start | 是否可以开始游戏 |
| all_disconnected | 是否所有玩家都已断开连接 |

---

### RoomManager

**位置**: `src/server/room/manager.py`

**职责**: 单例模式，管理所有游戏房间的生命周期。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| rooms | Dict[str, GameRoom] | 房间字典 |
| player_rooms | Dict[int, str] | 玩家所在房间映射 |
| _lock | asyncio.Lock | 异步锁 |
| _room_counter | int | 房间计数器 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `get_instance()` | 获取房间管理器单例 |
| `create_room(name, host_id, config)` | 创建新房间 |
| `destroy_room(room_id)` | 销毁房间 |
| `join_room(player_id, nickname, room_id)` | 玩家加入房间 |
| `leave_room(player_id)` | 玩家离开房间 |
| `set_player_ready(player_id, ready)` | 设置玩家准备状态 |
| `get_player_room(player_id)` | 获取玩家所在的房间 |
| `get_room(room_id)` | 获取指定房间 |
| `get_all_rooms()` | 获取所有房间列表 |
| `find_rooms(filter_)` | 根据条件查找房间 |
| `find_available_room()` | 查找一个可加入的房间 |
| `cleanup_idle_rooms()` | 清理空闲房间 |
| `get_stats()` | 获取统计信息 |

---

## 游戏核心

### SharedHeroPool

**位置**: `src/server/game/hero_pool.py`

**职责**: 管理8人共享的英雄池。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| pool | Dict[str, List[HeroInstance]] | 英雄池 {hero_id: [instances]} |
| drawn_count | Dict[str, int] | 已抽取数量 |
| total_count | Dict[str, int] | 总数量配置 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `draw(count, level)` | 抽取指定数量的英雄 |
| `return_hero(hero_instance)` | 归还英雄到池中 |
| `get_remaining(hero_id)` | 获取指定英雄剩余数量 |

---

### HeroFactory

**位置**: `src/server/game/hero_pool.py`

**职责**: 创建英雄实例。

**主要方法**:
| 方法 | 说明 |
|------|------|
| `create(hero_id, star)` | 创建指定英雄实例 |
| `upgrade(instances)` | 合成升级英雄 |

---

### ShopManager

**位置**: `src/server/game/hero_pool.py`

**职责**: 管理商店刷新和购买。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| hero_pool | SharedHeroPool | 英雄池引用 |
| slots | List[Optional[HeroInstance]] | 商店槽位 |
| locked | bool | 是否锁定 |
| level | int | 玩家等级 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `refresh()` | 刷新商店 |
| `buy(slot_index)` | 购买指定槽位英雄 |
| `lock_shop()` | 锁定商店 |
| `unlock_shop()` | 解锁商店 |

---

### SynergyManager

**位置**: `src/server/game/synergy.py`

**职责**: 计算和管理羁绊激活。

**主要方法**:
| 方法 | 说明 |
|------|------|
| `calculate_synergies(heroes)` | 计算阵容羁绊 |
| `get_active_synergies(heroes)` | 获取激活的羁绊 |
| `apply_synergy_effects(heroes, synergies)` | 应用羁绊效果 |

---

### EconomyManager

**位置**: `src/server/game/economy.py`

**职责**: 管理玩家经济（金币、经验、等级）。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| gold | int | 当前金币 |
| level | int | 当前等级 |
| exp | int | 当前经验 |
| win_streak | int | 连胜场次 |
| lose_streak | int | 连败场次 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `add_income()` | 添加回合收入 |
| `spend_gold(amount)` | 消耗金币 |
| `buy_exp()` | 购买经验 |
| `can_level_up()` | 检查是否可以升级 |
| `calculate_income()` | 计算本回合收入 |

---

### BattleSimulator

**位置**: `src/server/game/battle/simulator.py`

**职责**: 确定性战斗模拟。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| attacker_units | List[Unit] | 攻击方单位 |
| defender_units | List[Unit] | 防守方单位 |
| current_frame | int | 当前帧数 |
| random_seed | int | 随机种子 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `simulate(max_frames)` | 执行战斗模拟 |
| `step()` | 执行单帧 |
| `get_state()` | 获取当前战斗状态 |
| `is_finished()` | 检查战斗是否结束 |
| `get_result()` | 获取战斗结果 |

---

## 匹配系统

### QueueEntry

**位置**: `src/server/match/queue.py`

**职责**: 代表一个正在等待匹配的玩家。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| player_id | str | 玩家ID |
| rating | PlayerRating | 玩家段位信息 |
| elo_score | int | ELO 分数 |
| join_time | int | 加入队列时间戳 |
| state | QueueState | 条目状态 |
| priority | QueuePriority | 优先级 |
| search_range | int | 当前搜索范围 |

---

### MatchQueue

**位置**: `src/server/match/queue.py`

**职责**: 管理匹配队列。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| queues | Dict[Tier, List[QueueEntry]] | 分段位队列 |
| config | MatchConfig | 匹配配置 |

**主要方法**:
| 方法 | 说明 |
|------|------|
| `enqueue(entry)` | 玩家入队 |
| `dequeue(player_id)` | 玩家出队 |
| `find_match()` | 尝试匹配 |
| `expand_search(entry)` | 扩大搜索范围 |

---

### PlayerRating

**位置**: `src/server/match/rating.py`

**职责**: 存储玩家段位信息。

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| player_id | str | 玩家ID |
| tier | Tier | 段位 |
| stars | int | 星星数 |
| lp | int | 胜点 |
| wins | int | 胜场 |
| losses | int | 负场 |

---

### EloCalculator

**位置**: `src/server/match/elo.py`

**职责**: ELO 积分计算。

**主要方法**:
| 方法 | 说明 |
|------|------|
| `calculate_new_rating(player_rating, opponent_rating, won)` | 计算新积分 |
| `expected_score(rating_a, rating_b)` | 计算预期胜率 |

---

## 数据模型

### PlayerDB

**位置**: `src/server/models/player.py`

**职责**: 玩家账户数据模型。

**字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 玩家唯一ID |
| user_id | str | 用户唯一标识 |
| username | Optional[str] | 用户名 |
| password_hash | Optional[str] | 密码哈希 |
| nickname | str | 玩家昵称 |
| avatar | Optional[str] | 头像URL |
| is_active | bool | 是否激活 |
| is_banned | bool | 是否封禁 |
| last_login_at | Optional[datetime] | 最后登录时间 |

---

### PlayerRankDB

**位置**: `src/server/models/player.py`

**职责**: 玩家段位数据模型。

**字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| player_id | int | 玩家ID（外键） |
| tier | RankTier | 段位 |
| sub_tier | int | 子段位(1-5) |
| stars | int | 星星数 |
| points | int | 积分 |
| max_tier | RankTier | 历史最高段位 |
| is_placed | bool | 是否完成定位赛 |

---

### PlayerStatsDB

**位置**: `src/server/models/player.py`

**职责**: 玩家统计数据模型。

**字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| player_id | int | 玩家ID（外键） |
| total_matches | int | 总对局数 |
| total_wins | int | 胜场数 |
| total_top4 | int | 前四场数 |
| total_damage_dealt | int | 总造成伤害 |
| total_kills | int | 总击杀数 |
| total_gold_earned | int | 总获得金币 |
| max_win_streak | int | 最大连胜 |
| fastest_win_round | int | 最快获胜回合 |

---

### HeroConfigDB

**位置**: `src/server/models/hero_config.py`

**职责**: 英雄配置数据模型。

**字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| hero_id | str | 英雄ID |
| name | str | 英雄名称 |
| cost | int | 费用(1-5) |
| races | List[str] | 种族列表 |
| classes | List[str] | 职业列表 |
| base_hp | int | 基础生命值 |
| base_attack | int | 基础攻击力 |
| base_defense | int | 基础防御力 |
| attack_speed | float | 攻击速度 |
| skill | dict | 技能配置 |

---

## 通信协议

### BaseMessage

**位置**: `src/shared/protocol/messages.py`

**职责**: 所有消息的基类。

**字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | MessageType | 消息类型 |
| seq | Optional[int] | 消息序列号 |
| timestamp | Optional[int] | 消息时间戳 |

---

### MessageType

**位置**: `src/shared/protocol/messages.py`

**职责**: 消息类型枚举。

**主要类型**:
| 类型 | 方向 | 说明 |
|------|------|------|
| CONNECT | C→S | 连接请求 |
| CONNECTED | S→C | 连接成功 |
| HEARTBEAT | C→S | 心跳 |
| HEARTBEAT_ACK | S→C | 心跳响应 |
| JOIN_ROOM | C→S | 加入房间 |
| ROOM_JOINED | S→C | 加入成功 |
| SHOP_REFRESH | C→S | 刷新商店 |
| SHOP_REFRESHED | S→C | 商店已刷新 |
| HERO_PLACE | C→S | 放置英雄 |
| ROUND_START | S→C | 回合开始 |
| BATTLE_START | S→C | 战斗开始 |
| GAME_OVER | S→C | 游戏结束 |
| ERROR | S→C | 错误消息 |

---

### MessageCodec

**位置**: `src/shared/protocol/codec.py`

**职责**: 消息编解码。

**主要方法**:
| 方法 | 说明 |
|------|------|
| `encode_message(message)` | 编码消息为 JSON |
| `decode_message(data)` | 解码 JSON 为消息对象 |

---

## 类图关系

```
┌─────────────────┐
│ WebSocketHandler│
└────────┬────────┘
         │
         │ 管理
         ▼
┌─────────────────┐     ┌─────────────────┐
│ SessionManager  │────<│     Session     │
└─────────────────┘     └─────────────────┘
                                │
                                │ 关联
                                ▼
┌─────────────────┐     ┌─────────────────┐
│   RoomManager   │────<│    GameRoom     │
└─────────────────┘     └────────┬────────┘
                                 │
                                 │ 包含
                                 ▼
                        ┌─────────────────┐
                        │  PlayerInRoom   │
                        └─────────────────┘
                                 │
                                 │ 使用
                                 ▼
┌─────────────────────────────────────────────────┐
│                   游戏核心                       │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │SharedHeroPool│ │SynergyMgr  │ │EconomyMgr  │ │
│  └─────────────┘ └─────────────┘ └────────────┘ │
│  ┌─────────────┐ ┌─────────────┐               │
│  │ ShopManager │ │ BattleSim   │               │
│  └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────┘
```
