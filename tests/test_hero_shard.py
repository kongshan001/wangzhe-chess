"""
王者之奕 - 英雄碎片系统测试

测试英雄碎片系统的核心功能：
- 碎片管理
- 英雄合成（100碎片=1星，3个1星+50碎片=2星等）
- 英雄分解获得碎片
- 批量合成/分解
- 碎片背包管理
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.server.hero_shard.models import (
    BatchComposeResult,
    BatchDecomposeResult,
    HeroComposeResult,
    HeroDecomposeResult,
    HeroShard,
    ShardComposition,
    ShardSource,
    ShardsBackpack,
    SHARD_COMPOSITION_CONFIG,
    HERO_DECOMPOSE_CONFIG,
)
from src.server.hero_shard.manager import HeroShardManager


class TestHeroShardModels:
    """测试英雄碎片数据模型"""
    
    def test_hero_shard_creation(self):
        """测试碎片创建"""
        shard = HeroShard(
            hero_id="hero_001",
            hero_name="亚瑟",
            quantity=50,
            hero_cost=2,
        )
        
        assert shard.hero_id == "hero_001"
        assert shard.hero_name == "亚瑟"
        assert shard.quantity == 50
        assert shard.hero_cost == 2
    
    def test_hero_shard_add_shards(self):
        """测试增加碎片"""
        shard = HeroShard(hero_id="hero_001", hero_name="亚瑟")
        
        shard.add_shards(30, ShardSource.MATCH_REWARD)
        
        assert shard.quantity == 30
        assert shard.acquired_sources.get("match_reward") == 30
        assert shard.last_acquired_at is not None
    
    def test_hero_shard_remove_shards(self):
        """测试减少碎片"""
        shard = HeroShard(hero_id="hero_001", hero_name="亚瑟", quantity=100)
        
        # 成功减少
        result = shard.remove_shards(30)
        assert result == True
        assert shard.quantity == 70
        
        # 失败减少（数量不足）
        result = shard.remove_shards(100)
        assert result == False
        assert shard.quantity == 70
    
    def test_hero_shard_to_dict(self):
        """测试碎片序列化"""
        shard = HeroShard(
            hero_id="hero_001",
            hero_name="亚瑟",
            quantity=100,
            hero_cost=2,
            acquired_sources={"match_reward": 50, "daily_task": 50},
        )
        
        data = shard.to_dict()
        assert data["hero_id"] == "hero_001"
        assert data["hero_name"] == "亚瑟"
        assert data["quantity"] == 100
        assert data["hero_cost"] == 2
        assert data["acquired_sources"]["match_reward"] == 50
    
    def test_hero_shard_from_dict(self):
        """测试碎片反序列化"""
        data = {
            "hero_id": "hero_001",
            "hero_name": "亚瑟",
            "quantity": 100,
            "hero_cost": 2,
            "acquired_sources": {"match_reward": 100},
            "last_acquired_at": "2026-02-22T12:00:00",
        }
        
        shard = HeroShard.from_dict(data)
        assert shard.hero_id == "hero_001"
        assert shard.quantity == 100
        assert shard.hero_cost == 2


class TestShardComposition:
    """测试碎片合成配置"""
    
    def test_compose_one_star_config(self):
        """测试1星合成配置"""
        config = ShardComposition.get_for_star(1)
        
        assert config.target_star == 1
        assert config.shards_required == 100
        assert config.same_star_heroes == 0
    
    def test_compose_two_star_config(self):
        """测试2星合成配置"""
        config = ShardComposition.get_for_star(2)
        
        assert config.target_star == 2
        assert config.shards_required == 50
        assert config.same_star_heroes == 3
        assert config.hero_star_required == 1
    
    def test_compose_three_star_config(self):
        """测试3星合成配置"""
        config = ShardComposition.get_for_star(3)
        
        assert config.target_star == 3
        assert config.shards_required == 100
        assert config.same_star_heroes == 3
        assert config.hero_star_required == 2
    
    def test_can_compose_one_star(self):
        """测试检查是否可以合成1星"""
        config = ShardComposition.get_for_star(1)
        
        # 碎片足够，无英雄要求
        assert config.can_compose(100, 0) == True
        assert config.can_compose(99, 0) == False
    
    def test_can_compose_two_star(self):
        """测试检查是否可以合成2星"""
        config = ShardComposition.get_for_star(2)
        
        # 碎片足够，英雄数量足够
        assert config.can_compose(50, 3) == True
        # 碎片不足
        assert config.can_compose(49, 3) == False
        # 英雄数量不足
        assert config.can_compose(50, 2) == False


class TestShardsBackpack:
    """测试碎片背包"""
    
    def test_backpack_creation(self):
        """测试背包创建"""
        backpack = ShardsBackpack(player_id="player_001")
        
        assert backpack.player_id == "player_001"
        assert len(backpack.shards) == 0
        assert backpack.total_shards == 0
    
    def test_backpack_add_shards(self):
        """测试背包增加碎片"""
        backpack = ShardsBackpack(player_id="player_001")
        
        backpack.add_shards(
            hero_id="hero_001",
            hero_name="亚瑟",
            amount=50,
            source=ShardSource.MATCH_REWARD,
            hero_cost=2,
        )
        
        assert backpack.total_shards == 50
        assert "hero_001" in backpack.shards
        assert backpack.shards["hero_001"].quantity == 50
    
    def test_backpack_add_shards_twice(self):
        """测试背包多次增加同一英雄碎片"""
        backpack = ShardsBackpack(player_id="player_001")
        
        backpack.add_shards("hero_001", "亚瑟", 50, ShardSource.MATCH_REWARD, 2)
        backpack.add_shards("hero_001", "亚瑟", 30, ShardSource.DAILY_TASK, 2)
        
        assert backpack.total_shards == 80
        assert backpack.shards["hero_001"].quantity == 80
        assert backpack.shards["hero_001"].acquired_sources["match_reward"] == 50
        assert backpack.shards["hero_001"].acquired_sources["daily_task"] == 30
    
    def test_backpack_remove_shards(self):
        """测试背包减少碎片"""
        backpack = ShardsBackpack(player_id="player_001")
        backpack.add_shards("hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        
        result = backpack.remove_shards("hero_001", 30)
        
        assert result == True
        assert backpack.total_shards == 70
        assert backpack.shards["hero_001"].quantity == 70
    
    def test_backpack_remove_shards_insufficient(self):
        """测试背包减少碎片（数量不足）"""
        backpack = ShardsBackpack(player_id="player_001")
        backpack.add_shards("hero_001", "亚瑟", 50, ShardSource.MATCH_REWARD, 2)
        
        result = backpack.remove_shards("hero_001", 100)
        
        assert result == False
        assert backpack.total_shards == 50
    
    def test_backpack_get_composable_heroes(self):
        """测试获取可合成英雄列表"""
        backpack = ShardsBackpack(player_id="player_001")
        backpack.add_shards("hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        backpack.add_shards("hero_002", "妲己", 50, ShardSource.MATCH_REWARD, 3)
        backpack.add_shards("hero_003", "后羿", 150, ShardSource.MATCH_REWARD, 4)
        
        composable = backpack.get_composable_heroes()
        
        # 只有碎片>=100的可以合成
        assert len(composable) == 2
        hero_ids = [h["hero_id"] for h in composable]
        assert "hero_001" in hero_ids
        assert "hero_003" in hero_ids
        assert "hero_002" not in hero_ids


class TestHeroShardManager:
    """测试碎片管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建碎片管理器"""
        return HeroShardManager()
    
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert len(manager.player_backpacks) == 0
        assert len(manager.player_heroes) == 0
    
    def test_get_or_create_backpack(self, manager):
        """测试获取或创建背包"""
        backpack1 = manager.get_or_create_backpack("player_001")
        assert backpack1.player_id == "player_001"
        
        # 再次获取应该是同一个对象
        backpack2 = manager.get_or_create_backpack("player_001")
        assert backpack1 is backpack2
    
    def test_get_shard_quantity(self, manager):
        """测试获取碎片数量"""
        manager.add_shards("player_001", "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        
        quantity = manager.get_shard_quantity("player_001", "hero_001")
        assert quantity == 100
        
        # 不存在的英雄
        quantity = manager.get_shard_quantity("player_001", "hero_999")
        assert quantity == 0
    
    def test_add_shards(self, manager):
        """测试增加碎片"""
        manager.add_shards("player_001", "hero_001", "亚瑟", 50, ShardSource.MATCH_REWARD, 2)
        
        backpack = manager.get_or_create_backpack("player_001")
        assert backpack.total_shards == 50
        assert backpack.shards["hero_001"].quantity == 50
    
    def test_compose_one_star_success(self, manager):
        """测试合成1星英雄成功"""
        player_id = "player_001"
        hero_id = "hero_001"
        hero_name = "亚瑟"
        
        # 添加100碎片
        manager.add_shards(player_id, hero_id, hero_name, 100, ShardSource.MATCH_REWARD, 2)
        
        # 合成1星
        result = manager.compose_hero(player_id, hero_id, target_star=1, hero_name=hero_name)
        
        assert result.success == True
        assert result.hero_id == hero_id
        assert result.star_level == 1
        assert result.shards_used == 100
        assert result.heroes_used == 0
    
    def test_compose_one_star_insufficient_shards(self, manager):
        """测试合成1星英雄碎片不足"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 只添加50碎片
        manager.add_shards(player_id, hero_id, "亚瑟", 50, ShardSource.MATCH_REWARD, 2)
        
        # 合成1星
        result = manager.compose_hero(player_id, hero_id, target_star=1)
        
        assert result.success == False
        assert "碎片不足" in result.error_message
    
    def test_compose_two_star_success(self, manager):
        """测试合成2星英雄成功"""
        player_id = "player_001"
        hero_id = "hero_001"
        hero_name = "亚瑟"
        
        # 添加50碎片
        manager.add_shards(player_id, hero_id, hero_name, 50, ShardSource.MATCH_REWARD, 2)
        
        # 添加3个1星英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 1},
            {"hero_id": hero_id, "star": 1},
            {"hero_id": hero_id, "star": 1},
        ])
        
        # 合成2星
        result = manager.compose_hero(player_id, hero_id, target_star=2, hero_name=hero_name)
        
        assert result.success == True
        assert result.star_level == 2
        assert result.shards_used == 50
        assert result.heroes_used == 3
    
    def test_compose_two_star_insufficient_heroes(self, manager):
        """测试合成2星英雄数量不足"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 添加50碎片
        manager.add_shards(player_id, hero_id, "亚瑟", 50, ShardSource.MATCH_REWARD, 2)
        
        # 只添加2个1星英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 1},
            {"hero_id": hero_id, "star": 1},
        ])
        
        # 合成2星
        result = manager.compose_hero(player_id, hero_id, target_star=2)
        
        assert result.success == False
        assert "英雄数量不足" in result.error_message
    
    def test_decompose_one_star(self, manager):
        """测试分解1星英雄"""
        player_id = "player_001"
        hero_id = "hero_001"
        hero_name = "亚瑟"
        
        # 添加1星英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 1},
        ])
        
        # 分解
        result = manager.decompose_hero(player_id, hero_id, star_level=1, hero_name=hero_name, hero_cost=2)
        
        assert result.success == True
        assert result.shards_gained == 30
        
        # 检查碎片增加
        assert manager.get_shard_quantity(player_id, hero_id) == 30
    
    def test_decompose_two_star(self, manager):
        """测试分解2星英雄"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 添加2星英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 2},
        ])
        
        # 分解
        result = manager.decompose_hero(player_id, hero_id, star_level=2, hero_cost=2)
        
        assert result.success == True
        assert result.shards_gained == 120
    
    def test_decompose_three_star(self, manager):
        """测试分解3星英雄"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 添加3星英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 3},
        ])
        
        # 分解
        result = manager.decompose_hero(player_id, hero_id, star_level=3, hero_cost=2)
        
        assert result.success == True
        assert result.shards_gained == 420
    
    def test_decompose_insufficient_heroes(self, manager):
        """测试分解英雄数量不足"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 没有英雄
        manager.set_player_heroes(player_id, [])
        
        # 分解
        result = manager.decompose_hero(player_id, hero_id, star_level=1, hero_cost=2)
        
        assert result.success == False
        assert "没有" in result.error_message
    
    def test_batch_compose(self, manager):
        """测试批量合成"""
        player_id = "player_001"
        
        # 添加碎片
        manager.add_shards(player_id, "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        manager.add_shards(player_id, "hero_002", "妲己", 100, ShardSource.MATCH_REWARD, 3)
        manager.add_shards(player_id, "hero_003", "后羿", 50, ShardSource.MATCH_REWARD, 4)  # 不够
        
        # 批量合成
        compose_list = [
            {"hero_id": "hero_001", "hero_name": "亚瑟", "target_star": 1},
            {"hero_id": "hero_002", "hero_name": "妲己", "target_star": 1},
            {"hero_id": "hero_003", "hero_name": "后羿", "target_star": 1},  # 失败
        ]
        
        result = manager.batch_compose(player_id, compose_list)
        
        assert result.success_count == 2
        assert result.fail_count == 1
        assert result.total_shards_used == 200
    
    def test_batch_decompose(self, manager):
        """测试批量分解"""
        player_id = "player_001"
        
        # 添加英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": "hero_001", "star": 1},
            {"hero_id": "hero_002", "star": 1},
        ])
        
        # 批量分解
        decompose_list = [
            {"hero_id": "hero_001", "hero_name": "亚瑟", "star_level": 1, "hero_cost": 2},
            {"hero_id": "hero_002", "hero_name": "妲己", "star_level": 1, "hero_cost": 3},
        ]
        
        result = manager.batch_decompose(player_id, decompose_list)
        
        assert result.success_count == 2
        assert result.fail_count == 0
        assert result.total_shards_gained == 60  # 30 + 30
    
    def test_one_key_compose_all(self, manager):
        """测试一键合成"""
        player_id = "player_001"
        
        # 添加碎片
        manager.add_shards(player_id, "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        manager.add_shards(player_id, "hero_002", "妲己", 150, ShardSource.MATCH_REWARD, 3)
        manager.add_shards(player_id, "hero_003", "后羿", 50, ShardSource.MATCH_REWARD, 4)
        
        # 一键合成
        result = manager.one_key_compose_all(player_id)
        
        assert result.success_count == 2  # hero_001 和 hero_002
        assert result.total_shards_used == 200
    
    def test_get_composable_heroes(self, manager):
        """测试获取可合成英雄列表"""
        player_id = "player_001"
        
        # 添加碎片
        manager.add_shards(player_id, "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        manager.add_shards(player_id, "hero_002", "妲己", 50, ShardSource.MATCH_REWARD, 3)
        
        composable = manager.get_composable_heroes(player_id)
        
        assert len(composable) == 1
        assert composable[0]["hero_id"] == "hero_001"
    
    def test_clear_cache(self, manager):
        """测试清除缓存"""
        player_id = "player_001"
        
        # 创建数据
        manager.add_shards(player_id, "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        
        # 清除指定玩家缓存
        manager.clear_cache(player_id)
        
        assert player_id not in manager.player_backpacks
        assert player_id not in manager.player_heroes
    
    def test_clear_all_cache(self, manager):
        """测试清除所有缓存"""
        # 创建数据
        manager.add_shards("player_001", "hero_001", "亚瑟", 100, ShardSource.MATCH_REWARD, 2)
        manager.add_shards("player_002", "hero_002", "妲己", 100, ShardSource.MATCH_REWARD, 3)
        
        # 清除所有缓存
        manager.clear_cache()
        
        assert len(manager.player_backpacks) == 0
        assert len(manager.player_heroes) == 0


class TestCompositionConfig:
    """测试合成配置"""
    
    def test_shard_composition_config_exists(self):
        """测试合成配置存在"""
        assert 1 in SHARD_COMPOSITION_CONFIG
        assert 2 in SHARD_COMPOSITION_CONFIG
        assert 3 in SHARD_COMPOSITION_CONFIG
    
    def test_shard_composition_config_values(self):
        """测试合成配置值"""
        # 1星: 100碎片
        assert SHARD_COMPOSITION_CONFIG[1]["shards_required"] == 100
        assert SHARD_COMPOSITION_CONFIG[1]["same_star_heroes"] == 0
        
        # 2星: 3个1星 + 50碎片
        assert SHARD_COMPOSITION_CONFIG[2]["shards_required"] == 50
        assert SHARD_COMPOSITION_CONFIG[2]["same_star_heroes"] == 3
        assert SHARD_COMPOSITION_CONFIG[2]["hero_star_required"] == 1
        
        # 3星: 3个2星 + 100碎片
        assert SHARD_COMPOSITION_CONFIG[3]["shards_required"] == 100
        assert SHARD_COMPOSITION_CONFIG[3]["same_star_heroes"] == 3
        assert SHARD_COMPOSITION_CONFIG[3]["hero_star_required"] == 2


class TestDecomposeConfig:
    """测试分解配置"""
    
    def test_hero_decompose_config_exists(self):
        """测试分解配置存在"""
        assert 1 in HERO_DECOMPOSE_CONFIG
        assert 2 in HERO_DECOMPOSE_CONFIG
        assert 3 in HERO_DECOMPOSE_CONFIG
    
    def test_hero_decompose_config_values(self):
        """测试分解配置值"""
        assert HERO_DECOMPOSE_CONFIG[1] == 30
        assert HERO_DECOMPOSE_CONFIG[2] == 120
        assert HERO_DECOMPOSE_CONFIG[3] == 420


class TestEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def manager(self):
        """创建碎片管理器"""
        return HeroShardManager()
    
    def test_compose_same_hero_multiple_times(self, manager):
        """测试同一英雄多次合成"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 添加300碎片
        manager.add_shards(player_id, hero_id, "亚瑟", 300, ShardSource.MATCH_REWARD, 2)
        
        # 第一次合成
        result1 = manager.compose_hero(player_id, hero_id, target_star=1)
        assert result1.success == True
        
        # 第二次合成
        result2 = manager.compose_hero(player_id, hero_id, target_star=1)
        assert result2.success == True
        
        # 检查剩余碎片
        assert manager.get_shard_quantity(player_id, hero_id) == 100
    
    def test_decompose_then_compose(self, manager):
        """测试先分解后合成"""
        player_id = "player_001"
        hero_id = "hero_001"
        
        # 添加英雄
        manager.set_player_heroes(player_id, [
            {"hero_id": hero_id, "star": 1},
        ])
        
        # 分解获得30碎片
        result1 = manager.decompose_hero(player_id, hero_id, star_level=1, hero_cost=2)
        assert result1.success == True
        assert result1.shards_gained == 30
        
        # 再添加70碎片，总共100
        manager.add_shards(player_id, hero_id, "亚瑟", 70, ShardSource.MATCH_REWARD, 2)
        
        # 合成1星
        result2 = manager.compose_hero(player_id, hero_id, target_star=1)
        assert result2.success == True
    
    def test_empty_backpack(self, manager):
        """测试空背包"""
        player_id = "player_001"
        
        backpack_info = manager.get_backpack_info(player_id)
        assert backpack_info["total_shards"] == 0
        assert len(backpack_info["shards"]) == 0
    
    def test_compose_nonexistent_hero(self, manager):
        """测试合成不存在的英雄（无碎片）"""
        player_id = "player_001"
        
        result = manager.compose_hero(player_id, "nonexistent_hero", target_star=1)
        
        assert result.success == False
        assert "碎片不足" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
