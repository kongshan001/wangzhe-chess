"""
王者之奕 - 好友系统测试

测试好友系统的核心功能：
- 好友请求处理
- 好友关系管理
- 黑名单管理
- 私聊消息
- 组队功能
- 在线状态管理
"""

from datetime import datetime, timedelta

import pytest

from src.server.friendship import (
    FriendInfo,
    FriendRelation,
    FriendRequest,
    FriendRequestStatus,
    FriendshipManager,
    FriendStatus,
    PrivateMessage,
    TeamInfo,
    get_friendship_manager,
)


class TestFriendModels:
    """测试好友数据模型"""

    def test_friend_info_creation(self):
        """测试好友信息创建"""
        friend = FriendInfo(
            player_id="player_1",
            nickname="TestPlayer",
            avatar="avatar.png",
            status=FriendStatus.ONLINE,
            tier="gold",
            stars=3,
        )

        assert friend.player_id == "player_1"
        assert friend.nickname == "TestPlayer"
        assert friend.is_online is True
        assert friend.is_in_game is False
        assert friend.display_status == "在线"
        assert friend.display_rank == "gold 3星"

    def test_friend_info_to_dict(self):
        """测试好友信息序列化"""
        friend = FriendInfo(
            player_id="player_1",
            nickname="TestPlayer",
            status=FriendStatus.IN_GAME,
            tier="diamond",
            stars=5,
            in_game_info={"room_id": "room_123"},
        )

        data = friend.to_dict()

        assert data["player_id"] == "player_1"
        assert data["status"] == "in_game"
        assert data["status_text"] == "游戏中"
        assert data["is_online"] is True
        assert data["in_game_info"]["room_id"] == "room_123"

    def test_friend_request_creation(self):
        """测试好友请求创建"""
        request = FriendRequest(
            request_id="req_123",
            from_player_id="player_1",
            to_player_id="player_2",
            message="Hi!",
        )

        assert request.request_id == "req_123"
        assert request.is_pending is True
        assert request.is_expired is False
        assert request.can_accept is True

    def test_friend_request_accept(self):
        """测试接受好友请求"""
        request = FriendRequest(
            request_id="req_123",
            from_player_id="player_1",
            to_player_id="player_2",
        )

        assert request.accept() is True
        assert request.status == FriendRequestStatus.ACCEPTED
        assert request.is_pending is False

    def test_friend_request_reject(self):
        """测试拒绝好友请求"""
        request = FriendRequest(
            request_id="req_123",
            from_player_id="player_1",
            to_player_id="player_2",
        )

        assert request.reject() is True
        assert request.status == FriendRequestStatus.REJECTED

    def test_friend_request_expiry(self):
        """测试好友请求过期"""
        request = FriendRequest(
            request_id="req_123",
            from_player_id="player_1",
            to_player_id="player_2",
            created_at=datetime.now() - timedelta(days=8),
            expires_at=datetime.now() - timedelta(days=1),
        )

        assert request.is_expired is True
        assert request.can_accept is False

    def test_private_message_creation(self):
        """测试私聊消息创建"""
        msg = PrivateMessage(
            message_id="msg_123",
            from_player_id="player_1",
            to_player_id="player_2",
            content="Hello!",
        )

        assert msg.message_id == "msg_123"
        assert msg.is_read is False
        assert msg.message_type == "text"

        msg.mark_read()
        assert msg.is_read is True

    def test_team_info_creation(self):
        """测试队伍创建"""
        team = TeamInfo(
            team_id="team_123",
            leader_id="player_1",
            max_members=3,
        )

        assert team.team_id == "team_123"
        assert team.leader_id == "player_1"
        assert team.is_leader("player_1") is True
        assert team.is_member("player_1") is True
        assert team.member_count == 1
        assert team.is_full is False

    def test_team_add_member(self):
        """测试添加队伍成员"""
        team = TeamInfo(
            team_id="team_123",
            leader_id="player_1",
        )

        assert team.add_member("player_2") is True
        assert team.member_count == 2
        assert team.is_member("player_2") is True

        # 不能重复添加
        assert team.add_member("player_2") is False

    def test_team_remove_member(self):
        """测试移除队伍成员"""
        team = TeamInfo(
            team_id="team_123",
            leader_id="player_1",
            members=["player_1", "player_2"],
        )

        assert team.remove_member("player_2") is True
        assert team.member_count == 1

        # 队长不能离开
        assert team.remove_member("player_1") is False


