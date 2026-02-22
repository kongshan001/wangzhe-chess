"""
王者之奕 - 羁绊图鉴管理器

本模块实现羁绊图鉴的核心功能：
- 获取所有羁绊信息
- 获取羁绊激活次数
- 获取阵容推荐
- 模拟器功能
- 解锁羁绊成就

依赖:
- game/synergy.py: 羁绊定义和计算
- db/models/synergypedia.py: 数据库持久化
"""

from __future__ import annotations

import random
from typing import Any, Optional

import structlog

from src.server.game.synergy import (
    RACE_SYNERGIES,
    PROFESSION_SYNERGIES,
    SynergyManager,
)
from src.shared.models import SynergyType, Hero
from .models import (
    SynergypediaEntry,
    SynergypediaProgress,
    RecommendedLineup,
    SynergySimulation,
    SynergyAchievement,
)

logger = structlog.get_logger()


class SynergypediaManager:
    """
    羁绊图鉴管理器
    
    管理羁绊图鉴的所有功能。
    
    Attributes:
        synergy_manager: 羁绊管理器（来自游戏核心）
        _hero_configs: 英雄配置字典
        _player_progress: 玩家进度缓存
        _recommendations: 预设推荐阵容
    """
    
    def __init__(
        self,
        synergy_manager: Optional[SynergyManager] = None,
        hero_configs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        初始化羁绊图鉴管理器
        
        Args:
            synergy_manager: 羁绊管理器实例
            hero_configs: 英雄配置字典 {hero_id: HeroTemplate}
        """
        self.synergy_manager = synergy_manager or SynergyManager()
        self._hero_configs = hero_configs or {}
        self._player_progress: dict[str, dict[str, SynergypediaProgress]] = {}
        
        # 初始化推荐阵容
        self._recommendations = self._init_recommendations()
    
    def set_hero_configs(self, hero_configs: dict[str, Any]) -> None:
        """设置英雄配置"""
        self._hero_configs = hero_configs
    
    # ========================================================================
    # 羁绊信息获取
    # ========================================================================
    
    def get_all_synergies(self) -> list[SynergypediaEntry]:
        """
        获取所有羁绊信息
        
        Returns:
            羁绊图鉴条目列表
        """
        entries = []
        
        # 处理种族羁绊
        for name, synergy in RACE_SYNERGIES.items():
            related_heroes = self._get_heroes_with_synergy(name, SynergyType.RACE)
            entry = SynergypediaEntry.from_synergy(synergy, related_heroes)
            entries.append(entry)
        
        # 处理职业羁绊
        for name, synergy in PROFESSION_SYNERGIES.items():
            related_heroes = self._get_heroes_with_synergy(name, SynergyType.CLASS)
            entry = SynergypediaEntry.from_synergy(synergy, related_heroes)
            entries.append(entry)
        
        return entries
    
    def get_synergy_info(self, synergy_name: str) -> Optional[SynergypediaEntry]:
        """
        获取单个羁绊的详细信息
        
        Args:
            synergy_name: 羁绊名称
            
        Returns:
            羁绊图鉴条目，不存在返回 None
        """
        synergy = self.synergy_manager.get_synergy(synergy_name)
        if synergy is None:
            return None
        
        # 确定羁绊类型
        synergy_type = SynergyType.RACE
        if synergy_name in PROFESSION_SYNERGIES:
            synergy_type = SynergyType.CLASS
        
        related_heroes = self._get_heroes_with_synergy(synergy_name, synergy_type)
        return SynergypediaEntry.from_synergy(synergy, related_heroes)
    
    def get_synergies_by_type(self, synergy_type: SynergyType) -> list[SynergypediaEntry]:
        """
        获取指定类型的羁绊列表
        
        Args:
            synergy_type: 羁绊类型
            
        Returns:
            羁绊图鉴条目列表
        """
        entries = []
        
        if synergy_type == SynergyType.RACE:
            synergies = RACE_SYNERGIES
        else:
            synergies = PROFESSION_SYNERGIES
        
        for name, synergy in synergies.items():
            related_heroes = self._get_heroes_with_synergy(name, synergy_type)
            entry = SynergypediaEntry.from_synergy(synergy, related_heroes)
            entries.append(entry)
        
        return entries
    
    def _get_heroes_with_synergy(
        self,
        synergy_name: str,
        synergy_type: SynergyType,
    ) -> list[str]:
        """
        获取拥有指定羁绊的英雄列表
        
        Args:
            synergy_name: 羁绊名称
            synergy_type: 羁绊类型
            
        Returns:
            英雄ID列表
        """
        heroes = []
        
        for hero_id, config in self._hero_configs.items():
            if synergy_type == SynergyType.RACE:
                if config.race == synergy_name:
                    heroes.append(hero_id)
            else:
                if config.profession == synergy_name:
                    heroes.append(hero_id)
        
        # 按费用排序（高费用在前）
        heroes.sort(key=lambda h: self._hero_configs.get(h, {}).cost if isinstance(self._hero_configs.get(h), dict) else 0, reverse=True)
        
        return heroes
    
    # ========================================================================
    # 羁绊进度管理
    # ========================================================================
    
    def get_player_progress(
        self,
        player_id: str,
        synergy_name: Optional[str] = None,
    ) -> dict[str, SynergypediaProgress] | SynergypediaProgress | None:
        """
        获取玩家的羁绊进度
        
        Args:
            player_id: 玩家ID
            synergy_name: 羁绊名称（可选，不提供则返回所有）
            
        Returns:
            羁绊进度（单个或全部）
        """
        player_progress = self._player_progress.get(player_id, {})
        
        if synergy_name:
            return player_progress.get(synergy_name)
        
        return player_progress
    
    def update_player_progress(
        self,
        player_id: str,
        synergy_name: str,
        heroes_count: int,
        level_reached: int,
        is_win: bool,
    ) -> list[str]:
        """
        更新玩家的羁绊进度
        
        Args:
            player_id: 玩家ID
            synergy_name: 羁绊名称
            heroes_count: 使用的该羁绊英雄数
            level_reached: 达到的羁绊等级
            is_win: 是否获胜
            
        Returns:
            新解锁的成就列表
        """
        if player_id not in self._player_progress:
            self._player_progress[player_id] = {}
        
        if synergy_name not in self._player_progress[player_id]:
            self._player_progress[player_id][synergy_name] = SynergypediaProgress(
                synergy_name=synergy_name,
            )
        
        progress = self._player_progress[player_id][synergy_name]
        new_achievements = progress.update_with_game_result(
            heroes_count=heroes_count,
            level_reached=level_reached,
            is_win=is_win,
        )
        
        if new_achievements:
            logger.info(
                "羁绊成就解锁",
                player_id=player_id,
                synergy=synergy_name,
                achievements=new_achievements,
            )
        
        return new_achievements
    
    def record_game_synergies(
        self,
        player_id: str,
        heroes: list[Hero],
        is_win: bool,
    ) -> dict[str, list[str]]:
        """
        记录对局中所有羁绊的进度
        
        Args:
            player_id: 玩家ID
            heroes: 使用英雄列表
            is_win: 是否获胜
            
        Returns:
            羁绊名称到新成就列表的映射
        """
        results = {}
        
        # 计算激活的羁绊
        active_synergies = self.synergy_manager.calculate_active_synergies(heroes)
        
        # 统计各羁绊的英雄数量
        synergy_counts = self.synergy_manager.count_heroes_by_synergy(heroes)
        
        for synergy_info in active_synergies:
            synergy_name = synergy_info.synergy_name
            heroes_count = synergy_counts.get(synergy_name, 0)
            level_reached = 0
            if synergy_info.active_level:
                # 计算等级（第几级）
                synergy = self.synergy_manager.get_synergy(synergy_name)
                if synergy:
                    for i, level in enumerate(synergy.levels):
                        if level == synergy_info.active_level:
                            level_reached = i + 1
                            break
            
            new_achievements = self.update_player_progress(
                player_id=player_id,
                synergy_name=synergy_name,
                heroes_count=heroes_count,
                level_reached=level_reached,
                is_win=is_win,
            )
            
            if new_achievements:
                results[synergy_name] = new_achievements
        
        return results
    
    # ========================================================================
    # 阵容推荐
    # ========================================================================
    
    def get_recommended_lineups(
        self,
        synergy_name: Optional[str] = None,
        limit: int = 10,
    ) -> list[RecommendedLineup]:
        """
        获取推荐阵容
        
        Args:
            synergy_name: 羁绊名称（可选，用于筛选）
            limit: 返回数量限制
            
        Returns:
            推荐阵容列表
        """
        recommendations = self._recommendations
        
        if synergy_name:
            # 筛选包含指定羁绊的阵容
            recommendations = [
                r for r in recommendations
                if synergy_name in r.core_synergies
            ]
        
        # 按优先级排序
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        return recommendations[:limit]
    
    def _init_recommendations(self) -> list[RecommendedLineup]:
        """初始化预设推荐阵容"""
        return [
            # 人族法师阵容
            RecommendedLineup(
                name="人族法师流",
                description="以人族羁绊搭配法师，提供高额法术伤害和减魔抗效果",
                core_synergies=["人族", "法师"],
                hero_recommendations=[
                    {"hero_id": "mage_1", "priority": 5, "position": "back"},
                    {"hero_id": "mage_2", "priority": 5, "position": "back"},
                    {"hero_id": "mage_3", "priority": 4, "position": "mid"},
                    {"hero_id": "warrior_1", "priority": 4, "position": "front"},
                    {"hero_id": "warrior_2", "priority": 3, "position": "front"},
                ],
                priority=5,
                difficulty="medium",
                playstyle="burst",
                early_game="优先收集法师英雄，用战士过渡",
                mid_game="凑齐4法师2人族，开始发力",
                late_game="补齐6人族或4法师，追求极致输出",
            ),
            # 刺客切后流
            RecommendedLineup(
                name="刺客切后流",
                description="利用刺客羁绊的暴击加成，快速切入敌方后排",
                core_synergies=["刺客", "妖精"],
                hero_recommendations=[
                    {"hero_id": "assassin_1", "priority": 5, "position": "back"},
                    {"hero_id": "assassin_2", "priority": 5, "position": "back"},
                    {"hero_id": "assassin_3", "priority": 4, "position": "back"},
                    {"hero_id": "fairy_1", "priority": 4, "position": "mid"},
                    {"hero_id": "tank_1", "priority": 3, "position": "front"},
                ],
                priority=4,
                difficulty="hard",
                playstyle="assassin",
                early_game="收集刺客英雄，前排用坦克过渡",
                mid_game="凑齐4刺客获得30%暴击率",
                late_game="搭配妖精增加攻速，或者精灵增加闪避",
            ),
            # 龙族爆发流
            RecommendedLineup(
                name="龙族爆发流",
                description="利用龙族羁绊的开局满蓝效果，第一时间释放技能",
                core_synergies=["龙族", "法师"],
                hero_recommendations=[
                    {"hero_id": "dragon_1", "priority": 5, "position": "mid"},
                    {"hero_id": "dragon_2", "priority": 5, "position": "mid"},
                    {"hero_id": "dragon_3", "priority": 4, "position": "mid"},
                    {"hero_id": "mage_1", "priority": 4, "position": "back"},
                    {"hero_id": "tank_1", "priority": 3, "position": "front"},
                ],
                priority=4,
                difficulty="medium",
                playstyle="burst",
                early_game="寻找龙族英雄，龙族英雄通常费用较高",
                mid_game="3龙族+2法师可以开局秒人",
                late_game="补充更多法术英雄或控制",
            ),
            # 战士坦克流
            RecommendedLineup(
                name="战士坦克流",
                description="高护甲高血量的肉盾阵容，适合新手玩家",
                core_synergies=["战士", "坦克"],
                hero_recommendations=[
                    {"hero_id": "warrior_1", "priority": 5, "position": "front"},
                    {"hero_id": "warrior_2", "priority": 5, "position": "front"},
                    {"hero_id": "warrior_3", "priority": 4, "position": "front"},
                    {"hero_id": "tank_1", "priority": 4, "position": "front"},
                    {"hero_id": "tank_2", "priority": 3, "position": "front"},
                ],
                priority=5,
                difficulty="easy",
                playstyle="tank",
                early_game="收集战士和坦克英雄",
                mid_game="6战士阵容非常肉",
                late_game="补充射手或法师作为输出点",
            ),
            # 精灵闪避流
            RecommendedLineup(
                name="精灵闪避流",
                description="利用精灵羁绊的闪避效果，对抗物理阵容",
                core_synergies=["精灵", "游侠"],
                hero_recommendations=[
                    {"hero_id": "elf_1", "priority": 5, "position": "mid"},
                    {"hero_id": "elf_2", "priority": 5, "position": "mid"},
                    {"hero_id": "elf_3", "priority": 4, "position": "back"},
                    {"hero_id": "ranger_1", "priority": 4, "position": "back"},
                    {"hero_id": "ranger_2", "priority": 3, "position": "back"},
                ],
                priority=3,
                difficulty="medium",
                playstyle="dodge",
                early_game="收集精灵英雄，利用闪避过渡",
                mid_game="4精灵获得40%闪避率",
                late_game="搭配游侠增加攻速输出",
            ),
            # 亡灵射手流
            RecommendedLineup(
                name="亡灵射手流",
                description="亡灵减甲配合射手双重打击，物理输出流",
                core_synergies=["亡灵", "射手"],
                hero_recommendations=[
                    {"hero_id": "undead_1", "priority": 5, "position": "front"},
                    {"hero_id": "undead_2", "priority": 4, "position": "front"},
                    {"hero_id": "hunter_1", "priority": 5, "position": "back"},
                    {"hero_id": "hunter_2", "priority": 5, "position": "back"},
                    {"hero_id": "hunter_3", "priority": 4, "position": "back"},
                ],
                priority=4,
                difficulty="medium",
                playstyle="physical",
                early_game="收集射手英雄，用亡灵前排",
                mid_game="4亡灵减15甲，射手输出爆炸",
                late_game="补充更多射手或物理输出",
            ),
            # 魔种吸血流
            RecommendedLineup(
                name="魔种吸血流",
                description="魔种羁绊提供吸血效果，持续作战能力强",
                core_synergies=["魔种", "战士"],
                hero_recommendations=[
                    {"hero_id": "demon_1", "priority": 5, "position": "front"},
                    {"hero_id": "demon_2", "priority": 5, "position": "front"},
                    {"hero_id": "demon_3", "priority": 4, "position": "mid"},
                    {"hero_id": "warrior_1", "priority": 4, "position": "front"},
                    {"hero_id": "warrior_2", "priority": 3, "position": "front"},
                ],
                priority=3,
                difficulty="easy",
                playstyle="sustain",
                early_game="收集魔种英雄",
                mid_game="4魔种获得30%吸血，续航很强",
                late_game="搭配战士增加坦度",
            ),
            # 神族冷却流
            RecommendedLineup(
                name="神族冷却流",
                description="神族羁绊减少技能冷却，频繁释放技能",
                core_synergies=["神族", "术士"],
                hero_recommendations=[
                    {"hero_id": "god_1", "priority": 5, "position": "mid"},
                    {"hero_id": "god_2", "priority": 5, "position": "mid"},
                    {"hero_id": "warlock_1", "priority": 4, "position": "back"},
                    {"hero_id": "warlock_2", "priority": 4, "position": "back"},
                    {"hero_id": "tank_1", "priority": 3, "position": "front"},
                ],
                priority=4,
                difficulty="hard",
                playstyle="spell",
                early_game="神族英雄费用高，需要经济运营",
                mid_game="2神族减20%冷却，技能释放更快",
                late_game="4神族减50%冷却，技能无限放",
            ),
            # 机械护甲流
            RecommendedLineup(
                name="机械护甲流",
                description="机械羁绊增加护甲，对抗物理伤害",
                core_synergies=["机械", "战士"],
                hero_recommendations=[
                    {"hero_id": "mech_1", "priority": 5, "position": "front"},
                    {"hero_id": "mech_2", "priority": 4, "position": "front"},
                    {"hero_id": "warrior_1", "priority": 4, "position": "front"},
                    {"hero_id": "warrior_2", "priority": 3, "position": "front"},
                    {"hero_id": "hunter_1", "priority": 3, "position": "back"},
                ],
                priority=3,
                difficulty="easy",
                playstyle="tank",
                early_game="收集机械英雄",
                mid_game="4机械获得35点护甲",
                late_game="补充战士增加护甲上限",
            ),
            # 兽族血量流
            RecommendedLineup(
                name="兽族血量流",
                description="兽族羁绊增加生命值，前排非常肉",
                core_synergies=["兽族", "战士"],
                hero_recommendations=[
                    {"hero_id": "beast_1", "priority": 5, "position": "front"},
                    {"hero_id": "beast_2", "priority": 5, "position": "front"},
                    {"hero_id": "beast_3", "priority": 4, "position": "front"},
                    {"hero_id": "warrior_1", "priority": 4, "position": "front"},
                    {"hero_id": "mage_1", "priority": 3, "position": "back"},
                ],
                priority=3,
                difficulty="easy",
                playstyle="tank",
                early_game="收集兽族英雄作为前排",
                mid_game="4兽族获得500点生命值加成",
                late_game="补充输出英雄",
            ),
            # 混合阵容
            RecommendedLineup(
                name="万金油阵容",
                description="多种羁绊混合，适应性强",
                core_synergies=["人族", "战士", "法师"],
                hero_recommendations=[
                    {"hero_id": "warrior_1", "priority": 5, "position": "front"},
                    {"hero_id": "warrior_2", "priority": 4, "position": "front"},
                    {"hero_id": "mage_1", "priority": 5, "position": "back"},
                    {"hero_id": "mage_2", "priority": 4, "position": "back"},
                    {"hero_id": "tank_1", "priority": 4, "position": "front"},
                ],
                priority=4,
                difficulty="easy",
                playstyle="balanced",
                early_game="什么强用什么，灵活调整",
                mid_game="2战士+2法师+2人族",
                late_game="根据对手调整羁绊搭配",
            ),
        ]
    
    # ========================================================================
    # 模拟器功能
    # ========================================================================
    
    def simulate_synergies(
        self,
        hero_ids: list[str],
    ) -> SynergySimulation:
        """
        模拟羁绊激活情况
        
        Args:
            hero_ids: 选中的英雄ID列表
            
        Returns:
            模拟结果
        """
        # 从配置创建英雄实例
        heroes = []
        for hero_id in hero_ids:
            config = self._hero_configs.get(hero_id)
            if config:
                # 创建简化英雄实例用于羁绊计算
                hero = Hero(
                    instance_id=f"sim_{hero_id}",
                    template_id=hero_id,
                    name=config.name,
                    cost=config.cost,
                    star=1,
                    race=config.race,
                    profession=config.profession,
                    max_hp=config.base_hp,
                    hp=config.base_hp,
                    attack=config.base_attack,
                    defense=config.base_defense,
                    attack_speed=config.attack_speed,
                )
                heroes.append(hero)
        
        # 计算激活的羁绊
        active_synergies_result = self.synergy_manager.calculate_active_synergies(heroes)
        
        active_synergies = []
        inactive_synergies = []
        synergy_progress = {}
        total_bonuses: dict[str, float] = {}
        
        # 处理激活的羁绊
        for synergy_info in active_synergies_result:
            synergy_name = synergy_info.synergy_name
            synergy_def = self.synergy_manager.get_synergy(synergy_name)
            
            progress_data = {
                "name": synergy_name,
                "type": synergy_info.synergy_type.value,
                "count": synergy_info.count,
            }
            
            if synergy_info.active_level:
                # 计算等级
                level = 0
                if synergy_def:
                    for i, level_def in enumerate(synergy_def.levels):
                        if level_def == synergy_info.active_level:
                            level = i + 1
                            break
                
                active_synergies.append({
                    "name": synergy_name,
                    "type": synergy_info.synergy_type.value,
                    "count": synergy_info.count,
                    "level": level,
                    "effect": synergy_info.active_level.effect_description,
                    "stat_bonuses": synergy_info.active_level.stat_bonuses,
                })
                
                progress_data["is_active"] = True
                progress_data["current_level"] = level
                progress_data["current_effect"] = synergy_info.active_level.effect_description
                
                # 累加属性加成
                for stat, value in synergy_info.active_level.stat_bonuses.items():
                    total_bonuses[stat] = total_bonuses.get(stat, 0) + value
            else:
                progress_data["is_active"] = False
            
            # 添加下一级需求
            if synergy_def:
                next_req = synergy_def.get_next_level_requirement(synergy_info.count)
                progress_data["next_level_requirement"] = next_req
                progress_data["heroes_needed"] = (next_req - synergy_info.count) if next_req else 0
            
            synergy_progress[synergy_name] = progress_data
        
        # 检查未激活但相关的羁绊（英雄拥有但数量不足）
        all_synergy_names = set()
        for hero in heroes:
            all_synergy_names.add(hero.race)
            all_synergy_names.add(hero.profession)
        
        for synergy_name in all_synergy_names:
            if synergy_name not in synergy_progress:
                synergy_def = self.synergy_manager.get_synergy(synergy_name)
                if synergy_def:
                    inactive_synergies.append({
                        "name": synergy_name,
                        "type": synergy_def.synergy_type.value,
                        "count": 0,
                        "min_requirement": synergy_def.levels[0].required_count if synergy_def.levels else 0,
                    })
        
        # 生成推荐
        recommendations = self._generate_recommendations(heroes, active_synergies)
        
        return SynergySimulation(
            selected_heroes=hero_ids,
            active_synergies=active_synergies,
            inactive_synergies=inactive_synergies,
            synergy_progress=synergy_progress,
            recommendations=recommendations,
            total_bonuses=total_bonuses,
        )
    
    def _generate_recommendations(
        self,
        heroes: list[Hero],
        active_synergies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        生成推荐补充英雄
        
        Args:
            heroes: 当前选中的英雄
            active_synergies: 激活的羁绊
            
        Returns:
            推荐英雄列表
        """
        recommendations = []
        
        # 统计当前羁绊
        synergy_counts: dict[str, int] = {}
        for hero in heroes:
            synergy_counts[hero.race] = synergy_counts.get(hero.race, 0) + 1
            synergy_counts[hero.profession] = synergy_counts.get(hero.profession, 0) + 1
        
        # 找出接近升级的羁绊
        for synergy_name, count in synergy_counts.items():
            synergy_def = self.synergy_manager.get_synergy(synergy_name)
            if not synergy_def:
                continue
            
            next_req = synergy_def.get_next_level_requirement(count)
            if next_req and next_req - count <= 2:
                # 距离下一级只差1-2个英雄，推荐补充
                synergy_type = SynergyType.RACE if synergy_name in RACE_SYNERGIES else SynergyType.CLASS
                related_heroes = self._get_heroes_with_synergy(synergy_name, synergy_type)
                
                # 排除已有的英雄
                existing_ids = {h.template_id for h in heroes}
                recommended_heroes = [h for h in related_heroes if h not in existing_ids]
                
                if recommended_heroes:
                    recommendations.append({
                        "type": "upgrade_synergy",
                        "synergy_name": synergy_name,
                        "current_count": count,
                        "target_count": next_req,
                        "heroes_needed": next_req - count,
                        "recommended_heroes": recommended_heroes[:3],
                        "priority": 5 - (next_req - count),  # 差1个优先级4，差2个优先级3
                    })
        
        # 按优先级排序
        recommendations.sort(key=lambda r: r.get("priority", 0), reverse=True)
        
        return recommendations[:5]
    
    # ========================================================================
    # 成就系统
    # ========================================================================
    
    def get_synergy_achievements(
        self,
        synergy_name: Optional[str] = None,
    ) -> list[SynergyAchievement]:
        """
        获取羁绊成就列表
        
        Args:
            synergy_name: 羁绊名称（可选，不提供则返回所有）
            
        Returns:
            成就列表
        """
        achievements = []
        
        synergies_to_check = [synergy_name] if synergy_name else list(RACE_SYNERGIES.keys()) + list(PROFESSION_SYNERGIES.keys())
        
        for name in synergies_to_check:
            # 激活次数成就
            count_milestones = [
                (10, f"{name}入门者", f"激活{name}羁绊10次", {"gold": 100}),
                (50, f"{name}熟练者", f"激活{name}羁绊50次", {"gold": 300}),
                (100, f"{name}大师", f"激活{name}羁绊100次", {"gold": 500, "hero_shard": 10}),
                (500, f"{name}宗师", f"激活{name}羁绊500次", {"gold": 1000, "hero_shard": 50}),
            ]
            
            for i, (count, ach_name, desc, reward) in enumerate(count_milestones):
                achievements.append(SynergyAchievement(
                    achievement_id=f"synergy_{name}_count_{i}",
                    name=ach_name,
                    description=desc,
                    synergy_name=name,
                    requirement_type="activation_count",
                    requirement_value=count,
                    reward=reward,
                ))
            
            # 等级成就
            level_milestones = [
                (1, f"{name}初窥门径", f"激活{name}羁绊1级", {"gold": 50}),
                (2, f"{name}炉火纯青", f"激活{name}羁绊2级", {"gold": 100}),
                (3, f"{name}登峰造极", f"激活{name}羁绊3级", {"gold": 200, "hero_shard": 20}),
            ]
            
            for i, (level, ach_name, desc, reward) in enumerate(level_milestones):
                achievements.append(SynergyAchievement(
                    achievement_id=f"synergy_{name}_level_{i}",
                    name=ach_name,
                    description=desc,
                    synergy_name=name,
                    requirement_type="level_reached",
                    requirement_value=level,
                    reward=reward,
                ))
        
        return achievements
    
    def check_and_unlock_achievements(
        self,
        player_id: str,
        synergy_name: str,
    ) -> list[SynergyAchievement]:
        """
        检查并解锁成就
        
        Args:
            player_id: 玩家ID
            synergy_name: 羁绊名称
            
        Returns:
            新解锁的成就列表
        """
        progress = self.get_player_progress(player_id, synergy_name)
        if not progress:
            return []
        
        achievements = self.get_synergy_achievements(synergy_name)
        unlocked = []
        
        for achievement in achievements:
            if achievement.check_unlock(progress):
                unlocked.append(achievement)
                logger.info(
                    "羁绊成就解锁",
                    player_id=player_id,
                    achievement=achievement.name,
                )
        
        return unlocked


# ============================================================================
# 全局实例
# ============================================================================

# 全局羁绊图鉴管理器
synergypedia_manager = SynergypediaManager()
