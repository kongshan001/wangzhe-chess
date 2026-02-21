# 核心模块代码审查报告

**审查日期**: 2026-02-21  
**审查范围**: 
- `src/shared/models.py` - 核心数据模型
- `src/server/game/battle/simulator.py` - 战斗模拟器

---

## 一、models.py 审查

### 1.1 代码质量

#### 问题 M-001: Hero 类职责过重
- **严重程度**: 中
- **位置**: `src/shared/models.py:233-450`
- **描述**: Hero 类包含 16 个属性，混合了配置数据（name, cost, race）和运行时状态（hp, mana, state），违反单一职责原则
- **建议**: 将 Hero 拆分为 HeroConfig 和 HeroState
```python
@dataclass
class HeroConfig:
    """不可变配置"""
    template_id: str
    name: str
    cost: int
    race: str
    profession: str
    base_stats: HeroStats

@dataclass  
class HeroState:
    """运行时状态"""
    config: HeroConfig
    hp: int
    mana: int
    state: HeroState
    position: Optional[Position]
```

#### 问题 M-002: 序列化逻辑重复
- **严重程度**: 低
- **位置**: 多处 `to_dict`/`from_dict` 方法
- **描述**: 每个 dataclass 都有手动编写的序列化方法，代码重复且容易出错
- **建议**: 使用 `dataclasses.asdict` 或引入 mixin 基类
```python
from dataclasses import asdict
import json

class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**data)
```

---

### 1.2 性能优化

#### 问题 M-003: find_nearest_enemy 算法效率低
- **严重程度**: 高
- **位置**: `src/shared/models.py:564-581`
- **描述**: 每次调用都执行完整排序 O(n log n)，在频繁调用时成为性能瓶颈
```python
# 当前实现
enemies.sort(key=lambda e: from_pos.distance_to(e.position) if e.position else float('inf'))
return enemies[0]
```
- **建议**: 使用 min() 只找最近的一个 O(n)
```python
def find_nearest_enemy(self, from_pos: Position, enemy_board: Board) -> Optional[Hero]:
    enemies = enemy_board.get_all_heroes(alive_only=True)
    if not enemies:
        return None
    return min(
        enemies,
        key=lambda e: from_pos.distance_to(e.position) if e.position else float('inf'),
        default=None
    )
```

#### 问题 M-004: get_all_heroes 重复创建列表
- **严重程度**: 中
- **位置**: `src/shared/models.py:537-550`
- **描述**: 每次调用都创建新列表，在战斗循环中被频繁调用
- **建议**: 
  1. 缓存存活英雄列表，使用增量更新
  2. 返回生成器而非列表
```python
def get_alive_heroes_iter(self) -> Iterator[Hero]:
    """返回存活英雄迭代器，避免创建中间列表"""
    return (h for h in self.heroes.values() if h.is_alive())
```

#### 问题 M-005: Position 距离计算使用浮点数
- **严重程度**: 中
- **位置**: `src/shared/models.py:218-220`
- **描述**: `euclidean_distance` 使用浮点运算，可能导致非确定性
```python
def euclidean_distance(self, other: Position) -> float:
    return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```
- **建议**: 使用整数平方根或 Manhattan 距离替代

---

### 1.3 类型安全

#### 问题 M-006: effect_data 使用 Any 类型
- **严重程度**: 中
- **位置**: `src/shared/models.py:99`
- **描述**: `effect_data: dict[str, Any]` 完全失去类型检查
```python
effect_data: dict[str, Any] = field(default_factory=dict)
```
- **建议**: 定义明确的 TypedDict
```python
from typing import TypedDict

class EffectData(TypedDict, total=False):
    stun_duration: int
    slow_percent: int
    heal_amount: int
    shield_amount: int
    area_radius: int

@dataclass
class Skill:
    effect_data: EffectData = field(default_factory=dict)
```

#### 问题 M-007: from_dict 缺少输入验证
- **严重程度**: 高
- **位置**: 多处 `from_dict` 方法（如 115-126, 176-191, 381-406）
- **描述**: 直接访问字典键可能抛出 KeyError，未验证数据类型和范围
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> Skill:
    return cls(
        name=data["name"],  # 可能 KeyError
        damage=data.get("damage", 0),  # 未验证是否为 int
    )
