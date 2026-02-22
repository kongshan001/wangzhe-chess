"""
王者之奕 - 英雄碎片系统数据模型

本模块定义英雄碎片系统的数据类：
- HeroShard: 英雄碎片数据类
- ShardComposition: 碎片合成配置数据类
- ShardsBackpack: 玩家碎片背包数据类
- ShardSource: 碎片来源枚举

用于英雄碎片系统的数据处理和传输。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ShardSource(str, Enum):
    """碎片来源枚举"""
    MATCH_REWARD = "match_reward"      # 对局奖励
    DAILY_TASK = "daily_task"          # 每日任务
    SHOP_PURCHASE = "shop_purchase"    # 商店购买
    HERO_DECOMPOSE = "hero_decompose"  # 分解英雄
    CHECKIN_REWARD = "checkin_reward"  # 签到奖励
    EVENT_REWARD = "event_reward"      # 活动奖励
    SYSTEM_GRANT = "system_grant"      # 系统赠送
    EXCHANGE = "exchange"              # 交易获得


class StarLevel(int, Enum):
    """英雄星级枚举"""
    ONE = 1
    TWO = 2
    THREE = 3


# 合成配置常量
# 100碎片 = 1星英雄
# 3个1星 + 50碎片 = 2星英雄
# 3个2星 + 100碎片 = 3星英雄
SHARD_COMPOSITION_CONFIG = {
    1: {  # 合成1星
        "shards_required": 100,
        "same_star_heroes": 0,
    },
    2: {  # 合成2星
        "shards_required": 50,
        "same_star_heroes": 3,
        "hero_star_required": 1,
    },
    3: {  # 合成3星
        "shards_required": 100,
        "same_star_heroes": 3,
        "hero_star_required": 2,
    },
}

# 分解配置常量
# 1星英雄 -> 30碎片
# 2星英雄 -> 120碎片 (3*30 + 50*0.6)
# 3星英雄 -> 420碎片 (3*120 + 100*0.6)
HERO_DECOMPOSE_CONFIG = {
    1: 30,
    2: 120,
    3: 420,
}


@dataclass
class HeroShard:
    """
    英雄碎片数据类
    
    存储单个英雄碎片的数量和来源信息。
    
    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        quantity: 碎片数量
        max_quantity: 可持有最大数量（0表示无限制）
        acquired_sources: 各来源获得的碎片数量
        last_acquired_at: 最后获得时间
        hero_cost: 英雄费用（1-5）
    """
    
    hero_id: str
    hero_name: str = ""
    quantity: int = 0
    max_quantity: int = 0
    acquired_sources: Dict[str, int] = field(default_factory=dict)
    last_acquired_at: Optional[datetime] = None
    hero_cost: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hero_id": self.hero_id,
            "hero_name": self.hero_name,
            "quantity": self.quantity,
            "max_quantity": self.max_quantity,
            "acquired_sources": self.acquired_sources,
            "last_acquired_at": self.last_acquired_at.isoformat() if self.last_acquired_at else None,
            "hero_cost": self.hero_cost,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeroShard":
        """从字典创建"""
        return cls(
            hero_id=data["hero_id"],
            hero_name=data.get("hero_name", ""),
            quantity=data.get("quantity", 0),
            max_quantity=data.get("max_quantity", 0),
            acquired_sources=data.get("acquired_sources", {}),
            last_acquired_at=datetime.fromisoformat(data["last_acquired_at"]) if data.get("last_acquired_at") else None,
            hero_cost=data.get("hero_cost", 1),
        )
    
    def add_shards(self, amount: int, source: ShardSource) -> None:
        """
        增加碎片数量
        
        Args:
            amount: 增加数量
            source: 来源
        """
        self.quantity += amount
        source_key = source.value if isinstance(source, ShardSource) else source
        self.acquired_sources[source_key] = self.acquired_sources.get(source_key, 0) + amount
        self.last_acquired_at = datetime.now()
    
    def remove_shards(self, amount: int) -> bool:
        """
        减少碎片数量
        
        Args:
            amount: 减少数量
            
        Returns:
            是否成功
        """
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True


@dataclass
class ShardComposition:
    """
    碎片合成配置数据类
    
    存储合成某一星级英雄所需的配置。
    
    Attributes:
        target_star: 目标星级
        shards_required: 需要的碎片数量
        same_star_heroes: 需要的同星级英雄数量
        hero_star_required: 需要的英雄星级（合成更高星级时）
    """
    
    target_star: int
    shards_required: int = 100
    same_star_heroes: int = 0
    hero_star_required: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target_star": self.target_star,
            "shards_required": self.shards_required,
            "same_star_heroes": self.same_star_heroes,
            "hero_star_required": self.hero_star_required,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShardComposition":
        """从字典创建"""
        return cls(
            target_star=data["target_star"],
            shards_required=data.get("shards_required", 100),
            same_star_heroes=data.get("same_star_heroes", 0),
            hero_star_required=data.get("hero_star_required", 1),
        )
    
    @classmethod
    def get_for_star(cls, star_level: int) -> "ShardComposition":
        """
        获取指定星级的合成配置
        
        Args:
            star_level: 星级
            
        Returns:
            合成配置
        """
        config = SHARD_COMPOSITION_CONFIG.get(star_level, SHARD_COMPOSITION_CONFIG[1])
        return cls(
            target_star=star_level,
            shards_required=config["shards_required"],
            same_star_heroes=config.get("same_star_heroes", 0),
            hero_star_required=config.get("hero_star_required", 1),
        )
    
    def can_compose(self, shards: int, hero_count: int) -> bool:
        """
        检查是否可以合成
        
        Args:
            shards: 当前碎片数量
            hero_count: 当前同星级英雄数量
            
        Returns:
            是否可以合成
        """
        return shards >= self.shards_required and hero_count >= self.same_star_heroes


@dataclass
class HeroComposeResult:
    """
    英雄合成结果数据类
    
    Attributes:
        success: 是否成功
        hero_id: 英雄ID
        hero_name: 英雄名称
        star_level: 星级
        shards_used: 消耗的碎片数
        heroes_used: 消耗的英雄数量
        error_message: 错误信息
    """
    
    success: bool
    hero_id: str
    hero_name: str = ""
    star_level: int = 1
    shards_used: int = 0
    heroes_used: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "hero_id": self.hero_id,
            "hero_name": self.hero_name,
            "star_level": self.star_level,
            "shards_used": self.shards_used,
            "heroes_used": self.heroes_used,
            "error_message": self.error_message,
        }


@dataclass
class HeroDecomposeResult:
    """
    英雄分解结果数据类
    
    Attributes:
        success: 是否成功
        hero_id: 英雄ID
        hero_name: 英雄名称
        star_level: 星级
        shards_gained: 获得的碎片数
        error_message: 错误信息
    """
    
    success: bool
    hero_id: str
    hero_name: str = ""
    star_level: int = 1
    shards_gained: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "hero_id": self.hero_id,
            "hero_name": self.hero_name,
            "star_level": self.star_level,
            "shards_gained": self.shards_gained,
            "error_message": self.error_message,
        }


@dataclass
class ShardsBackpack:
    """
    玩家碎片背包数据类
    
    存储玩家的所有碎片信息。
    
    Attributes:
        player_id: 玩家ID
        shards: 英雄碎片字典 (hero_id -> HeroShard)
        total_shards: 总碎片数量（所有英雄）
        last_updated: 最后更新时间
    """
    
    player_id: str
    shards: Dict[str, HeroShard] = field(default_factory=dict)
    total_shards: int = 0
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "shards": {k: v.to_dict() for k, v in self.shards.items()},
            "total_shards": self.total_shards,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShardsBackpack":
        """从字典创建"""
        shards = {}
        for hero_id, shard_data in data.get("shards", {}).items():
            shards[hero_id] = HeroShard.from_dict(shard_data)
        
        return cls(
            player_id=data["player_id"],
            shards=shards,
            total_shards=data.get("total_shards", 0),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
        )
    
    def get_shard(self, hero_id: str) -> Optional[HeroShard]:
        """
        获取指定英雄的碎片
        
        Args:
            hero_id: 英雄ID
            
        Returns:
            碎片数据，如果不存在返回 None
        """
        return self.shards.get(hero_id)
    
    def get_shard_quantity(self, hero_id: str) -> int:
        """
        获取指定英雄的碎片数量
        
        Args:
            hero_id: 英雄ID
            
        Returns:
            碎片数量
        """
        shard = self.shards.get(hero_id)
        return shard.quantity if shard else 0
    
    def add_shards(
        self,
        hero_id: str,
        hero_name: str,
        amount: int,
        source: ShardSource,
        hero_cost: int = 1,
    ) -> None:
        """
        增加碎片
        
        Args:
            hero_id: 英雄ID
            hero_name: 英雄名称
            amount: 数量
            source: 来源
            hero_cost: 英雄费用
        """
        if hero_id not in self.shards:
            self.shards[hero_id] = HeroShard(
                hero_id=hero_id,
                hero_name=hero_name,
                hero_cost=hero_cost,
            )
        
        self.shards[hero_id].add_shards(amount, source)
        self.total_shards += amount
        self.last_updated = datetime.now()
    
    def remove_shards(self, hero_id: str, amount: int) -> bool:
        """
        减少碎片
        
        Args:
            hero_id: 英雄ID
            amount: 数量
            
        Returns:
            是否成功
        """
        shard = self.shards.get(hero_id)
        if not shard or shard.quantity < amount:
            return False
        
        shard.remove_shards(amount)
        self.total_shards -= amount
        self.last_updated = datetime.now()
        return True
    
    def get_composable_heroes(self) -> List[Dict[str, Any]]:
        """
        获取可以合成的英雄列表
        
        Returns:
            可合成英雄列表
        """
        result = []
        for hero_id, shard in self.shards.items():
            # 检查是否可以合成1星
            if shard.quantity >= 100:
                result.append({
                    "hero_id": hero_id,
                    "hero_name": shard.hero_name,
                    "shard_quantity": shard.quantity,
                    "composable_star": 1,
                    "can_compose": True,
                })
        return result
    
    def get_all_shards_list(self) -> List[HeroShard]:
        """
        获取所有碎片列表
        
        Returns:
            碎片列表
        """
        return list(self.shards.values())


@dataclass
class BatchComposeResult:
    """
    批量合成结果数据类
    
    Attributes:
        success_count: 成功数量
        fail_count: 失败数量
        total_shards_used: 总消耗碎片
        results: 每个英雄的合成结果
    """
    
    success_count: int = 0
    fail_count: int = 0
    total_shards_used: int = 0
    results: List[HeroComposeResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "total_shards_used": self.total_shards_used,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class BatchDecomposeResult:
    """
    批量分解结果数据类
    
    Attributes:
        success_count: 成功数量
        fail_count: 失败数量
        total_shards_gained: 总获得碎片
        results: 每个英雄的分解结果
    """
    
    success_count: int = 0
    fail_count: int = 0
    total_shards_gained: int = 0
    results: List[HeroDecomposeResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "total_shards_gained": self.total_shards_gained,
            "results": [r.to_dict() for r in self.results],
        }
