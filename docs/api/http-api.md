# HTTP API 文档

## 概述

王者之奕提供 RESTful HTTP API 用于玩家数据管理、排行榜查询等非实时操作。

## 基础信息

- **Base URL**: `/api`
- **Content-Type**: `application/json`

---

## 玩家接口

### 获取玩家信息

获取指定玩家的详细信息，包括基本信息、段位和统计数据。

**请求**

```
GET /api/players/{player_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| player_id | integer | 是 | 玩家ID |

**响应**

```json
{
  "id": 1,
  "user_id": "user_abc123",
  "nickname": "棋圣",
  "avatar": "https://example.com/avatar.png",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_login_at": "2024-01-15T12:00:00",
  "rank": {
    "tier": "gold",
    "sub_tier": 3,
    "stars": 2,
    "points": 1500,
    "max_tier": "platinum",
    "max_points": 1800,
    "display_rank": "黄金III 2星",
    "is_placed": true
  },
  "stats": {
    "total_matches": 100,
    "total_wins": 20,
    "total_top4": 50,
    "win_rate": 20.0,
    "top4_rate": 50.0,
    "avg_rank": 3.5,
    "total_damage_dealt": 50000,
    "total_kills": 1000,
    "total_gold_earned": 10000,
    "max_win_streak": 5,
    "fastest_win_round": 15
  }
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 404 | 玩家不存在 |

---

### 更新玩家信息

更新指定玩家的昵称或头像。

**请求**

```
PUT /api/players/{player_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| player_id | integer | 是 | 玩家ID |

**请求体**

```json
{
  "nickname": "新昵称",
  "avatar": "https://example.com/new-avatar.png"
}
```

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| nickname | string | 否 | 2-20字符 | 新昵称 |
| avatar | string | 否 | 最大500字符 | 新头像URL |

**响应**

返回更新后的玩家基本信息。

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 没有需要更新的字段 |
| 404 | 玩家不存在 |

---

### 获取玩家统计

获取指定玩家的游戏统计数据。

**请求**

```
GET /api/players/{player_id}/stats
```

**响应**

```json
{
  "total_matches": 100,
  "total_wins": 20,
  "total_top4": 50,
  "win_rate": 20.0,
  "top4_rate": 50.0,
  "avg_rank": 3.5,
  "total_damage_dealt": 50000,
  "total_kills": 1000,
  "total_gold_earned": 10000,
  "max_win_streak": 5,
  "fastest_win_round": 15
}
```

**统计字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| total_matches | integer | 总对局数 |
| total_wins | integer | 总胜场（第一名） |
| total_top4 | integer | 总前四场数 |
| win_rate | float | 胜率(%) |
| top4_rate | float | 前四率(%) |
| avg_rank | float | 平均排名 |
| total_damage_dealt | integer | 总造成伤害 |
| total_kills | integer | 总击杀数 |
| total_gold_earned | integer | 总获得金币 |
| max_win_streak | integer | 最大连胜 |
| fastest_win_round | integer | 最快获胜回合 |

---

### 获取玩家段位

获取指定玩家的段位信息。

**请求**

```
GET /api/players/{player_id}/rank
```

**响应**

```json
{
  "tier": "gold",
  "sub_tier": 3,
  "stars": 2,
  "points": 1500,
  "max_tier": "platinum",
  "max_points": 1800,
  "display_rank": "黄金III 2星",
  "is_placed": true
}
```

**段位字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| tier | string | 段位名称 |
| sub_tier | integer | 子段位(1-5) |
| stars | integer | 当前星数 |
| points | integer | 当前积分 |
| max_tier | string | 历史最高段位 |
| max_points | integer | 历史最高积分 |
| display_rank | string | 段位显示文本 |
| is_placed | boolean | 是否完成定位赛 |

**段位等级**

从低到高：
1. bronze - 青铜
2. silver - 白银
3. gold - 黄金
4. platinum - 铂金
5. diamond - 钻石
6. master - 大师
7. grandmaster - 宗师
8. king - 王者

---

### 获取玩家背包

获取指定玩家的背包物品列表。

**请求**

```
GET /api/players/{player_id}/inventory
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| item_type | string | 否 | 物品类型筛选 |

**响应**

```json
[
  {
    "id": 1,
    "item_type": "skin",
    "item_id": "skin_001",
    "quantity": 1,
    "extra_data": {"hero_id": "hero_001"},
    "expires_at": null,
    "is_expired": false
  }
]
```

**背包物品字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 物品记录ID |
| item_type | string | 物品类型 |
| item_id | string | 物品ID |
| quantity | integer | 数量 |
| extra_data | object | 额外数据 |
| expires_at | string | 过期时间（null表示永久） |
| is_expired | boolean | 是否已过期 |

---

### 搜索玩家

通过昵称搜索玩家列表。

**请求**

```
GET /api/players/
```

**查询参数**

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| query | string | 是 | 最少1字符 | 搜索关键词 |
| limit | integer | 否 | 1-100，默认10 | 返回数量限制 |

**响应**

```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "nickname": "棋圣",
      "avatar": "https://example.com/avatar.png"
    },
    {
      "id": 2,
      "nickname": "棋圣Master",
      "avatar": "https://example.com/avatar2.png"
    }
  ]
}
```

---

## 系统接口

### 根路径

获取服务基本信息。

**请求**

```
GET /
```

**响应**

```json
{
  "name": "王者之奕",
  "version": "0.1.0",
  "status": "running"
}
```

---

### 健康检查

检查服务健康状态。

**请求**

```
GET /health
```

**响应**

```json
{
  "status": "healthy"
}
```

---

## 错误响应格式

所有接口在发生错误时返回统一的错误格式：

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE"
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| PLAYER_NOT_FOUND | 404 | 玩家不存在 |
| INVALID_PARAMS | 400 | 请求参数错误 |
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