class TestFriendshipManager:
    """测试好友管理器"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        manager = FriendshipManager()
        manager.update_player_cache("player_1", "Player1", "avatar1.png", "gold", 3)
        manager.update_player_cache("player_2", "Player2", "avatar2.png", "silver", 2)
        manager.update_player_cache("player_3", "Player3", "avatar3.png", "diamond", 5)
        return manager

    def test_send_friend_request(self, manager):
        """测试发送好友请求"""
        request = manager.send_friend_request(
            from_player_id="player_1",
            to_player_id="player_2",
            message="Hi!",
        )

        assert request is not None
        assert request.from_player_id == "player_1"
        assert request.to_player_id == "player_2"
        assert request.message == "Hi!"
        assert request.is_pending is True

    def test_send_friend_request_to_self(self, manager):
        """测试不能添加自己为好友"""
        request = manager.send_friend_request(
            from_player_id="player_1",
            to_player_id="player_1",
        )

        assert request is None

    def test_accept_friend_request(self, manager):
        """测试接受好友请求"""
        # 发送请求
        request = manager.send_friend_request(
            from_player_id="player_1",
            to_player_id="player_2",
        )

        assert request is not None

        # 接受请求
        assert manager.accept_friend_request(request.request_id) is True

        # 检查是否成为好友
        assert manager.is_friend("player_1", "player_2") is True
        assert manager.is_friend("player_2", "player_1") is True

    def test_reject_friend_request(self, manager):
        """测试拒绝好友请求"""
        request = manager.send_friend_request(
            from_player_id="player_1",
            to_player_id="player_2",
        )

        assert manager.reject_friend_request(request.request_id) is True

        # 不应该成为好友
        assert manager.is_friend("player_1", "player_2") is False

    def test_remove_friend(self, manager):
        """测试删除好友"""
        # 先添加好友
        request = manager.send_friend_request("player_1", "player_2")
        manager.accept_friend_request(request.request_id)

        assert manager.is_friend("player_1", "player_2") is True

        # 删除好友
        assert manager.remove_friend("player_1", "player_2") is True
        assert manager.is_friend("player_1", "player_2") is False
        assert manager.is_friend("player_2", "player_1") is False

    def test_block_player(self, manager):
        """测试拉黑玩家"""
        assert manager.block_player("player_1", "player_2") is True

        # 检查是否在黑名单中
        assert manager.is_blocked("player_2", "player_1") is True

        # 被拉黑后不能发送好友请求
        request = manager.send_friend_request("player_2", "player_1")
        assert request is None

    def test_unblock_player(self, manager):
        """测试取消拉黑"""
        manager.block_player("player_1", "player_2")
        assert manager.is_blocked("player_2", "player_1") is True

        manager.unblock_player("player_1", "player_2")
        assert manager.is_blocked("player_2", "player_1") is False

    def test_block_removes_friendship(self, manager):
        """测试拉黑后自动解除好友关系"""
        # 先添加好友
        request = manager.send_friend_request("player_1", "player_2")
        manager.accept_friend_request(request.request_id)
        assert manager.is_friend("player_1", "player_2") is True

        # 拉黑后应该解除好友
        manager.block_player("player_1", "player_2")
        assert manager.is_friend("player_1", "player_2") is False

    def test_private_message(self, manager):
        """测试私聊消息"""
        msg = manager.send_private_message(
            from_player_id="player_1",
            to_player_id="player_2",
            content="Hello!",
        )

        assert msg is not None
        assert msg.from_player_id == "player_1"
        assert msg.to_player_id == "player_2"
        assert msg.content == "Hello!"
        assert msg.is_read is False

    def test_private_message_blocked(self, manager):
        """测试被拉黑后不能发送私聊"""
        manager.block_player("player_2", "player_1")

        msg = manager.send_private_message(
            from_player_id="player_1",
            to_player_id="player_2",
            content="Hello!",
        )

        assert msg is None

    def test_get_private_messages(self, manager):
        """测试获取聊天记录"""
        # 发送多条消息
        manager.send_private_message("player_1", "player_2", "Hello!")
        manager.send_private_message("player_2", "player_1", "Hi there!")
        manager.send_private_message("player_1", "player_2", "How are you?")

        messages = manager.get_private_messages("player_1", "player_2")

        assert len(messages) == 3

    def test_mark_messages_read(self, manager):
        """测试标记消息已读"""
        manager.send_private_message("player_1", "player_2", "Hello!")
        manager.send_private_message("player_1", "player_2", "Hi!")

        count = manager.mark_messages_read("player_2", "player_1")
        assert count == 2

    def test_create_team(self, manager):
        """测试创建队伍"""
        team = manager.create_team("player_1")

        assert team is not None
        assert team.leader_id == "player_1"
        assert team.is_member("player_1") is True
        assert team.member_count == 1

    def test_join_team(self, manager):
        """测试加入队伍"""
        team = manager.create_team("player_1")

        assert manager.join_team("player_2", team.team_id) is True
        assert team.member_count == 2
        assert team.is_member("player_2") is True

    def test_leave_team(self, manager):
        """测试离开队伍"""
        team = manager.create_team("player_1")
        manager.join_team("player_2", team.team_id)

        assert manager.leave_team("player_2") is True
        assert team.is_member("player_2") is False

    def test_leader_cannot_leave(self, manager):
        """测试队长不能离开队伍"""
        team = manager.create_team("player_1")

        # 队长离开会解散队伍
        result = manager.leave_team("player_1")
        assert result is True
        assert manager.get_team(team.team_id) is None

    def test_kick_team_member(self, manager):
        """测试踢出队伍成员"""
        team = manager.create_team("player_1")
        manager.join_team("player_2", team.team_id)

        assert manager.kick_from_team("player_1", "player_2") is True
        assert team.is_member("player_2") is False

    def test_online_status(self, manager):
        """测试在线状态"""
        manager.set_player_online("player_1")
        assert manager.get_player_status("player_1") == FriendStatus.ONLINE

        manager.set_player_status("player_1", FriendStatus.IN_GAME, {"room_id": "room_123"})
        assert manager.get_player_status("player_1") == FriendStatus.IN_GAME

        manager.set_player_offline("player_1")
        assert manager.get_player_status("player_1") == FriendStatus.OFFLINE

    def test_get_friends(self, manager):
        """测试获取好友列表"""
        # 添加好友
        request = manager.send_friend_request("player_1", "player_2")
        manager.accept_friend_request(request.request_id)

        friends = manager.get_friends("player_1")
        assert len(friends) == 1
        assert friends[0].player_id == "player_2"

    def test_search_players(self, manager):
        """测试搜索玩家"""
        results = manager.search_players("Player")
        assert len(results) >= 1

        results = manager.search_players("Player1")
        assert len(results) == 1
        assert results[0]["player_id"] == "player_1"

    def test_get_pending_requests(self, manager):
        """测试获取待处理请求"""
        manager.send_friend_request("player_1", "player_2")
        manager.send_friend_request("player_3", "player_2")

        pending = manager.get_pending_requests("player_2")
        assert len(pending) == 2

    def test_get_sent_requests(self, manager):
        """测试获取已发送请求"""
        manager.send_friend_request("player_1", "player_2")
        manager.send_friend_request("player_1", "player_3")

        sent = manager.get_sent_requests("player_1")
        assert len(sent) == 2


class TestFriendStatus:
    """测试好友状态"""

    def test_status_enum_values(self):
        """测试状态枚举值"""
        assert FriendStatus.ONLINE.value == "online"
        assert FriendStatus.OFFLINE.value == "offline"
        assert FriendStatus.IN_GAME.value == "in_game"
        assert FriendStatus.IN_QUEUE.value == "in_queue"
        assert FriendStatus.IN_ROOM.value == "in_room"

    def test_relation_enum_values(self):
        """测试关系枚举值"""
        assert FriendRelation.FRIEND.value == "friend"
        assert FriendRelation.BLOCKED.value == "blocked"
        assert FriendRelation.BLOCKED_BY.value == "blocked_by"


class TestFriendshipManagerSingleton:
    """测试好友管理器单例"""

    def test_get_singleton(self):
        """测试获取单例"""
        manager1 = get_friendship_manager()
        manager2 = get_friendship_manager()

        assert manager1 is manager2


class TestFriendRequestScenarios:
    """测试好友请求场景"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return FriendshipManager()

    def test_duplicate_friend_request(self, manager):
        """测试重复发送好友请求"""
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")

        # 发送第一个请求
        request1 = manager.send_friend_request("p1", "p2")
        assert request1 is not None

        # 重复发送应该返回同一个请求
        request2 = manager.send_friend_request("p1", "p2")
        assert request2.request_id == request1.request_id

    def test_already_friends_request(self, manager):
        """测试已为好友时发送请求"""
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")

        # 添加好友
        request = manager.send_friend_request("p1", "p2")
        manager.accept_friend_request(request.request_id)

        # 再次发送请求应该失败
        new_request = manager.send_friend_request("p1", "p2")
        assert new_request is None

    def test_cancel_friend_request(self, manager):
        """测试取消好友请求"""
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")

        request = manager.send_friend_request("p1", "p2")
        assert request is not None

        # 取消请求
        assert manager.cancel_friend_request(request.request_id) is True

        # 再次检查待处理请求
        pending = manager.get_pending_requests("p2")
        assert len(pending) == 0


