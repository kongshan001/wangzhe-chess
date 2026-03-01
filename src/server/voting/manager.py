"""
王者之奕 - 投票管理器

本模块提供投票系统的管理功能：
- VotingManager: 投票管理器类
- 创建投票
- 获取投票列表
- 投票操作
- 结束投票
- 计算投票结果
- 发放投票奖励
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import (
    DEFAULT_PARTICIPATION_REWARDS,
    DEFAULT_WIN_BONUS_REWARDS,
    VIP_VOTE_WEIGHTS,
    PlayerVote,
    RewardType,
    VotingInfo,
    VotingOption,
    VotingPoll,
    VotingResult,
    VotingReward,
    VotingStatus,
    VotingType,
)

logger = logging.getLogger(__name__)


class VotingManager:
    """
    投票管理器

    负责管理所有投票相关的操作：
    - 投票配置加载
    - 创建投票
    - 获取投票列表
    - 投票操作
    - 结束投票
    - 计算结果
    - 发放奖励

    Attributes:
        polls: 投票列表 (poll_id -> VotingPoll)
        player_votes: 玩家投票记录 (player_id -> {poll_id -> PlayerVote})
        config_path: 配置文件路径
    """

    # 投票持续时间（天）
    DEFAULT_DURATION_DAYS = 7

    def __init__(self, config_path: str | None = None):
        """
        初始化投票管理器

        Args:
            config_path: 投票配置文件路径
        """
        self.polls: dict[str, VotingPoll] = {}
        self.player_votes: dict[str, dict[str, PlayerVote]] = {}
        self.config_path = config_path

        # 加载配置
        if config_path:
            self.load_config(config_path)

        logger.info("VotingManager initialized")

    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载投票模板

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Voting config file not found: {config_path}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # 加载投票模板
            templates = data.get("voting_templates", [])
            for template_data in templates:
                # 只加载标记为auto_create的模板
                if template_data.get("auto_create", False):
                    poll = self._create_poll_from_template(template_data)
                    if poll:
                        self.polls[poll.poll_id] = poll

            logger.info(f"Loaded {len(self.polls)} voting templates from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load voting config: {e}")

    def _create_poll_from_template(self, template: dict[str, Any]) -> VotingPoll | None:
        """从模板创建投票"""
        try:
            poll_id = f"poll_{template['voting_type']}_{uuid.uuid4().hex[:8]}"

            options = []
            for opt_data in template.get("options", []):
                option = VotingOption(
                    option_id=f"opt_{uuid.uuid4().hex[:8]}",
                    poll_id=poll_id,
                    title=opt_data["title"],
                    description=opt_data.get("description", ""),
                    icon=opt_data.get("icon"),
                    extra_data=opt_data.get("extra_data", {}),
                )
                options.append(option)

            # 创建奖励
            participation_reward = []
            for r in template.get("participation_reward", []):
                participation_reward.append(
                    VotingReward(
                        reward_id=r.get("reward_id", f"reward_{uuid.uuid4().hex[:8]}"),
                        reward_type=RewardType(r["reward_type"]),
                        item_id=r.get("item_id"),
                        quantity=r.get("quantity", 1),
                    )
                )

            win_bonus_reward = []
            for r in template.get("win_bonus_reward", []):
                win_bonus_reward.append(
                    VotingReward(
                        reward_id=r.get("reward_id", f"reward_{uuid.uuid4().hex[:8]}"),
                        reward_type=RewardType(r["reward_type"]),
                        item_id=r.get("item_id"),
                        quantity=r.get("quantity", 1),
                        is_bonus=True,
                    )
                )

            now = datetime.now()
            start_time = now
            end_time = now + timedelta(
                days=template.get("duration_days", self.DEFAULT_DURATION_DAYS)
            )

            poll = VotingPoll(
                poll_id=poll_id,
                title=template["title"],
                description=template.get("description", ""),
                voting_type=VotingType(template["voting_type"]),
                status=VotingStatus.ONGOING,
                options=options,
                start_time=start_time,
                end_time=end_time,
                participation_reward=participation_reward or DEFAULT_PARTICIPATION_REWARDS.copy(),
                win_bonus_reward=win_bonus_reward or DEFAULT_WIN_BONUS_REWARDS.copy(),
                min_vip_level=template.get("min_vip_level", 0),
                tags=template.get("tags", []),
            )

            return poll

        except Exception as e:
            logger.error(f"Failed to create poll from template: {e}")
            return None

    def create_poll(
        self,
        title: str,
        voting_type: VotingType,
        options: list[dict[str, Any]],
        description: str = "",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        participation_reward: list[VotingReward] | None = None,
        win_bonus_reward: list[VotingReward] | None = None,
        min_vip_level: int = 0,
        created_by: str | None = None,
        tags: list[str] | None = None,
    ) -> VotingPoll:
        """
        创建新投票

        Args:
            title: 投票标题
            voting_type: 投票类型
            options: 选项列表 [{"title": "xxx", "description": "xxx", ...}, ...]
            description: 投票描述
            start_time: 开始时间
            end_time: 结束时间
            participation_reward: 参与奖励
            win_bonus_reward: 投中额外奖励
            min_vip_level: 最低VIP等级要求
            created_by: 创建者ID
            tags: 标签列表

        Returns:
            创建的投票对象
        """
        poll_id = f"poll_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        # 创建选项
        poll_options = []
        for opt_data in options:
            option = VotingOption(
                option_id=f"opt_{uuid.uuid4().hex[:8]}",
                poll_id=poll_id,
                title=opt_data["title"],
                description=opt_data.get("description", ""),
                icon=opt_data.get("icon"),
                extra_data=opt_data.get("extra_data", {}),
            )
            poll_options.append(option)

        # 设置默认时间
        if start_time is None:
            start_time = now
        if end_time is None:
            end_time = now + timedelta(days=self.DEFAULT_DURATION_DAYS)

        poll = VotingPoll(
            poll_id=poll_id,
            title=title,
            description=description,
            voting_type=voting_type,
            status=VotingStatus.ONGOING,
            options=poll_options,
            start_time=start_time,
            end_time=end_time,
            participation_reward=participation_reward or DEFAULT_PARTICIPATION_REWARDS.copy(),
            win_bonus_reward=win_bonus_reward or DEFAULT_WIN_BONUS_REWARDS.copy(),
            min_vip_level=min_vip_level,
            created_by=created_by,
            tags=tags or [],
        )

        self.polls[poll_id] = poll

        logger.info(f"Created new poll: {poll_id}, title={title}, type={voting_type.value}")

        return poll

    def get_poll(self, poll_id: str) -> VotingPoll | None:
        """
        获取投票详情

        Args:
            poll_id: 投票ID

        Returns:
            投票对象，不存在返回None
        """
        return self.polls.get(poll_id)

    def get_polls(
        self,
        status: VotingStatus | None = None,
        voting_type: VotingType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[VotingPoll]:
        """
        获取投票列表

        Args:
            status: 状态过滤
            voting_type: 类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            投票列表
        """
        polls = list(self.polls.values())

        # 过滤
        if status:
            polls = [p for p in polls if p.status == status]
        if voting_type:
            polls = [p for p in polls if p.voting_type == voting_type]

        # 按创建时间倒序
        polls.sort(key=lambda p: p.created_at, reverse=True)

        return polls[offset : offset + limit]

    def get_active_polls(self) -> list[VotingPoll]:
        """
        获取所有进行中的投票

        Returns:
            进行中的投票列表
        """
        return [p for p in self.polls.values() if p.is_active()]

    def get_vote_weight(self, vip_level: int) -> int:
        """
        获取投票权重

        Args:
            vip_level: VIP等级

        Returns:
            投票权重
        """
        return VIP_VOTE_WEIGHTS.get(vip_level, 1)

    def has_voted(self, player_id: str, poll_id: str) -> bool:
        """
        检查玩家是否已投票

        Args:
            player_id: 玩家ID
            poll_id: 投票ID

        Returns:
            是否已投票
        """
        player_polls = self.player_votes.get(player_id, {})
        return poll_id in player_polls

    def get_player_vote(self, player_id: str, poll_id: str) -> PlayerVote | None:
        """
        获取玩家投票记录

        Args:
            player_id: 玩家ID
            poll_id: 投票ID

        Returns:
            投票记录，不存在返回None
        """
        player_polls = self.player_votes.get(player_id, {})
        return player_polls.get(poll_id)

    def vote(
        self,
        player_id: str,
        poll_id: str,
        option_id: str,
        vip_level: int = 0,
    ) -> tuple[PlayerVote | None, str | None]:
        """
        执行投票

        Args:
            player_id: 玩家ID
            poll_id: 投票ID
            option_id: 选项ID
            vip_level: VIP等级

        Returns:
            (投票记录, 错误信息) - 成功时错误信息为None
        """
        # 检查投票是否存在
        poll = self.polls.get(poll_id)
        if not poll:
            return None, "投票不存在"

        # 检查投票是否进行中
        if not poll.is_active():
            return None, "投票未开始或已结束"

        # 检查VIP等级要求
        if poll.min_vip_level > 0 and vip_level < poll.min_vip_level:
            return None, f"需要VIP{poll.min_vip_level}以上才能参与投票"

        # 检查是否已投票
        if self.has_voted(player_id, poll_id):
            return None, "您已参与过此投票"

        # 检查选项是否存在
        option = poll.get_option(option_id)
        if not option:
            return None, "选项不存在"

        # 计算投票权重
        vote_weight = self.get_vote_weight(vip_level)
        is_vip = vip_level > 0

        # 创建投票记录
        vote_id = f"vote_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        vote = PlayerVote(
            vote_id=vote_id,
            poll_id=poll_id,
            player_id=player_id,
            option_id=option_id,
            vote_weight=vote_weight,
            vote_time=now,
            is_vip=is_vip,
        )

        # 更新选项票数
        option.vote_count += vote_weight

        # 更新投票统计
        poll.total_votes += vote_weight
        poll.total_voters += 1
        poll.updated_at = now

        # 更新百分比
        poll.update_percentages()

        # 保存投票记录
        if player_id not in self.player_votes:
            self.player_votes[player_id] = {}
        self.player_votes[player_id][poll_id] = vote

        logger.info(
            f"Player {player_id} voted: poll={poll_id}, option={option_id}, weight={vote_weight}"
        )

        return vote, None

    def end_poll(self, poll_id: str) -> tuple[VotingResult | None, str | None]:
        """
        结束投票

        Args:
            poll_id: 投票ID

        Returns:
            (投票结果, 错误信息) - 成功时错误信息为None
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return None, "投票不存在"

        if poll.status == VotingStatus.ENDED:
            return None, "投票已结束"

        # 计算结果
        result = self.calculate_results(poll_id)
        if not result:
            return None, "计算结果失败"

        # 更新状态
        now = datetime.now()
        poll.status = VotingStatus.ENDED
        poll.updated_at = now
        poll.winning_option_id = result.winning_option.option_id if result.winning_option else None

        logger.info(f"Poll {poll_id} ended, winner={poll.winning_option_id}")

        return result, None

    def calculate_results(self, poll_id: str) -> VotingResult | None:
        """
        计算投票结果

        Args:
            poll_id: 投票ID

        Returns:
            投票结果，不存在返回None
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return None

        # 更新百分比
        poll.update_percentages()

        # 获取获胜选项
        winning_option = poll.get_winning_option()

        # 构建结果列表
        results = []
        for option in poll.options:
            results.append(
                {
                    "option_id": option.option_id,
                    "title": option.title,
                    "vote_count": option.vote_count,
                    "percentage": option.percentage,
                }
            )

        # 按票数排序
        results.sort(key=lambda r: r["vote_count"], reverse=True)

        result = VotingResult(
            poll_id=poll_id,
            winning_option=winning_option,
            total_votes=poll.total_votes,
            total_voters=poll.total_voters,
            results=results,
            ended_at=datetime.now(),
        )

        return result

    def get_voting_info(self, player_id: str, poll_id: str) -> VotingInfo | None:
        """
        获取投票信息（包含玩家投票状态）

        Args:
            player_id: 玩家ID
            poll_id: 投票ID

        Returns:
            投票信息，不存在返回None
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return None

        player_vote = self.get_player_vote(player_id, poll_id)
        player_voted = player_vote is not None

        can_vote = True
        reason = ""

        if player_voted:
            can_vote = False
            reason = "您已参与过此投票"
        elif not poll.is_active():
            can_vote = False
            reason = "投票未开始或已结束"

        return VotingInfo(
            poll=poll,
            player_voted=player_voted,
            player_vote=player_vote,
            can_vote=can_vote,
            reason=reason,
        )

    def get_rewards_to_claim(
        self,
        player_id: str,
        poll_id: str,
    ) -> tuple[list[VotingReward], str | None]:
        """
        获取待领取的奖励

        Args:
            player_id: 玩家ID
            poll_id: 投票ID

        Returns:
            (奖励列表, 错误信息)
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return [], "投票不存在"

        vote = self.get_player_vote(player_id, poll_id)
        if not vote:
            return [], "您未参与此投票"

        if vote.rewards_claimed:
            return [], "奖励已领取"

        if poll.status != VotingStatus.ENDED:
            return [], "投票尚未结束"

        rewards = []

        # 参与奖励
        rewards.extend(poll.participation_reward)

        # 检查是否投中获胜选项
        if poll.winning_option_id and vote.option_id == poll.winning_option_id:
            rewards.extend(poll.win_bonus_reward)

        return rewards, None

    def claim_rewards(
        self,
        player_id: str,
        poll_id: str,
    ) -> tuple[list[VotingReward], str | None]:
        """
        领取投票奖励

        Args:
            player_id: 玩家ID
            poll_id: 投票ID

        Returns:
            (奖励列表, 错误信息)
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return [], "投票不存在"

        vote = self.get_player_vote(player_id, poll_id)
        if not vote:
            return [], "您未参与此投票"

        if vote.rewards_claimed:
            return [], "奖励已领取"

        rewards, error = self.get_rewards_to_claim(player_id, poll_id)
        if error:
            return [], error

        # 标记已领取
        vote.rewards_claimed = True
        vote.rewards_claimed_at = datetime.now()

        logger.info(
            f"Player {player_id} claimed rewards for poll {poll_id}: {len(rewards)} rewards"
        )

        return rewards, None

    def check_and_end_expired_polls(self) -> list[VotingResult]:
        """
        检查并结束过期的投票

        Returns:
            结束的投票结果列表
        """
        results = []
        now = datetime.now()

        for poll in self.polls.values():
            if poll.status == VotingStatus.ONGOING and poll.end_time:
                if now > poll.end_time:
                    result, _ = self.end_poll(poll.poll_id)
                    if result:
                        results.append(result)

        if results:
            logger.info(f"Auto-ended {len(results)} expired polls")

        return results

    def cancel_poll(self, poll_id: str) -> tuple[bool, str | None]:
        """
        取消投票

        Args:
            poll_id: 投票ID

        Returns:
            (是否成功, 错误信息)
        """
        poll = self.polls.get(poll_id)
        if not poll:
            return False, "投票不存在"

        if poll.status == VotingStatus.ENDED:
            return False, "投票已结束，无法取消"

        poll.status = VotingStatus.CANCELLED
        poll.updated_at = datetime.now()

        logger.info(f"Poll {poll_id} cancelled")

        return True, None

    def clear_cache(self, player_id: str | None = None) -> None:
        """
        清除缓存

        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.player_votes.pop(player_id, None)
        else:
            self.player_votes.clear()


# 全局单例
_voting_manager: VotingManager | None = None


def get_voting_manager(config_path: str | None = None) -> VotingManager:
    """
    获取投票管理器单例

    Args:
        config_path: 配置文件路径

    Returns:
        投票管理器实例
    """
    global _voting_manager
    if _voting_manager is None:
        _voting_manager = VotingManager(config_path)
    return _voting_manager