```
- **建议**: 使用 Pydantic 或添加验证层
```python
from pydantic import BaseModel, validator

class SkillModel(BaseModel):
    name: str
    mana_cost: int = 50
    
    @validator('mana_cost')
    def validate_mana_cost(cls, v):
        if v < 0:
            raise ValueError('mana_cost must be non-negative')
        return v
```

#### 问题 M-008: target_type 使用字符串字面量
- **严重程度**: 中
- **位置**: `src/shared/models.py:97`
- **描述**: `target_type: str = "single"` 应使用枚举
- **建议**: 定义 TargetType 枚举
```python
class TargetType(Enum):
    SINGLE = "single"
    AREA = "area"
    ALL = "all"
    SELF = "self"
```

---

### 1.4 可测试性

#### 问题 M-009: 数据类包含业务逻辑
- **严重程度**: 中
- **位置**: `Hero.take_damage` (288-311), `Hero.heal` (313-325)
- **描述**: 数据模型类包含伤害计算等业务逻辑，测试时需要构造完整对象
- **建议**: 分离数据模型和业务逻辑
```python
class DamageCalculator:
    @staticmethod
    def calculate_damage(damage: int, defense: int, damage_type: DamageType) -> int:
        if damage_type == DamageType.TRUE:
            return damage
        return int(damage * 100 / (100 + defense))

@dataclass
class Hero:
    def take_damage(self, damage: int, damage_type: DamageType) -> int:
        return DamageCalculator.calculate_damage(damage, self.defense, damage_type)
```

#### 问题 M-010: 常量硬编码在模块中
- **严重程度**: 低
- **位置**: `src/shared/models.py:20-27`
- **描述**: 测试时难以覆盖边界条件
- **建议**: 通过依赖注入传入配置

---

### 1.5 扩展性

#### 问题 M-011: 羁绊系统缺乏灵活性
- **严重程度**: 中
- **位置**: `src/shared/models.py:947-963`
- **描述**: `get_active_level` 只支持固定阈值激活，无法支持渐进式加成
- **建议**: 支持自定义激活策略
```python
from abc import ABC, abstractmethod

class SynergyActivationStrategy(ABC):
    @abstractmethod
    def get_bonus(self, count: int) -> Optional[SynergyLevel]:
        pass

class ThresholdActivation(SynergyActivationStrategy):
    def get_bonus(self, count: int) -> Optional[SynergyLevel]:
        # 当前实现
        pass

class ProgressiveActivation(SynergyActivationStrategy):
    def get_bonus(self, count: int) -> Optional[SynergyLevel]:
        # 每增加一个英雄都提供加成
        pass
```

---

### 1.6 安全性

#### 问题 M-012: effect_data 可注入任意数据
- **严重程度**: 高
- **位置**: `src/shared/models.py:99`
- **描述**: `effect_data` 字典可以包含任意数据，可能导致代码注入或数据污染
- **建议**: 
  1. 限制允许的键名
  2. 验证值类型
  3. 深度冻结传入数据

```python
ALLOWED_EFFECT_KEYS = frozenset(['stun_duration', 'slow_percent', 'heal_amount'])

def __post_init__(self):
    unknown_keys = set(self.effect_data.keys()) - ALLOWED_EFFECT_KEYS
    if unknown_keys:
        raise ValueError(f"Unknown effect keys: {unknown_keys}")
```

---

## 二、simulator.py 审查

### 2.1 代码质量

#### 问题 S-001: BattleUnit 属性过多
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:47-301`
- **描述**: BattleUnit 有 12 个字段，部分可通过 Hero 获取但重复存储
- **建议**: 评估哪些字段需要缓存，哪些可以动态计算

#### 问题 S-002: 战斗流程缺少文档
- **严重程度**: 低
- **位置**: `BattleSimulator` 类
- **描述**: 战斗流程复杂但缺少状态机图或流程图说明
- **建议**: 添加状态机图注释

---

### 2.2 性能优化

