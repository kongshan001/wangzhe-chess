"""
王者之奕 - 投票系统测试

测试投票系统的核心功能：
- 投票创建
- 投票列表获取
- 投票操作
- 投票结果计算
- 奖励发放
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.server.voting.models import (
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
from src.server.voting.manager import VotingManager


class TestVotingModels:
    """测试投票数据模型"""
    
    def test_voting_option_creation(self):
        """测试投票选项创建"""
        option = VotingOption(
            option_id="opt_001",
            poll_id="poll_001",
            title="战士型英雄",
            description="高血量高防御的近战英雄",
        )
        
        assert option.option_id == "opt_001"
        assert option.poll_id == "poll_001"
        assert option.title == "战士型英雄"
        assert option.vote_count == 0
        assert option.percentage == 0.0
    
    def test_voting_option_to_dict(self):
        """测试投票选项序列化"""
        option = VotingOption(
            option_id="opt_001",
            poll_id="poll_001",
            title="战士型英雄",
            description="高血量高防御的近战英雄",
            vote_count=100,
            percentage=33.33,
        )
        
        data = option.to_dict()
        assert data["option_id"] == "opt_001"
        assert data["title"] == "战士型英雄"
        assert data["vote_count"] == 100
        assert data["percentage"] == 33.33
    
    def test_voting_reward_creation(self):
        """测试投票奖励创建"""
        reward = VotingReward(
            reward_id="reward_001",
            reward_type=RewardType.GOLD,
            quantity=100,
        )
        
        assert reward.reward_id == "reward_001"
        assert reward.reward_type == RewardType.GOLD
        assert reward.quantity == 100
        assert reward.is_bonus == False
    
    def test_voting_reward_to_dict(self):
        """测试投票奖励序列化"""
        reward = VotingReward(
            reward_id="reward_001",
            reward_type=RewardType.GOLD,
            quantity=100,
            is_bonus=True,
        )
        
        data = reward.to_dict()
        assert data["reward_type"] == "gold"
        assert data["is_bonus"] == True
    
    def test_player_vote_creation(self):
        """测试玩家投票记录创建"""
        vote = PlayerVote(
            vote_id="vote_001",
            poll_id="poll_001",
            player_id="player_001",
            option_id="opt_001",
            vote_weight=3,
            is_vip=True,
        )
        
        assert vote.vote_id == "vote_001"
        assert vote.player_id == "player_001"
        assert vote.option_id == "opt_001"
        assert vote.vote_weight == 3
        assert vote.is_vip == True
        assert vote.rewards_claimed == False
    
    def test_voting_poll_creation(self):
        """测试投票主题创建"""
        poll = VotingPoll(
            poll_id="poll_001",
            title="下一个新英雄投票",
            description="选择下一个加入游戏的英雄类型",
            voting_type=VotingType.NEW_HERO,
            status=VotingStatus.ONGOING,
        )
        
        assert poll.poll_id == "poll_001"
        assert poll.title == "下一个新英雄投票"
        assert poll.voting_type == VotingType.NEW_HERO
        assert poll.status == VotingStatus.ONGOING
        assert poll.total_votes == 0
        assert poll.total_voters == 0
    
    def test_voting_poll_is_active(self):
        """测试投票是否进行中"""
        now = datetime.now()
        
        # 进行中的投票
        poll1 = VotingPoll(
            poll_id="poll_001",
            title="测试投票",
            voting_type=VotingType.NEW_HERO,
            status=VotingStatus.ONGOING,
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=7),
        )
        assert poll1.is_active() == True
        
        # 未开始的投票
        poll2 = VotingPoll(
            poll_id="poll_002",
            title="测试投票",
            voting_type=VotingType.NEW_HERO,
            status=VotingStatus.ONGOING,
            start_time=now + timedelta(days=1),
        )
        assert poll2.is_active() == False
        
        # 已结束的投票
        poll3 = VotingPoll(
            poll_id="poll_003",
            title="测试投票",
            voting_type=VotingType.NEW_HERO,
            status=VotingStatus.ENDED,
        )
        assert poll3.is_active() == False
    
    def test_voting_poll_get_option(self):
        """测试获取投票选项"""
        option1 = VotingOption(
            option_id="opt_001",
            poll_id="poll_001",
            title="选项1",
        )
        option2 = VotingOption(
            option_id="opt_002",
            poll_id="poll_001",
            title="选项2",
        )
        
        poll = VotingPoll(
            poll_id="poll_001",
            title="测试投票",
            options=[option1, option2],
        )
        
        assert poll.get_option("opt_001") == option1
        assert poll.get_option("opt_002") == option2
        assert poll.get_option("opt_003") is None
    
    def test_voting_poll_update_percentages(self):
        """测试更新投票百分比"""
        option1 = VotingOption(
            option_id="opt_001",
            poll_id="poll_001",
            title="选项1",
            vote_count=60,
        )
        option2 = VotingOption(
            option_id="opt_002",
            poll_id="poll_001",
            title="选项2",
            vote_count=40,
        )
        
        poll = VotingPoll(
            poll_id="poll_001",
            title="测试投票",
            options=[option1, option2],
            total_votes=100,
        )
        
        poll.update_percentages()
        
        assert option1.percentage == 60.0
        assert option2.percentage == 40.0
    
    def test_voting_poll_get_winning_option(self):
        """测试获取获胜选项"""
        option1 = VotingOption(
            option_id="opt_001",
            poll_id="poll_001",
            title="选项1",
            vote_count=60,
        )
        option2 = VotingOption(
            option_id="opt_002",
            poll_id="poll_001",
            title="选项2",
            vote_count=40,
        )
        
        poll = VotingPoll(
            poll_id="poll_001",
            title="测试投票",
            options=[option1, option2],
        )
        
        winner = poll.get_winning_option()
        assert winner == option1


class TestVotingManager:
    """测试投票管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建投票管理器"""
        return VotingManager()
    
    def test_create_poll(self, manager):
        """测试创建投票"""
        options = [
            {"title": "战士型英雄", "description": "近战英雄"},
            {"title": "法师型英雄", "description": "远程法术英雄"},
        ]
        
        poll = manager.create_poll(
            title="新英雄投票",
            voting_type=VotingType.NEW_HERO,
            options=options,
            description="选择下一个新英雄",
        )
        
        assert poll.poll_id.startswith("poll_")
        assert poll.title == "新英雄投票"
        assert poll.voting_type == VotingType.NEW_HERO
        assert poll.status == VotingStatus.ONGOING
        assert len(poll.options) == 2
        assert poll.total_votes == 0
        assert poll.total_voters == 0
    
    def test_get_poll(self, manager):
        """测试获取投票"""
        # 创建投票
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项1"}, {"title": "选项2"}],
        )
        
        # 获取投票
        retrieved = manager.get_poll(poll.poll_id)
        assert retrieved == poll
        
        # 不存在的投票
        assert manager.get_poll("non_existent") is None
    
    def test_get_polls(self, manager):
        """测试获取投票列表"""
        # 创建多个投票
        poll1 = manager.create_poll(
            title="投票1",
            voting_type=VotingType.NEW_HERO,
            options=[{"title": "A"}, {"title": "B"}],
        )
        poll2 = manager.create_poll(
            title="投票2",
            voting_type=VotingType.BALANCE,
            options=[{"title": "C"}, {"title": "D"}],
        )
        
        # 获取所有投票
        polls = manager.get_polls()
        assert len(polls) == 2
        
        # 按类型过滤
        polls = manager.get_polls(voting_type=VotingType.NEW_HERO)
        assert len(polls) == 1
        assert polls[0].voting_type == VotingType.NEW_HERO
    
    def test_vote_success(self, manager):
        """测试成功投票"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
        )
        
        option_id = poll.options[0].option_id
        
        vote, error = manager.vote(
            player_id="player_001",
            poll_id=poll.poll_id,
            option_id=option_id,
            vip_level=0,
        )
        
        assert error is None
        assert vote is not None
        assert vote.player_id == "player_001"
        assert vote.option_id == option_id
        assert vote.vote_weight == 1
        
        # 检查票数更新
        updated_poll = manager.get_poll(poll.poll_id)
        assert updated_poll.total_votes == 1
        assert updated_poll.total_voters == 1
        assert updated_poll.options[0].vote_count == 1
    
    def test_vote_vip_extra_weight(self, manager):
        """测试VIP额外票数"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
        )
        
        option_id = poll.options[0].option_id
        
        # VIP3玩家投票
        vote, error = manager.vote(
            player_id="vip_player",
            poll_id=poll.poll_id,
            option_id=option_id,
            vip_level=3,
        )
        
        assert error is None
        assert vote.vote_weight == VIP_VOTE_WEIGHTS[3]
        
        # 检查票数（应该是VIP权重）
        updated_poll = manager.get_poll(poll.poll_id)
        assert updated_poll.total_votes == VIP_VOTE_WEIGHTS[3]
        assert updated_poll.total_voters == 1
    
    def test_vote_already_voted(self, manager):
        """测试重复投票"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
        )
        
        option_id = poll.options[0].option_id
        
        # 第一次投票
        manager.vote("player_001", poll.poll_id, option_id, 0)
        
        # 再次投票
        vote, error = manager.vote("player_001", poll.poll_id, option_id, 0)
        
        assert vote is None
        assert "已参与" in error
    
    def test_vote_non_existent_poll(self, manager):
        """测试对不存在的投票进行投票"""
        vote, error = manager.vote("player_001", "non_existent", "opt_001", 0)
        
        assert vote is None
        assert "不存在" in error
    
    def test_vote_non_existent_option(self, manager):
        """测试选择不存在的选项"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}],
        )
        
        vote, error = manager.vote("player_001", poll.poll_id, "non_existent", 0)
        
        assert vote is None
        assert "不存在" in error
    
    def test_has_voted(self, manager):
        """测试检查是否已投票"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}],
        )
        
        option_id = poll.options[0].option_id
        
        # 未投票
        assert manager.has_voted("player_001", poll.poll_id) == False
        
        # 投票后
        manager.vote("player_001", poll.poll_id, option_id, 0)
        assert manager.has_voted("player_001", poll.poll_id) == True
    
    def test_end_poll(self, manager):
        """测试结束投票"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
        )
        
        # 投票
        manager.vote("player_001", poll.poll_id, poll.options[0].option_id, 0)
        manager.vote("player_002", poll.poll_id, poll.options[1].option_id, 0)
        
        # 结束投票
        result, error = manager.end_poll(poll.poll_id)
        
        assert error is None
        assert result is not None
        assert result.poll_id == poll.poll_id
        assert result.total_votes == 2
        assert result.total_voters == 2
        assert result.winning_option is not None
        
        # 检查状态更新
        updated_poll = manager.get_poll(poll.poll_id)
        assert updated_poll.status == VotingStatus.ENDED
    
    def test_calculate_results(self, manager):
        """测试计算投票结果"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
        )
        
        # 投票（选项A: 60票, 选项B: 40票）
        option_a = poll.options[0].option_id
        option_b = poll.options[1].option_id
        
        # 60票给A
        for i in range(60):
            manager.vote(f"player_a_{i}", poll.poll_id, option_a, 0)
        
        # 40票给B
        for i in range(40):
            manager.vote(f"player_b_{i}", poll.poll_id, option_b, 0)
        
        # 计算结果
        result = manager.calculate_results(poll.poll_id)
        
        assert result is not None
        assert result.total_votes == 100
        assert result.total_voters == 100
        assert result.winning_option.option_id == option_a
        assert len(result.results) == 2
        assert result.results[0]["vote_count"] == 60
    
    def test_get_voting_info(self, manager):
        """测试获取投票信息"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}],
        )
        
        # 未投票的玩家
        info = manager.get_voting_info("player_001", poll.poll_id)
        assert info is not None
        assert info.player_voted == False
        assert info.can_vote == True
        
        # 投票后
        manager.vote("player_001", poll.poll_id, poll.options[0].option_id, 0)
        info = manager.get_voting_info("player_001", poll.poll_id)
        assert info.player_voted == True
        assert info.can_vote == False
    
    def test_claim_rewards(self, manager):
        """测试领取投票奖励"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}, {"title": "选项B"}],
            participation_reward=[
                VotingReward(reward_id="gold", reward_type=RewardType.GOLD, quantity=100),
            ],
            win_bonus_reward=[
                VotingReward(reward_id="bonus", reward_type=RewardType.GOLD, quantity=200, is_bonus=True),
            ],
        )
        
        option_a = poll.options[0].option_id
        option_b = poll.options[1].option_id
        
        # 玩家1投给获胜选项
        manager.vote("player_001", poll.poll_id, option_a, 0)
        # 玩家2投给失败选项
        manager.vote("player_002", poll.poll_id, option_b, 0)
        
        # 结束投票
        manager.end_poll(poll.poll_id)
        
        # 玩家1领取奖励（投中获胜选项）
        rewards1, error1 = manager.claim_rewards("player_001", poll.poll_id)
        assert error1 is None
        assert len(rewards1) == 2  # 参与奖励 + 投中额外奖励
        
        # 玩家2领取奖励（未投中获胜选项）
        rewards2, error2 = manager.claim_rewards("player_002", poll.poll_id)
        assert error2 is None
        assert len(rewards2) == 1  # 只有参与奖励
    
    def test_claim_rewards_already_claimed(self, manager):
        """测试重复领取奖励"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}],
        )
        
        manager.vote("player_001", poll.poll_id, poll.options[0].option_id, 0)
        manager.end_poll(poll.poll_id)
        
        # 第一次领取
        manager.claim_rewards("player_001", poll.poll_id)
        
        # 再次领取
        rewards, error = manager.claim_rewards("player_001", poll.poll_id)
        assert rewards == []
        assert "已领取" in error
    
    def test_cancel_poll(self, manager):
        """测试取消投票"""
        poll = manager.create_poll(
            title="测试投票",
            voting_type=VotingType.CUSTOM,
            options=[{"title": "选项A"}],
        )
        
        success, error = manager.cancel_poll(poll.poll_id)
        
        assert success == True
        assert error is None
        
        updated_poll = manager.get_poll(poll.poll_id)
        assert updated_poll.status == VotingStatus.CANCELLED
    
    def test_get_vote_weight(self, manager):
        """测试获取投票权重"""
        # 普通玩家
        assert manager.get_vote_weight(0) == 1
        
        # VIP玩家
        assert manager.get_vote_weight(1) == 2
        assert manager.get_vote_weight(3) == 4
        assert manager.get_vote_weight(6) == 10
        
        # 未定义的VIP等级
        assert manager.get_vote_weight(99) == 1  # 返回默认值


class TestVotingManagerWithConfig:
    """测试带配置的投票管理器"""
    
    def test_load_config(self, tmp_path):
        """测试从配置文件加载"""
        config_content = '''{
            "version": "1.0.0",
            "voting_templates": [
                {
                    "title": "测试投票",
                    "description": "测试描述",
                    "voting_type": "new_hero",
                    "auto_create": true,
                    "duration_days": 7,
                    "options": [
                        {"title": "选项1", "description": "描述1"},
                        {"title": "选项2", "description": "描述2"}
                    ],
                    "participation_reward": [
                        {"reward_type": "gold", "quantity": 50}
                    ]
                }
            ]
        }'''
        
        config_file = tmp_path / "votings.json"
        config_file.write_text(config_content)
        
        manager = VotingManager(config_path=str(config_file))
        
        # 检查是否加载了投票
        assert len(manager.polls) >= 1
        
        # 检查投票内容
        poll = list(manager.polls.values())[0]
        assert poll.title == "测试投票"
        assert poll.voting_type == VotingType.NEW_HERO
        assert len(poll.options) == 2
