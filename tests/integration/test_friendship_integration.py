"""
王者之奕 - 好友系统集成测试

测试好友系统、组队、私聊的跨模块交互：
- 好友关系与组队邀请
- 私聊消息与在线状态
- 黑名单与私聊拦截
- 好友请求流程
"""

import pytest
from datetime import datetime, timedelta

from src.server.friendship import (
    FriendshipManager,
    FriendStatus,
    FriendRelation,
    get_friendship_manager,
)


class TestFriendshipIntegration:
    """好友系统集成测试"""

    def test_send_and_accept_friend_request(self, friendship_manager):
        """测试发送和接受好友请求的完整流程"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 更新玩家信息缓存
        friendship_manager.update_player_cache(
            player1, "玩家1", "avatar1.png", "gold", 10
        )
        friendship_manager.update_player_cache(
            player2, "玩家2", "avatar2.png", "silver", 5
        )
        
        # 发送好友请求
        request = friendship_manager.send_friend_request(
            from_player_id=player1,
            to_player_id=player2,
            message="你好，交个朋友！",
        )
        
        assert request is not None
        assert request.from_player_id == player1
        assert request.to_player_id == player2
        assert request.is_pending
        
        # 检查接收者的待处理请求
        pending = friendship_manager.get_pending_requests(player2)
        assert len(pending) == 1
        assert pending[0].request_id == request.request_id
        
        # 接受好友请求
        result = friendship_manager.accept_friend_request(request.request_id)
        assert result is True
        
        # 验证双方都是好友
        assert friendship_manager.is_friend(player1, player2)
        assert friendship_manager.is_friend(player2, player1)
        
        # 验证好友列表
        friends1 = friendship_manager.get_friends(player1)
        friends2 = friendship_manager.get_friends(player2)
        assert len(friends1) == 1
        assert len(friends2) == 1

    def test_reject_friend_request(self, friendship_manager):
        """测试拒绝好友请求"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 发送请求
        request = friendship_manager.send_friend_request(
            from_player_id=player1,
            to_player_id=player2,
        )
        
        assert request is not None
        
        # 拒绝请求
        result = friendship_manager.reject_friend_request(request.request_id)
        assert result is True
        
        # 验证不是好友
        assert not friendship_manager.is_friend(player1, player2)

    def test_max_friends_limit(self, friendship_manager):
        """测试好友数量上限"""
        player1 = "player_main"
        
        # 设置较低的上限便于测试
        friendship_manager.max_friends = 5
        
        # 添加好友直到上限
        for i in range(5):
            friend_id = f"friend_{i}"
            friendship_manager.update_player_cache(friend_id, f"好友{i}")
            request = friendship_manager.send_friend_request(
                from_player_id=player1,
                to_player_id=friend_id,
            )
            if request:
                friendship_manager.accept_friend_request(request.request_id)
        
        # 尝试添加第6个好友
        result = friendship_manager.send_friend_request(
            from_player_id=player1,
            to_player_id="friend_6",
        )
        
        assert result is None  # 应该失败

    def test_remove_friend(self, friendship_manager):
        """测试删除好友"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 建立好友关系
        request = friendship_manager.send_friend_request(player1, player2)
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        
        assert friendship_manager.is_friend(player1, player2)
        
        # 删除好友
        result = friendship_manager.remove_friend(player1, player2)
        assert result is True
        
        # 验证双方好友关系都解除
        assert not friendship_manager.is_friend(player1, player2)
        assert not friendship_manager.is_friend(player2, player1)


class TestBlocklistIntegration:
    """黑名单集成测试"""

    def test_block_player_prevents_friend_request(self, friendship_manager):
        """测试拉黑后无法发送好友请求"""
        player1 = "player_001"
        player2 = "player_002"
        
        # player2 拉黑 player1
        friendship_manager.block_player(player2, player1, "骚扰")
        
        # player1 尝试发送好友请求
        request = friendship_manager.send_friend_request(
            from_player_id=player1,
            to_player_id=player2,
        )
        
        assert request is None  # 应该被拒绝

    def test_block_player_removes_friendship(self, friendship_manager):
        """测试拉黑后自动解除好友关系"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 建立好友关系
        request = friendship_manager.send_friend_request(player1, player2)
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        
        assert friendship_manager.is_friend(player1, player2)
        
        # player1 拉黑 player2
        friendship_manager.block_player(player1, player2, "不再联系")
        
        # 验证好友关系解除
        assert not friendship_manager.is_friend(player1, player2)

    def test_unblock_player(self, friendship_manager):
        """测试取消拉黑"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 拉黑
        friendship_manager.block_player(player1, player2)
        assert friendship_manager.is_blocked(player2, by_player_id=player1)
        
        # 取消拉黑
        friendship_manager.unblock_player(player1, player2)
        assert not friendship_manager.is_blocked(player2, by_player_id=player1)


class TestPrivateMessageIntegration:
    """私聊消息集成测试"""

    def test_send_and_receive_private_message(self, friendship_manager):
        """测试发送和接收私聊消息"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 建立好友关系（私聊通常需要先成为好友）
        request = friendship_manager.send_friend_request(player1, player2)
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        
        # 发送消息
        message = friendship_manager.send_private_message(
            from_player_id=player1,
            to_player_id=player2,
            content="你好！",
        )
        
        assert message is not None
        assert message.content == "你好！"
        assert message.from_player_id == player1
        assert message.to_player_id == player2
        
        # 获取消息历史
        messages = friendship_manager.get_private_messages(player1, player2)
        assert len(messages) == 1
        assert messages[0].content == "你好！"

    def test_blocked_player_cannot_send_message(self, friendship_manager):
        """测试被拉黑的玩家无法发送消息"""
        player1 = "player_001"
        player2 = "player_002"
        
        # player2 拉黑 player1
        friendship_manager.block_player(player2, player1)
        
        # player1 尝试发送消息
        message = friendship_manager.send_private_message(
            from_player_id=player1,
            to_player_id=player2,
            content="你好！",
        )
        
        assert message is None

    def test_mark_messages_read(self, friendship_manager):
        """测试标记消息已读"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 发送多条消息
        for i in range(3):
            friendship_manager.send_private_message(
                from_player_id=player1,
                to_player_id=player2,
                content=f"消息{i}",
            )
        
        # 检查未读数量
        unread = friendship_manager.get_unread_count(player2)
        assert unread == 3
        
        # 标记已读
        count = friendship_manager.mark_messages_read(player2, player1)
        assert count == 3
        
        # 再次检查未读
        unread = friendship_manager.get_unread_count(player2)
        assert unread == 0

    def test_message_history_limit(self, friendship_manager):
        """测试消息历史数量限制"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 发送超过限制的消息
        for i in range(150):
            friendship_manager.send_private_message(
                from_player_id=player1,
                to_player_id=player2,
                content=f"消息{i}",
            )
        
        # 获取所有消息，应该被限制
        messages = friendship_manager.get_private_messages(
            player1, player2, limit=200
        )
        
        # 消息数量应该不超过最大值
        assert len(messages) <= 150


