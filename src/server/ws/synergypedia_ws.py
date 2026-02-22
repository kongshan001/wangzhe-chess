"""
王者之奕 - 羁绊图鉴 WebSocket 处理器

本模块实现羁绊图鉴系统的 WebSocket 消息处理：
- GET_SYNERGY_PEDIA: 获取所有羁绊信息
- SYNERGY_PEDIA_INFO: 获取单个羁绊详情
- SIMULATE_SYNERGY: 羁绊模拟器
- GET_SYNERGY_RECOMMENDATIONS: 获取阵容推荐
- GET_SYNERGY_ACHIEVEMENTS: 获取羁绊成就
"""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING, Any, Optional

from src.shared.protocol import MessageType
from src.shared.protocol.messages import (
    BaseMessage,
    GetSynergypediaMessage,
    SynergyPediaListMessage,
    SynergypediaInfoMessage,
    SynergyPediaDetailMessage,
    SimulateSynergyMessage,
    SynergySimulationResultMessage,
    GetSynergyRecommendationsMessage,
    SynergyRecommendationsResultMessage,
    GetSynergyAchievementsMessage,
    SynergyAchievementsResultMessage,
    SynergyAchievementUnlockedMessage,
    SynergyPediaEntryData,
    SynergyAchievementData,
)
from src.server.synergypedia import (
    SynergypediaManager,
    synergypedia_manager,
)
from src.shared.models import SynergyType

if TYPE_CHECKING:
    from src.server.ws.handler import Session

logger = structlog.get_logger()