#### 问题 S-003: deepcopy 性能开销
- **严重程度**: 高
- **位置**: `src/server/game/battle/simulator.py:509-520`
- **描述**: 每个英雄都执行 deepcopy，对于复杂对象开销大
```python
for hero in self.board_a.get_all_heroes(alive_only=True):
    hero_copy = copy.deepcopy(hero)  # 深拷贝开销大
```
- **建议**: 实现 Hero 的 `__copy__` 方法或使用原型模式
```python
@dataclass
class Hero:
    def __copy__(self) -> Hero:
        return Hero(
            instance_id=self.instance_id,
            template_id=self.template_id,
            # ... 只复制需要的字段
            hp=self.hp,
            mana=self.mana,
            state=self.state,
        )
```

#### 问题 S-004: _get_all_alive_units 重复计算
- **严重程度**: 高
- **位置**: `src/server/game/battle/simulator.py:600-604`
- **描述**: 每个 tick 都重新过滤存活单位，复杂度 O(n)
```python
def _get_all_alive_units(self) -> list[BattleUnit]:
    units = [u for u in self.units_a if u.is_alive()]
    units.extend(u for u in self.units_b if u.is_alive())
    return units
```
- **建议**: 使用增量更新或维护存活列表
```python
class BattleSimulator:
    def __init__(self, ...):
        self._alive_units_a: set[str] = set()
        self._alive_units_b: set[str] = set()
    
    def _on_unit_death(self, unit: BattleUnit):
        if unit.team == 0:
            self._alive_units_a.discard(unit.instance_id)
        else:
            self._alive_units_b.discard(unit.instance_id)
```

#### 问题 S-005: 目标选择排序开销
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:638-639`
- **描述**: 每次选择目标都对所有敌人排序
```python
enemies_with_dist = [(e, unit.distance_to(e)) for e in enemies]
enemies_with_dist.sort(key=lambda x: x[1])
```
- **建议**: 使用 heap 或只找最小值
```python
import heapq

def _select_nearest_enemy(self, unit: BattleUnit, enemies: list[BattleUnit]) -> Optional[BattleUnit]:
    if not enemies:
        return None
    
    # 使用 nsmallest 避免完整排序
    nearest = heapq.nsmallest(1, enemies, key=lambda e: unit.distance_to(e))
    return nearest[0] if nearest else None
```

#### 问题 S-006: 战斗循环无早退机制
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:539-541`
- **描述**: 即使已分出胜负也要检查所有单位
- **建议**: 在 `_tick` 开头添加存活检查

---

### 2.3 类型安全

#### 问题 S-007: skill 参数类型为 Any
- **严重程度**: 高
- **位置**: `src/server/game/battle/simulator.py:743-744`
```python
def _get_skill_targets(
    self,
    caster: BattleUnit,
    skill: Any,  # 应该是 Skill 类型
) -> list[BattleUnit]:
```
- **建议**: 明确类型
```python
from shared.models import Skill

def _get_skill_targets(
    self,
    caster: BattleUnit,
    skill: Skill,
) -> list[BattleUnit]:
```

#### 问题 S-008: RNG choice 返回 Any
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:404-417`
- **描述**: `choice` 方法返回 `Any`，丢失类型信息
```python
def choice(self, items: list) -> Any:
```
- **建议**: 使用泛型
```python
from typing import TypeVar

T = TypeVar('T')

def choice(self, items: list[T]) -> Optional[T]:
    if not items:
        return None
    index = self.random_int(0, len(items) - 1)
    return items[index]
```

---

### 2.4 可测试性

#### 问题 S-009: BattleSimulator 状态耦合度高
- **严重程度**: 中
- **位置**: `BattleSimulator` 整体
- **描述**: 初始化、战斗循环、结果生成都在一个类中，难以单独测试
- **建议**: 拆分为多个组件
```python
class BattleInitializer:
    def initialize_units(self, board: Board, team: int) -> list[BattleUnit]:
        pass

class BattleEngine:
    def tick(self, units_a: list[BattleUnit], units_b: list[BattleUnit]) -> None:
        pass

class BattleResultBuilder:
    def build(self, winner: str, units: list[BattleUnit]) -> BattleResult:
        pass
```

#### 问题 S-010: 缺少可注入的随机数策略
- **严重程度**: 低
- **位置**: `src/server/game/battle/simulator.py:492`
- **描述**: RNG 硬编码为 DeterministicRNG，测试难以模拟特定场景
- **建议**: 支持注入不同的 RNG 实现
```python
from typing import Protocol

