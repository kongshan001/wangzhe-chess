"""
王者之奕 - 回放管理器

本模块提供回放系统的管理功能：
- 保存回放
- 获取回放列表
- 加载回放
- 播放回放控制
- 跳转到回合
- 倍速播放
- 删除回放
- 生成分享码
- 导入回放

与数据库层集成实现持久化。
"""

from __future__ import annotations

import json
import logging
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    PlaySpeed,
    PlayerSnapshot,
    Replay,
    ReplayFrame,
    ReplayListItem,
    ReplayMetadata,
    ReplaySession,
    ReplayStatus,
)

if TYPE_CHECKING:
    from ..db.database import Database

logger = logging.getLogger(__name__)

# 最大保存回放数量
MAX_REPLAYS_PER_PLAYER = 20

# 分享码长度
SHARE_CODE_LENGTH = 8


class ReplayManager:
    """
    回放管理器
    
    提供回放系统的核心功能。
    
    使用方式:
        manager = ReplayManager(database)
        
        # 保存回放
        replay = manager.save_replay(player_id, match_data)
        
        # 获取回放列表
        replays = manager.get_replay_list(player_id)
        
        # 加载回放
        replay = manager.load_replay(replay_id)
        
        # 创建播放会话
        session = manager.create_play_session(replay_id)
    """
    
    def __init__(self, database: Optional["Database"] = None) -> None:
        """
        初始化回放管理器
        
        Args:
            database: 数据库实例
        """
        self._database = database
        # 内存缓存：replay_id -> Replay
        self._replay_cache: Dict[str, Replay] = {}
        # 播放会话：session_id -> ReplaySession
        self._play_sessions: Dict[str, ReplaySession] = {}
        # 分享码映射：share_code -> replay_id
        self._share_codes: Dict[str, str] = {}
    
    @property
    def database(self) -> "Database":
        """获取数据库实例"""
        if self._database is None:
            from ..db.database import get_database
            self._database = get_database()
        return self._database
    
    # ========================================================================
    # 回放保存
    # ========================================================================
    
    async def save_replay(
        self,
        player_id: int,
        match_data: Dict[str, Any],
    ) -> Optional[Replay]:
        """
        保存回放
        
        Args:
            player_id: 玩家ID
            match_data: 对局数据，包含：
                - match_id: 对局ID
                - player_nickname: 玩家昵称
                - final_rank: 最终排名
                - total_rounds: 总回合数
                - duration_seconds: 对局时长
                - frames: 帧数据列表
                - initial_state: 初始状态
                - final_rankings: 最终排名
                - player_count: 玩家数量
                
        Returns:
            保存的回放对象，失败返回 None
        """
        try:
            # 检查回放数量限制
            current_count = await self._get_player_replay_count(player_id)
            if current_count >= MAX_REPLAYS_PER_PLAYER:
                # 删除最旧的回放
                await self._delete_oldest_replay(player_id)
            
            # 创建元数据
            metadata = ReplayMetadata(
                match_id=match_data.get("match_id", str(uuid.uuid4())),
                player_id=player_id,
                player_nickname=match_data.get("player_nickname", f"Player_{player_id}"),
                final_rank=match_data.get("final_rank", 0),
                total_rounds=match_data.get("total_rounds", 0),
                duration_seconds=match_data.get("duration_seconds", 0),
                player_count=match_data.get("player_count", 8),
                game_version=match_data.get("game_version", "1.0.0"),
            )
            
            # 创建帧列表
            frames = []
            for frame_data in match_data.get("frames", []):
                frames.append(ReplayFrame.from_dict(frame_data))
            
            # 创建回放对象
            replay = Replay(
                metadata=metadata,
                frames=frames,
                initial_state=match_data.get("initial_state"),
                final_rankings=match_data.get("final_rankings", []),
            )
            
            # 保存到数据库
            await self._save_replay_to_db(replay)
            
            # 缓存回放
            self._replay_cache[replay.replay_id] = replay
            
            logger.info(
                "保存回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": replay.replay_id,
                    "match_id": metadata.match_id,
                    "final_rank": metadata.final_rank,
                }
            )
            
            return replay
        
        except Exception as e:
            logger.exception(
                "保存回放失败",
                extra={"player_id": player_id, "error": str(e)},
            )
            return None
    
    # ========================================================================
    # 回放列表
    # ========================================================================
    
    async def get_replay_list(
        self,
        player_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> List[ReplayListItem]:
        """
        获取玩家的回放列表
        
        Args:
            player_id: 玩家ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            回放列表项
        """
        try:
            # 从数据库获取
            db_replays = await self._get_replays_from_db(
                player_id=player_id,
                page=page,
                page_size=page_size,
            )
            
            # 转换为列表项
            items = []
            for db_replay in db_replays:
                item = ReplayListItem(
                    replay_id=db_replay["replay_id"],
                    match_id=db_replay["match_id"],
                    player_nickname=db_replay["player_nickname"],
                    final_rank=db_replay["final_rank"],
                    total_rounds=db_replay["total_rounds"],
                    duration_seconds=db_replay["duration_seconds"],
                    created_at=db_replay["created_at"],
                    is_shared=db_replay.get("is_shared", False),
                    share_code=db_replay.get("share_code"),
                )
                items.append(item)
            
            return items
        
        except Exception as e:
            logger.exception(
                "获取回放列表失败",
                extra={"player_id": player_id, "error": str(e)},
            )
            return []
    
    # ========================================================================
    # 加载回放
    # ========================================================================
    
    async def load_replay(self, replay_id: str) -> Optional[Replay]:
        """
        加载回放
        
        Args:
            replay_id: 回放ID
            
        Returns:
            回放对象，不存在返回 None
        """
        try:
            # 先检查缓存
            if replay_id in self._replay_cache:
                return self._replay_cache[replay_id]
            
            # 从数据库加载
            replay = await self._load_replay_from_db(replay_id)
            
            if replay:
                # 缓存
                self._replay_cache[replay_id] = replay
            
            return replay
        
        except Exception as e:
            logger.exception(
                "加载回放失败",
                extra={"replay_id": replay_id, "error": str(e)},
            )
            return None
    
    # ========================================================================
    # 播放控制
    # ========================================================================
    
    def create_play_session(self, replay_id: str) -> Optional[ReplaySession]:
        """
        创建播放会话
        
        Args:
            replay_id: 回放ID
            
        Returns:
            播放会话，失败返回 None
        """
        session_id = str(uuid.uuid4())
        
        session = ReplaySession(
            session_id=session_id,
            replay_id=replay_id,
        )
        
        self._play_sessions[session_id] = session
        
        logger.debug(
            "创建播放会话",
            extra={"session_id": session_id, "replay_id": replay_id},
        )
        
        return session
    
    def get_play_session(self, session_id: str) -> Optional[ReplaySession]:
        """
        获取播放会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            播放会话
        """
        return self._play_sessions.get(session_id)
    
    def play_replay(self, session_id: str) -> bool:
        """
        开始/继续播放
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return False
        
        session.play()
        
        logger.debug(
            "开始播放回放",
            extra={"session_id": session_id, "replay_id": session.replay_id},
        )
        
        return True
    
    def pause_replay(self, session_id: str) -> bool:
        """
        暂停播放
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return False
        
        session.pause()
        
        logger.debug(
            "暂停播放回放",
            extra={"session_id": session_id},
        )
        
        return True
    
    def stop_replay(self, session_id: str) -> bool:
        """
        停止播放
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return False
        
        session.stop()
        
        logger.debug(
            "停止播放回放",
            extra={"session_id": session_id},
        )
        
        return True
    
    def set_play_speed(
        self,
        session_id: str,
        speed: PlaySpeed,
    ) -> bool:
        """
        设置播放速度
        
        Args:
            session_id: 会话ID
            speed: 播放速度
            
        Returns:
            是否成功
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return False
        
        session.set_speed(speed)
        
        logger.debug(
            "设置播放速度",
            extra={"session_id": session_id, "speed": speed.value},
        )
        
        return True
    
    def seek_to_round(
        self,
        session_id: str,
        round_num: int,
        total_frames: int,
    ) -> bool:
        """
        跳转到指定回合
        
        Args:
            session_id: 会话ID
            round_num: 回合数
            total_frames: 总帧数
            
        Returns:
            是否成功
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return False
        
        session.seek_to_round(round_num, total_frames)
        
        logger.debug(
            "跳转到回合",
            extra={"session_id": session_id, "round_num": round_num},
        )
        
        return True
    
    def advance_frame(
        self,
        session_id: str,
        total_frames: int,
    ) -> Optional[ReplayFrame]:
        """
        前进一帧
        
        Args:
            session_id: 会话ID
            total_frames: 总帧数
            
        Returns:
            新帧数据，播放结束返回 None
        """
        session = self._play_sessions.get(session_id)
        if not session:
            return None
        
        if not session.advance_frame(total_frames):
            return None
        
        # 获取当前帧
        # 需要从回放中获取帧数据
        return None  # 由调用方根据 frame_index 获取
    
    def close_play_session(self, session_id: str) -> bool:
        """
        关闭播放会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        if session_id in self._play_sessions:
            del self._play_sessions[session_id]
            logger.debug(
                "关闭播放会话",
                extra={"session_id": session_id},
            )
            return True
        return False
    
    # ========================================================================
    # 删除回放
    # ========================================================================
    
    async def delete_replay(
        self,
        player_id: int,
        replay_id: str,
    ) -> bool:
        """
        删除回放
        
        Args:
            player_id: 玩家ID
            replay_id: 回放ID
            
        Returns:
            是否成功
        """
        try:
            # 从数据库删除
            success = await self._delete_replay_from_db(player_id, replay_id)
            
            if success:
                # 清除缓存
                if replay_id in self._replay_cache:
                    del self._replay_cache[replay_id]
                
                # 清除分享码映射
                share_codes_to_remove = [
                    code for code, rid in self._share_codes.items()
                    if rid == replay_id
                ]
                for code in share_codes_to_remove:
                    del self._share_codes[code]
                
                logger.info(
                    "删除回放成功",
                    extra={"player_id": player_id, "replay_id": replay_id},
                )
            
            return success
        
        except Exception as e:
            logger.exception(
                "删除回放失败",
                extra={"player_id": player_id, "replay_id": replay_id, "error": str(e)},
            )
            return False
    
    # ========================================================================
    # 分享功能
    # ========================================================================
    
    async def generate_share_code(
        self,
        player_id: int,
        replay_id: str,
    ) -> Optional[str]:
        """
        生成分享码
        
        Args:
            player_id: 玩家ID
            replay_id: 回放ID
            
        Returns:
            分享码，失败返回 None
        """
        try:
            # 检查回放是否存在且属于该玩家
            replay = await self.load_replay(replay_id)
            if not replay or not replay.metadata:
                return None
            
            if replay.metadata.player_id != player_id:
                return None
            
            # 如果已有分享码，直接返回
            if replay.metadata.share_code:
                return replay.metadata.share_code
            
            # 生成唯一分享码
            share_code = self._generate_unique_share_code()
            
            # 更新元数据
            replay.metadata.share_code = share_code
            replay.metadata.is_shared = True
            
            # 保存到数据库
            await self._update_replay_share_code(replay_id, share_code)
            
            # 更新映射
            self._share_codes[share_code] = replay_id
            
            logger.info(
                "生成分享码成功",
                extra={
                    "player_id": player_id,
                    "replay_id": replay_id,
                    "share_code": share_code,
                }
            )
            
            return share_code
        
        except Exception as e:
            logger.exception(
                "生成分享码失败",
                extra={"player_id": player_id, "replay_id": replay_id, "error": str(e)},
            )
            return None
    
    async def import_replay(
        self,
        player_id: int,
        share_code: str,
    ) -> Optional[Replay]:
        """
        通过分享码导入回放
        
        Args:
            player_id: 导入者玩家ID
            share_code: 分享码
            
        Returns:
            导入的回放对象，失败返回 None
        """
        try:
            # 查找分享码对应的回放
            replay_id = self._share_codes.get(share_code)
            
            if not replay_id:
                # 从数据库查找
                replay_id = await self._find_replay_by_share_code(share_code)
                if not replay_id:
                    logger.warning(
                        "分享码无效",
                        extra={"share_code": share_code},
                    )
                    return None
            
            # 加载回放
            replay = await self.load_replay(replay_id)
            if not replay:
                return None
            
            logger.info(
                "导入回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": replay_id,
                    "share_code": share_code,
                }
            )
            
            return replay
        
        except Exception as e:
            logger.exception(
                "导入回放失败",
                extra={"player_id": player_id, "share_code": share_code, "error": str(e)},
            )
            return None
    
    # ========================================================================
    # 导出功能
    # ========================================================================
    
    async def export_replay(
        self,
        player_id: int,
        replay_id: str,
    ) -> Optional[str]:
        """
        导出回放为JSON字符串
        
        Args:
            player_id: 玩家ID
            replay_id: 回放ID
            
        Returns:
            JSON字符串，失败返回 None
        """
        try:
            replay = await self.load_replay(replay_id)
            if not replay:
                return None
            
            # 确保分享码存在
            if not replay.metadata or not replay.metadata.share_code:
                await self.generate_share_code(player_id, replay_id)
                replay = await self.load_replay(replay_id)
            
            return json.dumps(replay.to_dict(), ensure_ascii=False)
        
        except Exception as e:
            logger.exception(
                "导出回放失败",
                extra={"player_id": player_id, "replay_id": replay_id, "error": str(e)},
            )
            return None
    
    # ========================================================================
    # 私有方法
    # ========================================================================
    
    def _generate_unique_share_code(self) -> str:
        """生成唯一的分享码"""
        while True:
            code = secrets.token_hex(SHARE_CODE_LENGTH // 2).upper()
            if code not in self._share_codes:
                return code
    
    async def _get_player_replay_count(self, player_id: int) -> int:
        """获取玩家的回放数量"""
        try:
            from .models import ReplayDB
            async with self.database.get_session() as session:
                from sqlalchemy import select, func
                stmt = select(func.count()).where(ReplayDB.player_id == player_id)
                result = await session.scalar(stmt)
                return result or 0
        except Exception:
            return 0
    
    async def _delete_oldest_replay(self, player_id: int) -> bool:
        """删除最旧的回放"""
        try:
            from .models import ReplayDB
            async with self.database.get_session() as session:
                from sqlalchemy import select, delete
                # 找到最旧的回放
                stmt = select(ReplayDB).where(
                    ReplayDB.player_id == player_id
                ).order_by(ReplayDB.created_at.asc()).limit(1)
                result = await session.execute(stmt)
                oldest = result.scalar_one_or_none()
                
                if oldest:
                    await session.execute(
                        delete(ReplayDB).where(ReplayDB.id == oldest.id)
                    )
                    await session.commit()
                    return True
                return False
        except Exception:
            return False
    
    async def _save_replay_to_db(self, replay: Replay) -> bool:
        """保存回放到数据库"""
        try:
            # 导入 ReplayDB 模型
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                db_replay = ReplayDB(
                    replay_id=replay.replay_id,
                    player_id=replay.metadata.player_id,
                    match_id=replay.metadata.match_id,
                    player_nickname=replay.metadata.player_nickname,
                    final_rank=replay.metadata.final_rank,
                    total_rounds=replay.metadata.total_rounds,
                    duration_seconds=replay.metadata.duration_seconds,
                    player_count=replay.metadata.player_count,
                    game_version=replay.metadata.game_version,
                    frames=json.dumps([f.to_dict() for f in replay.frames]),
                    initial_state=json.dumps(replay.initial_state) if replay.initial_state else None,
                    final_rankings=json.dumps(replay.final_rankings) if replay.final_rankings else None,
                    is_shared=replay.metadata.is_shared,
                    share_code=replay.metadata.share_code,
                )
                session.add(db_replay)
                await session.commit()
                return True
        except Exception as e:
            logger.exception("保存回放到数据库失败", extra={"error": str(e)})
            return False
    
    async def _get_replays_from_db(
        self,
        player_id: int,
        page: int,
        page_size: int,
    ) -> List[Dict[str, Any]]:
        """从数据库获取回放列表"""
        try:
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                from sqlalchemy import select
                offset = (page - 1) * page_size
                stmt = select(ReplayDB).where(
                    ReplayDB.player_id == player_id
                ).order_by(ReplayDB.created_at.desc()).offset(offset).limit(page_size)
                
                result = await session.execute(stmt)
                replays = result.scalars().all()
                
                return [
                    {
                        "replay_id": r.replay_id,
                        "match_id": r.match_id,
                        "player_nickname": r.player_nickname,
                        "final_rank": r.final_rank,
                        "total_rounds": r.total_rounds,
                        "duration_seconds": r.duration_seconds,
                        "created_at": int(r.created_at.timestamp() * 1000) if r.created_at else 0,
                        "is_shared": r.is_shared,
                        "share_code": r.share_code,
                    }
                    for r in replays
                ]
        except Exception as e:
            logger.exception("从数据库获取回放列表失败", extra={"error": str(e)})
            return []
    
    async def _load_replay_from_db(self, replay_id: str) -> Optional[Replay]:
        """从数据库加载回放"""
        try:
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                from sqlalchemy import select
                stmt = select(ReplayDB).where(ReplayDB.replay_id == replay_id)
                result = await session.execute(stmt)
                db_replay = result.scalar_one_or_none()
                
                if not db_replay:
                    return None
                
                # 构建 Replay 对象
                metadata = ReplayMetadata(
                    match_id=db_replay.match_id,
                    player_id=db_replay.player_id,
                    player_nickname=db_replay.player_nickname,
                    final_rank=db_replay.final_rank,
                    total_rounds=db_replay.total_rounds,
                    duration_seconds=db_replay.duration_seconds,
                    player_count=db_replay.player_count,
                    created_at=int(db_replay.created_at.timestamp() * 1000) if db_replay.created_at else 0,
                    game_version=db_replay.game_version or "1.0.0",
                    is_shared=db_replay.is_shared,
                    share_code=db_replay.share_code,
                )
                
                frames = []
                if db_replay.frames:
                    frames_data = json.loads(db_replay.frames)
                    for fd in frames_data:
                        frames.append(ReplayFrame.from_dict(fd))
                
                initial_state = None
                if db_replay.initial_state:
                    initial_state = json.loads(db_replay.initial_state)
                
                final_rankings = []
                if db_replay.final_rankings:
                    final_rankings = json.loads(db_replay.final_rankings)
                
                return Replay(
                    replay_id=db_replay.replay_id,
                    metadata=metadata,
                    frames=frames,
                    initial_state=initial_state,
                    final_rankings=final_rankings,
                )
        except Exception as e:
            logger.exception("从数据库加载回放失败", extra={"error": str(e)})
            return None
    
    async def _delete_replay_from_db(
        self,
        player_id: int,
        replay_id: str,
    ) -> bool:
        """从数据库删除回放"""
        try:
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                from sqlalchemy import delete
                stmt = delete(ReplayDB).where(
                    ReplayDB.player_id == player_id,
                    ReplayDB.replay_id == replay_id,
                )
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.exception("从数据库删除回放失败", extra={"error": str(e)})
            return False
    
    async def _update_replay_share_code(
        self,
        replay_id: str,
        share_code: str,
    ) -> bool:
        """更新回放的分享码"""
        try:
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                from sqlalchemy import update
                stmt = update(ReplayDB).where(
                    ReplayDB.replay_id == replay_id
                ).values(
                    share_code=share_code,
                    is_shared=True,
                )
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.exception("更新分享码失败", extra={"error": str(e)})
            return False
    
    async def _find_replay_by_share_code(self, share_code: str) -> Optional[str]:
        """通过分享码查找回放ID"""
        try:
            from ..db.models.replay import ReplayDB
            
            async with self.database.get_session() as session:
                from sqlalchemy import select
                stmt = select(ReplayDB.replay_id).where(
                    ReplayDB.share_code == share_code
                )
                result = await session.scalar(stmt)
                if result:
                    self._share_codes[share_code] = result
                return result
        except Exception as e:
            logger.exception("查找分享码失败", extra={"error": str(e)})
            return None


# 全局管理器实例
_replay_manager: Optional[ReplayManager] = None


def get_replay_manager() -> ReplayManager:
    """获取回放管理器单例"""
    global _replay_manager
    if _replay_manager is None:
        _replay_manager = ReplayManager()
    return _replay_manager


def init_replay_manager(database: "Database") -> ReplayManager:
    """初始化回放管理器"""
    global _replay_manager
    _replay_manager = ReplayManager(database)
    return _replay_manager
