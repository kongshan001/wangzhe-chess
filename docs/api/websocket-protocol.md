# WebSocket 协议文档

## 概述

王者之奕使用 WebSocket 进行实时通信，包括游戏房间操作、战斗同步等。

## 连接

### 连接端点

```
ws://localhost:8000/ws/{player_id}
```

### 连接流程

1. 客户端建立 WebSocket 连接
2. 客户端发送 `connect` 消息进行认证
3. 服务器响应 `connected` 消息
4. 开始正常消息通信

## 消息格式

所有消息使用 JSON 格式：

```json
{
  "type": "message_type",
  "seq": 1,
  "timestamp": 1704067200000,
  "...": "其他字段"
}
```

### 基础字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 消息类型 |
| seq | integer | 否 | 消息序列号（用于请求-响应匹配） |
| timestamp | integer | 否 | 消息时间戳（毫秒） |

---

## 消息类型

### 连接相关

#### connect - 连接请求

客户端发送以建立连接。

```json
{
  "type": "connect",
  "player_id": "player_001",
  "token": "auth_token",
  "version": "1.0.0"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| player_id | string | 是 | 玩家ID |
| token | string | 是 | 认证令牌 |
| version | string | 否 | 客户端版本 |

---

#### connected - 连接成功

服务器响应连接请求。

```json
{
  "type": "connected",
  "player_id": "player_001",
  "session_id": "sess_1704067200000_1",
  "server_time": 1704067200000
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| player_id | string | 玩家ID |
| session_id | string | 会话ID（用于断线重连） |
| server_time | integer | 服务器时间戳 |

---

#### reconnect - 断线重连

客户端发送以恢复断开的连接。

```json
{
  "type": "reconnect",
  "player_id": "player_001",
  "session_id": "sess_1704067200000_1"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| player_id | string | 是 | 玩家ID |
| session_id | string | 是 | 原会话ID |

---

#### reconnected - 重连成功

服务器响应重连请求。

```json
{
  "type": "reconnected",
  "player_id": "player_001",
  "room_id": "room_001",
  "game_state": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| player_id | string | 玩家ID |
| room_id | string | 当前所在房间ID（可为null） |
| game_state | object | 当前游戏状态（如果在游戏中） |

---

#### heartbeat - 心跳

客户端定期发送心跳保持连接活跃。

```json
{
  "type": "heartbeat"
}
```

---

#### heartbeat_ack - 心跳响应

服务器响应心跳。

```json
{
  "type": "heartbeat_ack",
  "server_time": 1704067200000
}
```

---

#### disconnect - 断开连接

客户端主动断开连接。

```json
{
  "type": "disconnect",
  "reason": "正常退出"
}
```

---

### 房间相关

#### create_room - 创建房间

```json
{
  "type": "create_room",
  "name": "我的房间",
  "config": {
    "mode": "ranked"
  }
}
```

---

#### room_created - 房间创建成功

```json
{
  "type": "room_created",
  "room_id": "room_001",
  "name": "我的房间"
}
```

---

#### join_room - 加入房间

```json
{
  "type": "join_room",
  "room_id": "room_001",
  "slot": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| room_id | string | 否 | 房间ID（不提供则自动匹配） |
| slot | integer | 否 | 指定位置(0-7) |

---

#### room_joined - 加入房间成功

```json
{
  "type": "room_joined",
  "room_id": "room_001",
  "slot": 0,
  "room_state": {
    "name": "房间名称",
    "state": "waiting",
    "players": [...]
  }
}
```

---

#### leave_room - 离开房间

```json
{
  "type": "leave_room"
}
```

---

#### room_left - 离开房间成功

```json
{
  "type": "room_left",
  "room_id": "room_001"
}
```

---

#### ready - 准备

```json
{
  "type": "ready"
}
```

---

#### cancel_ready - 取消准备

```json
{
  "type": "cancel_ready"
}
```

---

#### player_joined - 玩家加入广播

服务器广播给房间内所有玩家。

```json
{
  "type": "player_joined",
  "player": {
    "player_id": 1,
    "nickname": "棋圣",
    "slot": 0
  }
}
```

---

#### player_left - 玩家离开广播

```json
{
  "type": "player_left",
  "player_id": 1
}
```

---

#### player_ready_changed - 准备状态变化广播

```json
{
  "type": "player_ready_changed",
  "player_id": 1,
  "ready": true
}
```

---

### 商店操作

#### shop_refresh - 刷新商店

```json
{
  "type": "shop_refresh"
}
```

---

#### shop_refreshed - 商店已刷新

```json
{
  "type": "shop_refreshed",
  "heroes": [
    {"id": "hero_001", "name": "亚瑟", "cost": 1, "star": 1},
    {"id": "hero_002", "name": "后羿", "cost": 2, "star": 1}
  ],
  "gold_cost": 2
}
```

---

#### shop_buy - 购买英雄

```json
{
  "type": "shop_buy",
  "hero_index": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| hero_index | integer | 是 | 商店槽位索引(0-4) |

---

#### shop_buy_success - 购买成功

```json
{
  "type": "shop_buy_success",
  "hero": {"id": "hero_001", "name": "亚瑟"},
  "gold_cost": 1,
  "remaining_gold": 50
}
```

---

#### hero_sell - 出售英雄

```json
{
  "type": "hero_sell",
  "hero_instance_id": "instance_001"
}
```

---

#### hero_sold - 英雄已出售

```json
{
  "type": "hero_sold",
  "gold_gained": 1,
  "remaining_gold": 51
}
```

---

### 英雄操作

#### hero_place - 放置英雄到棋盘

```json
{
  "type": "hero_place",
  "hero_instance_id": "instance_001",
  "position": {"x": 3, "y": 4}
}
```

---

#### hero_move - 移动英雄

```json
{
  "type": "hero_move",
  "hero_instance_id": "instance_001",
  "from_position": {"x": 3, "y": 4},
  "to_position": {"x": 4, "y": 5}
}
```

---

#### hero_remove - 移除英雄（放回备战席）

```json
{
  "type": "hero_remove",
  "hero_instance_id": "instance_001"
}
```

---

#### hero_upgrade - 合成升级英雄

```json
{
  "type": "hero_upgrade",
  "hero_id": "hero_001"
}
```

---

### 游戏流程

#### game_start - 游戏开始

```json
{
  "type": "game_start",
  "room_id": "room_001"
}
```

---

#### round_start - 回合开始

```json
{
  "type": "round_start",
  "round": 1
}
```

---

#### preparation_start - 准备阶段开始

```json
{
  "type": "preparation_start",
  "round": 1,
  "duration": 30,
  "gold_earned": {
    "base": 5,
    "interest": 2,
    "streak": 1,
    "total": 8
  }
}
```

---

#### battle_start - 战斗阶段开始

```json
{
  "type": "battle_start",
  "round": 1,
  "duration": 60
}
```

---

#### round_end - 回合结束

```json
{
  "type": "round_end",
  "round": 1,
  "results": [
    {
      "attacker_id": 1,
      "defender_id": 2,
      "winner_id": 1,
      "damage": 5
    }
  ]
}
```

---

#### game_over - 游戏结束

```json
{
  "type": "game_over",
  "rankings": [
    {"rank": 1, "player_id": 1, "nickname": "棋圣"},
    {"rank": 2, "player_id": 2, "nickname": "棋圣2"}
  ],
  "total_rounds": 25
}
```

---

### 玩家状态

#### player_state_update - 玩家状态更新

```json
{
  "type": "player_state_update",
  "player_id": 1,
  "state": {
    "hp": 80,
    "gold": 50,
    "level": 5,
    "exp": 3
  }
}
```

---

#### player_hp_update - 血量更新

```json
{
  "type": "player_hp_update",
  "player_id": 1,
  "hp": 80,
  "damage": 5
}
```

---

#### player_gold_update - 金币更新

```json
{
  "type": "player_gold_update",
  "player_id": 1,
  "gold": 50,
  "change": 8
}
```

---

#### player_level_update - 等级更新

```json
{
  "type": "player_level_update",
  "player_id": 1,
  "level": 6
}
```

---

#### player_eliminated - 玩家被淘汰

```json
{
  "type": "player_eliminated",
  "player_id": 1,
  "rank": 5
}
```

---

### 战斗同步

#### battle_sync - 战斗状态同步

```json
{
  "type": "battle_sync",
  "frame": 100,
  "units": [
    {
      "instance_id": "unit_001",
      "hp": 800,
      "position": {"x": 3.5, "y": 4.2},
      "target_id": "unit_002",
      "state": "attacking"
    }
  ]
}
```

---

#### battle_event - 战斗事件

```json
{
  "type": "battle_event",
  "event_type": "damage",
  "frame": 105,
  "source_id": "unit_001",
  "target_id": "unit_002",
  "value": 150
}
```

**事件类型 (event_type)**：
- `damage` - 造成伤害
- `heal` - 治疗
- `death` - 死亡
- `skill_cast` - 技能释放
- `critical` - 暴击

---

### 其他

#### synergy_update - 羁绊状态更新

```json
{
  "type": "synergy_update",
  "player_id": 1,
  "synergies": {
    "warrior": {"count": 3, "level": 1, "active": true},
    "mage": {"count": 2, "level": 0, "active": false}
  }
}
```

---

#### buy_exp - 购买经验

```json
{
  "type": "buy_exp"
}
```

---

#### exp_gained - 获得经验

```json
{
  "type": "exp_gained",
  "player_id": 1,
  "exp_gained": 4,
  "current_exp": 7,
  "exp_needed": 12
}
```

---

#### level_up - 等级提升

```json
{
  "type": "level_up",
  "player_id": 1,
  "new_level": 6
}
```

---

#### error - 错误消息

```json
{
  "type": "error",
  "code": 2101,
  "message": "无效的消息格式",
  "details": {},
  "seq": 1
}
```

---

## 错误码

| 范围 | 分类 |
|------|------|
| 2000-2099 | 连接相关错误 |
| 2100-2199 | 消息相关错误 |
| 2200-2299 | 房间相关错误 |
| 2300-2399 | 游戏相关错误 |

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 2001 | 无效的认证令牌 |
| 2002 | 玩家不存在 |
| 2003 | 会话已过期 |
| 2004 | 已在其他设备连接 |
| 2101 | 无效的消息格式 |
| 2102 | 未知的消息类型 |
| 2201 | 房间不存在 |
| 2202 | 房间已满 |
| 2203 | 不在该房间中 |
| 2301 | 游戏尚未开始 |
| 2302 | 无效的操作 |
| 2303 | 不是你的回合 |

---

## 心跳机制

- **心跳间隔**: 30 秒
- **心跳超时**: 60 秒
- **最大连续超时**: 3 次

客户端应每隔 30 秒发送一次 `heartbeat` 消息。如果连续 3 次心跳未响应，服务器将断开连接。