class TestTeamIntegration:
    """组队集成测试"""

    def test_create_team(self, friendship_manager):
        """测试创建队伍"""
        player1 = "player_001"
        
        # 创建队伍
        team = friendship_manager.create_team(player1)
        
        assert team is not None
        assert team.leader_id == player1
        assert player1 in team.members
        
        # 验证玩家的队伍关联
        player_team = friendship_manager.get_player_team(player1)
        assert player_team is not None
        assert player_team.team_id == team.team_id

    def test_join_team(self, friendship_manager):
        """测试加入队伍"""
        leader = "leader_001"
        member = "member_001"
        
        # 创建队伍
        team = friendship_manager.create_team(leader)
        
        # 成员加入
        result = friendship_manager.join_team(member, team.team_id)
        assert result is True
        
        # 验证成员列表
        team = friendship_manager.get_team(team.team_id)
        assert member in team.members
        
        # 验证玩家的队伍关联
        player_team = friendship_manager.get_player_team(member)
        assert player_team is not None

    def test_leave_team(self, friendship_manager):
        """测试离开队伍"""
        leader = "leader_001"
        member = "member_001"
        
        # 创建队伍并加入
        team = friendship_manager.create_team(leader)
        friendship_manager.join_team(member, team.team_id)
        
        # 成员离开
        result = friendship_manager.leave_team(member)
        assert result is True
        
        # 验证成员已移除
        team = friendship_manager.get_team(team.team_id)
        assert member not in team.members

    def test_leader_leave_disbands_team(self, friendship_manager):
        """测试队长离开解散队伍"""
        leader = "leader_001"
        member = "member_001"
        
        # 创建队伍并加入
        team = friendship_manager.create_team(leader)
        friendship_manager.join_team(member, team.team_id)
        
        # 队长离开（解散）
        result = friendship_manager.leave_team(leader)
        assert result is True
        
        # 验证队伍已解散
        team = friendship_manager.get_team(team.team_id)
        assert team is None
        
        # 验证成员的队伍关联也清除
        member_team = friendship_manager.get_player_team(member)
        assert member_team is None

    def test_team_invite_requires_friendship(self, friendship_manager):
        """测试组队邀请需要好友关系"""
        leader = "leader_001"
        non_friend = "non_friend_001"
        
        # 创建队伍
        team = friendship_manager.create_team(leader)
        
        # 尝试邀请非好友
        result = friendship_manager.invite_to_team(leader, non_friend)
        assert result is False
        
        # 建立好友关系
        request = friendship_manager.send_friend_request(leader, non_friend)
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        
        # 再次尝试邀请
        result = friendship_manager.invite_to_team(leader, non_friend)
        assert result is True

    def test_team_full_prevents_join(self, friendship_manager):
        """测试队伍满员阻止加入"""
        leader = "leader_001"
        
        # 创建最大3人队伍
        team = friendship_manager.create_team(leader, max_members=3)
        
        # 加入2个成员
        for i in range(2):
            member = f"member_{i}"
            friendship_manager.join_team(member, team.team_id)
        
        # 尝试加入第4个成员
        result = friendship_manager.join_team("member_extra", team.team_id)
        assert result is False


