"""
王者之奕 - 匹配队列

本模块实现了游戏的匹配队列系统，包括：
- 按段位分队列
- FIFO 匹配逻辑
- 扩大搜索范围机制（等待时间越长，范围越大）
- 超时处理
- AI 填充（人不够时）

队列系统是匹配的核心组件，负责管理等待中的玩家
并为他们找到合适的对手。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable, Awaitable

from .rating import Tier, PlayerRating, TIER_CONFIGS


class QueueState(Enum):
    """队列条目状态"""
    WAITING = "waiting"        # 等待中
    MATCHING = "matching"      # 匹配中
    MATCHED = "matched"        # 已匹配
    TIMEOUT = "timeout"        # 超时
    CANCELLED = "cancelled"    # 已取消


class QueuePriority(Enum):
    """队列优先级"""
    NORMAL = 0       # 普通玩家
    HIGH = 1         # 高优先级（如VIP）
    PRIORITIZED = 2  # 长时间等待的玩家


@dataclass
class QueueEntry:
    """
    队列条目
    
    代表一个正在等待匹配的玩家。
    
    Attributes:
        player_id: 玩家ID
        rating: 玩家段位信息
        elo_score: 玩家 ELO 分数
        join_time: 加入队列时间戳（毫秒）
        state: 条目状态
        priority: 优先级
        match_callback: 匹配成功回调
        search_range: 当前搜索范围（ELO 差值）
        last_search_time: 上次搜索时间
        attempts: 匹配尝试次数
        metadata: 额外元数据
    """
    player_id: str
    rating: PlayerRating
    elo_score: int = 1200
    join_time: float = field(default_factory=time.time)
    state: QueueState = QueueState.WAITING
    priority: QueuePriority = QueuePriority.NORMAL
    match_callback: Optional[Callable[[dict[str, Any]], Awaitable[None]]] = None
    search_range: int = 50  # 初始搜索范围
    last_search_time: float = field(default_factory=time.time)
    attempts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def tier(self) -> Tier:
        """获取玩家段位"""
        return self.rating.tier
    
    @property
    def stars(self) -> int:
        """获取玩家星级"""
        return self.rating.stars
    
    def get_wait_time_ms(self) -> int:
        """
        获取等待时间（毫秒）
        
        Returns:
            已等待的毫秒数
        """
        return int((time.time() - self.join_time) * 1000)
    
    def get_wait_time_seconds(self) -> float:
        """
        获取等待时间（秒）
        
        Returns:
            已等待的秒数
        """
        return time.time() - self.join_time
    
    def expand_search_range(self, base_expansion: int = 25) -> int:
        """
        扩大搜索范围
        
        根据等待时间动态扩大搜索范围。
        等待越久，范围越大。
        
        Args:
            base_expansion: 基础扩展值
            
        Returns:
            新的搜索范围
        """
        wait_seconds = self.get_wait_time_seconds()
        
        # 扩展策略：
        # 0-30秒：不扩展
        # 30-60秒：每10秒扩展25
        # 60-120秒：每10秒扩展50
        # 120秒+：每10秒扩展100
        
        if wait_seconds < 30:
            expansion = 0
        elif wait_seconds < 60:
            expansion = int((wait_seconds - 30) / 10) * 25
        elif wait_seconds < 120:
            expansion = 75 + int((wait_seconds - 60) / 10) * 50
        else:
            expansion = 375 + int((wait_seconds - 120) / 10) * 100
        
        # 最大搜索范围
        self.search_range = min(500, 50 + expansion)
        return self.search_range
    
    def is_within_range(self, other_elo: int) -> bool:
        """
        检查另一个玩家的 ELO 是否在搜索范围内
        
        Args:
            other_elo: 对方 ELO 分数
            
        Returns:
            是否在范围内
        """
        return abs(self.elo_score - other_elo) <= self.search_range
    
    def calculate_match_quality(self, other: QueueEntry) -> float:
        """
        计算与另一个玩家的匹配质量
        
        返回 0.0 - 1.0 的分数，越高表示匹配越好。
        
        Args:
            other: 另一个队列条目
            
        Returns:
            匹配质量分数
        """
        # ELO 差距影响（0-0.5）
        elo_diff = abs(self.elo_score - other.elo_score)
        elo_score = max(0, 0.5 - elo_diff / 1000)
        
        # 等待时间奖励（0-0.3）
        # 等待时间越长，匹配质量阈值降低
        wait_bonus = min(0.3, self.get_wait_time_seconds() / 300)
        
        # 同段位奖励（0-0.2）
        tier_bonus = 0.2 if self.tier == other.tier else 0.1
        
        return min(1.0, elo_score + wait_bonus + tier_bonus)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "player_id": self.player_id,
            "tier": self.tier.value,
            "tier_name": self.tier.get_display_name(),
            "stars": self.stars,
            "elo_score": self.elo_score,
            "join_time": self.join_time,
            "wait_time_ms": self.get_wait_time_ms(),
            "state": self.state.value,
            "priority": self.priority.value,
            "search_range": self.search_range,
            "attempts": self.attempts,
        }


@dataclass
class QueueConfig:
    """
    队列配置
    
    定义匹配队列的各项参数。
    
    Attributes:
        max_queue_size: 队列最大容量
        match_size: 单局游戏玩家数量
        timeout_seconds: 超时时间（秒）
        initial_search_range: 初始搜索范围
        max_search_range: 最大搜索范围
        range_expansion_interval: 范围扩展间隔（秒）
        ai_fill_timeout: AI 填充超时（秒）
        enable_ai_fill: 是否启用 AI 填充
        min_match_quality: 最低匹配质量
    """
    max_queue_size: int = 1000
    match_size: int = 8  # 自走棋标准8人局
    timeout_seconds: int = 300  # 5分钟
    initial_search_range: int = 50
    max_search_range: int = 500
    range_expansion_interval: float = 10.0
    ai_fill_timeout: int = 60  # 1分钟后开始 AI 填充
    enable_ai_fill: bool = True
    min_match_quality: float = 0.3


class MatchQueue:
    """
    匹配队列
    
    管理等待匹配的玩家，实现按段位分队列和 FIFO 匹配。
    使用 asyncio 实现异步操作，thread-safe。
    
    Attributes:
        config: 队列配置
        _queues: 按段位分组的队列字典
        _all_entries: 所有条目的字典 {player_id: entry}
        _lock: 异步锁，保证线程安全
        _match_callback: 匹配成功回调
    """
    
    def __init__(self, config: Optional[QueueConfig] = None):
        """
        初始化匹配队列
        
        Args:
            config: 队列配置
        """
        self.config = config or QueueConfig()
        
        # 按段位分组的队列
        self._queues: dict[Tier, list[QueueEntry]] = {
            tier: [] for tier in Tier
        }
        
        # 所有条目的快速索引
        self._all_entries: dict[str, QueueEntry] = {}
        
        # 异步锁，保证线程安全
        self._lock = asyncio.Lock()
        
        # 匹配成功回调
        self._match_callback: Optional[Callable[[list[QueueEntry]], Awaitable[None]]] = None
        
        # 后台任务
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
    
    def set_match_callback(
        self, 
        callback: Callable[[list[QueueEntry]], Awaitable[None]]
    ) -> None:
        """
        设置匹配成功回调
        
        Args:
            callback: 异步回调函数
        """
        self._match_callback = callback
    
    async def join(
        self,
        player_id: str,
        rating: PlayerRating,
        elo_score: int,
        priority: QueuePriority = QueuePriority.NORMAL,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        玩家加入队列
        
        Args:
            player_id: 玩家ID
            rating: 段位信息
            elo_score: ELO 分数
            priority: 优先级
            metadata: 额外元数据
            
        Returns:
            是否成功加入
        """
        async with self._lock:
            # 检查是否已在队列中
            if player_id in self._all_entries:
                return False
            
            # 检查队列是否已满
            if len(self._all_entries) >= self.config.max_queue_size:
                return False
            
            # 创建队列条目
            entry = QueueEntry(
                player_id=player_id,
                rating=rating,
                elo_score=elo_score,
                priority=priority,
                metadata=metadata or {},
                search_range=self.config.initial_search_range,
            )
            
            # 添加到段位队列
            tier_queue = self._queues[rating.tier]
            tier_queue.append(entry)
            
            # 添加到索引
            self._all_entries[player_id] = entry
            
            return True
    
    async def leave(self, player_id: str) -> Optional[QueueEntry]:
        """
        玩家离开队列
        
        Args:
            player_id: 玩家ID
            
        Returns:
            被移除的条目，如果不存在返回None
        """
        async with self._lock:
            entry = self._all_entries.pop(player_id, None)
            if entry is None:
                return None
            
            # 从段位队列移除
            tier_queue = self._queues[entry.tier]
            if entry in tier_queue:
                tier_queue.remove(entry)
            
            entry.state = QueueState.CANCELLED
            return entry
    
    async def get_entry(self, player_id: str) -> Optional[QueueEntry]:
        """
        获取玩家的队列条目
        
        Args:
            player_id: 玩家ID
            
        Returns:
            队列条目，如果不存在返回None
        """
        return self._all_entries.get(player_id)
    
    async def get_queue_size(self, tier: Optional[Tier] = None) -> int:
        """
        获取队列大小
        
        Args:
            tier: 指定段位，None 表示总大小
            
        Returns:
            队列中的玩家数量
        """
        if tier is not None:
            return len(self._queues[tier])
        return len(self._all_entries)
    
    async def get_wait_time_estimate(self, tier: Tier) -> int:
        """
        估算等待时间
        
        根据当前队列状态估算该段位玩家的等待时间。
        
        Args:
            tier: 段位
            
        Returns:
            预估等待秒数
        """
        queue_size = len(self._queues[tier])
        
        if queue_size >= self.config.match_size:
            # 人足够，立即匹配
            return 5
        
        # 根据当前人数估算
        # 假设每秒有 0.5 人加入
        needed = self.config.match_size - queue_size
        estimated_seconds = needed * 2
        
        # 考虑 AI 填充
        if self.config.enable_ai_fill:
            estimated_seconds = min(estimated_seconds, self.config.ai_fill_timeout)
        
        return estimated_seconds
    
    def _find_matches_in_tier(self, tier: Tier) -> list[list[QueueEntry]]:
        """
        在指定段位队列中寻找匹配
        
        使用 FIFO + 范围扩展的策略。
        
        Args:
            tier: 段位
            
        Returns:
            匹配组列表
        """
        matches = []
        tier_queue = self._queues[tier]
        
        if len(tier_queue) < 2:
            return matches
        
        # 已匹配的条目
        matched_ids: set[str] = set()
        
        for entry in tier_queue:
            if entry.player_id in matched_ids:
                continue
            if entry.state != QueueState.WAITING:
                continue
            
            # 扩大搜索范围
            entry.expand_search_range()
            entry.attempts += 1
            
            # 寻找匹配的玩家
            match_group = [entry]
            matched_ids.add(entry.player_id)
            
            for other in tier_queue:
                if other.player_id in matched_ids:
                    continue
                if other.state != QueueState.WAITING:
                    continue
                
                # 检查是否在搜索范围内
                if entry.is_within_range(other.elo_score):
                    # 检查匹配质量
                    quality = entry.calculate_match_quality(other)
                    if quality >= self.config.min_match_quality:
                        match_group.append(other)
                        matched_ids.add(other.player_id)
                        
                        # 达到人数要求
                        if len(match_group) >= self.config.match_size:
                        break
            
            # 至少需要 2 人才能匹配
            if len(match_group) >= 2:
                for e in match_group:
                    e.state = QueueState.MATCHED
                matches.append(match_group)
        
        return matches
    
    def _find_cross_tier_matches(self) -> list[list[QueueEntry]]:
        """
        寻找跨段位匹配
        
        当某段位人数不足时，尝试匹配相邻段位。
        
        Returns:
            匹配组列表
        """
        matches = []
        
        # 按段位顺序遍历
        for tier in Tier:
            tier_queue = self._queues[tier]
            waiting = [e for e in tier_queue if e.state == QueueState.WAITING]
            
            if not waiting:
                continue
            
            for entry in waiting[:]:  # 使用副本遍历
                if entry.state != QueueState.WAITING:
                    continue
                
                # 扩大搜索范围
                entry.expand_search_range()
                
                match_group = [entry]
                
                # 在相邻段位寻找
                adjacent_tiers = self._get_adjacent_tiers(tier)
                
                for adj_tier in adjacent_tiers:
                    adj_queue = self._queues[adj_tier]
                    for other in adj_queue:
                        if other.state != QueueState.WAITING:
                            continue
                        if other.player_id == entry.player_id:
                            continue
                        
                        if entry.is_within_range(other.elo_score):
                            match_group.append(other)
                            if len(match_group) >= self.config.match_size:
                            break
                    
                    if len(match_group) >= self.config.match_size:
                    break
                
                if len(match_group) >= 2:
                    for e in match_group:
                        e.state = QueueState.MATCHED
                    matches.append(match_group)
        
        return matches
    
    def _get_adjacent_tiers(self, tier: Tier) -> list[Tier]:
        """
        获取相邻段位
        
        Args:
            tier: 当前段位
            
        Returns:
            相邻段位列表
        """
        adjacent = []
        if tier.value > 1:
            adjacent.append(Tier(tier.value - 1))
        if tier.value < len(Tier):
            adjacent.append(Tier(tier.value + 1))
        return adjacent
    
    def _check_timeouts(self) -> list[QueueEntry]:
        """
        检查超时的条目
        
        Returns:
            超时的条目列表
        """
        timeout_entries = []
        current_time = time.time()
        timeout_threshold = current_time - self.config.timeout_seconds
        
        for entry in list(self._all_entries.values()):
            if entry.state != QueueState.WAITING:
                continue
            
            if entry.join_time < timeout_threshold:
                entry.state = QueueState.TIMEOUT
                timeout_entries.append(entry)
        
        return timeout_entries
    
    def _should_fill_with_ai(self, match_group: list[QueueEntry]) -> bool:
        """
        判断是否应该用 AI 填充
        
        Args:
            match_group: 当前匹配组
            
        Returns:
            是否需要 AI 填充
        """
        if not self.config.enable_ai_fill:
            return False
        
        # 检查等待时间
        max_wait = max(e.get_wait_time_seconds() for e in match_group)
        return max_wait >= self.config.ai_fill_timeout
    
    async def _process_matches(self) -> list[list[QueueEntry]]:
        """
        处理匹配
        
        寻找并返回所有匹配的玩家组。
        
        Returns:
            匹配组列表
        """
        all_matches = []
        
        # 1. 先在同段位内匹配
        for tier in Tier:
            matches = self._find_matches_in_tier(tier)
            all_matches.extend(matches)
        
        # 2. 跨段位匹配
        cross_matches = self._find_cross_tier_matches()
        all_matches.extend(cross_matches)
        
        # 3. 检查超时
        timeout_entries = self._check_timeouts()
        for entry in timeout_entries:
            await self.leave(entry.player_id)
        
        # 4. AI 填充检查
        final_matches = []
        for match in all_matches:
            # 检查是否需要 AI 填充
            if len(match) < self.config.match_size:
                if self._should_fill_with_ai(match):
                    # 标记需要 AI 填充
                    for entry in match:
                        entry.metadata["needs_ai_fill"] = True
                        entry.metadata["ai_count"] = self.config.match_size - len(match)
            
            final_matches.append(match)
            
            # 从队列移除已匹配的条目
            for entry in match:
                await self.leave(entry.player_id)
        
        return final_matches
    
    async def start_processor(self) -> None:
        """
        启动匹配处理器
        
        后台持续运行，定期处理匹配。
        """
        self._running = True
        
        async def process_loop():
            while self._running:
                try:
                    matches = await self._process_matches()
                    
                    if matches and self._match_callback:
                        for match in matches:
                            await self._match_callback(match)
                    
                    # 等待一段时间再处理
                    await asyncio.sleep(1.0)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # 记录错误但继续运行
                    print(f"Match processor error: {e}")
                    await asyncio.sleep(5.0)
        
        self._processor_task = asyncio.create_task(process_loop())
    
    async def stop_processor(self) -> None:
        """
        停止匹配处理器
        """
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None
    
    async def force_match(
        self, 
        player_ids: list[str]
    ) -> Optional[list[QueueEntry]]:
        """
        强制匹配指定玩家
        
        用于特殊情况，如好友组队匹配。
        
        Args:
            player_ids: 玩家ID列表
            
        Returns:
            匹配组，如果有玩家不在队列中返回None
        """
        async with self._lock:
            entries = []
            for pid in player_ids:
                entry = self._all_entries.get(pid)
                if entry is None:
                    return None
                entries.append(entry)
            
            # 标记为已匹配
            for entry in entries:
                entry.state = QueueState.MATCHED
                # 从队列移除
                tier_queue = self._queues[entry.tier]
                if entry in tier_queue:
                    tier_queue.remove(entry)
                self._all_entries.pop(entry.player_id, None)
            
            return entries
    
    def get_queue_stats(self) -> dict[str, Any]:
        """
        获取队列统计信息
        
        Returns:
            统计信息字典
        """
        tier_counts = {}
        for tier, queue in self._queues.items():
            tier_counts[tier.get_display_name()] = len(queue)
        
        # 计算平均等待时间
        wait_times = [
            e.get_wait_time_seconds() 
            for e in self._all_entries.values()
        ]
        avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
        
        return {
            "total_players": len(self._all_entries),
            "tier_distribution": tier_counts,
            "average_wait_time": round(avg_wait, 2),
            "is_processing": self._running,
        }
    
    async def clear(self) -> int:
        """
        清空队列
        
        Returns:
            清除的条目数量
        """
        async with self._lock:
            count = len(self._all_entries)
            
            for entry in self._all_entries.values():
                entry.state = QueueState.CANCELLED
            
            self._all_entries.clear()
            for tier in self._queues:
                self._queues[tier].clear()
            
            return count


