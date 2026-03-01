"""
王者之奕 - 表情系统测试

测试表情系统的功能：
- 表情管理器
- 表情发送/接收
- 表情解锁
- 快捷键设置
- 表情历史
"""

from datetime import datetime

import pytest

from src.server.emote.manager import (
    EmoteManager,
    get_emote_manager,
)
from src.server.emote.models import (
    Emote,
    EmoteCategory,
    EmoteData,
    EmoteHistory,
    EmoteType,
    PlayerEmote,
)


class TestEmoteModels:
    """表情数据模型测试"""

    def test_emote_creation(self):
        """测试表情创建"""
        emote = Emote(
            emote_id="test_emote",
            name="测试表情",
            description="这是一个测试表情",
            category=EmoteCategory.DEFAULT,
            emote_type=EmoteType.STATIC,
            asset_url="/assets/emotes/test.png",
            is_free=True,
            sort_order=1,
        )

        assert emote.emote_id == "test_emote"
        assert emote.name == "测试表情"
        assert emote.category == EmoteCategory.DEFAULT
        assert emote.emote_type == EmoteType.STATIC
        assert emote.is_free is True

    def test_emote_to_dict(self):
        """测试表情转换为字典"""
        emote = Emote(
            emote_id="test_emote",
            name="测试表情",
            category=EmoteCategory.DEFAULT,
            emote_type=EmoteType.ANIMATED,
            asset_url="/assets/emotes/test.gif",
            is_free=True,
        )

        data = emote.to_dict()

        assert data["emote_id"] == "test_emote"
        assert data["name"] == "测试表情"
        assert data["category"] == "default"
        assert data["emote_type"] == "animated"
        assert data["is_free"] is True

    def test_emote_from_dict(self):
        """测试从字典创建表情"""
        data = {
            "emote_id": "test_emote",
            "name": "测试表情",
            "description": "测试描述",
            "category": "premium",
            "emote_type": "sound",
            "asset_url": "/assets/emotes/test.gif",
            "sound_url": "/assets/sounds/test.mp3",
            "is_free": False,
            "sort_order": 10,
        }

        emote = Emote.from_dict(data)

        assert emote.emote_id == "test_emote"
        assert emote.name == "测试表情"
        assert emote.category == EmoteCategory.PREMIUM
        assert emote.emote_type == EmoteType.SOUND
        assert emote.sound_url == "/assets/sounds/test.mp3"
        assert emote.is_free is False

    def test_emote_unlock_check_free(self):
        """测试免费表情解锁检查"""
        emote = Emote(
            emote_id="free_emote",
            name="免费表情",
            is_free=True,
        )

        # 免费表情应该总是解锁
        assert emote.check_unlock({}) is True
        assert emote.check_unlock({"total_wins": 0}) is True

    def test_emote_unlock_check_wins(self):
        """测试胜利次数解锁条件"""
        emote = Emote(
            emote_id="victory_emote",
            name="胜利表情",
            is_free=False,
            unlock_condition={
                "type": "wins",
                "count": 10,
            },
        )

        # 不满足条件
        assert emote.check_unlock({"total_wins": 5}) is False

        # 刚好满足
        assert emote.check_unlock({"total_wins": 10}) is True

        # 超过条件
        assert emote.check_unlock({"total_wins": 20}) is True

    def test_emote_unlock_check_rank(self):
        """测试段位解锁条件"""
        emote = Emote(
            emote_id="diamond_emote",
            name="钻石表情",
            is_free=False,
            unlock_condition={
                "type": "rank",
                "tier": "diamond",
            },
        )

        # 低段位不满足
        assert emote.check_unlock({"tier": "gold"}) is False

        # 满足条件
        assert emote.check_unlock({"tier": "diamond"}) is True

        # 更高段位
        assert emote.check_unlock({"tier": "master"}) is True

    def test_emote_unlock_check_achievement(self):
        """测试成就解锁条件"""
        emote = Emote(
            emote_id="special_emote",
            name="特殊表情",
            is_free=False,
            unlock_condition={
                "type": "achievement",
                "achievement_id": "dragon_master",
            },
        )

        # 未达成成就
        assert emote.check_unlock({"achievements": []}) is False

        # 已达成成就
        assert emote.check_unlock({"achievements": ["dragon_master"]}) is True

    def test_player_emote_creation(self):
        """测试玩家表情创建"""
        player_emote = PlayerEmote(
            player_id="player1",
            emote_id="test_emote",
            hotkey="1",
            use_count=5,
        )

        assert player_emote.player_id == "player1"
        assert player_emote.emote_id == "test_emote"
        assert player_emote.hotkey == "1"
        assert player_emote.use_count == 5
        assert player_emote.unlocked_at is not None

    def test_emote_history_creation(self):
        """测试表情历史创建"""
        history = EmoteHistory(
            history_id="eh_123",
            room_id="room1",
            from_player_id="player1",
            emote_id="hello",
            to_player_id="player2",
            round_number=5,
        )

        assert history.history_id == "eh_123"
        assert history.room_id == "room1"
        assert history.from_player_id == "player1"
        assert history.emote_id == "hello"
        assert history.to_player_id == "player2"
        assert history.round_number == 5
        assert history.created_at is not None


