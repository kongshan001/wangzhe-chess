"""
王者之奕 - 投票系统 WebSocket 处理器

本模块实现投票系统的 WebSocket 消息处理：
- GET_VOTING_LIST: 获取投票列表
- VOTING_LIST: 投票列表响应
- GET_VOTING_DETAILS: 获取投票详情
- VOTING_DETAILS: 投票详情响应
- VOTE: 投票
- VOTE_CASTED: 投票成功响应
- GET_VOTING_RESULTS: 获取投票结果
- VOTING_RESULTS: 投票结果响应
- CLAIM_VOTING_REWARDS: 领取投票奖励
- VOTING_REWARDS_CLAIMED: 奖励领取成功响应
"""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING, Any, Optional

from ...shared.protocol import MessageType
from ...shared.protocol import (
    BaseMessage,
    GetVotingListMessage,
    VotingListMessage,
    GetVotingDetailsMessage,
    VotingDetailsMessage,
    VoteMessage,
    VoteCastedMessage,
    GetVotingResultsMessage,
    VotingResultsMessage,
    ClaimVotingRewardsMessage,
    VotingRewardsClaimedMessage,
    VotingOptionData,
    VotingRewardData,
    VotingPollData,
    VotingInfoData,
    VotingResultData,
    ErrorMessage,
)
from src.server.voting import (
    VotingManager,
    get_voting_manager,
    VotingPoll,
    VotingOption,
    VotingReward,
    VotingInfo,
    VotingResult,
    PlayerVote,
    VotingStatus,
    VotingType,
    RewardType,
)

if TYPE_CHECKING:
    from src.server.ws.handler import Session

logger = structlog.get_logger()


