"""
王者之奕 - 确定性战斗模拟器

本模块实现确定性的战斗模拟系统，包括：
- 自动寻敌、攻击、技能释放
- 伤害计算
- 确定性保证（相同输入→相同输出）

战斗模拟采用时间步进方式，使用整数运算避免浮点精度问题。
所有随机操作通过确定性随机数生成器实现。
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional

from shared.constants import (
    ATTACK_MANA_GAIN,
    BASE_DAMAGE_PER_SURVIVOR,
    BATTLE_TIME_STEP_MS,
    DAMAGE_MANA_GAIN_RATE,
    FIXED_POINT_PRECISION,
    INITIAL_MANA,
    MAX_MANA,
    STAR_DAMAGE_MULTIPLIER,
)
from shared.models import (
    Board,
    DamageEvent,
    DamageType,
    DeathEvent,
    Hero,
    HeroState,
    Position,
    SkillEvent,
    BattleResult,
)


# ============================================================================
# 战斗单元（战斗中的英雄状态）
# ============================================================================

@dataclass
class BattleUnit:
    """
    战斗单元
    
    战斗中英雄的运行时状态，包含战斗相关的临时属性。
    为了确定性，所有数值使用整数（定点数）。
    
    Attributes:
        hero: 英雄实例（副本）
        team: 所属队伍 (0=玩家A, 1=玩家B)
        current_hp: 当前生命值（使用定点数，乘以FIXED_POINT_PRECISION）
        current_mana: 当前蓝量
        attack_cooldown: 攻击冷却剩余时间（毫秒）
        skill_cooldown: 技能冷却剩余时间（毫秒）
        target_id: 当前目标ID
        state: 战斗状态
        position_x: 当前位置X（使用定点数）
        position_y: 当前位置Y（使用定点数）
    """
    hero: Hero
    team: int
    current_hp: int  # 定点数表示
    current_mana: int
    attack_cooldown: int = 0
    skill_cooldown: int = 0
    target_id: Optional[str] = None
    state: HeroState = HeroState.IDLE
    position_x: int = 0  # 定点数
    position_y: int = 0  # 定点数
    
    # 临时状态效果
    stunned_until: int = 0
    invulnerable_until: int = 0
    
    def __post_init__(self) -> None:
        """初始化位置和生命值"""
        self.current_hp = self.hero.max_hp * FIXED_POINT_PRECISION
        self.current_mana = self.hero.mana
        
        if self.hero.position:
            self.position_x = self.hero.position.x * FIXED_POINT_PRECISION
            self.position_y = self.hero.position.y * FIXED_POINT_PRECISION
    
    @property
    def instance_id(self) -> str:
        """获取实例ID"""
        return self.hero.instance_id
    
    @property
    def max_hp(self) -> int:
        """获取最大生命值（定点数）"""
        return self.hero.max_hp * FIXED_POINT_PRECISION
    
    @property
    def attack(self) -> int:
        """获取攻击力"""
        return self.hero.attack
    
    @property
    def defense(self) -> int:
        """获取防御力"""
        return self.hero.defense
    
    @property
    def attack_speed(self) -> int:
        """
        获取攻击速度（转换为攻击间隔毫秒）
        
        使用定点数表示，1.0攻击速度 = 1000ms间隔
        """
        if self.hero.attack_speed <= 0:
            return 1000 * FIXED_POINT_PRECISION
        # 攻击间隔 = 1000 / 攻击速度
        return int(1000 * FIXED_POINT_PRECISION / self.hero.attack_speed)
    
    @property
    def hp_percent(self) -> int:
        """获取生命值百分比（0-100）"""
        if self.hero.max_hp == 0:
            return 0
        return int(self.current_hp * 100 / self.max_hp)
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.current_hp > 0
    
    def can_act(self, current_time: int) -> bool:
        """检查是否可以行动"""
        return (
            self.is_alive()
            and self.state != HeroState.DEAD
            and current_time >= self.stunned_until
        )
    
    def can_attack(self, current_time: int) -> bool:
        """检查是否可以攻击"""
        return (
            self.can_act(current_time)
            and self.attack_cooldown <= current_time
        )
    
    def can_cast_skill(self) -> bool:
        """检查是否可以释放技能"""
        if not self.hero.skill:
            return False
        return (
            self.is_alive()
            and self.current_mana >= self.hero.skill.mana_cost
            and self.skill_cooldown <= 0
        )
    
    def take_damage(
        self,
        damage: int,
        damage_type: DamageType,
        current_time: int,
    ) -> int:
        """
        受到伤害
        
        Args:
            damage: 原始伤害值
            damage_type: 伤害类型
            current_time: 当前时间
            
        Returns:
            实际受到的伤害值（定点数）
        """
        if not self.is_alive():
            return 0
        
        # 无敌状态
        if current_time < self.invulnerable_until:
            return 0
        
        # 计算实际伤害
        if damage_type == DamageType.TRUE:
            actual_damage = damage * FIXED_POINT_PRECISION
        else:
            # 伤害减免公式：实际伤害 = 伤害 * 100 / (100 + 防御)
            # 使用整数运算
            actual_damage = damage * 100 * FIXED_POINT_PRECISION // (100 + self.defense)
        
        self.current_hp -= actual_damage
        
        # 检查死亡
        if self.current_hp <= 0:
            self.current_hp = 0
            self.state = HeroState.DEAD
        
        # 受击回蓝
        if self.is_alive():
            mana_gain = int(damage * DAMAGE_MANA_GAIN_RATE)
            self.gain_mana(mana_gain)
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        治疗
        
        Args:
            amount: 治疗量
            
        Returns:
            实际治疗量（定点数）
        """
        if not self.is_alive():
            return 0
        
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount * FIXED_POINT_PRECISION)
        return self.current_hp - old_hp
    
    def gain_mana(self, amount: int) -> int:
        """
        获得蓝量
        
        Args:
            amount: 蓝量增加量
            
        Returns:
            实际获得的蓝量
        """
        old_mana = self.current_mana
        self.current_mana = min(MAX_MANA, self.current_mana + amount)
        return self.current_mana - old_mana
    
    def use_mana(self, amount: int) -> bool:
        """
        消耗蓝量
        
        Args:
            amount: 消耗量
            
        Returns:
            是否成功
        """
        if self.current_mana < amount:
            return False
        self.current_mana -= amount
        return True
    
    def get_position(self) -> tuple[int, int]:
        """获取当前位置（转换为整数坐标）"""
        return (
            self.position_x // FIXED_POINT_PRECISION,
            self.position_y // FIXED_POINT_PRECISION,
        )
    
    def set_position(self, x: int, y: int) -> None:
        """设置位置（使用整数坐标）"""
        self.position_x = x * FIXED_POINT_PRECISION
        self.position_y = y * FIXED_POINT_PRECISION
    
    def distance_to(self, other: BattleUnit) -> int:
        """
        计算到另一个单位的曼哈顿距离
        
        Returns:
            距离（整数）
        """
        dx = abs(self.position_x - other.position_x) // FIXED_POINT_PRECISION
        dy = abs(self.position_y - other.position_y) // FIXED_POINT_PRECISION
        return dx + dy
    
    def euclidean_distance_to(self, other: BattleUnit) -> int:
        """
        计算到另一个单位的欧几里得距离（定点数）
        
        使用整数近似避免浮点运算。
        
        Returns:
            距离（定点数）
        """
        dx = self.position_x - other.position_x
        dy = self.position_y - other.position_y
        # 使用近似开方：sqrt(a) ≈ (a * 1000) / (1000 + a/2000)
        # 或者使用整数平方根
        dist_sq = dx * dx + dy * dy
        return _integer_sqrt(dist_sq)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "instance_id": self.instance_id,
            "team": self.team,
            "current_hp": self.current_hp // FIXED_POINT_PRECISION,
            "max_hp": self.hero.max_hp,
            "current_mana": self.current_mana,
            "state": self.state.value,
            "position": self.get_position(),
        }


