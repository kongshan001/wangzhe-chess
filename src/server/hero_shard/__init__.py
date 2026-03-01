"""
王者之奕 - 英雄碎片系统

本模块提供英雄碎片系统的完整功能：
- 碎片获取和管理
- 英雄合成（100碎片=1星，3个1星+50碎片=2星等）
- 英雄分解获得碎片
- 批量合成/分解
- 碎片背包管理

主要导出：
- HeroShardManager: 碎片管理器
- get_hero_shard_manager: 获取管理器单例
- 数据模型: HeroShard, ShardComposition, ShardsBackpack 等
"""

from .manager import (
    HeroShardManager,
    get_hero_shard_manager,
)
from .models import (
    HERO_DECOMPOSE_CONFIG,
    SHARD_COMPOSITION_CONFIG,
    BatchComposeResult,
    BatchDecomposeResult,
    HeroComposeResult,
    HeroDecomposeResult,
    HeroShard,
    ShardComposition,
    ShardsBackpack,
    ShardSource,
    StarLevel,
)

__all__ = [
    # 管理器
    "HeroShardManager",
    "get_hero_shard_manager",
    # 数据模型
    "HeroShard",
    "ShardComposition",
    "ShardsBackpack",
    "ShardSource",
    "StarLevel",
    "HeroComposeResult",
    "HeroDecomposeResult",
    "BatchComposeResult",
    "BatchDecomposeResult",
    # 配置常量
    "HERO_DECOMPOSE_CONFIG",
    "SHARD_COMPOSITION_CONFIG",
]
