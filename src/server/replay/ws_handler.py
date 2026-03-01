"""
王者之奕 - 回放系统 WebSocket 处理器

本模块提供回放系统相关的 WebSocket 消息处理：
- 保存回放
- 获取回放列表
- 加载回放
- 删除回放
- 播放控制（播放/暂停/停止/倍速/跳转）
- 导出回放
- 导入回放

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...shared.protocol import (
    BaseMessage,
    DeleteReplayMessage,
    ErrorMessage,
    ExportReplayMessage,
    GetReplayListMessage,
    ImportReplayMessage,
    LoadReplayMessage,
    ReplayControlMessage,
    ReplayData,
    ReplayDeletedMessage,
    ReplayExportedMessage,
    ReplayFrameData,
    ReplayImportedMessage,
    ReplayListItemData,
    ReplayListMessage,
    ReplayLoadedMessage,
    ReplayMetadataData,
    ReplayPlayerSnapshotData,
    ReplaySavedMessage,
    ReplayStateUpdateMessage,
    SaveReplayMessage,
)
from ..replay import (
    PlaySpeed,
    Replay,
    ReplayFrame,
    ReplayManager,
    ReplaySession,
    get_replay_manager,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class ReplayWSHandler:
    """
    回放系统 WebSocket 处理器

    处理所有回放相关的 WebSocket 消息。

    使用方式:
        handler = ReplayWSHandler()

        @ws_handler.on_message(MessageType.SAVE_REPLAY)
        async def handle_save_replay(session, message):
            return await replay_handler.handle_save_replay(session, message)
    """

    def __init__(self) -> None:
        """初始化处理器"""
        self._manager: ReplayManager | None = None

    @property
    def manager(self) -> ReplayManager:
        """获取回放管理器"""
        if self._manager is None:
            self._manager = get_replay_manager()
        return self._manager

    # ========================================================================
    # 消息处理
    # ========================================================================

    async def handle_save_replay(
        self,
        session: Session,
        message: SaveReplayMessage,
    ) -> BaseMessage | None:
        """
        处理保存回放请求

        Args:
            session: WebSocket 会话
            message: 保存回放消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 保存回放
            replay = await self.manager.save_replay(
                player_id=player_id,
                match_data=message.match_data,
            )

            if replay is None:
                return ErrorMessage(
                    code=6001,
                    message="保存回放失败",
                    seq=message.seq,
                )

            logger.info(
                "保存回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": replay.replay_id,
                    "match_id": message.match_id,
                },
            )

            return ReplaySavedMessage(
                replay_id=replay.replay_id,
                match_id=message.match_id,
                message="回放保存成功",
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "保存回放异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="保存回放失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_get_replay_list(
        self,
        session: Session,
        message: GetReplayListMessage,
    ) -> BaseMessage | None:
        """
        处理获取回放列表请求

        Args:
            session: WebSocket 会话
            message: 获取回放列表消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 获取回放列表
            items = await self.manager.get_replay_list(
                player_id=player_id,
                page=message.page,
                page_size=message.page_size,
            )

            # 转换为消息格式
            replay_list = [
                ReplayListItemData(
                    replay_id=item.replay_id,
                    match_id=item.match_id,
                    player_nickname=item.player_nickname,
                    final_rank=item.final_rank,
                    total_rounds=item.total_rounds,
                    duration_seconds=item.duration_seconds,
                    duration_minutes=round(item.duration_seconds / 60, 1),
                    created_at=item.created_at,
                    is_shared=item.is_shared,
                    share_code=item.share_code,
                )
                for item in items
            ]

            logger.debug(
                "获取回放列表",
                extra={
                    "player_id": player_id,
                    "page": message.page,
                    "count": len(replay_list),
                },
            )

            return ReplayListMessage(
                replays=replay_list,
                page=message.page,
                page_size=message.page_size,
                total_count=len(replay_list),  # 简化处理
                max_replays=20,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "获取回放列表异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="获取回放列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_load_replay(
        self,
        session: Session,
        message: LoadReplayMessage,
    ) -> BaseMessage | None:
        """
        处理加载回放请求

        Args:
            session: WebSocket 会话
            message: 加载回放消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 加载回放
            replay = await self.manager.load_replay(message.replay_id)

            if replay is None:
                return ErrorMessage(
                    code=6002,
                    message="回放不存在",
                    seq=message.seq,
                )

            # 转换为消息格式
            replay_data = self._convert_replay_to_data(replay)

            logger.info(
                "加载回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": message.replay_id,
                },
            )

            return ReplayLoadedMessage(
                replay=replay_data,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "加载回放异常",
                extra={"player_id": player_id, "replay_id": message.replay_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="加载回放失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_delete_replay(
        self,
        session: Session,
        message: DeleteReplayMessage,
    ) -> BaseMessage | None:
        """
        处理删除回放请求

        Args:
            session: WebSocket 会话
            message: 删除回放消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 删除回放
            success = await self.manager.delete_replay(
                player_id=player_id,
                replay_id=message.replay_id,
            )

            if not success:
                return ErrorMessage(
                    code=6003,
                    message="删除回放失败",
                    seq=message.seq,
                )

            logger.info(
                "删除回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": message.replay_id,
                },
            )

            return ReplayDeletedMessage(
                replay_id=message.replay_id,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "删除回放异常",
                extra={"player_id": player_id, "replay_id": message.replay_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="删除回放失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_replay_control(
        self,
        session: Session,
        message: ReplayControlMessage,
    ) -> BaseMessage | None:
        """
        处理回放控制请求

        Args:
            session: WebSocket 会话
            message: 回放控制消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            action = message.action.lower()

            if action == "play":
                success = self.manager.play_replay(message.session_id)
            elif action == "pause":
                success = self.manager.pause_replay(message.session_id)
            elif action == "stop":
                success = self.manager.stop_replay(message.session_id)
            elif action == "speed":
                if message.speed is None:
                    return ErrorMessage(
                        code=6004,
                        message="缺少播放速度参数",
                        seq=message.seq,
                    )
                speed = PlaySpeed(message.speed)
                success = self.manager.set_play_speed(message.session_id, speed)
            elif action == "seek":
                if message.round_num is None:
                    return ErrorMessage(
                        code=6005,
                        message="缺少跳转回合参数",
                        seq=message.seq,
                    )
                # 获取会话对应的回放
                play_session = self.manager.get_play_session(message.session_id)
                if play_session is None:
                    return ErrorMessage(
                        code=6006,
                        message="播放会话不存在",
                        seq=message.seq,
                    )
                # 加载回放获取总帧数
                replay = await self.manager.load_replay(play_session.replay_id)
                if replay is None:
                    return ErrorMessage(
                        code=6002,
                        message="回放不存在",
                        seq=message.seq,
                    )
                success = self.manager.seek_to_round(
                    message.session_id,
                    message.round_num,
                    replay.get_frame_count(),
                )
            else:
                return ErrorMessage(
                    code=6007,
                    message=f"未知的控制动作: {action}",
                    seq=message.seq,
                )

            if not success:
                return ErrorMessage(
                    code=6008,
                    message="回放控制失败",
                    seq=message.seq,
                )

            # 获取更新后的会话状态
            play_session = self.manager.get_play_session(message.session_id)
            if play_session is None:
                return ErrorMessage(
                    code=6006,
                    message="播放会话不存在",
                    seq=message.seq,
                )

            # 加载回放获取当前帧
            replay = await self.manager.load_replay(play_session.replay_id)
            current_frame = None
            total_frames = 0
            if replay:
                total_frames = replay.get_frame_count()
                if 0 <= play_session.current_frame_index < total_frames:
                    frame = replay.frames[play_session.current_frame_index]
                    current_frame = self._convert_frame_to_data(frame)

            logger.debug(
                "回放控制",
                extra={
                    "player_id": player_id,
                    "session_id": message.session_id,
                    "action": action,
                },
            )

            return ReplayStateUpdateMessage(
                session_id=message.session_id,
                status=play_session.status.value,
                current_round=play_session.current_round,
                current_frame_index=play_session.current_frame_index,
                total_frames=total_frames,
                speed=play_session.speed.value,
                current_frame=current_frame,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "回放控制异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="回放控制失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_export_replay(
        self,
        session: Session,
        message: ExportReplayMessage,
    ) -> BaseMessage | None:
        """
        处理导出回放请求

        Args:
            session: WebSocket 会话
            message: 导出回放消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 导出回放
            export_data = await self.manager.export_replay(
                player_id=player_id,
                replay_id=message.replay_id,
            )

            if export_data is None:
                return ErrorMessage(
                    code=6009,
                    message="导出回放失败",
                    seq=message.seq,
                )

            # 获取分享码
            replay = await self.manager.load_replay(message.replay_id)
            share_code = replay.metadata.share_code if replay and replay.metadata else ""

            logger.info(
                "导出回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": message.replay_id,
                    "share_code": share_code,
                },
            )

            return ReplayExportedMessage(
                replay_id=message.replay_id,
                share_code=share_code,
                export_data=export_data,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "导出回放异常",
                extra={"player_id": player_id, "replay_id": message.replay_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="导出回放失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_import_replay(
        self,
        session: Session,
        message: ImportReplayMessage,
    ) -> BaseMessage | None:
        """
        处理导入回放请求

        Args:
            session: WebSocket 会话
            message: 导入回放消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            # 导入回放
            if message.share_code:
                replay = await self.manager.import_replay(
                    player_id=player_id,
                    share_code=message.share_code,
                )
            elif message.import_data:
                # 从导入数据创建回放
                import json

                data = json.loads(message.import_data)
                replay = Replay.from_dict(data)
            else:
                return ErrorMessage(
                    code=6010,
                    message="缺少分享码或导入数据",
                    seq=message.seq,
                )

            if replay is None:
                return ErrorMessage(
                    code=6011,
                    message="导入回放失败",
                    seq=message.seq,
                )

            # 转换为消息格式
            replay_data = self._convert_replay_to_data(replay)

            logger.info(
                "导入回放成功",
                extra={
                    "player_id": player_id,
                    "replay_id": replay.replay_id,
                    "share_code": message.share_code,
                },
            )

            return ReplayImportedMessage(
                replay=replay_data,
                message="回放导入成功",
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "导入回放异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=6000,
                message="导入回放失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _convert_replay_to_data(self, replay: Replay) -> ReplayData:
        """将 Replay 对象转换为 ReplayData"""
        metadata = None
        if replay.metadata:
            metadata = ReplayMetadataData(
                match_id=replay.metadata.match_id,
                player_id=replay.metadata.player_id,
                player_nickname=replay.metadata.player_nickname,
                final_rank=replay.metadata.final_rank,
                total_rounds=replay.metadata.total_rounds,
                duration_seconds=replay.metadata.duration_seconds,
                player_count=replay.metadata.player_count,
                created_at=replay.metadata.created_at,
                game_version=replay.metadata.game_version,
                is_shared=replay.metadata.is_shared,
                share_code=replay.metadata.share_code,
                tags=replay.metadata.tags,
            )

        frames = [self._convert_frame_to_data(frame) for frame in replay.frames]

        return ReplayData(
            replay_id=replay.replay_id,
            metadata=metadata,
            frames=frames,
            initial_state=replay.initial_state,
            final_rankings=replay.final_rankings,
        )

    def _convert_frame_to_data(self, frame: ReplayFrame) -> ReplayFrameData:
        """将 ReplayFrame 对象转换为 ReplayFrameData"""
        player_snapshots = {}
        for pid, snapshot in frame.player_snapshots.items():
            player_snapshots[str(pid)] = ReplayPlayerSnapshotData(
                player_id=snapshot.player_id,
                nickname=snapshot.nickname,
                avatar=snapshot.avatar,
                tier=snapshot.tier,
                hp=snapshot.hp,
                gold=snapshot.gold,
                level=snapshot.level,
                exp=snapshot.exp,
                board=snapshot.board,
                bench=snapshot.bench,
                synergies=snapshot.synergies,
                equipment=snapshot.equipment,
            )

        return ReplayFrameData(
            round_num=frame.round_num,
            phase=frame.phase,
            timestamp=frame.timestamp,
            player_snapshots=player_snapshots,
            shop_data=frame.shop_data,
            battle_data=frame.battle_data,
            events=frame.events,
        )

    def create_play_session(self, replay_id: str) -> ReplaySession | None:
        """
        创建播放会话

        Args:
            replay_id: 回放ID

        Returns:
            播放会话
        """
        return self.manager.create_play_session(replay_id)

    def close_play_session(self, session_id: str) -> bool:
        """
        关闭播放会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        return self.manager.close_play_session(session_id)


# 全局处理器实例
replay_ws_handler = ReplayWSHandler()
