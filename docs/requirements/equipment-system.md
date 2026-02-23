# 英雄装备系统需求文档

> 策划角色输出 | 2026-02-23

## 1. 背景与目标

### 1.1 业务背景

王者之奕作为自走棋游戏，需要装备系统来丰富游戏策略深度。当前系统已有基础的装备配置和合成检查，但缺少完整的穿戴、卸下和合成执行功能。

### 1.2 目标用户

- 游戏玩家：通过装备系统增强英雄战斗力
- 开发团队：需要清晰的接口和可扩展的架构

### 1.3 预期效果

- 玩家可以为英雄穿戴装备，获得属性加成
- 玩家可以卸下装备，灵活调整配置
- 玩家可以通过合成获得更强大的装备
- 系统需要支持 WebSocket 实时通信

## 2. 功能详情

### 2.1 核心功能

#### 2.1.1 装备穿戴

- 玩家选择背包中的装备和目标英雄
- 系统检查英雄装备槽位是否已满（最多3件）
- 系统检查装备是否已被其他英雄穿戴
- 穿戴成功后，装备属性立即应用到英雄

#### 2.1.2 装备卸下

- 玩家选择英雄身上已穿戴的装备
- 装备卸下后返回玩家背包
- 英雄属性立即更新（移除装备加成）

#### 2.1.3 装备合成

- 玩家选择两件符合合成配方的基础装备
- 系统检查合成配方是否存在
- 合成成功后，新装备放入背包
- 原装备被消耗

### 2.2 用户故事

```
作为一名玩家
我希望能为我的英雄装备道具
以便在战斗中获得优势
```

```
作为一名玩家
我希望能在战斗准备阶段更换装备
以便针对不同对手调整策略
```

```
作为一名玩家
我希望将低级装备合成为高级装备
以便最大化装备效果
```

### 2.3 交互流程

```
┌─────────────────────────────────────────────────────────────┐
│                     装备穿戴流程                              │
├─────────────────────────────────────────────────────────────┤
│  1. 客户端发送 EQUIP_ITEM 请求                               │
│     - equipment_id: 装备实例ID                                │
│     - hero_instance_id: 英雄实例ID                            │
│                                                              │
│  2. 服务器验证                                                │
│     - 检查装备是否存在且未装备                                 │
│     - 检查英雄是否存在                                         │
│     - 检查英雄装备槽位是否已满                                 │
│                                                              │
│  3. 执行穿戴                                                  │
│     - 更新装备的 equipped_to 字段                             │
│     - 更新英雄的 equipment 列表                               │
│     - 重新计算英雄属性                                         │
│                                                              │
│  4. 返回响应 EQUIP_ITEM_SUCCESS                              │
│     - 返回更新后的英雄信息                                     │
└─────────────────────────────────────────────────────────────┘
```

## 3. 技术方案

### 3.1 数据模型

#### 3.1.1 装备实例 (EquipmentInstance)

```python
@dataclass
class EquipmentInstance:
    """装备实例"""
    instance_id: str              # 装备实例唯一ID
    equipment_id: str             # 装备配置ID（指向Equipment）
    equipped_to: Optional[str]    # 装备给哪个英雄（hero_instance_id）
    acquired_at: int              # 获取时间戳
```

#### 3.1.2 英雄模型扩展

```python
# 在 Hero 类中添加
equipment: List[str] = field(default_factory=list)  # 装备的装备实例ID列表（最多3个）
```

#### 3.1.3 玩家模型扩展

```python
# 在 Player 类中添加
equipment_bag: List[EquipmentInstance] = field(default_factory=list)  # 装备背包
```

### 3.2 核心类设计

#### 3.2.1 EquipmentService

```python
class EquipmentService:
    """装备业务服务"""
    
    def equip_item(
        self,
        player: Player,
        equipment_instance_id: str,
        hero_instance_id: str
    ) -> EquipResult:
        """装备穿戴"""
        pass
    
    def unequip_item(
        self,
        player: Player,
        equipment_instance_id: str
    ) -> UnequipResult:
        """装备卸下"""
        pass
    
    def craft_equipment(
        self,
        player: Player,
        equipment_ids: List[str]
    ) -> CraftResult:
        """装备合成"""
        pass
    
    def recalculate_hero_stats(
        self,
        hero: Hero,
        equipment_manager: EquipmentManager
    ) -> None:
        """重新计算英雄属性"""
        pass
```

### 3.3 接口设计

#### 3.3.1 WebSocket 消息类型

```python
# 客户端 -> 服务器
EQUIP_ITEM = "equip_item"           # 穿戴装备
UNEQUIP_ITEM = "unequip_item"       # 卸下装备
CRAFT_EQUIPMENT = "craft_equipment" # 合成装备
GET_EQUIPMENT_BAG = "get_equipment_bag"  # 获取装备背包

# 服务器 -> 客户端
ITEM_EQUIPPED = "item_equipped"     # 装备穿戴成功
ITEM_UNEQUIPPED = "item_unequipped" # 装备卸下成功
EQUIPMENT_CRAFTED = "equipment_crafted"  # 装备合成成功
EQUIPMENT_BAG = "equipment_bag"     # 装备背包响应
```

#### 3.3.2 消息结构

