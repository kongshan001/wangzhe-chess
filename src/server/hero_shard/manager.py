"""
王者之奕 - 英雄碎片管理器

本模块提供英雄碎片系统的管理功能：
- HeroShardManager: 碎片管理器类
- 碎片数量管理
- 英雄合成逻辑
- 英雄分解逻辑
- 批量合成/分解
- 碎片背包管理
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .models import (
    HERO_DECOMPOSE_CONFIG,
    BatchComposeResult,
    BatchDecomposeResult,
    HeroComposeResult,
    HeroDecomposeResult,
    HeroShard,
    ShardComposition,
    ShardsBackpack,
    ShardSource,
)

logger = logging.getLogger(__name__)


class HeroShardManager:
    """
    英雄碎片管理器

    负责管理所有碎片相关的操作：
    - 碎片获取和消耗
    - 英雄合成（100碎片=1星，3个1星+50碎片=2星等）
    - 英雄分解获得碎片
    - 批量合成/分解
    - 碎片背包管理

    Attributes:
        player_backpacks: 玩家碎片背包 (player_id -> ShardsBackpack)
        player_heroes: 玩家英雄数据 (player_id -> List[dict])
    """

    def __init__(self):
        """初始化碎片管理器"""
        self.player_backpacks: dict[str, ShardsBackpack] = {}
        self.player_heroes: dict[str, list[dict[str, Any]]] = {}

        logger.info("HeroShardManager initialized")

    # ==================== 碎片背包管理 ====================

    def get_or_create_backpack(self, player_id: str) -> ShardsBackpack:
        """
        获取或创建玩家碎片背包

        Args:
            player_id: 玩家ID

        Returns:
            玩家碎片背包
        """
        if player_id not in self.player_backpacks:
            self.player_backpacks[player_id] = ShardsBackpack(player_id=player_id)
        return self.player_backpacks[player_id]

    def get_shard_quantity(self, player_id: str, hero_id: str) -> int:
        """
        获取玩家某英雄的碎片数量

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID

        Returns:
            碎片数量
        """
        backpack = self.player_backpacks.get(player_id)
        if not backpack:
            return 0
        return backpack.get_shard_quantity(hero_id)

    def get_all_shards(self, player_id: str) -> list[HeroShard]:
        """
        获取玩家所有碎片

        Args:
            player_id: 玩家ID

        Returns:
            碎片列表
        """
        backpack = self.get_or_create_backpack(player_id)
        return backpack.get_all_shards_list()

    def get_backpack_info(self, player_id: str) -> dict[str, Any]:
        """
        获取玩家碎片背包信息

        Args:
            player_id: 玩家ID

        Returns:
            背包信息字典
        """
        backpack = self.get_or_create_backpack(player_id)
        return {
            "player_id": player_id,
            "shards": [s.to_dict() for s in backpack.get_all_shards_list()],
            "total_shards": backpack.total_shards,
            "last_updated": backpack.last_updated.isoformat() if backpack.last_updated else None,
        }

    # ==================== 碎片获取 ====================

    def add_shards(
        self,
        player_id: str,
        hero_id: str,
        hero_name: str,
        amount: int,
        source: ShardSource,
        hero_cost: int = 1,
    ) -> None:
        """
        增加碎片

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            hero_name: 英雄名称
            amount: 数量
            source: 来源
            hero_cost: 英雄费用
        """
        backpack = self.get_or_create_backpack(player_id)
        backpack.add_shards(hero_id, hero_name, amount, source, hero_cost)

        logger.info(
            f"Player {player_id} gained {amount} shards for hero {hero_id} from {source.value}"
        )

    def add_shards_batch(
        self,
        player_id: str,
        shards_data: list[dict[str, Any]],
        source: ShardSource,
    ) -> None:
        """
        批量增加碎片

        Args:
            player_id: 玩家ID
            shards_data: 碎片数据列表 [{"hero_id": "xxx", "hero_name": "xxx", "amount": 10, "hero_cost": 1}, ...]
            source: 来源
        """
        for data in shards_data:
            self.add_shards(
                player_id=player_id,
                hero_id=data["hero_id"],
                hero_name=data.get("hero_name", ""),
                amount=data["amount"],
                source=source,
                hero_cost=data.get("hero_cost", 1),
            )

    # ==================== 英雄合成 ====================

    def get_composition_config(self, target_star: int) -> ShardComposition:
        """
        获取合成配置

        Args:
            target_star: 目标星级

        Returns:
            合成配置
        """
        return ShardComposition.get_for_star(target_star)

    def can_compose(
        self,
        player_id: str,
        hero_id: str,
        target_star: int,
        hero_name: str = "",
    ) -> tuple[bool, str | None]:
        """
        检查是否可以合成英雄

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            target_star: 目标星级
            hero_name: 英雄名称

        Returns:
            (是否可以合成, 错误信息)
        """
        # 获取合成配置
        config = self.get_composition_config(target_star)

        # 检查碎片数量
        shard_quantity = self.get_shard_quantity(player_id, hero_id)
        if shard_quantity < config.shards_required:
            return (
                False,
                f"碎片不足，需要 {config.shards_required} 碎片，当前只有 {shard_quantity} 碎片",
            )

        # 检查需要的英雄数量（2星及以上需要）
        if config.same_star_heroes > 0:
            player_hero_list = self.player_heroes.get(player_id, [])
            same_star_count = sum(
                1
                for h in player_hero_list
                if h.get("hero_id") == hero_id and h.get("star", 1) == config.hero_star_required
            )

            if same_star_count < config.same_star_heroes:
                return (
                    False,
                    f"英雄数量不足，需要 {config.same_star_heroes} 个 {config.hero_star_required} 星 {hero_name}，当前只有 {same_star_count} 个",
                )

        return True, None

    def compose_hero(
        self,
        player_id: str,
        hero_id: str,
        target_star: int = 1,
        hero_name: str = "",
    ) -> HeroComposeResult:
        """
        合成英雄

        合成规则：
        - 100碎片 = 1星英雄
        - 3个1星 + 50碎片 = 2星英雄
        - 3个2星 + 100碎片 = 3星英雄

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            target_star: 目标星级
            hero_name: 英雄名称

        Returns:
            合成结果
        """
        # 检查是否可以合成
        can_compose, error = self.can_compose(player_id, hero_id, target_star, hero_name)
        if not can_compose:
            return HeroComposeResult(
                success=False,
                hero_id=hero_id,
                hero_name=hero_name,
                star_level=target_star,
                error_message=error,
            )

        # 获取合成配置
        config = self.get_composition_config(target_star)

        # 扣除碎片
        backpack = self.get_or_create_backpack(player_id)
        backpack.remove_shards(hero_id, config.shards_required)

        # 扣除英雄（如果需要）
        heroes_used = 0
        if config.same_star_heroes > 0:
            self._consume_heroes(
                player_id, hero_id, config.hero_star_required, config.same_star_heroes
            )
            heroes_used = config.same_star_heroes

        # 添加新英雄
        self._add_hero(player_id, hero_id, hero_name, target_star)

        logger.info(
            f"Player {player_id} composed {target_star}-star hero {hero_id} ({hero_name}), "
            f"used {config.shards_required} shards, {heroes_used} heroes"
        )

        return HeroComposeResult(
            success=True,
            hero_id=hero_id,
            hero_name=hero_name,
            star_level=target_star,
            shards_used=config.shards_required,
            heroes_used=heroes_used,
        )

    def quick_compose_one_star(
        self,
        player_id: str,
        hero_id: str,
        hero_name: str = "",
    ) -> HeroComposeResult:
        """
        快速合成1星英雄（100碎片=1星）

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            hero_name: 英雄名称

        Returns:
            合成结果
        """
        return self.compose_hero(player_id, hero_id, target_star=1, hero_name=hero_name)

    # ==================== 英雄分解 ====================

    def get_decompose_shards(self, star_level: int) -> int:
        """
        获取分解英雄获得的碎片数量

        Args:
            star_level: 英雄星级

        Returns:
            碎片数量
        """
        return HERO_DECOMPOSE_CONFIG.get(star_level, 30)

    def can_decompose(
        self,
        player_id: str,
        hero_id: str,
        star_level: int,
        hero_name: str = "",
    ) -> tuple[bool, str | None]:
        """
        检查是否可以分解英雄

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            star_level: 英雄星级
            hero_name: 英雄名称

        Returns:
            (是否可以分解, 错误信息)
        """
        # 检查玩家是否拥有该英雄
        player_hero_list = self.player_heroes.get(player_id, [])
        matching_heroes = [
            h
            for h in player_hero_list
            if h.get("hero_id") == hero_id and h.get("star", 1) == star_level
        ]

        if not matching_heroes:
            return False, f"没有 {star_level} 星的 {hero_name} 可以分解"

        return True, None

    def decompose_hero(
        self,
        player_id: str,
        hero_id: str,
        star_level: int,
        hero_name: str = "",
        hero_cost: int = 1,
    ) -> HeroDecomposeResult:
        """
        分解英雄获得碎片

        分解规则：
        - 1星英雄 -> 30碎片
        - 2星英雄 -> 120碎片
        - 3星英雄 -> 420碎片

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            star_level: 英雄星级
            hero_name: 英雄名称
            hero_cost: 英雄费用

        Returns:
            分解结果
        """
        # 检查是否可以分解
        can_decompose, error = self.can_decompose(player_id, hero_id, star_level, hero_name)
        if not can_decompose:
            return HeroDecomposeResult(
                success=False,
                hero_id=hero_id,
                hero_name=hero_name,
                star_level=star_level,
                error_message=error,
            )

        # 移除英雄
        self._remove_hero(player_id, hero_id, star_level)

        # 计算获得的碎片
        shards_gained = self.get_decompose_shards(star_level)

        # 增加碎片
        self.add_shards(
            player_id=player_id,
            hero_id=hero_id,
            hero_name=hero_name,
            amount=shards_gained,
            source=ShardSource.HERO_DECOMPOSE,
            hero_cost=hero_cost,
        )

        logger.info(
            f"Player {player_id} decomposed {star_level}-star hero {hero_id} ({hero_name}), "
            f"gained {shards_gained} shards"
        )

        return HeroDecomposeResult(
            success=True,
            hero_id=hero_id,
            hero_name=hero_name,
            star_level=star_level,
            shards_gained=shards_gained,
        )

    # ==================== 批量操作 ====================

    def batch_compose(
        self,
        player_id: str,
        compose_list: list[dict[str, Any]],
    ) -> BatchComposeResult:
        """
        批量合成英雄

        Args:
            player_id: 玩家ID
            compose_list: 合成列表 [{"hero_id": "xxx", "hero_name": "xxx", "target_star": 1}, ...]

        Returns:
            批量合成结果
        """
        result = BatchComposeResult()

        for item in compose_list:
            compose_result = self.compose_hero(
                player_id=player_id,
                hero_id=item["hero_id"],
                target_star=item.get("target_star", 1),
                hero_name=item.get("hero_name", ""),
            )

            result.results.append(compose_result)

            if compose_result.success:
                result.success_count += 1
                result.total_shards_used += compose_result.shards_used
            else:
                result.fail_count += 1

        logger.info(
            f"Player {player_id} batch compose: {result.success_count} success, {result.fail_count} failed"
        )

        return result

    def batch_decompose(
        self,
        player_id: str,
        decompose_list: list[dict[str, Any]],
    ) -> BatchDecomposeResult:
        """
        批量分解英雄

        Args:
            player_id: 玩家ID
            decompose_list: 分解列表 [{"hero_id": "xxx", "hero_name": "xxx", "star_level": 1, "hero_cost": 1}, ...]

        Returns:
            批量分解结果
        """
        result = BatchDecomposeResult()

        for item in decompose_list:
            decompose_result = self.decompose_hero(
                player_id=player_id,
                hero_id=item["hero_id"],
                star_level=item.get("star_level", 1),
                hero_name=item.get("hero_name", ""),
                hero_cost=item.get("hero_cost", 1),
            )

            result.results.append(decompose_result)

            if decompose_result.success:
                result.success_count += 1
                result.total_shards_gained += decompose_result.shards_gained
            else:
                result.fail_count += 1

        logger.info(
            f"Player {player_id} batch decompose: {result.success_count} success, {result.fail_count} failed"
        )

        return result

    def one_key_compose_all(self, player_id: str) -> BatchComposeResult:
        """
        一键合成所有可合成的英雄（只合成1星）

        Args:
            player_id: 玩家ID

        Returns:
            批量合成结果
        """
        backpack = self.get_or_create_backpack(player_id)
        composable = backpack.get_composable_heroes()

        compose_list = [
            {
                "hero_id": item["hero_id"],
                "hero_name": item["hero_name"],
                "target_star": 1,
            }
            for item in composable
        ]

        return self.batch_compose(player_id, compose_list)

    # ==================== 英雄管理（内部方法） ====================

    def set_player_heroes(self, player_id: str, heroes: list[dict[str, Any]]) -> None:
        """
        设置玩家英雄列表（用于测试或同步）

        Args:
            player_id: 玩家ID
            heroes: 英雄列表
        """
        self.player_heroes[player_id] = heroes

    def get_player_heroes(self, player_id: str) -> list[dict[str, Any]]:
        """
        获取玩家英雄列表

        Args:
            player_id: 玩家ID

        Returns:
            英雄列表
        """
        return self.player_heroes.get(player_id, [])

    def _add_hero(self, player_id: str, hero_id: str, hero_name: str, star_level: int) -> None:
        """
        添加英雄到玩家列表

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            hero_name: 英雄名称
            star_level: 星级
        """
        if player_id not in self.player_heroes:
            self.player_heroes[player_id] = []

        self.player_heroes[player_id].append(
            {
                "hero_id": hero_id,
                "hero_name": hero_name,
                "star": star_level,
                "acquired_at": datetime.now().isoformat(),
            }
        )

    def _remove_hero(self, player_id: str, hero_id: str, star_level: int) -> bool:
        """
        从玩家列表移除英雄

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            star_level: 星级

        Returns:
            是否成功
        """
        if player_id not in self.player_heroes:
            return False

        heroes = self.player_heroes[player_id]
        for i, hero in enumerate(heroes):
            if hero.get("hero_id") == hero_id and hero.get("star", 1) == star_level:
                heroes.pop(i)
                return True

        return False

    def _consume_heroes(self, player_id: str, hero_id: str, star_level: int, count: int) -> int:
        """
        消耗指定数量的英雄

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            star_level: 星级
            count: 数量

        Returns:
            实际消耗数量
        """
        if player_id not in self.player_heroes:
            return 0

        heroes = self.player_heroes[player_id]
        consumed = 0
        to_remove = []

        for i, hero in enumerate(heroes):
            if consumed >= count:
                break
            if hero.get("hero_id") == hero_id and hero.get("star", 1) == star_level:
                to_remove.append(i)
                consumed += 1

        # 从后往前删除，避免索引问题
        for i in sorted(to_remove, reverse=True):
            heroes.pop(i)

        return consumed

    # ==================== 查询方法 ====================

    def get_composable_heroes(self, player_id: str) -> list[dict[str, Any]]:
        """
        获取可合成的英雄列表

        Args:
            player_id: 玩家ID

        Returns:
            可合成英雄列表
        """
        backpack = self.get_or_create_backpack(player_id)
        return backpack.get_composable_heroes()

    def get_composition_requirements(self, target_star: int) -> dict[str, Any]:
        """
        获取合成要求

        Args:
            target_star: 目标星级

        Returns:
            合成要求字典
        """
        config = self.get_composition_config(target_star)
        return config.to_dict()

    def get_decompose_rewards(self, star_level: int) -> dict[str, Any]:
        """
        获取分解奖励

        Args:
            star_level: 星级

        Returns:
            分解奖励字典
        """
        shards = self.get_decompose_shards(star_level)
        return {
            "star_level": star_level,
            "shards_gained": shards,
        }

    # ==================== 缓存管理 ====================

    def clear_cache(self, player_id: str | None = None) -> None:
        """
        清除缓存

        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.player_backpacks.pop(player_id, None)
            self.player_heroes.pop(player_id, None)
        else:
            self.player_backpacks.clear()
            self.player_heroes.clear()


# 全局单例
_hero_shard_manager: HeroShardManager | None = None


def get_hero_shard_manager() -> HeroShardManager:
    """
    获取碎片管理器单例

    Returns:
        碎片管理器实例
    """
    global _hero_shard_manager
    if _hero_shard_manager is None:
        _hero_shard_manager = HeroShardManager()
    return _hero_shard_manager