class AIPlayerGenerator:
    """
    AI 玩家生成器
    
    用于生成 AI 玩家填充人机对战。
    """
    
    _counter = 0
    
    @classmethod
    def generate_ai_player(
        cls, 
        target_elo: int,
        tier: Tier
    ) -> dict[str, Any]:
        """
        生成一个 AI 玩家
        
        Args:
            target_elo: 目标 ELO 分数
            tier: 段位
            
        Returns:
            AI 玩家信息
        """
        cls._counter += 1
        
        # 在目标 ELO 附近随机波动
        import random
        elo_variation = random.randint(-50, 50)
        ai_elo = target_elo + elo_variation
        
        return {
            "player_id": f"ai_{cls._counter:06d}",
            "is_ai": True,
            "elo_score": ai_elo,
            "tier": tier,
            "tier_name": tier.get_display_name(),
            "display_name": f"AI助手{cls._counter}",
            "avatar": "ai_default",
        }
    
    @classmethod
    def generate_ai_team(
        cls,
        target_elo: int,
        tier: Tier,
        count: int
    ) -> list[dict[str, Any]]:
        """
        生成一组 AI 玩家
        
        Args:
            target_elo: 目标 ELO 分数
            tier: 段位
            count: 数量
            
        Returns:
            AI 玩家列表
        """
        return [
            cls.generate_ai_player(target_elo, tier)
            for _ in range(count)
        ]