class TestTeamScenarios:
    """测试组队场景"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        manager = FriendshipManager()
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")
        manager.update_player_cache("p3", "Player3")
        return manager

    def test_team_full(self, manager):
        """测试队伍已满"""
        team = manager.create_team("p1")
        manager.join_team("p2", team.team_id)
        manager.join_team("p3", team.team_id)

        assert team.is_full is True

        # 添加第四个成员应该失败
        manager.update_player_cache("p4", "Player4")
        assert manager.join_team("p4", team.team_id) is False

    def test_player_already_in_team(self, manager):
        """测试玩家已在队伍中"""
        team1 = manager.create_team("p1")

        # 创建另一个队伍时应该自动离开旧队伍
        team2 = manager.create_team("p1")

        assert manager.get_team(team1.team_id) is None
        assert manager.get_player_team("p1").team_id == team2.team_id


class TestPrivateMessageScenarios:
    """测试私聊场景"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        manager = FriendshipManager()
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")
        return manager

    def test_message_order(self, manager):
        """测试消息顺序"""
        manager.send_private_message("p1", "p2", "msg1")
        manager.send_private_message("p1", "p2", "msg2")
        manager.send_private_message("p1", "p2", "msg3")

        messages = manager.get_private_messages("p1", "p2")

        assert len(messages) == 3
        assert messages[0].content == "msg1"
        assert messages[1].content == "msg2"
        assert messages[2].content == "msg3"

    def test_unread_count(self, manager):
        """测试未读消息计数"""
        manager.send_private_message("p1", "p2", "msg1")
        manager.send_private_message("p1", "p2", "msg2")
        manager.send_private_message("p2", "p1", "msg3")

        # p2有2条未读消息
        assert manager.get_unread_count("p2") == 2

        # p1有1条未读消息
        assert manager.get_unread_count("p1") == 1


# 异步测试（如果需要）
@pytest.mark.asyncio
class TestAsyncFriendship:
    """异步好友系统测试"""

    async def test_async_operations(self):
        """测试异步操作"""
        manager = FriendshipManager()
        manager.update_player_cache("p1", "Player1")
        manager.update_player_cache("p2", "Player2")

        # 简单的异步测试
        request = manager.send_friend_request("p1", "p2")
        assert request is not None

        result = manager.accept_friend_request(request.request_id)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