class SynergypediaWSHandler:
    """
    羁绊图鉴 WebSocket 处理器
    
    处理羁绊图鉴相关的 WebSocket 消息。
    
    Attributes:
        manager: 羁绊图鉴管理器
    """
    
    def __init__(
        self,
        manager: Optional[SynergypediaManager] = None,
    ) -> None:
        """
        初始化处理器
        
        Args:
            manager: 羁绊图鉴管理器实例
        """
        self.manager = manager or synergypedia_manager
    
    def register_handlers(self, ws_handler: Any) -> None:
        """
        注册消息处理器
        
        Args:
            ws_handler: WebSocket 主处理器
        """
        ws_handler._handlers[MessageType.GET_SYNERGY_PEDIA] = self.handle_get_synergy_pedia
        ws_handler._handlers[MessageType.SYNERGY_PEDIA_INFO] = self.handle_synergy_pedia_info
        ws_handler._handlers[MessageType.SIMULATE_SYNERGY] = self.handle_simulate_synergy
        ws_handler._handlers[MessageType.GET_SYNERGY_RECOMMENDATIONS] = self.handle_get_recommendations
        ws_handler._handlers[MessageType.GET_SYNERGY_ACHIEVEMENTS] = self.handle_get_achievements
    
    async def handle_get_synergy_pedia(
        self,
        session: Session,
        message: GetSynergypediaMessage,
    ) -> SynergyPediaListMessage:
        """
        处理获取羁绊图鉴请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            羁绊图鉴列表响应
        """
        logger.info(
            "获取羁绊图鉴",
            player_id=session.player_id,
        )
        
        # 获取所有羁绊
        all_entries = self.manager.get_all_synergies()
        
        # 分类
        races = []
        professions = []
        
        for entry in all_entries:
            # 获取玩家进度
            progress = self.manager.get_player_progress(
                player_id=session.player_id,
                synergy_name=entry.name,
            )
            
            entry_data = SynergyPediaEntryData(
                name=entry.name,
                synergy_type=entry.synergy_type.value,
                description=entry.description,
                levels=entry.levels,
                related_heroes=entry.related_heroes,
                icon=entry.icon,
                tips=entry.tips,
                progress=progress.to_dict() if progress else None,
            )
            
            if entry.synergy_type == SynergyType.RACE:
                races.append(entry_data)
            else:
                professions.append(entry_data)
        
        return SynergyPediaListMessage(
            races=races,
            professions=professions,
            total_count=len(all_entries),
            seq=message.seq,
        )
    
    async def handle_synergy_pedia_info(
        self,
        session: Session,
        message: SynergypediaInfoMessage,
    ) -> SynergyPediaDetailMessage:
        """
        处理获取单个羁绊详情请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            羁绊详情响应
        """
        synergy_name = message.synergy_name
        
        logger.info(
            "获取羁绊详情",
            player_id=session.player_id,
            synergy=synergy_name,
        )
        
        # 获取羁绊信息
        entry = self.manager.get_synergy_info(synergy_name)
        if entry is None:
            return SynergyPediaDetailMessage(
                entry=SynergyPediaEntryData(
                    name=synergy_name,
                    synergy_type="unknown",
                    description="羁绊不存在",
                    levels=[],
                ),
                seq=message.seq,
            )
        
        # 获取玩家进度
        progress = self.manager.get_player_progress(
            player_id=session.player_id,
            synergy_name=synergy_name,
        )
        
        # 获取相关推荐阵容
        recommendations = self.manager.get_recommended_lineups(
            synergy_name=synergy_name,
            limit=5,
        )
        
        entry_data = SynergyPediaEntryData(
            name=entry.name,
            synergy_type=entry.synergy_type.value,
            description=entry.description,
            levels=entry.levels,
            related_heroes=entry.related_heroes,
            icon=entry.icon,
            tips=entry.tips,
            progress=progress.to_dict() if progress else None,
        )
        
        return SynergyPediaDetailMessage(
            entry=entry_data,
            progress=progress.to_dict() if progress else None,
            recommended_lineups=[r.to_dict() for r in recommendations],
            seq=message.seq,
        )
    
    async def handle_simulate_synergy(
        self,
        session: Session,
        message: SimulateSynergyMessage,
    ) -> SynergySimulationResultMessage:
        """
        处理羁绊模拟器请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            模拟结果响应
        """
        hero_ids = message.hero_ids
        
        logger.info(
            "羁绊模拟",
            player_id=session.player_id,
            hero_count=len(hero_ids),
        )
        
        # 执行模拟
        result = self.manager.simulate_synergies(hero_ids)
        
        return SynergySimulationResultMessage(
            selected_heroes=result.selected_heroes,
            active_synergies=result.active_synergies,
            inactive_synergies=result.inactive_synergies,
            synergy_progress=result.synergy_progress,
            recommendations=result.recommendations,
            total_bonuses=result.total_bonuses,
            seq=message.seq,
        )
    
    async def handle_get_recommendations(
        self,
        session: Session,
        message: GetSynergyRecommendationsMessage,
    ) -> SynergyRecommendationsResultMessage:
        """
        处理获取阵容推荐请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            推荐结果响应
        """
        synergy_name = message.synergy_name
        limit = message.limit
        
        logger.info(
            "获取阵容推荐",
            player_id=session.player_id,
            synergy=synergy_name,
            limit=limit,
        )
        
        # 获取推荐
        recommendations = self.manager.get_recommended_lineups(
            synergy_name=synergy_name,
            limit=limit,
        )
        
        return SynergyRecommendationsResultMessage(
            recommendations=[r.to_dict() for r in recommendations],
            total_count=len(recommendations),
            seq=message.seq,
        )
    
    async def handle_get_achievements(
        self,
        session: Session,
        message: GetSynergyAchievementsMessage,
    ) -> SynergyAchievementsResultMessage:
        """
        处理获取羁绊成就请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            成就列表响应
        """
        synergy_name = message.synergy_name
        
        logger.info(
            "获取羁绊成就",
            player_id=session.player_id,
            synergy=synergy_name,
        )
        
        # 获取成就列表
        achievements = self.manager.get_synergy_achievements(synergy_name)
        
        # 检查并更新解锁状态
        if synergy_name:
            # 单个羁绊
            progress = self.manager.get_player_progress(
                player_id=session.player_id,
                synergy_name=synergy_name,
            )
            if progress:
                for achievement in achievements:
                    achievement.check_unlock(progress)
        else:
            # 所有羁绊
            all_progress = self.manager.get_player_progress(session.player_id)
            for achievement in achievements:
                progress = all_progress.get(achievement.synergy_name)
                if progress:
                    achievement.check_unlock(progress)
        
        # 转换为数据格式
        achievement_data = []
        unlocked_count = 0
        
        for achievement in achievements:
            progress_value = 0
            if synergy_name:
                progress = self.manager.get_player_progress(
                    player_id=session.player_id,
                    synergy_name=achievement.synergy_name,
                )
                if progress:
                    if achievement.requirement_type == "activation_count":
                        progress_value = progress.activation_count
                    elif achievement.requirement_type == "level_reached":
                        progress_value = progress.highest_level_reached
                    elif achievement.requirement_type == "max_heroes":
                        progress_value = progress.max_heroes_used
            
            if achievement.is_unlocked:
                unlocked_count += 1
            
            achievement_data.append(SynergyAchievementData(
                achievement_id=achievement.achievement_id,
                name=achievement.name,
                description=achievement.description,
                synergy_name=achievement.synergy_name,
                requirement_type=achievement.requirement_type,
                requirement_value=achievement.requirement_value,
                reward=achievement.reward,
                is_unlocked=achievement.is_unlocked,
                progress=progress_value,
            ))
        
        return SynergyAchievementsResultMessage(
            achievements=achievement_data,
            total_count=len(achievements),
            unlocked_count=unlocked_count,
            seq=message.seq,
        )
    
    async def notify_achievement_unlocked(
        self,
        player_id: str,
        achievement: Any,
        rewards: dict[str, Any],
    ) -> None:
        """
        通知玩家成就解锁
        
        Args:
            player_id: 玩家ID
            achievement: 解锁的成就
            rewards: 获得的奖励
        """
        # 这个方法需要配合主 WebSocket 处理器使用
        # 用于在游戏过程中通知玩家解锁了成就
        logger.info(
            "羁绊成就解锁通知",
            player_id=player_id,
            achievement=achievement.name,
        )


# ============================================================================
# 全局实例
# ============================================================================

synergypedia_ws_handler = SynergypediaWSHandler()
