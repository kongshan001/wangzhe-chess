"""
王者之奕 - 排行榜 WebSocket 处理器

本模块提供排行榜相关的 WebSocket 消息处理：
- 获取排行榜
- 获取玩家排名
- 获取排行榜列表
- 领取排行榜奖励

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..leaderboard import (
    LeaderboardManager,
    LeaderboardType,
    LeaderboardPeriod,
    get_leaderboard_manager,
)
from ...shared.protocol import (
    BaseMessage,
    ClaimLeaderboardRewardMessage,
    ErrorMessage,
    GetLeaderboardMessage,
    GetPlayerRankMessage,
    LeaderboardDataMessage,
    LeaderboardEntryData,
    LeaderboardListMessage,
    LeaderboardListResultMessage,
    LeaderboardOverviewData,
    LeaderboardRewardClaimedMessage,
    LeaderboardRewardData,
    PlayerRankInfoData,
    PlayerRankInfoMessage,
    MessageType,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class LeaderboardWSHandler:
    """
    排行榜 WebSocket 处理器
    
    处理所有排行榜相关的 WebSocket 消息。
    
    使用方式:
        handler = LeaderboardWSHandler()
        
        @ws_handler.on_message(MessageType.GET_LEADERBOARD)
        async def handle_get_leaderboard(session, message):
            return await leaderboard_handler.handle_get_leaderboard(session, message)
    """
    
    def __init__(self) -> None:
        """初始化处理器"""
        self._manager: Optional[LeaderboardManager] = None
    
    @property
    def manager(self) -> LeaderboardManager:
        """获取排行榜管理器"""
        if self._manager is None:
            self._manager = get_leaderboard_manager()
        return self._manager
    
    async def handle_get_leaderboard(
        self,
        session: "Session",
        message: GetLeaderboardMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取排行榜请求
        
        Args:
            session: WebSocket 会话
            message: 获取排行榜消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 解析排行榜类型
            try:
                lb_type = LeaderboardType(message.leaderboard_type)
            except ValueError:
                lb_type = LeaderboardType.TIER
            
            # 解析排行榜周期
            try:
                period = LeaderboardPeriod(message.period)
            except ValueError:
                period = LeaderboardPeriod.WEEKLY
            
            # 获取排行榜数据
            leaderboard_data = self.manager.get_leaderboard(
                leaderboard_type=lb_type,
                period=period,
                page=message.page,
                page_size=message.page_size,
            )
            
            # 转换为消息格式
            entries = [
                LeaderboardEntryData(
                    player_id=entry.player_id,
                    nickname=entry.nickname,
                    avatar=entry.avatar,
                    rank=entry.rank,
                    score=entry.score,
                    tier=entry.tier,
                    stars=entry.stars,
                    display_rank=entry.display_rank,
                    extra_data=entry.extra_data,
                )
                for entry in leaderboard_data.entries
            ]
            
            logger.info(
                "获取排行榜",
                player_id=player_id,
                leaderboard_type=lb_type.value,
                period=period.value,
                page=message.page,
                count=len(entries),
            )
            
            return LeaderboardDataMessage(
                leaderboard_type=leaderboard_data.leaderboard_type.value,
                leaderboard_type_name=leaderboard_data.leaderboard_type.display_name,
                period=leaderboard_data.period.value,
                period_name=leaderboard_data.period.display_name,
                entries=entries,
                total_count=leaderboard_data.total_count,
                page=leaderboard_data.page,
                page_size=leaderboard_data.page_size,
                total_pages=(leaderboard_data.total_count + leaderboard_data.page_size - 1) // leaderboard_data.page_size if leaderboard_data.page_size > 0 else 0,
                updated_at=leaderboard_data.updated_at.isoformat() if leaderboard_data.updated_at else None,
                period_start=leaderboard_data.period_start.isoformat() if leaderboard_data.period_start else None,
                period_end=leaderboard_data.period_end.isoformat() if leaderboard_data.period_end else None,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取排行榜异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4000,
                message="获取排行榜失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_player_rank(
        self,
        session: "Session",
        message: GetPlayerRankMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取玩家排名请求
        
        Args:
            session: WebSocket 会话
            message: 获取玩家排名消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            ranks = []
            
            if message.leaderboard_type and message.period:
                # 获取指定类型和周期的排名
                try:
                    lb_type = LeaderboardType(message.leaderboard_type)
                    period = LeaderboardPeriod(message.period)
                except ValueError:
                    return ErrorMessage(
                        code=4001,
                        message="无效的排行榜类型或周期",
                        seq=message.seq,
                    )
                
                rank_info = self.manager.get_player_rank(player_id, lb_type, period)
                ranks.append(self._rank_info_to_data(rank_info))
            
            else:
                # 获取所有排名
                all_ranks = self.manager.get_player_all_ranks(player_id)
                for rank_info in all_ranks.values():
                    ranks.append(self._rank_info_to_data(rank_info))
            
            logger.info(
                "获取玩家排名",
                player_id=player_id,
                count=len(ranks),
            )
            
            return PlayerRankInfoMessage(
                ranks=ranks,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取玩家排名异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4000,
                message="获取玩家排名失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_leaderboard_list(
        self,
        session: "Session",
        message: LeaderboardListMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取排行榜列表请求
        
        Args:
            session: WebSocket 会话
            message: 获取排行榜列表消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取排行榜列表
            list_data = self.manager.get_leaderboard_list()
            
            # 转换为消息格式
            leaderboards = [
                LeaderboardOverviewData(
                    type=lb["type"],
                    type_name=lb["type_name"],
                    period=lb["period"],
                    period_name=lb["period_name"],
                    total_count=lb["total_count"],
                    top_players=lb["top_players"],
                    updated_at=lb.get("updated_at"),
                )
                for lb in list_data.get("leaderboards", [])
            ]
            
            logger.info(
                "获取排行榜列表",
                player_id=player_id,
                count=len(leaderboards),
            )
            
            return LeaderboardListResultMessage(
                leaderboards=leaderboards,
                page=list_data.get("page", 1),
                page_size=list_data.get("page_size", 20),
                total_count=list_data.get("total_count", 0),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取排行榜列表异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4000,
                message="获取排行榜列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_claim_reward(
        self,
        session: "Session",
        message: ClaimLeaderboardRewardMessage,
    ) -> Optional[BaseMessage]:
        """
        处理领取排行榜奖励请求
        
        Args:
            session: WebSocket 会话
            message: 领取奖励消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 解析排行榜类型
            try:
                lb_type = LeaderboardType(message.leaderboard_type)
            except ValueError:
                return ErrorMessage(
                    code=4001,
                    message="无效的排行榜类型",
                    seq=message.seq,
                )
            
            # 解析排行榜周期
            try:
                period = LeaderboardPeriod(message.period)
            except ValueError:
                return ErrorMessage(
                    code=4001,
                    message="无效的排行榜周期",
                    seq=message.seq,
                )
            
            # 领取奖励
            reward = self.manager.claim_reward(player_id, lb_type, period)
            
            if reward is None:
                # 检查是否已领取
                rank_info = self.manager.get_player_rank(player_id, lb_type, period)
                if rank_info.rewards_claimed:
                    return ErrorMessage(
                        code=4003,
                        message="奖励已领取",
                        seq=message.seq,
                    )
                elif not rank_info.is_ranked:
                    return ErrorMessage(
                        code=4004,
                        message="未上榜，无法领取奖励",
                        seq=message.seq,
                    )
                else:
                    return ErrorMessage(
                        code=4005,
                        message="当前排名无奖励",
                        seq=message.seq,
                    )
            
            # 获取玩家排名
            rank_info = self.manager.get_player_rank(player_id, lb_type, period)
            
            logger.info(
                "领取排行榜奖励",
                player_id=player_id,
                leaderboard_type=lb_type.value,
                period=period.value,
                rank=rank_info.rank,
                gold=reward.gold,
                exp=reward.exp,
            )
            
            return LeaderboardRewardClaimedMessage(
                leaderboard_type=lb_type.value,
                period=period.value,
                rank=rank_info.rank,
                reward=LeaderboardRewardData(
                    gold=reward.gold,
                    exp=reward.exp,
                    title=reward.title,
                    avatar_frame=reward.avatar_frame,
                    items=reward.items,
                ),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "领取排行榜奖励异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4000,
                message="领取奖励失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _rank_info_to_data(self, rank_info: Any) -> PlayerRankInfoData:
        """将排名信息转换为消息数据"""
        return PlayerRankInfoData(
            player_id=rank_info.player_id,
            leaderboard_type=rank_info.leaderboard_type.value,
            leaderboard_type_name=rank_info.leaderboard_type.display_name,
            period=rank_info.period.value,
            period_name=rank_info.period.display_name,
            rank=rank_info.rank,
            score=rank_info.score,
            total_players=rank_info.total_players,
            percentile=rank_info.percentile,
            history_rank=rank_info.history_rank,
            rank_change_text=rank_info.rank_change_text,
            rewards_claimed=rank_info.rewards_claimed,
            best_rank=rank_info.best_rank,
            is_ranked=rank_info.is_ranked,
        )
    
    def update_player_stats(
        self,
        player_id: str,
        nickname: str,
        avatar: str,
        tier: str,
        stars: int,
        tier_score: int,
        win_count: int,
        total_count: int,
        first_place_count: int,
        max_damage: int,
        total_gold: int,
        extra_data: Optional[dict] = None,
    ) -> None:
        """
        更新玩家排行榜统计
        
        在对局结束时调用以更新排行榜数据。
        
        Args:
            player_id: 玩家ID
            nickname: 玩家昵称
            avatar: 玩家头像
            tier: 段位
            stars: 星数
            tier_score: 段位积分
            win_count: 胜利场数
            total_count: 总场数
            first_place_count: 第一名次数
            max_damage: 单局最高伤害
            total_gold: 累计金币
            extra_data: 额外数据
        """
        self.manager.update_player_data(
            player_id=player_id,
            nickname=nickname,
            avatar=avatar,
            tier=tier,
            stars=stars,
            tier_score=tier_score,
            win_count=win_count,
            total_count=total_count,
            first_place_count=first_place_count,
            max_damage=max_damage,
            total_gold=total_gold,
            extra_data=extra_data,
        )


# 全局处理器实例
leaderboard_ws_handler = LeaderboardWSHandler()