class VotingWSHandler:
    """
    投票系统 WebSocket 处理器
    
    处理投票相关的 WebSocket 消息。
    
    Attributes:
        manager: 投票管理器
    """
    
    def __init__(
        self,
        manager: Optional[VotingManager] = None,
    ) -> None:
        """
        初始化处理器
        
        Args:
            manager: 投票管理器实例
        """
        self.manager = manager or get_voting_manager()
    
    def register_handlers(self, ws_handler: Any) -> None:
        """
        注册消息处理器
        
        Args:
            ws_handler: WebSocket 主处理器
        """
        ws_handler._handlers[MessageType.GET_VOTING_LIST] = self.handle_get_voting_list
        ws_handler._handlers[MessageType.GET_VOTING_DETAILS] = self.handle_get_voting_details
        ws_handler._handlers[MessageType.VOTE] = self.handle_vote
        ws_handler._handlers[MessageType.GET_VOTING_RESULTS] = self.handle_get_voting_results
        ws_handler._handlers[MessageType.CLAIM_VOTING_REWARDS] = self.handle_claim_voting_rewards
    
    async def handle_get_voting_list(
        self,
        session: Session,
        message: GetVotingListMessage,
    ) -> VotingListMessage:
        """
        处理获取投票列表请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            投票列表响应
        """
        logger.info(
            "获取投票列表",
            player_id=session.player_id,
            status=message.status,
            voting_type=message.voting_type,
        )
        
        # 解析过滤条件
        status_filter = None
        if message.status:
            try:
                status_filter = VotingStatus(message.status)
            except ValueError:
                pass
        
        type_filter = None
        if message.voting_type:
            try:
                type_filter = VotingType(message.voting_type)
            except ValueError:
                pass
        
        # 获取投票列表
        polls = self.manager.get_polls(
            status=status_filter,
            voting_type=type_filter,
            limit=message.limit,
            offset=message.offset,
        )
        
        # 转换为响应格式
        poll_data_list = []
        for poll in polls:
            poll_data = self._convert_poll_to_data(poll)
            poll_data_list.append(poll_data)
        
        # 计算总数（简化处理）
        total_count = len(self.manager.polls)
        
        return VotingListMessage(
            polls=poll_data_list,
            total_count=total_count,
            seq=message.seq,
        )
    
    async def handle_get_voting_details(
        self,
        session: Session,
        message: GetVotingDetailsMessage,
    ) -> BaseMessage:
        """
        处理获取投票详情请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            投票详情响应或错误消息
        """
        logger.info(
            "获取投票详情",
            player_id=session.player_id,
            poll_id=message.poll_id,
        )
        
        # 获取投票信息
        info = self.manager.get_voting_info(session.player_id, message.poll_id)
        
        if not info:
            return ErrorMessage(
                error_code=2401,
                error_message="投票不存在",
                seq=message.seq,
            )
        
        # 转换为响应格式
        poll_data = self._convert_poll_to_data(info.poll)
        
        # 构建投票信息数据
        info_data = VotingInfoData(
            poll=poll_data,
            player_voted=info.player_voted,
            player_option_id=info.player_vote.option_id if info.player_vote else None,
            player_vote_weight=info.player_vote.vote_weight if info.player_vote else 1,
            can_vote=info.can_vote,
            reason=info.reason,
        )
        
        return VotingDetailsMessage(
            info=info_data,
            seq=message.seq,
        )
    
    async def handle_vote(
        self,
        session: Session,
        message: VoteMessage,
    ) -> BaseMessage:
        """
        处理投票请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            投票成功响应或错误消息
        """
        logger.info(
            "玩家投票",
            player_id=session.player_id,
            poll_id=message.poll_id,
            option_id=message.option_id,
        )
        
        # 获取玩家VIP等级（从session metadata或玩家数据中获取）
        vip_level = getattr(session, "vip_level", 0)
        if hasattr(session, "metadata") and session.metadata:
            vip_level = session.metadata.get("vip_level", 0)
        
        # 执行投票
        vote, error = self.manager.vote(
            player_id=session.player_id,
            poll_id=message.poll_id,
            option_id=message.option_id,
            vip_level=vip_level,
        )
        
        if error:
            logger.warning(
                "投票失败",
                player_id=session.player_id,
                poll_id=message.poll_id,
                error=error,
            )
            return ErrorMessage(
                error_code=2402,
                error_message=error,
                seq=message.seq,
            )
        
        # 获取更新后的投票信息
        poll = self.manager.get_poll(message.poll_id)
        poll_data = self._convert_poll_to_data(poll) if poll else None
        
        return VoteCastedMessage(
            poll_id=message.poll_id,
            option_id=message.option_id,
            vote_weight=vote.vote_weight if vote else 1,
            updated_poll=poll_data,
            seq=message.seq,
        )
    
    async def handle_get_voting_results(
        self,
        session: Session,
        message: GetVotingResultsMessage,
    ) -> BaseMessage:
        """
        处理获取投票结果请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            投票结果响应或错误消息
        """
        logger.info(
            "获取投票结果",
            player_id=session.player_id,
            poll_id=message.poll_id,
        )
        
        # 获取投票
        poll = self.manager.get_poll(message.poll_id)
        if not poll:
            return ErrorMessage(
                error_code=2401,
                error_message="投票不存在",
                seq=message.seq,
            )
        
        # 计算结果
        result = self.manager.calculate_results(message.poll_id)
        if not result:
            return ErrorMessage(
                error_code=2403,
                error_message="计算结果失败",
                seq=message.seq,
            )
        
        # 转换为响应格式
        result_data = self._convert_result_to_data(result)
        
        return VotingResultsMessage(
            result=result_data,
            seq=message.seq,
        )
    
    async def handle_claim_voting_rewards(
        self,
        session: Session,
        message: ClaimVotingRewardsMessage,
    ) -> BaseMessage:
        """
        处理领取投票奖励请求
        
        Args:
            session: WebSocket 会话
            message: 请求消息
            
        Returns:
            奖励领取成功响应或错误消息
        """
        logger.info(
            "领取投票奖励",
            player_id=session.player_id,
            poll_id=message.poll_id,
        )
        
        # 领取奖励
        rewards, error = self.manager.claim_rewards(
            player_id=session.player_id,
            poll_id=message.poll_id,
        )
        
        if error:
            logger.warning(
                "领取奖励失败",
                player_id=session.player_id,
                poll_id=message.poll_id,
                error=error,
            )
            return ErrorMessage(
                error_code=2404,
                error_message=error,
                seq=message.seq,
            )
        
        # 检查是否投中获胜选项
        poll = self.manager.get_poll(message.poll_id)
        vote = self.manager.get_player_vote(session.player_id, message.poll_id)
        is_winner = False
        if poll and vote and poll.winning_option_id:
            is_winner = (vote.option_id == poll.winning_option_id)
        
        # 转换奖励格式
        reward_data_list = []
        for reward in rewards:
            reward_data = VotingRewardData(
                reward_id=reward.reward_id,
                reward_type=reward.reward_type.value if isinstance(reward.reward_type, RewardType) else reward.reward_type,
                item_id=reward.item_id,
                quantity=reward.quantity,
                is_bonus=reward.is_bonus,
            )
            reward_data_list.append(reward_data)
        
        logger.info(
            "奖励领取成功",
            player_id=session.player_id,
            poll_id=message.poll_id,
            rewards_count=len(rewards),
            is_winner=is_winner,
        )
        
        return VotingRewardsClaimedMessage(
            poll_id=message.poll_id,
            rewards=reward_data_list,
            is_winner=is_winner,
            seq=message.seq,
        )
    
    def _convert_poll_to_data(self, poll: VotingPoll) -> VotingPollData:
        """将投票对象转换为响应数据"""
        options_data = []
        for option in poll.options:
            option_data = VotingOptionData(
                option_id=option.option_id,
                title=option.title,
                description=option.description,
                icon=option.icon,
                vote_count=option.vote_count,
                percentage=option.percentage,
            )
            options_data.append(option_data)
        
        return VotingPollData(
            poll_id=poll.poll_id,
            title=poll.title,
            description=poll.description,
            voting_type=poll.voting_type.value if isinstance(poll.voting_type, VotingType) else poll.voting_type,
            status=poll.status.value if isinstance(poll.status, VotingStatus) else poll.status,
            options=options_data,
            start_time=poll.start_time.isoformat() if poll.start_time else None,
            end_time=poll.end_time.isoformat() if poll.end_time else None,
            total_votes=poll.total_votes,
            total_voters=poll.total_voters,
            min_vip_level=poll.min_vip_level,
            tags=poll.tags,
        )
    
    def _convert_result_to_data(self, result: VotingResult) -> VotingResultData:
        """将投票结果转换为响应数据"""
        results_data = []
        for result_item in result.results:
            option_data = VotingOptionData(
                option_id=result_item["option_id"],
                title=result_item["title"],
                description="",  # 结果中没有描述
                icon=None,
                vote_count=result_item["vote_count"],
                percentage=result_item["percentage"],
            )
            results_data.append(option_data)
        
        winning_option_data = None
        if result.winning_option:
            winning_option_data = VotingOptionData(
                option_id=result.winning_option.option_id,
                title=result.winning_option.title,
                description=result.winning_option.description,
                icon=result.winning_option.icon,
                vote_count=result.winning_option.vote_count,
                percentage=result.winning_option.percentage,
            )
        
        return VotingResultData(
            poll_id=result.poll_id,
            winning_option_id=result.winning_option.option_id if result.winning_option else None,
            winning_option=winning_option_data,
            total_votes=result.total_votes,
            total_voters=result.total_voters,
            results=results_data,
            ended_at=result.ended_at.isoformat() if result.ended_at else None,
        )


# 全局处理器实例
_voting_ws_handler: Optional[VotingWSHandler] = None


def get_voting_ws_handler(manager: Optional[VotingManager] = None) -> VotingWSHandler:
    """
    获取投票 WebSocket 处理器单例
    
    Args:
        manager: 投票管理器实例
        
    Returns:
        投票 WebSocket 处理器实例
    """
    global _voting_ws_handler
    if _voting_ws_handler is None:
        _voting_ws_handler = VotingWSHandler(manager)
    return _voting_ws_handler