```python
# 穿戴装备请求
class EquipItemMessage(BaseMessage):
    type: MessageType = MessageType.EQUIP_ITEM
    equipment_instance_id: str
    hero_instance_id: str

# 穿戴装备响应
class ItemEquippedMessage(BaseMessage):
    type: MessageType = MessageType.ITEM_EQUIPPED
    equipment_instance_id: str
    hero_instance_id: str
    hero: HeroData  # 更新后的英雄信息

# 合成装备请求
class CraftEquipmentMessage(BaseMessage):
    type: MessageType = MessageType.CRAFT_EQUIPMENT
    equipment_instance_ids: List[str]  # 要合成的装备ID列表

# 合成装备响应
class EquipmentCraftedMessage(BaseMessage):
    type: MessageType = MessageType.EQUIPMENT_CRAFTED
    consumed_ids: List[str]      # 消耗的装备ID
    new_equipment: EquipmentInstanceData  # 新装备
```

### 3.4 关键算法

#### 3.4.1 属性计算算法

```python
def calculate_total_stats(hero: Hero, equipment_manager: EquipmentManager) -> EquipmentStats:
    """
    计算英雄的总属性加成
    
    Args:
        hero: 英雄实例
        equipment_manager: 装备管理器
        
    Returns:
        合并后的属性加成
    """
    total = EquipmentStats()
    for eq_instance_id in hero.equipment:
        eq_config = equipment_manager.get_equipment(eq_instance_id.equipment_id)
        if eq_config:
            total = total + eq_config.stats
    return total
```

## 4. 实现要求

### 4.1 后端实现

- [x] 扩展 `Hero` 模型，添加 `equipment` 字段
- [x] 扩展 `Player` 模型，添加 `equipment_bag` 字段
- [x] 创建 `EquipmentInstance` 数据类
- [x] 创建 `EquipmentService` 服务类
- [x] 实现装备穿戴逻辑
- [x] 实现装备卸下逻辑
- [x] 实现装备合成逻辑
- [x] 实现属性重算逻辑

### 4.2 接口开发

- [x] 添加 WebSocket 消息类型
- [x] 创建装备相关消息类
- [x] 创建 WebSocket 处理器

### 4.3 配置文件

- [x] 扩展装备配置文件

## 5. 测试用例

### 5.1 正常流程

| 测试场景 | 输入 | 预期输出 |
|---------|------|---------|
| 穿戴装备 | 背包装备ID + 英雄ID | 装备成功，英雄属性更新 |
| 卸下装备 | 已穿戴的装备ID | 装备返回背包，英雄属性更新 |
| 合成装备 | 两件基础装备ID | 消耗原装备，获得高级装备 |

### 5.2 边界条件

| 测试场景 | 输入 | 预期输出 |
|---------|------|---------|
| 英雄装备槽已满 | 第4件装备 | 失败，返回错误 |
| 装备已被穿戴 | 已装备的装备ID | 失败，返回错误 |
| 合成配方不存在 | 无效的装备组合 | 失败，返回错误 |
| 英雄已满装备 | 合成后超过3件 | 特殊处理逻辑 |

### 5.3 异常处理

| 测试场景 | 输入 | 预期输出 |
|---------|------|---------|
| 装备不存在 | 无效ID | 返回 EQUIPMENT_NOT_FOUND 错误 |
| 英雄不存在 | 无效ID | 返回 HERO_NOT_FOUND 错误 |
| 非法操作 | 其他玩家的装备 | 返回 PERMISSION_DENIED 错误 |

## 6. 验收标准

### 6.1 功能验收

- [ ] 玩家可以正常穿戴装备到英雄
- [ ] 玩家可以正常从英雄卸下装备
- [ ] 玩家可以正常合成装备
- [ ] 装备属性正确应用到英雄
- [ ] 卸下装备后属性正确移除

### 6.2 性能验收

- [ ] 单次操作响应时间 < 100ms
- [ ] 属性计算正确无误

### 6.3 安全验收

- [ ] 无法操作其他玩家的装备
- [ ] 无法重复穿戴同一装备
- [ ] 装备槽位限制被正确执行

## 7. 风险评估

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 属性计算性能 | 中 | 使用缓存机制 |
| 数据一致性 | 高 | 使用事务保护 |

### 7.2 进度风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 需求变更 | 中 | 保持接口灵活性 |

## 8. 附录

### 8.1 装备配置示例

```json
{
  "equipment": [
    {
      "equipment_id": "eq_001",
      "name": "铁剑",
      "tier": 1,
      "rarity": "common",
      "stats": {
        "attack": 15,
        "armor": 0,
        "spell_power": 0,
        "hp": 0,
        "attack_speed": 0
      },
      "recipe": [],
      "description": "基础攻击装备"
    },
    {
      "equipment_id": "eq_006",
      "name": "暴风大剑",
      "tier": 2,
      "rarity": "rare",
      "stats": {
        "attack": 40,
        "armor": 0,
        "spell_power": 0,
        "hp": 0,
        "attack_speed": 0
      },
      "recipe": ["eq_001", "eq_001"],
      "description": "两把铁剑合成"
    }
  ]
}
```

### 8.2 错误码定义

| 错误码 | 名称 | 描述 |
|--------|------|------|
| 2001 | EQUIPMENT_NOT_FOUND | 装备不存在 |
| 2002 | EQUIPMENT_ALREADY_EQUIPPED | 装备已被穿戴 |
| 2003 | HERO_EQUIPMENT_FULL | 英雄装备槽已满 |
| 2004 | INVALID_RECIPE | 无效的合成配方 |
| 2005 | HERO_NOT_FOUND | 英雄不存在 |
| 2006 | INSUFFICIENT_EQUIPMENT | 装备数量不足 |
