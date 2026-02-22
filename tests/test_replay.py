"""
王者之奕 - 回放系统测试

本模块测试回放系统的核心功能：
- 回放数据模型
- 回放管理器
- WebSocket 消息处理
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.server.replay.models import (
    PlaySpeed,
    PlayerSnapshot,
    Replay,
    ReplayFrame,
    ReplayListItem,
    ReplayMetadata,
    ReplaySession,
    ReplayStatus,
)
from src.server.replay.manager import (
    MAX_REPLAYS_PER_PLAYER,
    ReplayManager,
)


# ============================================================================
# 数据模型测试
# ============================================================================

class TestPlayerSnapshot:
    """测试 PlayerSnapshot 数据模型"""
    
    def test_create_player_snapshot(self):
        """测试创建玩家快照"""
        snapshot = PlayerSnapshot(
            player_id=1,
            nickname="测试玩家",
            hp=100,
            gold=50,
            level=5,
        )
        
        assert snapshot.player_id == 1
        assert snapshot.nickname == "测试玩家"
        assert snapshot.hp == 100
        assert snapshot.gold == 50
        assert snapshot.level == 5
    
    def test_player_snapshot_to_dict(self):
        """测试玩家快照转字典"""
        snapshot = PlayerSnapshot(
            player_id=1,
            nickname="测试玩家",
            hp=80,
            gold=30,
            board=[{"hero_id": "hero_1"}],
        )
        
        data = snapshot.to_dict()
        
        assert data["player_id"] == 1
        assert data["nickname"] == "测试玩家"
        assert data["hp"] == 80
        assert data["board"] == [{"hero_id": "hero_1"}]
    
    def test_player_snapshot_from_dict(self):
        """测试从字典创建玩家快照"""
        data = {
            "player_id": 2,
            "nickname": "玩家2",
            "hp": 50,
            "gold": 100,
            "level": 7,
            "exp": 20,
        }
        
        snapshot = PlayerSnapshot.from_dict(data)
        
        assert snapshot.player_id == 2
        assert snapshot.nickname == "玩家2"
        assert snapshot.hp == 50
        assert snapshot.gold == 100


class TestReplayFrame:
    """测试 ReplayFrame 数据模型"""
    
    def test_create_replay_frame(self):
        """测试创建回放帧"""
        frame = ReplayFrame(
            round_num=1,
            phase="preparation",
        )
        
        assert frame.round_num == 1
        assert frame.phase == "preparation"
        assert frame.player_snapshots == {}
    
    def test_replay_frame_with_snapshots(self):
        """测试带玩家快照的回放帧"""
        snapshot = PlayerSnapshot(
            player_id=1,
            nickname="玩家1",
        )
        
        frame = ReplayFrame(
            round_num=5,
            phase="battle",
            player_snapshots={1: snapshot},
        )
        
        assert len(frame.player_snapshots) == 1
        assert frame.player_snapshots[1].nickname == "玩家1"
    
    def test_replay_frame_to_dict_and_from_dict(self):
        """测试回放帧序列化和反序列化"""
        snapshot = PlayerSnapshot(
            player_id=1,
            nickname="玩家1",
            hp=100,
        )
        
        frame = ReplayFrame(
            round_num=3,
            phase="preparation",
            player_snapshots={1: snapshot},
            events=[{"type": "buy", "hero_id": "hero_1"}],
        )
        
        # 序列化
        data = frame.to_dict()
        
        # 反序列化
        restored = ReplayFrame.from_dict(data)
        
        assert restored.round_num == 3
        assert restored.phase == "preparation"
        assert len(restored.player_snapshots) == 1
        assert len(restored.events) == 1


class TestReplayMetadata:
    """测试 ReplayMetadata 数据模型"""
    
    def test_create_metadata(self):
        """测试创建回放元数据"""
        metadata = ReplayMetadata(
            match_id="match_123",
            player_id=1,
            player_nickname="测试玩家",
            final_rank=1,
            total_rounds=30,
            duration_seconds=1800,
        )
        
        assert metadata.match_id == "match_123"
        assert metadata.player_id == 1
        assert metadata.final_rank == 1
        assert metadata.total_rounds == 30
        assert metadata.duration_seconds == 1800
    
    def test_metadata_to_dict_and_from_dict(self):
        """测试元数据序列化和反序列化"""
        metadata = ReplayMetadata(
            match_id="match_456",
            player_id=2,
            player_nickname="玩家2",
            final_rank=3,
            total_rounds=25,
            duration_seconds=1500,
            tags=["前四"],
        )
        
        data = metadata.to_dict()
        restored = ReplayMetadata.from_dict(data)
        
        assert restored.match_id == "match_456"
        assert restored.final_rank == 3
        assert "前四" in restored.tags


class TestReplay:
    """测试 Replay 数据模型"""
    
    def test_create_replay(self):
        """测试创建回放"""
        replay = Replay()
        
        assert replay.replay_id is not None
        assert replay.frames == []
    
    def test_replay_with_data(self):
        """测试带数据的回放"""
        metadata = ReplayMetadata(
            match_id="match_1",
            player_id=1,
            player_nickname="玩家1",
        )
        
        frame = ReplayFrame(round_num=1, phase="preparation")
        
        replay = Replay(
            metadata=metadata,
            frames=[frame],
        )
        
        assert replay.metadata.player_id == 1
        assert len(replay.frames) == 1
    
    def test_replay_get_frame(self):
        """测试获取指定帧"""
        frame1 = ReplayFrame(round_num=1, phase="preparation")
        frame2 = ReplayFrame(round_num=2, phase="battle")
        
        replay = Replay(frames=[frame1, frame2])
        
        assert replay.get_frame(1) == frame1
        assert replay.get_frame(2) == frame2
        assert replay.get_frame(3) is None
    
    def test_replay_to_dict_and_from_dict(self):
        """测试回放序列化和反序列化"""
        metadata = ReplayMetadata(
            match_id="match_test",
            player_id=1,
            player_nickname="测试",
            final_rank=1,
        )
        
        snapshot = PlayerSnapshot(player_id=1, nickname="测试")
        frame = ReplayFrame(
            round_num=1,
            phase="preparation",
            player_snapshots={1: snapshot},
        )
        
        replay = Replay(
            metadata=metadata,
            frames=[frame],
            final_rankings=[{"player_id": 1, "rank": 1}],
        )
        
        data = replay.to_dict()
        restored = Replay.from_dict(data)
        
        assert restored.metadata.match_id == "match_test"
        assert len(restored.frames) == 1
        assert len(restored.final_rankings) == 1
    
    def test_compute_data_hash(self):
        """测试计算数据哈希"""
        replay = Replay()
        
        hash1 = replay.compute_data_hash()
        hash2 = replay.compute_data_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 16


class TestReplaySession:
    """测试 ReplaySession 数据模型"""
    
    def test_create_session(self):
        """测试创建播放会话"""
        session = ReplaySession(
            session_id="session_1",
            replay_id="replay_1",
        )
        
        assert session.session_id == "session_1"
        assert session.replay_id == "replay_1"
        assert session.status == ReplayStatus.IDLE
    
    def test_session_play_pause_stop(self):
        """测试会话播放控制"""
        session = ReplaySession(
            session_id="session_1",
            replay_id="replay_1",
        )
        
        # 播放
        session.play()
        assert session.status == ReplayStatus.PLAYING
        
        # 暂停
        session.pause()
        assert session.status == ReplayStatus.PAUSED
        
        # 停止
        session.stop()
        assert session.status == ReplayStatus.ENDED
        assert session.current_frame_index == 0
    
    def test_session_set_speed(self):
        """测试设置播放速度"""
        session = ReplaySession(
            session_id="session_1",
            replay_id="replay_1",
        )
        
        session.set_speed(PlaySpeed.FAST)
        assert session.speed == PlaySpeed.FAST
    
    def test_session_seek(self):
        """测试跳转"""
        session = ReplaySession(
            session_id="session_1",
            replay_id="replay_1",
        )
        
        session.seek_to_round(5, 10)
        assert session.current_round == 5
        assert session.current_frame_index == 4
        
        # 跳转超出范围
        session.seek_to_round(20, 10)
        assert session.current_frame_index == 9  # 最大索引


class TestPlaySpeed:
    """测试播放速度枚举"""
    
    def test_play_speed_values(self):
        """测试播放速度值"""
        assert PlaySpeed.SLOW.value == 0.5
        assert PlaySpeed.NORMAL.value == 1.0
        assert PlaySpeed.FAST.value == 2.0
        assert PlaySpeed.VERY_FAST.value == 4.0


class TestReplayListItem:
    """测试回放列表项"""
    
    def test_create_list_item(self):
        """测试创建列表项"""
        item = ReplayListItem(
            replay_id="replay_1",
            match_id="match_1",
            player_nickname="玩家",
            final_rank=1,
            total_rounds=30,
            duration_seconds=1800,
        )
        
        assert item.replay_id == "replay_1"
        assert item.final_rank == 1
    
    def test_list_item_to_dict(self):
        """测试列表项转字典"""
        item = ReplayListItem(
            replay_id="replay_1",
            match_id="match_1",
            player_nickname="玩家",
            duration_seconds=1800,
        )
        
        data = item.to_dict()
        
        assert data["duration_minutes"] == 30.0
    
    def test_list_item_from_replay(self):
        """测试从回放创建列表项"""
        metadata = ReplayMetadata(
            match_id="match_1",
            player_id=1,
            player_nickname="玩家",
            final_rank=2,
            total_rounds=25,
            duration_seconds=1500,
        )
        
        replay = Replay(metadata=metadata)
        item = ReplayListItem.from_replay(replay)
        
        assert item.match_id == "match_1"
        assert item.final_rank == 2
        assert item.total_rounds == 25


# ============================================================================
# 管理器测试
# ============================================================================

class TestReplayManager:
    """测试 ReplayManager"""
    
    def test_create_manager(self):
        """测试创建管理器"""
        manager = ReplayManager()
        
        assert manager is not None
        assert manager._replay_cache == {}
        assert manager._play_sessions == {}
    
    def test_generate_unique_share_code(self):
        """测试生成唯一分享码"""
        manager = ReplayManager()
        
        codes = set()
        for _ in range(100):
            code = manager._generate_unique_share_code()
            assert code not in codes
            codes.add(code)
            assert len(code) == 8
    
    def test_create_play_session(self):
        """测试创建播放会话"""
        manager = ReplayManager()
        
        session = manager.create_play_session("replay_1")
        
        assert session is not None
        assert session.replay_id == "replay_1"
        assert manager.get_play_session(session.session_id) == session
    
    def test_play_control(self):
        """测试播放控制"""
        manager = ReplayManager()
        session = manager.create_play_session("replay_1")
        
        # 播放
        manager.play_replay(session.session_id)
        assert session.status == ReplayStatus.PLAYING
        
        # 暂停
        manager.pause_replay(session.session_id)
        assert session.status == ReplayStatus.PAUSED
        
        # 设置速度
        manager.set_play_speed(session.session_id, PlaySpeed.FAST)
        assert session.speed == PlaySpeed.FAST
    
    def test_seek_to_round(self):
        """测试跳转到回合"""
        manager = ReplayManager()
        session = manager.create_play_session("replay_1")
        
        manager.seek_to_round(session.session_id, 5, 10)
        
        assert session.current_round == 5
        assert session.current_frame_index == 4
    
    def test_close_play_session(self):
        """测试关闭播放会话"""
        manager = ReplayManager()
        session = manager.create_play_session("replay_1")
        
        result = manager.close_play_session(session.session_id)
        
        assert result is True
        assert manager.get_play_session(session.session_id) is None
    
    def test_advance_frame(self):
        """测试前进帧"""
        manager = ReplayManager()
        session = manager.create_play_session("replay_1")
        
        # 前进
        result = manager.advance_frame(session.session_id, 10)
        
        assert session.current_frame_index == 1
        
        # 到达末尾
        session.current_frame_index = 9
        result = manager.advance_frame(session.session_id, 10)
        
        assert result is None
        assert session.status == ReplayStatus.ENDED
    
    @pytest.mark.asyncio
    async def test_save_replay_with_mock_db(self):
        """测试保存回放（模拟数据库）"""
        manager = ReplayManager()
        
        # 模拟数据库
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        manager._database = mock_db
        
        # 模拟获取回放数量
        with patch.object(manager, '_get_player_replay_count', return_value=5):
            with patch.object(manager, '_save_replay_to_db', return_value=True):
                match_data = {
                    "match_id": "match_1",
                    "player_nickname": "测试玩家",
                    "final_rank": 1,
                    "total_rounds": 30,
                    "duration_seconds": 1800,
                    "frames": [],
                }
                
                replay = await manager.save_replay(1, match_data)
                
                assert replay is not None
                assert replay.metadata.player_nickname == "测试玩家"


# ============================================================================
# 常量测试
# ============================================================================

class TestConstants:
    """测试常量"""
    
    def test_max_replays_per_player(self):
        """测试最大回放数量"""
        assert MAX_REPLAYS_PER_PLAYER == 20


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
