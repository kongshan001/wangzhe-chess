"""
王者之奕 - 表情系统管理器

本模块提供表情系统的管理功能：
- EmoteManager: 表情管理器类
- 表情列表获取
- 表情发送/接收
- 表情解锁管理
- 快捷键设置
- 表情历史记录
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from .models import (
    Emote,
    EmoteCategory,
    EmoteData,
    EmoteHistory,
    EmoteType,
    PlayerEmote,
)

if TYPE_CHECKING:
    from src.server.ws.handler import WebSocketHandler

logger = logging.getLogger(__name__)


class EmoteManager:
    """
    表情系统管理器
    
    负责管理所有表情相关的操作：
    - 表情配置加载
    - 表情列表获取
    - 表情发送/接收
    - 表情解锁管理
    - 快捷键设置
    - 表情历史记录
    
    Attributes:
        emotes: 所有表情 (emote_id -> Emote)
        player_emotes: 玩家拥有的表情 (player_id -> {emote_id: PlayerEmote})
        emote_history: 表情发送历史 (room_id -> [EmoteHistory])
        player_hotkeys: 玩家快捷键映射 (player_id -> {hotkey: emote_id})
    """
    
    def __init__(self, ws_handler: Optional["WebSocketHandler"] = None):
        """
        初始化表情管理器
        
        Args:
            ws_handler: WebSocket处理器（用于发送实时消息）
        """
        self._ws_handler = ws_handler
        
        # 所有表情
        self.emotes: Dict[str, Emote] = {}
        
        # 玩家拥有的表情
        self.player_emotes: Dict[str, Dict[str, PlayerEmote]] = {}
        
        # 表情发送历史 (每个房间的历史)
        self.emote_history: Dict[str, List[EmoteHistory]] = {}
        
        # 玩家快捷键映射
        self.player_hotkeys: Dict[str, Dict[str, str]] = {}  # player_id -> {hotkey: emote_id}
        
        # 配置
        self.max_history_per_room = 100
        self.emote_cooldown_seconds = 3  # 发送冷却时间
        self.max_hotkeys = 8  # 最大快捷键数量
        
        # 冷却记录
        self._cooldowns: Dict[str, datetime] = {}  # player_id -> last_emote_time
        
        # 加载表情配置
        self._load_emotes_config()
        
        logger.info("EmoteManager initialized")
    
    def set_ws_handler(self, handler: "WebSocketHandler") -> None:
        """设置WebSocket处理器"""
        self._ws_handler = handler
    
    def _load_emotes_config(self) -> None:
        """加载表情配置文件"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "emotes.json"
        
        if not config_path.exists():
            logger.warning(f"Emotes config not found: {config_path}")
            self._create_default_emotes()
            return
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 加载表情
            for emote_data in config.get("emotes", []):
                emote = Emote.from_dict(emote_data)
                self.emotes[emote.emote_id] = emote
            
            logger.info(f"Loaded {len(self.emotes)} emotes from config")
            
        except Exception as e:
            logger.error(f"Failed to load emotes config: {e}")
            self._create_default_emotes()
    
    def _create_default_emotes(self) -> None:
        """创建默认表情"""
        default_emotes = [
            Emote(
                emote_id="hello",
                name="你好",
                description="打招呼",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/hello.png",
                is_free=True,
                sort_order=1,
            ),
            Emote(
                emote_id="good_game",
                name="打得不错",
                description="称赞对手",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/good_game.png",
                is_free=True,
                sort_order=2,
            ),
            Emote(
                emote_id="thanks",
                name="谢谢",
                description="表示感谢",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/thanks.png",
                is_free=True,
                sort_order=3,
            ),
            Emote(
                emote_id="well_played",
                name="精彩操作",
                description="称赞精彩操作",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.ANIMATED,
                asset_url="/assets/emotes/well_played.gif",
                is_free=True,
                sort_order=4,
            ),
            Emote(
                emote_id="luck",
                name="运气不错",
                description="运气真好",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/luck.png",
                is_free=True,
                sort_order=5,
            ),
            Emote(
                emote_id="thinking",
                name="思考中",
                description="正在思考",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.ANIMATED,
                asset_url="/assets/emotes/thinking.gif",
                is_free=True,
                sort_order=6,
            ),
            Emote(
                emote_id="oops",
                name="失误了",
                description="不小心失误",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/oops.png",
                is_free=True,
                sort_order=7,
            ),
            Emote(
                emote_id="gg",
                name="GG",
                description="Good Game",
                category=EmoteCategory.DEFAULT,
                emote_type=EmoteType.STATIC,
                asset_url="/assets/emotes/gg.png",
                is_free=True,
                sort_order=8,
            ),
        ]
        
        for emote in default_emotes:
            self.emotes[emote.emote_id] = emote
        
        logger.info(f"Created {len(default_emotes)} default emotes")
    
    # ========================================================================
    # 表情列表获取
    # ========================================================================
    
    def get_all_emotes(self) -> List[Emote]:
        """
        获取所有表情列表
        
        Returns:
            表情列表（按排序顺序）
        """
        return sorted(self.emotes.values(), key=lambda e: e.sort_order)
    
    def get_emotes_by_category(self, category: EmoteCategory) -> List[Emote]:
        """
        获取指定分类的表情
        
        Args:
            category: 表情分类
            
        Returns:
            该分类的表情列表
        """
        return [
            emote for emote in self.emotes.values()
            if emote.category == category
        ]
    
    def get_emote(self, emote_id: str) -> Optional[Emote]:
        """
        获取单个表情
        
        Args:
            emote_id: 表情ID
            
        Returns:
            表情对象，不存在返回None
        """
        return self.emotes.get(emote_id)
    
    def get_emotes_list_data(self) -> List[Dict[str, Any]]:
        """
        获取表情列表数据（用于发送给客户端）
        
        Returns:
            表情数据列表
        """
        return [emote.to_dict() for emote in self.get_all_emotes()]
    
    # ========================================================================
    # 玩家表情管理
    # ========================================================================
    
    def get_player_emotes(self, player_id: str) -> List[PlayerEmote]:
        """
        获取玩家拥有的表情
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家表情列表
        """
        return list(self.player_emotes.get(player_id, {}).values())
    
    def get_player_emote(self, player_id: str, emote_id: str) -> Optional[PlayerEmote]:
        """
        获取玩家对特定表情的拥有状态
        
        Args:
            player_id: 玩家ID
            emote_id: 表情ID
            
        Returns:
            玩家表情对象，不存在返回None
        """
        player_emotes = self.player_emotes.get(player_id, {})
        return player_emotes.get(emote_id)
    
    def has_emote(self, player_id: str, emote_id: str) -> bool:
        """
        检查玩家是否拥有表情
        
        Args:
            player_id: 玩家ID
            emote_id: 表情ID
            
        Returns:
            是否拥有
        """
        return emote_id in self.player_emotes.get(player_id, {})
    
    def get_unlocked_emotes(
        self,
        player_id: str,
        player_stats: Optional[Dict[str, Any]] = None,
    ) -> List[Emote]:
        """
        获取玩家已解锁的表情
        
        Args:
            player_id: 玩家ID
            player_stats: 玩家统计数据（用于检查解锁条件）
            
        Returns:
            已解锁的表情列表
        """
        unlocked = []
        player_emotes = self.player_emotes.get(player_id, {})
        
        for emote in self.emotes.values():
            # 已拥有的表情
            if emote.emote_id in player_emotes:
                unlocked.append(emote)
                continue
            
            # 免费表情
            if emote.is_free:
                unlocked.append(emote)
                continue
            
            # 检查解锁条件
            if player_stats and emote.check_unlock(player_stats):
                unlocked.append(emote)
        
        return unlocked
    
    def get_unlocked_emotes_data(
        self,
        player_id: str,
        player_stats: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取玩家已解锁表情的数据
        
        Args:
            player_id: 玩家ID
            player_stats: 玩家统计数据
            
        Returns:
            已解锁表情的数据列表
        """
        emotes = self.get_unlocked_emotes(player_id, player_stats)
        player_emotes = self.player_emotes.get(player_id, {})
        
        result = []
        for emote in emotes:
            data = emote.to_dict()
            player_emote = player_emotes.get(emote.emote_id)
            if player_emote:
                data["hotkey"] = player_emote.hotkey
                data["use_count"] = player_emote.use_count
            else:
                data["hotkey"] = None
                data["use_count"] = 0
            result.append(data)
        
        return result
    
    # ========================================================================
    # 表情解锁
    # ========================================================================
    
    def unlock_emote(
        self,
        player_id: str,
        emote_id: str,
    ) -> Optional[PlayerEmote]:
        """
        解锁表情
        
        Args:
            player_id: 玩家ID
            emote_id: 表情ID
            
        Returns:
            玩家表情对象，失败返回None
        """
        emote = self.emotes.get(emote_id)
        if not emote:
            logger.warning(f"Emote not found: {emote_id}")
            return None
        
        # 检查是否已拥有
        if self.has_emote(player_id, emote_id):
            logger.debug(f"Player {player_id} already has emote {emote_id}")
            return self.get_player_emote(player_id, emote_id)
        
        # 创建玩家表情
        player_emote = PlayerEmote(
            player_id=player_id,
            emote_id=emote_id,
        )
        
        # 存储
        if player_id not in self.player_emotes:
            self.player_emotes[player_id] = {}
        self.player_emotes[player_id][emote_id] = player_emote
        
        logger.info(f"Player {player_id} unlocked emote {emote_id}")
        
        return player_emote
    
    def check_and_unlock_emotes(
        self,
        player_id: str,
        player_stats: Dict[str, Any],
    ) -> List[Emote]:
        """
        检查并解锁符合条件的表情
        
        Args:
            player_id: 玩家ID
            player_stats: 玩家统计数据
            
        Returns:
            新解锁的表情列表
        """
        newly_unlocked = []
        
        for emote in self.emotes.values():
            if self.has_emote(player_id, emote.emote_id):
                continue
            
            if emote.check_unlock(player_stats):
                self.unlock_emote(player_id, emote.emote_id)
                newly_unlocked.append(emote)
        
        if newly_unlocked:
            logger.info(
                f"Player {player_id} unlocked {len(newly_unlocked)} new emotes"
            )
        
        return newly_unlocked
    
    # ========================================================================
    # 表情发送
    # ========================================================================
    
    def can_send_emote(self, player_id: str) -> bool:
        """
        检查玩家是否可以发送表情（冷却时间检查）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否可以发送
        """
        last_time = self._cooldowns.get(player_id)
        if last_time is None:
            return True
        
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed >= self.emote_cooldown_seconds
    
    def get_cooldown_remaining(self, player_id: str) -> float:
        """
        获取剩余冷却时间
        
        Args:
            player_id: 玩家ID
            
        Returns:
            剩余秒数（0表示无冷却）
        """
        last_time = self._cooldowns.get(player_id)
        if last_time is None:
            return 0.0
        
        elapsed = (datetime.now() - last_time).total_seconds()
        remaining = self.emote_cooldown_seconds - elapsed
        return max(0.0, remaining)
    
    async def send_emote(
        self,
        room_id: str,
        from_player_id: str,
        emote_id: str,
        to_player_id: Optional[str] = None,
        round_number: int = 0,
        from_nickname: str = "",
    ) -> Optional[EmoteHistory]:
        """
        发送表情
        
        Args:
            room_id: 房间ID
            from_player_id: 发送者ID
            emote_id: 表情ID
            to_player_id: 目标玩家ID（None=所有玩家）
            round_number: 回合数
            from_nickname: 发送者昵称
            
        Returns:
            表情历史记录，失败返回None
        """
        # 检查表情是否存在
        emote = self.emotes.get(emote_id)
        if not emote:
            logger.warning(f"Emote not found: {emote_id}")
            return None
        
        # 检查玩家是否拥有表情
        if not self.has_emote(from_player_id, emote_id) and not emote.is_free:
            logger.warning(
                f"Player {from_player_id} doesn't have emote {emote_id}"
            )
            return None
        
        # 检查冷却时间
        if not self.can_send_emote(from_player_id):
            remaining = self.get_cooldown_remaining(from_player_id)
            logger.debug(
                f"Player {from_player_id} on cooldown ({remaining:.1f}s remaining)"
            )
            return None
        
        # 创建历史记录
        history_id = f"eh_{uuid.uuid4().hex[:12]}"
        history = EmoteHistory(
            history_id=history_id,
            room_id=room_id,
            from_player_id=from_player_id,
            to_player_id=to_player_id,
            emote_id=emote_id,
            round_number=round_number,
        )
        
        # 存储历史
        if room_id not in self.emote_history:
            self.emote_history[room_id] = []
        self.emote_history[room_id].append(history)
        
        # 限制历史数量
        if len(self.emote_history[room_id]) > self.max_history_per_room:
            self.emote_history[room_id] = self.emote_history[room_id][-self.max_history_per_room:]
        
        # 更新冷却
        self._cooldowns[from_player_id] = datetime.now()
        
        # 更新使用次数
        player_emote = self.get_player_emote(from_player_id, emote_id)
        if player_emote:
            player_emote.use_count += 1
        else:
            # 如果是免费表情，创建记录
            self.unlock_emote(from_player_id, emote_id)
            player_emote = self.get_player_emote(from_player_id, emote_id)
            if player_emote:
                player_emote.use_count = 1
        
        logger.info(
            f"Emote sent: {emote_id} from {from_player_id} to {to_player_id or 'all'} in {room_id}"
        )
        
        return history
    
    # ========================================================================
    # 表情历史
    # ========================================================================
    
    def get_room_emote_history(
        self,
        room_id: str,
        limit: int = 50,
    ) -> List[EmoteHistory]:
        """
        获取房间的表情历史
        
        Args:
            room_id: 房间ID
            limit: 返回数量限制
            
        Returns:
            表情历史列表
        """
        history = self.emote_history.get(room_id, [])
        return history[-limit:]
    
    def get_player_emote_history(
        self,
        player_id: str,
        room_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[EmoteHistory]:
        """
        获取玩家的表情历史
        
        Args:
            player_id: 玩家ID
            room_id: 房间ID（可选）
            limit: 返回数量限制
            
        Returns:
            表情历史列表
        """
        if room_id:
            history = self.emote_history.get(room_id, [])
            return [h for h in history if h.from_player_id == player_id][-limit:]
        
        # 搜索所有房间
        result = []
        for room_history in self.emote_history.values():
            for h in room_history:
                if h.from_player_id == player_id:
                    result.append(h)
        
        # 按时间排序
        result.sort(key=lambda h: h.created_at or datetime.min, reverse=True)
        return result[:limit]
    
    def clear_room_history(self, room_id: str) -> int:
        """
        清除房间的表情历史
        
        Args:
            room_id: 房间ID
            
        Returns:
            清除的记录数量
        """
        count = len(self.emote_history.get(room_id, []))
        self.emote_history.pop(room_id, None)
        return count
    
    # ========================================================================
    # 快捷键管理
    # ========================================================================
    
    def set_emote_hotkey(
        self,
        player_id: str,
        emote_id: str,
        hotkey: str,
    ) -> bool:
        """
        设置表情快捷键
        
        Args:
            player_id: 玩家ID
            emote_id: 表情ID
            hotkey: 快捷键（如 "1", "2", "ctrl+1" 等）
            
        Returns:
            是否成功
        """
        # 检查表情是否存在
        if emote_id not in self.emotes:
            logger.warning(f"Emote not found: {emote_id}")
            return False
        
        # 检查玩家是否拥有表情
        if not self.has_emote(player_id, emote_id):
            # 如果是免费表情，先解锁
            emote = self.emotes[emote_id]
            if not emote.is_free:
                logger.warning(
                    f"Player {player_id} doesn't have emote {emote_id}"
                )
                return False
            self.unlock_emote(player_id, emote_id)
        
        # 初始化快捷键映射
        if player_id not in self.player_hotkeys:
            self.player_hotkeys[player_id] = {}
        
        # 检查快捷键是否已被使用
        old_emote_id = self.player_hotkeys[player_id].get(hotkey)
        if old_emote_id:
            # 清除旧表情的快捷键
            old_player_emote = self.get_player_emote(player_id, old_emote_id)
            if old_player_emote:
                old_player_emote.hotkey = None
        
        # 检查表情是否已有其他快捷键
        player_emote = self.get_player_emote(player_id, emote_id)
        if player_emote and player_emote.hotkey:
            # 清除旧快捷键
            self.player_hotkeys[player_id].pop(player_emote.hotkey, None)
        
        # 设置新快捷键
        self.player_hotkeys[player_id][hotkey] = emote_id
        if player_emote:
            player_emote.hotkey = hotkey
        
        logger.info(
            f"Player {player_id} set hotkey {hotkey} for emote {emote_id}"
        )
        
        return True
    
    def remove_emote_hotkey(
        self,
        player_id: str,
        emote_id: str,
    ) -> bool:
        """
        移除表情快捷键
        
        Args:
            player_id: 玩家ID
            emote_id: 表情ID
            
        Returns:
            是否成功
        """
        player_emote = self.get_player_emote(player_id, emote_id)
        if not player_emote or not player_emote.hotkey:
            return False
        
        hotkey = player_emote.hotkey
        
        # 清除映射
        if player_id in self.player_hotkeys:
            self.player_hotkeys[player_id].pop(hotkey, None)
        
        player_emote.hotkey = None
        
        logger.info(
            f"Player {player_id} removed hotkey for emote {emote_id}"
        )
        
        return True
    
    def get_player_hotkeys(self, player_id: str) -> Dict[str, str]:
        """
        获取玩家的快捷键映射
        
        Args:
            player_id: 玩家ID
            
        Returns:
            快捷键映射 {hotkey: emote_id}
        """
        return self.player_hotkeys.get(player_id, {}).copy()
    
    def get_emote_by_hotkey(self, player_id: str, hotkey: str) -> Optional[Emote]:
        """
        根据快捷键获取表情
        
        Args:
            player_id: 玩家ID
            hotkey: 快捷键
            
        Returns:
            表情对象，不存在返回None
        """
        hotkeys = self.player_hotkeys.get(player_id, {})
        emote_id = hotkeys.get(hotkey)
        if emote_id:
            return self.emotes.get(emote_id)
        return None
    
    # ========================================================================
    # 数据持久化（占位）
    # ========================================================================
    
    def load_from_db(self) -> None:
        """从数据库加载数据"""
        # TODO: 实现数据库加载
        pass
    
    def save_to_db(self) -> None:
        """保存数据到数据库"""
        # TODO: 实现数据库保存
        pass


# 全局单例
_emote_manager: Optional[EmoteManager] = None


def get_emote_manager() -> EmoteManager:
    """获取表情管理器单例"""
    global _emote_manager
    if _emote_manager is None:
        _emote_manager = EmoteManager()
    return _emote_manager