class TestEmoteManager:
    """表情管理器测试"""

    @pytest.fixture
    def emote_manager(self):
        """创建表情管理器"""
        return EmoteManager()

    def test_manager_initialization(self, emote_manager):
        """测试管理器初始化"""
        assert emote_manager is not None
        assert len(emote_manager.emotes) > 0
        # 应该有默认表情
        assert "hello" in emote_manager.emotes

    def test_get_all_emotes(self, emote_manager):
        """测试获取所有表情"""
        emotes = emote_manager.get_all_emotes()

        assert len(emotes) > 0
        # 应该按排序顺序返回
        for i in range(len(emotes) - 1):
            assert emotes[i].sort_order <= emotes[i + 1].sort_order

    def test_get_emotes_by_category(self, emote_manager):
        """测试按分类获取表情"""
        default_emotes = emote_manager.get_emotes_by_category(EmoteCategory.DEFAULT)

        assert len(default_emotes) > 0
        for emote in default_emotes:
            assert emote.category == EmoteCategory.DEFAULT

    def test_get_emote(self, emote_manager):
        """测试获取单个表情"""
        emote = emote_manager.get_emote("hello")

        assert emote is not None
        assert emote.emote_id == "hello"
        assert emote.name == "你好"

        # 不存在的表情
        assert emote_manager.get_emote("nonexistent") is None

    def test_unlock_emote(self, emote_manager):
        """测试解锁表情"""
        player_id = "player1"
        emote_id = "hello"

        # 解锁免费表情
        result = emote_manager.unlock_emote(player_id, emote_id)

        assert result is not None
        assert result.player_id == player_id
        assert result.emote_id == emote_id

        # 检查是否已拥有
        assert emote_manager.has_emote(player_id, emote_id)

    def test_has_emote(self, emote_manager):
        """测试检查玩家是否拥有表情"""
        player_id = "player1"
        emote_id = "hello"

        # 未解锁
        assert emote_manager.has_emote(player_id, emote_id) is False

        # 解锁后
        emote_manager.unlock_emote(player_id, emote_id)
        assert emote_manager.has_emote(player_id, emote_id) is True

    def test_get_unlocked_emotes(self, emote_manager):
        """测试获取已解锁表情"""
        player_id = "player1"

        # 免费表情应该都是解锁的
        unlocked = emote_manager.get_unlocked_emotes(player_id)

        # 所有免费表情都应该在列表中
        free_emotes = [e for e in emote_manager.emotes.values() if e.is_free]
        assert len(unlocked) >= len(free_emotes)

    def test_can_send_emote_cooldown(self, emote_manager):
        """测试表情发送冷却"""
        player_id = "player1"

        # 初始应该可以发送
        assert emote_manager.can_send_emote(player_id) is True

        # 设置冷却
        emote_manager._cooldowns[player_id] = datetime.now()

        # 应该在冷却中
        assert emote_manager.can_send_emote(player_id) is False

    def test_get_cooldown_remaining(self, emote_manager):
        """测试获取剩余冷却时间"""
        player_id = "player1"

        # 无冷却
        assert emote_manager.get_cooldown_remaining(player_id) == 0.0

        # 设置冷却
        emote_manager._cooldowns[player_id] = datetime.now()
        remaining = emote_manager.get_cooldown_remaining(player_id)

        # 应该有剩余时间
        assert remaining > 0
        assert remaining <= emote_manager.emote_cooldown_seconds

    @pytest.mark.asyncio
    async def test_send_emote(self, emote_manager):
        """测试发送表情"""
        room_id = "room1"
        from_player_id = "player1"
        emote_id = "hello"

        # 先解锁表情
        emote_manager.unlock_emote(from_player_id, emote_id)

        # 发送表情
        history = await emote_manager.send_emote(
            room_id=room_id,
            from_player_id=from_player_id,
            emote_id=emote_id,
            to_player_id=None,  # 发送给所有人
            round_number=1,
            from_nickname="测试玩家",
        )

        assert history is not None
        assert history.room_id == room_id
        assert history.from_player_id == from_player_id
        assert history.emote_id == emote_id
        assert history.to_player_id is None

        # 检查历史记录
        room_history = emote_manager.get_room_emote_history(room_id)
        assert len(room_history) == 1
        assert room_history[0].emote_id == emote_id

    @pytest.mark.asyncio
    async def test_send_emote_to_specific_player(self, emote_manager):
        """测试发送表情给特定玩家"""
        room_id = "room1"
        from_player_id = "player1"
        to_player_id = "player2"
        emote_id = "hello"

        # 先解锁表情
        emote_manager.unlock_emote(from_player_id, emote_id)

        # 发送表情
        history = await emote_manager.send_emote(
            room_id=room_id,
            from_player_id=from_player_id,
            emote_id=emote_id,
            to_player_id=to_player_id,
            round_number=1,
            from_nickname="测试玩家",
        )

        assert history is not None
        assert history.to_player_id == to_player_id

    @pytest.mark.asyncio
    async def test_send_emote_cooldown_enforced(self, emote_manager):
        """测试表情发送冷却限制"""
        player_id = "player1"
        emote_id = "hello"

        # 先解锁表情
        emote_manager.unlock_emote(player_id, emote_id)

        # 发送第一次
        history1 = await emote_manager.send_emote(
            room_id="room1",
            from_player_id=player_id,
            emote_id=emote_id,
        )
        assert history1 is not None

        # 立即发送第二次应该被拒绝（冷却中）
        history2 = await emote_manager.send_emote(
            room_id="room1",
            from_player_id=player_id,
            emote_id=emote_id,
        )
        assert history2 is None

    def test_set_emote_hotkey(self, emote_manager):
        """测试设置表情快捷键"""
        player_id = "player1"
        emote_id = "hello"
        hotkey = "1"

        # 先解锁表情
        emote_manager.unlock_emote(player_id, emote_id)

        # 设置快捷键
        result = emote_manager.set_emote_hotkey(player_id, emote_id, hotkey)

        assert result is True

        # 检查快捷键映射
        hotkeys = emote_manager.get_player_hotkeys(player_id)
        assert hotkeys.get(hotkey) == emote_id

        # 通过快捷键获取表情
        emote = emote_manager.get_emote_by_hotkey(player_id, hotkey)
        assert emote is not None
        assert emote.emote_id == emote_id

    def test_remove_emote_hotkey(self, emote_manager):
        """测试移除表情快捷键"""
        player_id = "player1"
        emote_id = "hello"
        hotkey = "1"

        # 先设置快捷键
        emote_manager.unlock_emote(player_id, emote_id)
        emote_manager.set_emote_hotkey(player_id, emote_id, hotkey)

        # 移除快捷键
        result = emote_manager.remove_emote_hotkey(player_id, emote_id)

        assert result is True

        # 检查快捷键已移除
        hotkeys = emote_manager.get_player_hotkeys(player_id)
        assert hotkey not in hotkeys

    def test_emote_hotkey_override(self, emote_manager):
        """测试表情快捷键覆盖"""
        player_id = "player1"
        emote_id1 = "hello"
        emote_id2 = "good_game"
        hotkey = "1"

        # 解锁两个表情
        emote_manager.unlock_emote(player_id, emote_id1)
        emote_manager.unlock_emote(player_id, emote_id2)

        # 设置第一个表情的快捷键
        emote_manager.set_emote_hotkey(player_id, emote_id1, hotkey)

        # 用同一个快捷键设置第二个表情（应该覆盖）
        emote_manager.set_emote_hotkey(player_id, emote_id2, hotkey)

        # 检查快捷键现在是第二个表情
        emote = emote_manager.get_emote_by_hotkey(player_id, hotkey)
        assert emote.emote_id == emote_id2

    def test_get_room_emote_history(self, emote_manager):
        """测试获取房间表情历史"""
        room_id = "room1"

        # 初始为空
        history = emote_manager.get_room_emote_history(room_id)
        assert len(history) == 0

    def test_clear_room_history(self, emote_manager):
        """测试清除房间历史"""
        room_id = "room1"

        # 添加一些历史记录
        emote_manager.emote_history[room_id] = [
            EmoteHistory(
                history_id="eh_1",
                room_id=room_id,
                from_player_id="player1",
                emote_id="hello",
            )
        ]

        # 清除
        count = emote_manager.clear_room_history(room_id)

        assert count == 1
        assert room_id not in emote_manager.emote_history