def _integer_sqrt(n: int) -> int:
    """
    整数平方根（牛顿法）
    
    Args:
        n: 输入值
        
    Returns:
        整数平方根
    """
    if n < 0:
        return 0
    if n == 0:
        return 0
    
    x = n
    y = (x + 1) // 2
    
    while y < x:
        x = y
        y = (x + n // x) // 2
    
    return x


# ============================================================================
# 确定性随机数生成器
# ============================================================================

class DeterministicRNG:
    """
    确定性随机数生成器
    
    使用哈希函数实现确定性随机序列。
    相同的种子和调用序列总是产生相同的输出。
    
    Attributes:
        seed: 随机种子
        counter: 调用计数器
    """
    
    def __init__(self, seed: int) -> None:
        """
        初始化随机数生成器
        
        Args:
            seed: 随机种子
        """
        self.seed = seed
        self.counter = 0
    
    def _hash(self, data: bytes) -> int:
        """计算哈希值"""
        return int(hashlib.sha256(data).hexdigest()[:16], 16)
    
    def random_int(self, min_val: int, max_val: int) -> int:
        """
        生成指定范围的随机整数
        
        Args:
            min_val: 最小值（包含）
            max_val: 最大值（包含）
            
        Returns:
            随机整数
        """
        if min_val >= max_val:
            return min_val
        
        data = f"{self.seed}:{self.counter}".encode()
        self.counter += 1
        
        hash_val = self._hash(data)
        range_size = max_val - min_val + 1
        return min_val + (hash_val % range_size)
    
    def random_percent(self) -> int:
        """
        生成0-100的随机百分比
        
        Returns:
            随机百分比
        """
        return self.random_int(0, 100)
    
    def check_probability(self, probability: int) -> bool:
        """
        检查概率是否触发
        
        Args:
            probability: 概率（0-100）
            
        Returns:
            是否触发
        """
        if probability <= 0:
            return False
        if probability >= 100:
            return True
        return self.random_percent() < probability
    
    def choice(self, items: list) -> Any:
        """
        从列表中随机选择一个元素
        
        Args:
            items: 列表
            
        Returns:
            随机选择的元素
        """
        if not items:
            return None
        index = self.random_int(0, len(items) - 1)
        return items[index]
    
    def shuffle(self, items: list) -> list:
        """
        随机打乱列表（Fisher-Yates算法）
        
        Args:
            items: 列表
            
        Returns:
            打乱后的新列表
        """
        result = list(items)
        for i in range(len(result) - 1, 0, -1):
            j = self.random_int(0, i)
            result[i], result[j] = result[j], result[i]
        return result


# ============================================================================
# 战斗模拟器
# ============================================================================

class BattleSimulator:
    """
    确定性战斗模拟器
    
    模拟两个棋盘之间的战斗。
    
    特点：
    1. 确定性：相同输入产生相同输出
    2. 时间步进：按固定时间步长推进
    3. 整数运算：避免浮点精度问题
    
    战斗流程：
    1. 初始化战斗单元
    2. 按时间步长循环：
       - 检查胜利条件
       - 选择目标
       - 执行攻击
       - 释放技能
       - 更新状态
    3. 生成战斗结果
    
    Attributes:
        board_a: 玩家A的棋盘
        board_b: 玩家B的棋盘
        random_seed: 随机种子
        rng: 确定性随机数生成器
        units_a: 玩家A的战斗单元
        units_b: 玩家B的战斗单元
        current_time: 当前时间（毫秒）
        max_time: 最大战斗时间（毫秒）
        events: 战斗事件列表
    """
    
    def __init__(
        self,
        board_a: Board,
        board_b: Board,
        random_seed: int = 0,
        max_time_ms: int = 60000,  # 60秒
    ) -> None:
        """
        初始化战斗模拟器
        
        Args:
            board_a: 玩家A的棋盘
            board_b: 玩家B的棋盘
            random_seed: 随机种子
            max_time_ms: 最大战斗时间（毫秒）
        """
        self.board_a = board_a
        self.board_b = board_b
        self.random_seed = random_seed
        self.rng = DeterministicRNG(random_seed)
        self.max_time = max_time_ms
        
        # 战斗单元
        self.units_a: list[BattleUnit] = []
        self.units_b: list[BattleUnit] = []
        
        # 状态
        self.current_time = 0
        self.events: list[dict[str, Any]] = []
        self.is_finished = False
        self.winner: Optional[str] = None
    
    def initialize(self) -> None:
        """初始化战斗"""
        # 创建战斗单元（深拷贝英雄）
        self.units_a = []
        for hero in self.board_a.get_all_heroes(alive_only=True):
            hero_copy = copy.deepcopy(hero)
            hero_copy.mana = INITIAL_MANA
            unit = BattleUnit(hero=hero_copy, team=0)
            self.units_a.append(unit)
        
        self.units_b = []
        for hero in self.board_b.get_all_heroes(alive_only=True):
            hero_copy = copy.deepcopy(hero)
            hero_copy.mana = INITIAL_MANA
            unit = BattleUnit(hero=hero_copy, team=1)
            self.units_b.append(unit)
        
        # 随机初始化行动顺序
        self.units_a = self.rng.shuffle(self.units_a)
        self.units_b = self.rng.shuffle(self.units_b)
    
    def simulate(self) -> BattleResult:
        """
        执行战斗模拟
        
        Returns:
            战斗结果
        """
        if self.is_finished:
            return self._create_result()
        
        self.initialize()
        
        # 战斗主循环
        while not self.is_finished and self.current_time <= self.max_time:
            self._tick()
            self.current_time += BATTLE_TIME_STEP_MS
        
        return self._create_result()
    
    def _tick(self) -> None:
        """单步更新"""
        # 检查胜利条件
        if self._check_victory():
            return
        
        # 更新所有单位
        all_units = self._get_all_alive_units()
        
        for unit in all_units:
            if not unit.can_act(self.current_time):
                continue
            
            # 选择目标
            target = self._select_target(unit)
            if target is None:
                continue
            
            unit.target_id = target.instance_id
            
            # 检查是否可以释放技能
            if unit.can_cast_skill():
                self._cast_skill(unit)
            # 检查是否可以攻击
            elif unit.can_attack(self.current_time):
                self._attack(unit, target)
    
    def _check_victory(self) -> bool:
        """
        检查胜利条件
        
        Returns:
            是否已分出胜负
        """
        alive_a = [u for u in self.units_a if u.is_alive()]
        alive_b = [u for u in self.units_b if u.is_alive()]
        
        if not alive_a and not alive_b:
            # 双方同归于尽
            self.winner = "draw"
            self.is_finished = True
            return True
        
        if not alive_a:
            self.winner = self.board_b.owner_id or "player_b"
            self.is_finished = True
            return True
        
        if not alive_b:
            self.winner = self.board_a.owner_id or "player_a"
            self.is_finished = True
            return True
        
        return False
    
    def _get_all_alive_units(self) -> list[BattleUnit]:
        """获取所有存活的战斗单元"""
        units = [u for u in self.units_a if u.is_alive()]
        units.extend(u for u in self.units_b if u.is_alive())
        return units
    
    def _get_enemy_units(self, unit: BattleUnit) -> list[BattleUnit]:
        """获取敌方单位列表"""
        if unit.team == 0:
            return [u for u in self.units_b if u.is_alive()]
        return [u for u in self.units_a if u.is_alive()]
    
    def _select_target(self, unit: BattleUnit) -> Optional[BattleUnit]:
        """
        选择攻击目标
        
        优先选择：
        1. 当前目标（如果在攻击范围内）
        2. 最近的敌人
        3. 随机敌人
        
        Args:
            unit: 选择目标的单位
            
        Returns:
            目标单位，如果没有返回None
        """
        enemies = self._get_enemy_units(unit)
        if not enemies:
            return None
        
        # 如果有当前目标且仍然存活
        if unit.target_id:
            for enemy in enemies:
                if enemy.instance_id == unit.target_id:
                    return enemy
        
        # 选择最近的敌人
        enemies_with_dist = [(e, unit.distance_to(e)) for e in enemies]
        enemies_with_dist.sort(key=lambda x: x[1])
        
        # 如果有多个最近敌人，随机选择
        min_dist = enemies_with_dist[0][1]
        nearest_enemies = [e for e, d in enemies_with_dist if d == min_dist]
        
        if len(nearest_enemies) == 1:
            return nearest_enemies[0]
        
        return self.rng.choice(nearest_enemies)
    
    def _attack(self, attacker: BattleUnit, target: BattleUnit) -> None:
        """
        执行普通攻击
        
        Args:
            attacker: 攻击者
            target: 目标
        """
        attacker.state = HeroState.ATTACKING
        
        # 计算伤害
        damage = attacker.attack
        
        # 应用伤害
        actual_damage = target.take_damage(damage, DamageType.PHYSICAL, self.current_time)
        actual_damage_int = actual_damage // FIXED_POINT_PRECISION
        
        # 记录事件
        self._record_damage_event(
            attacker.instance_id,
            target.instance_id,
            actual_damage_int,
            DamageType.PHYSICAL,
            is_skill=False,
        )
        
        # 攻击者回蓝
        attacker.gain_mana(ATTACK_MANA_GAIN)
        
        # 设置攻击冷却
        attacker.attack_cooldown = self.current_time + attacker.attack_speed // FIXED_POINT_PRECISION
        
        # 检查目标是否死亡
        if not target.is_alive():
            self._record_death_event(target.instance_id, attacker.instance_id)
        
        attacker.state = HeroState.IDLE
    
    def _cast_skill(self, caster: BattleUnit) -> None:
        """
        释放技能
        
        Args:
            caster: 技能释放者
        """
        skill = caster.hero.skill
        if skill is None:
            return
        
        caster.state = HeroState.CASTING
        
        # 消耗蓝量
        caster.use_mana(skill.mana_cost)
        
        # 获取技能目标
        targets = self._get_skill_targets(caster, skill)
        
        # 记录技能事件
        self._record_skill_event(
            caster.instance_id,
            skill.name,
            [t.instance_id for t in targets],
        )
        
        # 对每个目标造成伤害或效果
        for target in targets:
            if skill.damage > 0:
                actual_damage = target.take_damage(
                    skill.damage,
                    skill.damage_type,
                    self.current_time,
                )
                actual_damage_int = actual_damage // FIXED_POINT_PRECISION
                
                self._record_damage_event(
                    caster.instance_id,
                    target.instance_id,
                    actual_damage_int,
                    skill.damage_type,
                    is_skill=True,
                )
                
                # 检查死亡
                if not target.is_alive():
                    self._record_death_event(target.instance_id, caster.instance_id)
        
        # 设置技能冷却
        caster.skill_cooldown = skill.cooldown
        
        caster.state = HeroState.IDLE
    
    def _get_skill_targets(
        self,
        caster: BattleUnit,
        skill: Any,
    ) -> list[BattleUnit]:
        """
        获取技能目标
        
        Args:
            caster: 技能释放者
            skill: 技能定义
            
        Returns:
            目标列表
        """
        enemies = self._get_enemy_units(caster)
        allies = self.units_a if caster.team == 0 else self.units_b
        alive_allies = [u for u in allies if u.is_alive()]
        
        target_type = skill.target_type
        
        if target_type == "self":
            return [caster]
        
        if target_type == "single":
            if not enemies:
                return []
            # 选择最近的敌人
            target = self._select_target(caster)
            return [target] if target else []
        
        if target_type == "area":
            if not enemies:
                return []
            # 选择范围内的敌人（简化：随机选择最多3个）
            selected = []
            for enemy in enemies[:3]:
                selected.append(enemy)
            return selected
        
        if target_type == "all":
            return enemies
        
        # 默认返回空列表
        return []
    
    def _record_damage_event(
        self,
        source_id: str,
        target_id: str,
        damage: int,
        damage_type: DamageType,
        is_skill: bool,
    ) -> None:
        """记录伤害事件"""
        event = {
            "type": "damage",
            "time_ms": self.current_time,
            "source_id": source_id,
            "target_id": target_id,
            "damage": damage,
            "damage_type": damage_type.value,
            "is_skill": is_skill,
        }
        self.events.append(event)
    
    def _record_death_event(self, hero_id: str, killer_id: str) -> None:
        """记录死亡事件"""
        event = {
            "type": "death",
            "time_ms": self.current_time,
            "hero_id": hero_id,
            "killer_id": killer_id,
        }
        self.events.append(event)
    
    def _record_skill_event(
        self,
        hero_id: str,
        skill_name: str,
        targets: list[str],
    ) -> None:
        """记录技能事件"""
        event = {
            "type": "skill",
            "time_ms": self.current_time,
            "hero_id": hero_id,
            "skill_name": skill_name,
            "targets": targets,
        }
        self.events.append(event)
    
    def _create_result(self) -> BattleResult:
        """
        创建战斗结果
        
        Returns:
            战斗结果
        """
        # 确定胜负
        if self.winner == "draw":
            winner = "draw"
            loser = "draw"
        elif self.winner == self.board_a.owner_id or self.winner == "player_a":
            winner = self.board_a.owner_id or "player_a"
            loser = self.board_b.owner_id or "player_b"
        else:
            winner = self.board_b.owner_id or "player_b"
            loser = self.board_a.owner_id or "player_a"
        
        # 计算存活者
        survivors_a = [u.instance_id for u in self.units_a if u.is_alive()]
        survivors_b = [u.instance_id for u in self.units_b if u.is_alive()]
        
        # 计算玩家伤害
        # 伤害 = 存活敌方英雄数 * 基础伤害 * 星级加成
        player_a_damage = 0
        player_b_damage = 0
        
        if winner != "draw":
            if winner == self.board_a.owner_id or winner == "player_a":
                # A赢了，B受到伤害
                for unit in self.units_a:
                    if unit.is_alive():
                        multiplier = STAR_DAMAGE_MULTIPLIER.get(unit.hero.star, 1.0)
                        player_b_damage += int(BASE_DAMAGE_PER_SURVIVOR * multiplier)
            else:
                # B赢了，A受到伤害
                for unit in self.units_b:
                    if unit.is_alive():
                        multiplier = STAR_DAMAGE_MULTIPLIER.get(unit.hero.star, 1.0)
                        player_a_damage += int(BASE_DAMAGE_PER_SURVIVOR * multiplier)
        
        return BattleResult(
            winner=winner,
            loser=loser,
            player_a_damage=player_a_damage,
            player_b_damage=player_b_damage,
            survivors_a=survivors_a,
            survivors_b=survivors_b,
            battle_duration_ms=self.current_time,
            events=list(self.events),
            random_seed=self.random_seed,
        )


# ============================================================================
# 辅助函数
# ============================================================================

def simulate_battle(
    board_a: Board,
    board_b: Board,
    random_seed: int = 0,
) -> BattleResult:
    """
    模拟战斗的便捷函数
    
    Args:
        board_a: 玩家A的棋盘
        board_b: 玩家B的棋盘
        random_seed: 随机种子
        
    Returns:
        战斗结果
    """
    simulator = BattleSimulator(board_a, board_b, random_seed)
    return simulator.simulate()


def create_test_board(
    owner_id: str,
    heroes: Optional[list[Hero]] = None,
) -> Board:
    """
    创建测试用棋盘
    
    Args:
        owner_id: 拥有者ID
        heroes: 英雄列表
        
    Returns:
        棋盘实例
    """
    board = Board.create_empty(owner_id)
    
    if heroes:
        for i, hero in enumerate(heroes):
            x = i % 4
            y = i // 4
            pos = Position(x=x, y=y)
            board.place_hero(hero, pos)
    
    return board


def create_test_hero(
    instance_id: str,
    name: str,
    hp: int = 100,
    attack: int = 10,
    defense: int = 5,
    attack_speed: float = 1.0,
    mana_cost: int = 50,
    skill_damage: int = 30,
) -> Hero:
    """
    创建测试用英雄
    
    Args:
        instance_id: 实例ID
        name: 英雄名称
        hp: 生命值
        attack: 攻击力
        defense: 防御力
        attack_speed: 攻击速度
        mana_cost: 技能蓝耗
        skill_damage: 技能伤害
        
    Returns:
        英雄实例
    """
    from shared.models import Skill, HeroTemplate
    
    skill = Skill(
        name=f"{name}技能",
        description="测试技能",
        mana_cost=mana_cost,
        damage=skill_damage,
        damage_type=DamageType.MAGICAL,
        target_type="single",
    )
    
    template = HeroTemplate(
        hero_id=f"test_{name}",
        name=name,
        cost=1,
        race="人族",
        profession="战士",
        base_hp=hp,
        base_attack=attack,
        base_defense=defense,
        attack_speed=attack_speed,
        skill=skill,
    )
    
    return Hero.create_from_template(template, instance_id, star=1)
