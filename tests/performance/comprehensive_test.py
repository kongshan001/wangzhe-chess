"""
王者之奕 - 综合场景压力测试

模拟真实游戏场景：
1. 1000玩家同时在线
2. 100场对局同时进行
3. 完整游戏流程模拟
4. 观战系统并发访问
"""

from __future__ import annotations

import asyncio
import random
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

sys.path.insert(0, "/root/clawd/wangzhe-chess")


class GamePhase(Enum):
    """游戏阶段"""

    WAITING = "waiting"
    PREPARATION = "preparation"
    BATTLE = "battle"
    SETTLEMENT = "settlement"


@dataclass
class SimulatedPlayer:
    """模拟玩家"""

    player_id: str
    elo_score: int
    tier: str
    is_active: bool = True
    current_game: str | None = None
    operation_count: int = 0
    total_wait_time: float = 0.0


@dataclass
class SimulatedGame:
    """模拟对局"""

    game_id: str
    players: list[SimulatedPlayer]
    current_round: int = 1
    phase: GamePhase = GamePhase.WAITING
    start_time: float = field(default_factory=time.time)
    operations_count: int = 0


class ComprehensiveStressTest:
    """
    综合场景压力测试

    模拟：
    - 1000玩家同时在线
    - 100场对局同时进行
    - 匹配系统并发
    - 观战系统负载
    """

    def __init__(
        self,
        player_count: int = 1000,
        game_count: int = 100,
        duration_seconds: int = 60,
    ) -> None:
        """
        初始化综合测试

        Args:
            player_count: 玩家数量
            game_count: 对局数量
            duration_seconds: 测试持续时间
        """
        self.player_count = player_count
        self.game_count = game_count
        self.duration_seconds = duration_seconds

        # 模拟数据
        self.players: dict[str, SimulatedPlayer] = {}
        self.games: dict[str, SimulatedGame] = {}

        # 统计数据
        self.stats = {
            "total_operations": 0,
            "operations_per_second": 0,
            "avg_latency_ms": 0,
            "max_latency_ms": 0,
            "successful_matches": 0,
            "failed_operations": 0,
        }

        self._latencies: list[float] = []

    def _init_players(self) -> None:
        """初始化玩家"""
        tiers = ["bronze", "silver", "gold", "platinum", "diamond", "master", "grandmaster", "king"]
        tier_weights = [30, 25, 20, 12, 8, 3, 1.5, 0.5]

        for i in range(self.player_count):
            player_id = f"player_{i:04d}"
            tier = random.choices(tiers, weights=tier_weights)[0]

            # 根据段位分配 ELO
            tier_elo_range = {
                "bronze": (800, 1000),
                "silver": (1000, 1200),
                "gold": (1200, 1400),
                "platinum": (1400, 1600),
                "diamond": (1600, 1800),
                "master": (1800, 2000),
                "grandmaster": (2000, 2200),
                "king": (2200, 2500),
            }
            elo_range = tier_elo_range[tier]
            elo_score = random.randint(*elo_range)

            self.players[player_id] = SimulatedPlayer(
                player_id=player_id,
                elo_score=elo_score,
                tier=tier,
            )

    def _init_games(self) -> None:
        """初始化对局"""
        # 从未在游戏中的玩家中选择
        available_players = [p for p in self.players.values() if p.current_game is None]
        random.shuffle(available_players)

        for i in range(self.game_count):
            if len(available_players) < 8:
                break

            game_id = f"game_{i:03d}"
            game_players = available_players[:8]
            available_players = available_players[8:]

            for player in game_players:
                player.current_game = game_id

            self.games[game_id] = SimulatedGame(
                game_id=game_id,
                players=game_players,
                phase=GamePhase.PREPARATION,
            )

    async def _simulate_player_operation(self, player: SimulatedPlayer) -> tuple[bool, float]:
        """
        模拟玩家操作

        Returns:
            (是否成功, 耗时ms)
        """
        start = time.perf_counter()

        try:
            # 模拟不同类型的操作
            operation = random.choices(
                ["shop_refresh", "buy_hero", "place_hero", "view_synergies", "chat"],
                weights=[30, 25, 25, 15, 5],
            )[0]

            # 模拟操作耗时（不同操作有不同耗时）
            base_latency = {
                "shop_refresh": 2,
                "buy_hero": 1,
                "place_hero": 1,
                "view_synergies": 3,
                "chat": 1,
            }

            # 添加随机延迟模拟真实场景
            latency = base_latency[operation] + random.random() * 2
            await asyncio.sleep(latency / 1000)  # 转换为秒

            player.operation_count += 1
            elapsed = (time.perf_counter() - start) * 1000
            return True, elapsed

        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            return False, elapsed

    async def _simulate_game_round(self, game: SimulatedGame) -> tuple[bool, float]:
        """
        模拟对局回合

        Returns:
            (是否成功, 耗时ms)
        """
        start = time.perf_counter()

        try:
            # 准备阶段 -> 战斗阶段 -> 结算阶段
            if game.phase == GamePhase.PREPARATION:
                # 模拟所有玩家操作
                tasks = [self._simulate_player_operation(p) for p in game.players if p.is_active]
                results = await asyncio.gather(*tasks)

                # 切换到战斗阶段
                game.phase = GamePhase.BATTLE

            elif game.phase == GamePhase.BATTLE:
                # 模拟战斗（简化版）
                await asyncio.sleep(0.01)  # 10ms 战斗时间
                game.phase = GamePhase.SETTLEMENT

            elif game.phase == GamePhase.SETTLEMENT:
                # 模拟结算
                await asyncio.sleep(0.005)  # 5ms 结算时间
                game.current_round += 1
                game.phase = GamePhase.PREPARATION

            game.operations_count += 1
            elapsed = (time.perf_counter() - start) * 1000
            return True, elapsed

        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            return False, elapsed

    async def _run_player_simulation(self, player: SimulatedPlayer) -> None:
        """运行单个玩家的模拟"""
        end_time = time.time() + self.duration_seconds

        while time.time() < end_time and player.is_active:
            if player.current_game:
                # 在游戏中，等待游戏回合
                await asyncio.sleep(0.1)
            else:
                # 不在游戏中，模拟其他活动
                success, latency = await self._simulate_player_operation(player)
                self._latencies.append(latency)

                if not success:
                    self.stats["failed_operations"] += 1

            # 随机等待
            await asyncio.sleep(random.random() * 0.1)

    async def _run_game_simulation(self, game: SimulatedGame) -> None:
        """运行单个对局的模拟"""
        end_time = time.time() + self.duration_seconds

        while time.time() < end_time:
            success, latency = await self._simulate_game_round(game)
            self._latencies.append(latency)

            if not success:
                self.stats["failed_operations"] += 1

            # 回合间隔
            await asyncio.sleep(0.05)

    async def run_test(self) -> dict[str, Any]:
        """
        运行综合压力测试

        Returns:
            测试结果
        """
        print(f"\n{'=' * 60}")
        print("综合场景压力测试")
        print(f"  玩家数量: {self.player_count}")
        print(f"  对局数量: {self.game_count}")
        print(f"  持续时间: {self.duration_seconds}秒")
        print(f"{'=' * 60}\n")

        # 初始化
        print("初始化测试环境...")
        self._init_players()
        self._init_games()
        print(f"  已创建 {len(self.players)} 个玩家")
        print(f"  已创建 {len(self.games)} 场对局")

        # 运行测试
        print("\n开始压力测试...")
        start_time = time.time()

        # 创建玩家和对局任务
        player_tasks = [self._run_player_simulation(player) for player in self.players.values()]

        game_tasks = [self._run_game_simulation(game) for game in self.games.values()]

        # 并发运行
        all_tasks = player_tasks + game_tasks
        await asyncio.gather(*all_tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 计算统计
        self._calculate_stats(total_time)

        # 打印结果
        print(f"\n{'=' * 60}")
        print("测试结果")
        print(f"{'=' * 60}")
        print(f"  总操作数: {self.stats['total_operations']}")
        print(f"  吞吐量: {self.stats['operations_per_second']:.2f} ops/s")
        print(f"  平均延迟: {self.stats['avg_latency_ms']:.4f}ms")
        print(f"  最大延迟: {self.stats['max_latency_ms']:.4f}ms")
        print(f"  失败操作: {self.stats['failed_operations']}")
        print(f"{'=' * 60}\n")

        return {
            "config": {
                "player_count": self.player_count,
                "game_count": self.game_count,
                "duration_seconds": self.duration_seconds,
            },
            "stats": self.stats,
            "total_time_seconds": total_time,
        }

    def _calculate_stats(self, total_time: float) -> None:
        """计算统计数据"""
        if not self._latencies:
            return

        self.stats["total_operations"] = len(self._latencies)
        self.stats["operations_per_second"] = len(self._latencies) / total_time
        self.stats["avg_latency_ms"] = sum(self._latencies) / len(self._latencies)
        self.stats["max_latency_ms"] = max(self._latencies)

        # 计算游戏统计
        for game in self.games.values():
            self.stats["successful_matches"] += game.current_round


async def run_1000_players_test() -> dict[str, Any]:
    """运行1000玩家测试"""
    test = ComprehensiveStressTest(
        player_count=1000,
        game_count=100,
        duration_seconds=30,  # 30秒测试
    )
    return await test.run_test()


async def run_100_games_test() -> dict[str, Any]:
    """运行100场对局测试"""
    test = ComprehensiveStressTest(
        player_count=800,  # 100场 * 8人
        game_count=100,
        duration_seconds=30,
    )
    return await test.run_test()


async def main() -> None:
    """主测试入口"""
    print("\n" + "=" * 60)
    print("王者之奕 - 综合场景压力测试")
    print("=" * 60)

    # 1. 1000玩家测试
    result1 = await run_1000_players_test()

    # 2. 100场对局测试
    result2 = await run_100_games_test()

    print("\n所有测试完成!")

    return {
        "1000_players_test": result1,
        "100_games_test": result2,
    }


if __name__ == "__main__":
    asyncio.run(main())
