"""
王者之奕 - 英雄碎片系统 WebSocket 处理器

本模块实现英雄碎片系统的 WebSocket 消息处理：
- 获取碎片背包
- 合成英雄
- 分解英雄
- 批量合成/分解
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.shared.protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
)
from src.shared.protocol.messages import (
    BatchComposeMessage,
    BatchComposeResultMessage,
    BatchDecomposeMessage,
    BatchDecomposeResultMessage,
    CanComposeNotifyMessage,
    ComposeHeroMessage,
    ComposeRequirementsMessage,
    DecomposeHeroMessage,
    DecomposeRewardsMessage,
    GetComposeRequirementsMessage,
    GetDecomposeRewardsMessage,
    GetShardBackpackMessage,
    HeroComposedMessage,
    HeroDecomposedMessage,
    HeroShardData,
    OneKeyComposeMessage,
    ShardBackpackMessage,
    ShardUpdatedMessage,
)
from .manager import HeroShardManager, get_hero_shard_manager
from .models import ShardSource

if TYPE_CHECKING:
    from src.server.ws.handler import Session

import structlog

logger = structlog.get_logger()


class HeroShardWSHandler:
    """
    英雄碎片系统 WebSocket 处理器
    
    处理所有碎片相关的 WebSocket 消息。
    
    Attributes:
        shard_manager: 碎片管理器
    """
    
    def __init__(self, shard_manager: Optional[HeroShardManager] = None):
        """
        初始化碎片 WebSocket 处理器
        
        Args:
            shard_manager: 碎片管理器（可选，默认使用全局单例）
        """
        self.shard_manager = shard_manager or get_hero_shard_manager()
    
    async def handle_get_shard_backpack(
        self,
        session: Session,
        message: GetShardBackpackMessage,
    ) -> ShardBackpackMessage:
        """
        处理获取碎片背包请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            碎片背包响应
        """
        player_id = session.player_id
        
        # 获取背包信息
        backpack_info = self.shard_manager.get_backpack_info(player_id)
        
        # 转换为 HeroShardData 列表
        shards_data = []
        for shard_data in backpack_info.get("shards", []):
            shard = HeroShardData(
                hero_id=shard_data["hero_id"],
                hero_name=shard_data.get("hero_name", ""),
                quantity=shard_data.get("quantity", 0),
                hero_cost=shard_data.get("hero_cost", 1),
                last_acquired_at=shard_data.get("last_acquired_at"),
                can_compose=shard_data.get("quantity", 0) >= 100,
            )
            shards_data.append(shard)
        
        # 筛选特定英雄
        if message.hero_id:
            shards_data = [s for s in shards_data if s.hero_id == message.hero_id]
        
        return ShardBackpackMessage(
            shards=shards_data,
            total_shards=backpack_info.get("total_shards", 0),
            total_heroes=len(shards_data),
            seq=message.seq,
        )
    
    async def handle_compose_hero(
        self,
        session: Session,
        message: ComposeHeroMessage,
    ) -> BaseMessage:
        """
        处理合成英雄请求
        
        合成规则：
        - 100碎片 = 1星英雄
        - 3个1星 + 50碎片 = 2星英雄
        - 3个2星 + 100碎片 = 3星英雄
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            合成结果响应或错误消息
        """
        player_id = session.player_id
        hero_id = message.hero_id
        target_star = message.target_star
        hero_name = message.hero_name
        
        # 执行合成
        result = self.shard_manager.compose_hero(
            player_id=player_id,
            hero_id=hero_id,
            target_star=target_star,
            hero_name=hero_name,
        )
        
        if not result.success:
            return ErrorMessage(
                code=5001,
                message=result.error_message or "合成失败",
                seq=message.seq,
            )
        
        logger.info(
            "Hero composed",
            player_id=player_id,
            hero_id=hero_id,
            star_level=target_star,
            shards_used=result.shards_used,
        )
        
        return HeroComposedMessage(
            hero_id=hero_id,
            hero_name=hero_name,
            star_level=target_star,
            shards_used=result.shards_used,
            heroes_used=result.heroes_used,
            success=True,
            seq=message.seq,
        )
    
    async def handle_decompose_hero(
        self,
        session: Session,
        message: DecomposeHeroMessage,
    ) -> BaseMessage:
        """
        处理分解英雄请求
        
        分解规则：
        - 1星英雄 -> 30碎片
        - 2星英雄 -> 120碎片
        - 3星英雄 -> 420碎片
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            分解结果响应或错误消息
        """
        player_id = session.player_id
        hero_id = message.hero_id
        star_level = message.star_level
        hero_name = message.hero_name
        hero_cost = message.hero_cost
        
        # 执行分解
        result = self.shard_manager.decompose_hero(
            player_id=player_id,
            hero_id=hero_id,
            star_level=star_level,
            hero_name=hero_name,
            hero_cost=hero_cost,
        )
        
        if not result.success:
            return ErrorMessage(
                code=5002,
                message=result.error_message or "分解失败",
                seq=message.seq,
            )
        
        logger.info(
            "Hero decomposed",
            player_id=player_id,
            hero_id=hero_id,
            star_level=star_level,
            shards_gained=result.shards_gained,
        )
        
        return HeroDecomposedMessage(
            hero_id=hero_id,
            hero_name=hero_name,
            star_level=star_level,
            shards_gained=result.shards_gained,
            success=True,
            seq=message.seq,
        )
    
    async def handle_batch_compose(
        self,
        session: Session,
        message: BatchComposeMessage,
    ) -> BatchComposeResultMessage:
        """
        处理批量合成请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            批量合成结果响应
        """
        player_id = session.player_id
        compose_list = message.compose_list
        
        # 执行批量合成
        result = self.shard_manager.batch_compose(player_id, compose_list)
        
        logger.info(
            "Batch compose",
            player_id=player_id,
            success_count=result.success_count,
            fail_count=result.fail_count,
        )
        
        return BatchComposeResultMessage(
            success_count=result.success_count,
            fail_count=result.fail_count,
            total_shards_used=result.total_shards_used,
            results=[r.to_dict() for r in result.results],
            seq=message.seq,
        )
    
    async def handle_batch_decompose(
        self,
        session: Session,
        message: BatchDecomposeMessage,
    ) -> BatchDecomposeResultMessage:
        """
        处理批量分解请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            批量分解结果响应
        """
        player_id = session.player_id
        decompose_list = message.decompose_list
        
        # 执行批量分解
        result = self.shard_manager.batch_decompose(player_id, decompose_list)
        
        logger.info(
            "Batch decompose",
            player_id=player_id,
            success_count=result.success_count,
            fail_count=result.fail_count,
        )
        
        return BatchDecomposeResultMessage(
            success_count=result.success_count,
            fail_count=result.fail_count,
            total_shards_gained=result.total_shards_gained,
            results=[r.to_dict() for r in result.results],
            seq=message.seq,
        )
    
    async def handle_one_key_compose(
        self,
        session: Session,
        message: OneKeyComposeMessage,
    ) -> BatchComposeResultMessage:
        """
        处理一键合成请求（合成所有可合成的1星英雄）
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            批量合成结果响应
        """
        player_id = session.player_id
        
        # 执行一键合成
        result = self.shard_manager.one_key_compose_all(player_id)
        
        logger.info(
            "One key compose",
            player_id=player_id,
            success_count=result.success_count,
            fail_count=result.fail_count,
        )
        
        return BatchComposeResultMessage(
            success_count=result.success_count,
            fail_count=result.fail_count,
            total_shards_used=result.total_shards_used,
            results=[r.to_dict() for r in result.results],
            seq=message.seq,
        )
    
    async def handle_get_compose_requirements(
        self,
        session: Session,
        message: GetComposeRequirementsMessage,
    ) -> ComposeRequirementsMessage:
        """
        处理获取合成要求请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            合成要求响应
        """
        target_star = message.target_star
        
        # 获取合成要求
        requirements = self.shard_manager.get_composition_requirements(target_star)
        
        return ComposeRequirementsMessage(
            target_star=requirements["target_star"],
            shards_required=requirements["shards_required"],
            same_star_heroes=requirements.get("same_star_heroes", 0),
            hero_star_required=requirements.get("hero_star_required", 1),
            seq=message.seq,
        )
    
    async def handle_get_decompose_rewards(
        self,
        session: Session,
        message: GetDecomposeRewardsMessage,
    ) -> DecomposeRewardsMessage:
        """
        处理获取分解奖励请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            分解奖励响应
        """
        star_level = message.star_level
        
        # 获取分解奖励
        rewards = self.shard_manager.get_decompose_rewards(star_level)
        
        return DecomposeRewardsMessage(
            star_level=rewards["star_level"],
            shards_gained=rewards["shards_gained"],
            seq=message.seq,
        )


def register_hero_shard_handlers(ws_handler: Any) -> None:
    """
    注册英雄碎片系统的 WebSocket 处理器
    
    Args:
        ws_handler: WebSocket 处理器实例
    """
    shard_handler = HeroShardWSHandler()
    
    @ws_handler.on_message(MessageType.GET_SHARD_BACKPACK)
    async def handle_get_shard_backpack(session: Session, message: GetShardBackpackMessage):
        return await shard_handler.handle_get_shard_backpack(session, message)
    
    @ws_handler.on_message(MessageType.COMPOSE_HERO)
    async def handle_compose_hero(session: Session, message: ComposeHeroMessage):
        return await shard_handler.handle_compose_hero(session, message)
    
    @ws_handler.on_message(MessageType.DECOMPOSE_HERO)
    async def handle_decompose_hero(session: Session, message: DecomposeHeroMessage):
        return await shard_handler.handle_decompose_hero(session, message)
    
    @ws_handler.on_message(MessageType.BATCH_COMPOSE)
    async def handle_batch_compose(session: Session, message: BatchComposeMessage):
        return await shard_handler.handle_batch_compose(session, message)
    
    @ws_handler.on_message(MessageType.BATCH_DECOMPOSE)
    async def handle_batch_decompose(session: Session, message: BatchDecomposeMessage):
        return await shard_handler.handle_batch_decompose(session, message)
    
    @ws_handler.on_message(MessageType.ONE_KEY_COMPOSE)
    async def handle_one_key_compose(session: Session, message: OneKeyComposeMessage):
        return await shard_handler.handle_one_key_compose(session, message)
    
    @ws_handler.on_message(MessageType.GET_COMPOSE_REQUIREMENTS)
    async def handle_get_compose_requirements(session: Session, message: GetComposeRequirementsMessage):
        return await shard_handler.handle_get_compose_requirements(session, message)
    
    @ws_handler.on_message(MessageType.GET_DECOMPOSE_REWARDS)
    async def handle_get_decompose_rewards(session: Session, message: GetDecomposeRewardsMessage):
        return await shard_handler.handle_get_decompose_rewards(session, message)
    
    logger.info("Hero shard WebSocket handlers registered")
