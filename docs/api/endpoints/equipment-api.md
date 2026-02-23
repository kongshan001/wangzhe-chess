# 装备系统 WebSocket API

> API 文档 | 2026-02-23

## 概述

装备系统提供以下 WebSocket 接口：
- 穿戴装备
- 卸下装备
- 合成装备
- 获取装备背包

## 消息类型

### 客户端 -> 服务器

| 消息类型 | 说明 |
|---------|------|
| `equip_item` | 穿戴装备请求 |
| `unequip_item` | 卸下装备请求 |
| `craft_equipment` | 合成装备请求 |
| `get_equipment_bag` | 获取装备背包请求 |

### 服务器 -> 客户端

| 消息类型 | 说明 |
|---------|------|
| `item_equipped` | 装备穿戴成功响应 |
| `item_unequipped` | 装备卸下成功响应 |
| `equipment_crafted` | 装备合成成功响应 |
| `equipment_bag_data` | 装备背包响应 |
| `error` | 错误响应 |

---

## 穿戴装备

### 请求

```json
{
  "type": "equip_item",
  "seq": 1,
  "equipment_instance_id": "eq_inst_1234567890_1",
  "hero_instance_id": "hero_001"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "equip_item" |
| seq | integer | 否 | 消息序列号 |
| equipment_instance_id | string | 是 | 装备实例ID |
| hero_instance_id | string | 是 | 目标英雄实例ID |

### 成功响应

```json
{
  "type": "item_equipped",
  "seq": 1,
  "timestamp": 1234567890123,
  "equipment_instance_id": "eq_inst_1234567890_1",
  "hero_instance_id": "hero_001",
  "hero": {
    "instance_id": "hero_001",
    "template_id": "template_001",
    "name": "测试英雄",
    "cost": 1,
    "star": 1,
    "race": "人族",
    "profession": "战士",
    "max_hp": 100,
    "hp": 100,
    "attack": 10,
    "defense": 5,
    "attack_speed": 1.0,
    "mana": 0,
    "position": null
  }
}
```

### 错误响应

```json
{
  "type": "error",
  "seq": 1,
  "timestamp": 1234567890123,
  "code": 2003,
  "message": "英雄装备槽已满"
}
```

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 2001 | 装备不存在 |
| 2002 | 装备已被穿戴 |
| 2003 | 英雄装备槽已满 |
| 2005 | 英雄不存在 |

---

## 卸下装备

### 请求

```json
{
  "type": "unequip_item",
  "seq": 2,
  "equipment_instance_id": "eq_inst_1234567890_1"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "unequip_item" |
| seq | integer | 否 | 消息序列号 |
| equipment_instance_id | string | 是 | 装备实例ID |

### 成功响应

```json
{
  "type": "item_unequipped",
  "seq": 2,
  "timestamp": 1234567890123,
  "equipment_instance_id": "eq_inst_1234567890_1",
  "hero_instance_id": "hero_001",
  "hero": {
    "instance_id": "hero_001",
    // ... 英雄信息
  },
  "equipment": {
    "instance_id": "eq_inst_1234567890_1",
    "equipment_id": "eq_001",
    "equipped_to": null,
    "acquired_at": 1234567890123
  }
}
```

### 错误响应

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 2001 | 装备不存在 |
| 2007 | 装备未被穿戴 |
| 2005 | 穿戴该装备的英雄不存在 |

---

## 合成装备

### 请求

```json
{
  "type": "craft_equipment",
  "seq": 3,
  "equipment_instance_ids": [
    "eq_inst_1234567890_1",
    "eq_inst_1234567890_2"
  ]
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "craft_equipment" |
| seq | integer | 否 | 消息序列号 |
| equipment_instance_ids | array | 是 | 要合成的装备实例ID列表（至少2个） |

### 成功响应

```json
{
  "type": "equipment_crafted",
  "seq": 3,
  "timestamp": 1234567890123,
  "consumed_ids": [
    "eq_inst_1234567890_1",
    "eq_inst_1234567890_2"
  ],
  "new_equipment": {
    "instance_id": "eq_inst_1234567890123_1",
    "equipment_id": "eq_006",
    "equipped_to": null,
    "acquired_at": 1234567890123
  }
}
```

### 错误响应

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 2001 | 装备不存在 |
| 2002 | 装备已被穿戴（不能合成已穿戴的装备） |
| 2004 | 无效的合成配方 |
| 2006 | 装备数量不足 |

---

## 获取装备背包

### 请求

```json
{
  "type": "get_equipment_bag",
  "seq": 4
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "get_equipment_bag" |
| seq | integer | 否 | 消息序列号 |

### 成功响应

```json
{
  "type": "equipment_bag_data",
  "seq": 4,
  "timestamp": 1234567890123,
  "equipment": [
    {
      "instance_id": "eq_inst_1234567890_1",
      "equipment_id": "eq_001",
      "equipped_to": "hero_001",
      "acquired_at": 1234567890123
    },
    {
      "instance_id": "eq_inst_1234567890_2",
      "equipment_id": "eq_002",
      "equipped_to": null,
      "acquired_at": 1234567890456
    }
  ]
}
```

---

## 数据模型

### EquipmentInstanceData

| 字段 | 类型 | 说明 |
|------|------|------|
| instance_id | string | 装备实例唯一ID |
| equipment_id | string | 装备配置ID |
| equipped_to | string \| null | 穿戴的英雄ID（null表示在背包中） |
| acquired_at | integer | 获取时间戳（毫秒） |

### HeroData

| 字段 | 类型 | 说明 |
|------|------|------|
| instance_id | string | 英雄实例唯一ID |
| template_id | string | 英雄模板ID |
| name | string | 英雄名称 |
| cost | integer | 费用（1-5） |
| star | integer | 星级（1-3） |
| race | string | 种族 |
| profession | string | 职业 |
| max_hp | integer | 最大生命值 |
| hp | integer | 当前生命值 |
| attack | integer | 攻击力 |
| defense | integer | 防御力 |
| attack_speed | float | 攻击速度 |
| mana | integer | 当前蓝量 |
| position | object \| null | 位置信息 |

---

## 业务规则

### 装备槽位限制
- 每个英雄最多装备 3 件装备
- 装备槽位满后无法穿戴新装备

### 装备穿戴规则
- 只能穿戴背包中未装备的装备
- 装备穿戴后立即对英雄生效

### 装备卸下规则
- 只能卸下已穿戴的装备
- 卸下后装备返回背包

### 装备合成规则
- 需要至少 2 件装备才能合成
- 不能合成已穿戴的装备
- 合成消耗原材料，生成新装备
- 需要匹配有效的合成配方
