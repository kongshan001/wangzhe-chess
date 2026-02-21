"""
王者之奕 - 游戏房间模块

本模块实现游戏房间的核心逻辑：
- GameRoom: 8人游戏房间管理
- 游戏状态机（等待→准备→战斗→结算）
- 回合控制
- 玩家数据同步

游戏流程：
1. 玩家加入房间（WAITING 状态）
2. 玩家准备（PREPARING 状态）
3. 所有人准备好后开始战斗（BATTLING 状态）
4. 战斗结束结算（SETTLING 状态）
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from config.settings import settings


logger = structlog.get_logger()


class RoomState(str, Enum):
    """
    房间状态枚举
    
    定义游戏房间可能处于的所有状态：
    - WAITING: 等待玩家加入
    - PREPARING: 准备阶段，玩家可以调整阵容
    - BATTLING: 战斗阶段，自动进行战斗
    - SETTLING: 结算阶段，计算本回合结果
    - FINISHED: 游戏结束
    """
    
    WAITING = "waiting"       # 等待玩家
    PREPARING = "preparing"   # 准备阶段
    BATTLING = "battling"     # 战斗阶段
    SETTLING = "settling"     # 结算阶段
    FINISHED = "finished"     # 游戏结束


class PlayerState(str, Enum):
    """
    玩家状态枚举
    
    定义玩家在房间中的状态：
    - CONNECTED: 已连接但未准备
    - READY: 已准备
    - PLAYING: 游戏中
    - DISCONNECTED: 已断开连接
    - ELIMINATED: 已被淘汰
    """
    
    CONNECTED = "connected"     # 已连接
    READY = "ready"             # 已准备
    PLAYING = "playing"         # 游戏中
    DISCONNECTED = "disconnected"  # 断开连接
    ELIMINATED = "eliminated"   # 已淘汰


@dataclass
class PlayerInRoom:
    """
    房间内的玩家数据
    
    存储玩家在当前房间/游戏中的所有状态信息。
    
    Attributes:
        player_id: 玩家ID
        nickname: 玩家昵称
        state: 玩家状态
        slot: 房间内位置（0-7）
        hp: 当前生命值
        gold: 当前金币
        level: 当前等级
        exp: 当前经验值
        win_streak: 当前连胜
        lose_streak: 当前连败
        heroes: 当前持有的英雄列表
        bench: 备战席英雄
        board: 棋盘上的英雄
        synergies: 当前激活的羁绊
        ready_at: 准备时间
        connected_at: 连接时间
        last_action_at: 最后操作时间
    """
    
    player_id: int
    nickname: str
    state: PlayerState = PlayerState.CONNECTED
    slot: int = 0
    
    # 游戏属性
    hp: int = 100
    gold: int = 0
    level: int = 1
    exp: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    
    # 英雄相关
    heroes: List[Dict[str, Any]] = field(default_factory=list)
    bench: List[Dict[str, Any]] = field(default_factory=list)
    board: List[Dict[str, Any]] = field(default_factory=list)
    synergies: Dict[str, int] = field(default_factory=dict)
    
    # 时间戳
    ready_at: Optional[datetime] = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_action_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于JSON序列化）
        
        Returns:
            包含玩家所有状态信息的字典
        """
        return {
            "player_id": self.player_id,
            "nickname": self.nickname,
            "state": self.state.value,
            "slot": self.slot,
            "hp": self.hp,
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "hero_count": len(self.heroes),
            "board_count": len(self.board),
            "synergies": self.synergies,
        }
    
    @property
    def is_alive(self) -> bool:
        """检查玩家是否还活着"""
        return self.hp > 0 and self.state != PlayerState.ELIMINATED
    
    @property
    def is_ready(self) -> bool:
        """检查玩家是否已准备"""
        return self.state == PlayerState.READY
    
    @property
    def is_connected(self) -> bool:
        """检查玩家是否在线"""
        return self.state not in [PlayerState.DISCONNECTED, PlayerState.ELIMINATED]
    
    def set_ready(self) -> None:
        """设置玩家为已准备状态"""
        self.state = PlayerState.READY
        self.ready_at = datetime.now()
        self.last_action_at = datetime.now()
    
    def set_playing(self) -> None:
        """设置玩家为游戏中状态"""
        self.state = PlayerState.PLAYING
    
    def set_disconnected(self) -> None:
        """设置玩家为断开连接状态"""
        self.state = PlayerState.DISCONNECTED
    
    def eliminate(self) -> None:
        """淘汰玩家"""
        self.state = PlayerState.ELIMINATED
        self.hp = 0
    
    def take_damage(self, damage: int) -> int:
        """
        扣除生命值
        
        Args:
            damage: 伤害值
            
        Returns:
            扣除后的生命值
        """
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.eliminate()
        return self.hp
    
    def heal(self, amount: int) -> int:
        """
        恢复生命值
        
        Args:
            amount: 恢复量
            
        Returns:
            恢复后的生命值
        """
        self.hp = min(100, self.hp + amount)
        return self.hp
    
    def add_gold(self, amount: int) -> int:
        """
        增加金币
        
        Args:
            amount: 金币数量
            
        Returns:
            增加后的金币数
        """
        self.gold += amount
        return self.gold
    
    def spend_gold(self, amount: int) -> bool:
        """
        消耗金币
        
        Args:
            amount: 金币数量
            
        Returns:
            是否成功（金币是否足够）
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
    
    def add_exp(self, amount: int) -> bool:
        """
        增加经验值并检查是否升级
        
        Args:
            amount: 经验值数量
            
        Returns:
            是否升级
        """
        self.exp += amount
        # 升级所需经验 = level * 2 + 2
        exp_needed = self.level * 2 + 2
        if self.exp >= exp_needed:
            self.exp -= exp_needed
            self.level += 1
            return True
        return False


class GameRoom:
    """
    游戏房间类
    
    管理8人自走棋游戏房间的所有逻辑。
    
    状态机转换：
    WAITING → PREPARING → BATTLING → SETTLING → (循环 PREPARING...)
                         ↓
                      FINISHED
    
    Attributes:
        room_id: 房间唯一ID
        name: 房间名称
        state: 房间状态
        host_id: 房主ID
        players: 玩家字典
        max_players: 最大玩家数（8）
        current_round: 当前回合
        phase_start_time: 当前阶段开始时间
        config: 房间配置
        callbacks: 回调函数集合
    """
    
    def __init__(
        self,
        room_id: Optional[str] = None,
        name: str = "",
        host_id: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化游戏房间
        
        Args:
            room_id: 房间ID（不提供则自动生成）
            name: 房间名称
            host_id: 房主ID
            config: 房间配置
        """
        self.room_id: str = room_id or str(uuid.uuid4())
        self.name: str = name or f"房间-{self.room_id[:6]}"
        self.state: RoomState = RoomState.WAITING
        self.host_id: Optional[int] = host_id
        self.players: Dict[int, PlayerInRoom] = {}
        self.spectators: Set[int] = set()
        
        # 游戏配置
        self.max_players: int = settings.game.MAX_PLAYERS_PER_ROOM
        self.config: Dict[str, Any] = config or {}
        
        # 回合相关
        self.current_round: int = 0
        self.phase_start_time: Optional[datetime] = None
        self.round_results: List[Dict[str, Any]] = []
        
        # 时间控制
        self.buy_phase_duration: int = settings.game.BUY_PHASE_DURATION
        self.battle_phase_duration: int = settings.game.BATTLE_PHASE_DURATION
        
        # 回调函数
        self._on_state_change: Optional[Callable[[RoomState, RoomState], None]] = None
        self._on_player_join: Optional[Callable[[PlayerInRoom], None]] = None
        self._on_player_leave: Optional[Callable[[int], None]] = None
        self._on_round_start: Optional[Callable[[int], None]] = None
        self._on_round_end: Optional[Callable[[int, Dict], None]] = None
        self._on_game_end: Optional[Callable[[Dict], None]] = None
        
        # 异步任务
        self._phase_task: Optional[asyncio.Task] = None
        self._lock: asyncio.Lock = asyncio.Lock()
        
        logger.info(
            "房间已创建",
            room_id=self.room_id,
            name=self.name,
            max_players=self.max_players,
        )
    
    # ========================================================================
    # 属性访问
    # ========================================================================
    
    @property
    def player_count(self) -> int:
        """获取当前玩家数量"""
        return len(self.players)
    
    @property
    def alive_count(self) -> int:
        """获取存活玩家数量"""
        return sum(1 for p in self.players.values() if p.is_alive)
    
    @property
    def ready_count(self) -> int:
        """获取已准备玩家数量"""
        return sum(1 for p in self.players.values() if p.is_ready)
    
    @property
    def is_full(self) -> bool:
        """检查房间是否已满"""
        return self.player_count >= self.max_players
    
    @property
    def is_empty(self) -> bool:
        """检查房间是否为空"""
        return self.player_count == 0
    
    @property
    def can_start(self) -> bool:
        """检查是否可以开始游戏"""
        # 至少2人，所有人已准备，当前为等待状态
        return (
            self.player_count >= 2
            and self.ready_count == self.player_count
            and self.state == RoomState.WAITING
        )
    
    @property
    def all_disconnected(self) -> bool:
        """检查是否所有玩家都已断开连接"""
        return all(not p.is_connected for p in self.players.values())
    
    # ========================================================================
    # 回调设置
    # ========================================================================
    
    def on_state_change(self, callback: Callable[[RoomState, RoomState], None]) -> None:
        """设置状态变化回调"""
        self._on_state_change = callback
    
    def on_player_join(self, callback: Callable[[PlayerInRoom], None]) -> None:
        """设置玩家加入回调"""
        self._on_player_join = callback
    
    def on_player_leave(self, callback: Callable[[int], None]) -> None:
        """设置玩家离开回调"""
        self._on_player_leave = callback
    
    def on_round_start(self, callback: Callable[[int], None]) -> None:
        """设置回合开始回调"""
        self._on_round_start = callback
    
    def on_round_end(self, callback: Callable[[int, Dict], None]) -> None:
        """设置回合结束回调"""
        self._on_round_end = callback
    
    def on_game_end(self, callback: Callable[[Dict], None]) -> None:
        """设置游戏结束回调"""
        self._on_game_end = callback
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    async def _set_state(self, new_state: RoomState) -> None:
        """
        设置房间状态（内部方法）
        
        Args:
            new_state: 新状态
        """
        old_state = self.state
        self.state = new_state
        self.phase_start_time = datetime.now()
        
        logger.info(
            "房间状态变更",
            room_id=self.room_id,
            old_state=old_state.value,
            new_state=new_state.value,
        )
        
        if self._on_state_change:
            try:
                self._on_state_change(old_state, new_state)
            except Exception as e:
                logger.error("状态变更回调失败", error=str(e))
    
    # ========================================================================
    # 玩家管理
    # ========================================================================
    
    async def add_player(
        self,
        player_id: int,
        nickname: str,
        slot: Optional[int] = None,
    ) -> Optional[PlayerInRoom]:
        """
        添加玩家到房间
        
        Args:
            player_id: 玩家ID
            nickname: 玩家昵称
            slot: 指定位置（可选）
            
        Returns:
            玩家实例，如果添加失败返回None
        """
        async with self._lock:
            # 检查是否已在房间中
            if player_id in self.players:
                logger.warning("玩家已在房间中", player_id=player_id)
                return None
            
            # 检查房间是否已满
            if self.is_full:
                logger.warning("房间已满", room_id=self.room_id)
                return None
            
            # 检查房间状态
            if self.state != RoomState.WAITING:
                logger.warning("游戏已开始，无法加入", state=self.state.value)
                return None
            
            # 分配位置
            if slot is None:
                used_slots = {p.slot for p in self.players.values()}
                for i in range(self.max_players):
                    if i not in used_slots:
                        slot = i
                        break
            
            # 创建玩家实例
            player = PlayerInRoom(
                player_id=player_id,
                nickname=nickname,
                slot=slot,
                gold=settings.game.STARTING_GOLD,
                hp=settings.game.STARTING_HEALTH,
            )
            
            self.players[player_id] = player
            
            # 如果是第一个玩家，设为房主
            if self.host_id is None:
                self.host_id = player_id
            
            logger.info(
                "玩家加入房间",
                player_id=player_id,
                nickname=nickname,
                room_id=self.room_id,
                slot=slot,
            )
            
            if self._on_player_join:
                try:
                    self._on_player_join(player)
                except Exception as e:
                    logger.error("玩家加入回调失败", error=str(e))
            
            return player
    
    async def remove_player(self, player_id: int) -> bool:
        """
        从房间移除玩家
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功移除
        """
        async with self._lock:
            if player_id not in self.players:
                return False
            
            player = self.players[player_id]
            
            # 如果游戏进行中，标记为断开连接而不是移除
            if self.state in [RoomState.PREPARING, RoomState.BATTLING, RoomState.SETTLING]:
                player.set_disconnected()
                logger.info(
                    "玩家断开连接",
                    player_id=player_id,
                    room_id=self.room_id,
                )
            else:
                # 游戏未开始，直接移除
                del self.players[player_id]
                
                # 如果是房主，转让房主
                if self.host_id == player_id:
                    if self.players:
                        self.host_id = next(iter(self.players.keys()))
                    else:
                        self.host_id = None
                
                logger.info(
                    "玩家离开房间",
                    player_id=player_id,
                    room_id=self.room_id,
                )
            
            if self._on_player_leave:
                try:
                    self._on_player_leave(player_id)
                except Exception as e:
                    logger.error("玩家离开回调失败", error=str(e))
            
            return True
    
    async def set_player_ready(self, player_id: int, ready: bool = True) -> bool:
        """
        设置玩家准备状态
        
        Args:
            player_id: 玩家ID
            ready: 是否准备
            
        Returns:
            是否成功设置
        """
        async with self._lock:
            if player_id not in self.players:
                return False
            
            player = self.players[player_id]
            
            if ready:
                player.set_ready()
            else:
                player.state = PlayerState.CONNECTED
                player.ready_at = None
            
            logger.info(
                "玩家准备状态变更",
                player_id=player_id,
                ready=ready,
                room_id=self.room_id,
            )
            
            # 检查是否可以自动开始
            if self.can_start:
                asyncio.create_task(self.start_game())
            
            return True
    
    def get_player(self, player_id: int) -> Optional[PlayerInRoom]:
        """
        获取玩家实例
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家实例，如果不存在返回None
        """
        return self.players.get(player_id)
    
    def get_all_players(self) -> List[PlayerInRoom]:
        """获取所有玩家列表"""
        return list(self.players.values())
    
    def get_alive_players(self) -> List[PlayerInRoom]:
        """获取存活玩家列表"""
        return [p for p in self.players.values() if p.is_alive]
    
    # ========================================================================
    # 游戏流程控制
    # ========================================================================
    
    async def start_game(self) -> bool:
        """
        开始游戏
        
        Returns:
            是否成功开始
        """
        async with self._lock:
            if not self.can_start:
                logger.warning("无法开始游戏", state=self.state.value)
                return False
            
            # 切换到准备状态
            await self._set_state(RoomState.PREPARING)
            
            # 设置所有玩家为游戏中
            for player in self.players.values():
                player.set_playing()
            
            # 初始化第一回合
            self.current_round = 1
            
            logger.info(
                "游戏开始",
                room_id=self.room_id,
                player_count=self.player_count,
            )
            
            # 开始回合循环
            asyncio.create_task(self._game_loop())
            
            return True
    
    async def _game_loop(self) -> None:
        """
        游戏主循环
        
        循环执行：准备阶段 → 战斗阶段 → 结算阶段
        直到只剩一名玩家或满足其他结束条件
        """
        while self.state != RoomState.FINISHED:
            try:
                # 回合开始
                if self._on_round_start:
                    self._on_round_start(self.current_round)
                
                # 准备阶段
                await self._prepare_phase()
                
                if self.state == RoomState.FINISHED:
                    break
                
                # 战斗阶段
                await self._battle_phase()
                
                if self.state == RoomState.FINISHED:
                    break
                
                # 结算阶段
                await self._settle_phase()
                
                # 检查游戏是否结束
                if self._check_game_end():
                    await self._end_game()
                    break
                
                # 进入下一回合
                self.current_round += 1
                
            except asyncio.CancelledError:
                logger.info("游戏循环被取消", room_id=self.room_id)
                break
            except Exception as e:
                logger.error("游戏循环错误", error=str(e), room_id=self.room_id)
                await self._end_game()
                break
    
    async def _prepare_phase(self) -> None:
        """
        准备阶段
        
        玩家可以购买英雄、调整阵容
        """
        await self._set_state(RoomState.PREPARING)
        
        # 分发金币
        for player in self.get_alive_players():
            # 基础金币 + 利息 + 连胜/连败奖励
            base_gold = min(5, self.current_round)
            interest = min(5, player.gold // 10)
            streak_bonus = 0
            
            if player.win_streak >= 2:
                streak_bonus = min(3, player.win_streak)
            elif player.lose_streak >= 2:
                streak_bonus = min(3, player.lose_streak)
            
            total_gold = base_gold + interest + streak_bonus
            player.add_gold(total_gold)
            
            logger.debug(
                "分发金币",
                player_id=player.player_id,
                base=base_gold,
                interest=interest,
                streak=streak_bonus,
                total=total_gold,
            )
        
        # 等待准备阶段结束
        await asyncio.sleep(self.buy_phase_duration)
    
    async def _battle_phase(self) -> None:
        """
        战斗阶段
        
        自动进行玩家间的战斗
        """
        await self._set_state(RoomState.BATTLING)
        
        alive_players = self.get_alive_players()
        
        # 生成对战配对
        battles = self._generate_battles(alive_players)
        
        # 执行战斗（这里简化处理）
        battle_results = []
        for attacker, defender in battles:
            result = await self._execute_battle(attacker, defender)
            battle_results.append(result)
        
        # 等待战斗阶段结束
        await asyncio.sleep(self.battle_phase_duration)
    
    def _generate_battles(
        self,
        players: List[PlayerInRoom],
    ) -> List[tuple[PlayerInRoom, PlayerInRoom]]:
        """
        生成对战配对
        
        Args:
            players: 参战玩家列表
            
        Returns:
            对战配对列表 [(攻击方, 防守方), ...]
        """
        battles = []
        n = len(players)
        
        if n < 2:
            return battles
        
        # 简单的配对逻辑：随机配对
        import random
        shuffled = players.copy()
        random.shuffle(shuffled)
        
        for i in range(0, n - 1, 2):
            battles.append((shuffled[i], shuffled[i + 1]))
        
        # 奇数人时，最后一人打镜像
        if n % 2 == 1:
            battles.append((shuffled[-1], shuffled[-1]))
        
        return battles
    
    async def _execute_battle(
        self,
        attacker: PlayerInRoom,
        defender: PlayerInRoom,
    ) -> Dict[str, Any]:
        """
        执行单场战斗
        
        Args:
            attacker: 攻击方
            defender: 防守方
            
        Returns:
            战斗结果字典
        """
        # 简化的战斗逻辑：比较战力
        attacker_power = len(attacker.board) * 10 + attacker.level * 5
        defender_power = len(defender.board) * 10 + defender.level * 5
        
        # 添加随机性
        import random
        attacker_power += random.randint(-5, 5)
        defender_power += random.randint(-5, 5)
        
        result = {
            "round": self.current_round,
            "attacker_id": attacker.player_id,
            "defender_id": defender.player_id,
            "attacker_power": attacker_power,
            "defender_power": defender_power,
        }
        
        if attacker_power > defender_power:
            # 攻击方获胜
            damage = max(1, (attacker_power - defender_power) // 5)
            defender.take_damage(damage)
            attacker.win_streak += 1
            attacker.lose_streak = 0
            defender.win_streak = 0
            defender.lose_streak += 1
            result["winner_id"] = attacker.player_id
            result["damage"] = damage
        elif defender_power > attacker_power:
            # 防守方获胜
            damage = max(1, (defender_power - attacker_power) // 5)
            attacker.take_damage(damage)
            defender.win_streak += 1
            defender.lose_streak = 0
            attacker.win_streak = 0
            attacker.lose_streak += 1
            result["winner_id"] = defender.player_id
            result["damage"] = damage
        else:
            # 平局
            result["winner_id"] = None
            result["damage"] = 0
        
        return result
    
    async def _settle_phase(self) -> None:
        """
        结算阶段
        
        计算本回合结果，更新玩家状态
        """
        await self._set_state(RoomState.SETTLING)
        
        # 统计存活玩家
        alive = self.get_alive_players()
        
        # 记录回合结果
        round_result = {
            "round": self.current_round,
            "alive_count": len(alive),
            "players": [p.to_dict() for p in alive],
        }
        self.round_results.append(round_result)
        
        # 回合结束回调
        if self._on_round_end:
            self._on_round_end(self.current_round, round_result)
        
        # 短暂等待
        await asyncio.sleep(3)
    
    def _check_game_end(self) -> bool:
        """
        检查游戏是否结束
        
        Returns:
            游戏是否结束
        """
        alive = self.get_alive_players()
        return len(alive) <= 1 or self.all_disconnected
    
    async def _end_game(self) -> None:
        """
        结束游戏
        
        计算最终排名和奖励
        """
        await self._set_state(RoomState.FINISHED)
        
        # 计算排名
        alive_players = self.get_alive_players()
        all_players = list(self.players.values())
        
        # 按存活状态和血量排序
        ranked = sorted(
            all_players,
            key=lambda p: (p.is_alive, p.hp if p.is_alive else 0),
            reverse=True,
        )
        
        # 生成最终结果
        results = {
            "room_id": self.room_id,
            "total_rounds": self.current_round,
            "rankings": [
                {
                    "rank": i + 1,
                    "player_id": p.player_id,
                    "nickname": p.nickname,
                    "hp": p.hp,
                    "level": p.level,
                    "gold": p.gold,
                    "is_alive": p.is_alive,
                }
                for i, p in enumerate(ranked)
            ],
        }
        
        logger.info(
            "游戏结束",
            room_id=self.room_id,
            total_rounds=self.current_round,
            winner_id=ranked[0].player_id if ranked else None,
        )
        
        # 游戏结束回调
        if self._on_game_end:
            self._on_game_end(results)
    
    async def force_end(self) -> None:
        """
        强制结束游戏
        
        房主或管理员可以调用
        """
        if self._phase_task:
            self._phase_task.cancel()
        
        await self._end_game()
    
    # ========================================================================
    # 数据同步
    # ========================================================================
    
    def get_room_state(self) -> Dict[str, Any]:
        """
        获取房间完整状态（用于同步）
        
        Returns:
            包含房间所有状态的字典
        """
        return {
            "room_id": self.room_id,
            "name": self.name,
            "state": self.state.value,
            "host_id": self.host_id,
            "max_players": self.max_players,
            "player_count": self.player_count,
            "alive_count": self.alive_count,
            "current_round": self.current_round,
            "phase_start_time": self.phase_start_time.isoformat() if self.phase_start_time else None,
            "players": [p.to_dict() for p in self.players.values()],
            "config": self.config,
        }
    
    def get_player_state(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        获取指定玩家的详细状态
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家状态字典
        """
        player = self.get_player(player_id)
        if not player:
            return None
        
        state = player.to_dict()
        state["heroes"] = player.heroes
        state["bench"] = player.bench
        state["board"] = player.board
        return state
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（简化版）"""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "state": self.state.value,
            "host_id": self.host_id,
            "player_count": self.player_count,
            "max_players": self.max_players,
            "current_round": self.current_round,
        }
    
    def __repr__(self) -> str:
        return (
            f"<GameRoom(id={self.room_id}, state={self.state.value}, "
            f"players={self.player_count}/{self.max_players}, round={self.current_round})>"
        )