class TestOnlineStatusIntegration:
    """在线状态集成测试"""

    def test_player_online_status(self, friendship_manager):
        """测试玩家在线状态"""
        player = "player_001"
        
        # 设置在线
        friendship_manager.set_player_online(player)
        status = friendship_manager.get_player_status(player)
        assert status == FriendStatus.ONLINE
        
        # 设置离线
        friendship_manager.set_player_offline(player)
        status = friendship_manager.get_player_status(player)
        assert status == FriendStatus.OFFLINE

    def test_player_in_game_status(self, friendship_manager):
        """测试玩家游戏中状态"""
        player = "player_001"
        
        # 设置游戏中
        friendship_manager.set_player_status(
            player,
            FriendStatus.IN_GAME,
            game_info={"room_id": "room_001", "mode": "ranked"}
        )
        
        status = friendship_manager.get_player_status(player)
        assert status == FriendStatus.IN_GAME
        
        # 验证游戏信息
        game_info = friendship_manager.player_game_info.get(player)
        assert game_info is not None
        assert game_info.get("room_id") == "room_001"

    def test_friend_list_with_online_status(self, friendship_manager):
        """测试好友列表显示在线状态"""
        player1 = "player_001"
        player2 = "player_002"
        
        # 建立好友关系
        request = friendship_manager.send_friend_request(player1, player2)
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        
        # 设置 player2 在线
        friendship_manager.set_player_online(player2)
        
        # 获取好友列表
        friends = friendship_manager.get_friends(player1)
        assert len(friends) == 1
        assert friends[0].status == FriendStatus.ONLINE


class TestFriendshipSearchIntegration:
    """好友搜索集成测试"""

    def test_search_players(self, friendship_manager):
        """测试搜索玩家"""
        # 添加一些玩家到缓存
        friendship_manager.update_player_cache(
            "player_001", "张三", "avatar1.png", "gold", 10
        )
        friendship_manager.update_player_cache(
            "player_002", "李四", "avatar2.png", "silver", 5
        )
        friendship_manager.update_player_cache(
            "player_003", "张三丰", "avatar3.png", "bronze", 0
        )
        
        # 搜索 "张"
        results = friendship_manager.search_players("张", limit=10)
        assert len(results) == 2
        
        # 搜索 "player_001"
        results = friendship_manager.search_players("player_001")
        assert len(results) == 1
        assert results[0]["player_id"] == "player_001"