class TestEmoteData:
    """表情数据工具类测试"""

    def test_from_emote(self):
        """测试从表情创建消息数据"""
        emote = Emote(
            emote_id="test",
            name="测试",
            asset_url="/test.png",
            emote_type=EmoteType.STATIC,
        )

        data = EmoteData.from_emote(
            emote=emote,
            from_player_id="player1",
            from_nickname="测试玩家",
            to_player_id="player2",
            room_id="room1",
            round_number=5,
        )

        assert data["emote_id"] == "test"
        assert data["name"] == "测试"
        assert data["from_player_id"] == "player1"
        assert data["from_nickname"] == "测试玩家"
        assert data["to_player_id"] == "player2"
        assert data["room_id"] == "room1"
        assert data["round_number"] == 5
        assert "timestamp" in data

    def test_from_history(self):
        """测试从历史记录创建数据"""
        emote = Emote(
            emote_id="test",
            name="测试",
            asset_url="/test.png",
        )

        history = EmoteHistory(
            history_id="eh_1",
            room_id="room1",
            from_player_id="player1",
            emote_id="test",
            to_player_id="player2",
            round_number=5,
        )

        data = EmoteData.from_history(
            history=history,
            emote=emote,
            from_nickname="发送者",
            to_nickname="接收者",
        )

        assert data["history_id"] == "eh_1"
        assert data["emote_id"] == "test"
        assert data["from_nickname"] == "发送者"
        assert data["to_nickname"] == "接收者"


class TestEmoteManagerSingleton:
    """表情管理器单例测试"""

    def test_get_emote_manager_singleton(self):
        """测试获取表情管理器单例"""
        manager1 = get_emote_manager()
        manager2 = get_emote_manager()

        assert manager1 is manager2


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