class RNG(Protocol):
    def random_int(self, min_val: int, max_val: int) -> int: ...
    def choice(self, items: list[T]) -> Optional[T]: ...

class BattleSimulator:
    def __init__(
        self,
        board_a: Board,
        board_b: Board,
        rng: Optional[RNG] = None,
        random_seed: int = 0,
    ):
        self.rng = rng or DeterministicRNG(random_seed)
```

---

### 2.5 扩展性

#### 问题 S-011: 技能目标选择硬编码
- **严重程度**: 高
- **位置**: `src/server/game/battle/simulator.py:741-785`
- **描述**: 技能目标类型只支持 4 种固定模式，难以扩展
```python
if target_type == "single":
    # ...
elif target_type == "area":
    # 简化实现：只取前3个
    for enemy in enemies[:3]:
        selected.append(enemy)
```
- **建议**: 使用策略模式
```python
class TargetSelector(ABC):
    @abstractmethod
    def select(self, caster: BattleUnit, enemies: list[BattleUnit], allies: list[BattleUnit]) -> list[BattleUnit]:
        pass

class SingleTargetSelector(TargetSelector):
    def select(self, caster, enemies, allies) -> list[BattleUnit]:
        target = self._select_nearest(caster, enemies)
        return [target] if target else []

class AreaTargetSelector(TargetSelector):
    def __init__(self, radius: int = 3):
        self.radius = radius
    
    def select(self, caster, enemies, allies) -> list[BattleUnit]:
        # 基于距离的 AOE 选择
        pass
```

#### 问题 S-012: 伤害计算逻辑不可配置
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:183-189`
- **描述**: 伤害公式硬编码，无法支持不同的伤害类型或特殊效果
```python
actual_damage = damage * 100 * FIXED_POINT_PRECISION // (100 + self.defense)
```
- **建议**: 抽象为可配置的伤害计算器

---

### 2.6 安全性

#### 问题 S-013: RNG 种子未验证范围
- **严重程度**: 低
- **位置**: `src/server/game/battle/simulator.py:344-352`
- **描述**: 种子可能被恶意构造导致哈希冲突
- **建议**: 对种子进行范围验证或标准化

#### 问题 S-014: max_time_ms 可设为极大值
- **严重程度**: 中
- **位置**: `src/server/game/battle/simulator.py:478`
- **描述**: 无上界检查，可能导致无限循环或 DoS
```python
def __init__(
    self,
    board_a: Board,
    board_b: Board,
    random_seed: int = 0,
    max_time_ms: int = 60000,  # 无验证
):
```
- **建议**: 添加范围验证
```python
MAX_BATTLE_TIME_MS = 300000  # 5分钟

def __init__(self, ..., max_time_ms: int = 60000):
    if max_time_ms > MAX_BATTLE_TIME_MS:
        raise ValueError(f"max_time_ms cannot exceed {MAX_BATTLE_TIME_MS}")
    self.max_time = max_time_ms
```

---

## 三、总结

### 优先级排序

| 优先级 | 问题编号 | 描述 |
|--------|----------|------|
| P0 (紧急) | M-003, S-003, S-004 | 性能瓶颈 |
| P0 (紧急) | M-007, S-007 | 类型安全高风险 |
| P1 (重要) | M-012, S-011, S-014 | 安全性/扩展性 |
| P1 (重要) | M-006, S-008 | 类型安全 |
| P2 (一般) | M-001, M-009, S-009 | 代码质量/可测试性 |
| P3 (低) | M-002, M-010, S-002 | 改进项 |

### 重构建议路线图

**第一阶段 (性能优化)**:
1. 优化 `find_nearest_enemy` 使用 min() 替代 sort
2. 移除 deepcopy，实现轻量级复制
3. 使用增量更新替代存活单位过滤

**第二阶段 (类型安全)**:
1. 引入 Pydantic 进行数据验证
2. 消除所有 `Any` 类型
3. 添加 Literal/Enum 替代字符串字面量

**第三阶段 (架构改进)**:
1. 分离数据模型和业务逻辑
2. 引入策略模式处理技能目标选择
3. 提高组件可测试性
