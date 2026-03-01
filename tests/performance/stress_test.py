"""
王者之奕 - 压力测试套件

本模块包含完整的压力测试：
1. 战斗模拟器压力测试
2. 匹配系统并发测试
3. 英雄池性能测试
4. 观战系统负载测试
5. 综合场景测试

运行方式:
    pytest tests/performance/ -v
    python -m tests.performance.run_stress_test
"""

from __future__ import annotations

import asyncio
import os
import random
import statistics

# 设置路径
import sys
import time
from dataclasses import dataclass
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"
    ),
)

from server.game.battle.simulator import (
    BattleSimulator,
    create_test_board,
    create_test_hero,
)
from server.game.hero_pool import (
    SAMPLE_HEROES_CONFIG,
    HeroConfigLoader,
    SharedHeroPool,
    ShopManager,
)
from server.match.queue import (
    MatchQueue,
    QueueConfig,
)
from server.match.rating import PlayerRating, Tier
from server.spectator.manager import SpectatorManager


@dataclass
class PerformanceMetrics:
    """性能指标"""

    name: str
    total_time_ms: float
    operations: int
    ops_per_second: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    memory_used_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_time_ms": round(self.total_time_ms, 2),
            "operations": self.operations,
            "ops_per_second": round(self.ops_per_second, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 4),
            "min_latency_ms": round(self.min_latency_ms, 4),
            "max_latency_ms": round(self.max_latency_ms, 4),
            "p50_ms": round(self.p50_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "p99_ms": round(self.p99_ms, 4),
            "memory_used_mb": round(self.memory_used_mb, 2),
        }


class BattleSimulatorStressTest:
    """战斗模拟器压力测试"""

    def __init__(self) -> None:
        self.results: list[PerformanceMetrics] = []

    async def test_single_battle(self) -> float:
        """测试单场战斗耗时"""
        # 创建测试棋盘
        heroes_a = [create_test_hero(f"hero_a_{i}", f"英雄A{i}") for i in range(5)]
        heroes_b = [create_test_hero(f"hero_b_{i}", f"英雄B{i}") for i in range(5)]

        board_a = create_test_board("player_a", heroes_a)
        board_b = create_test_board("player_b", heroes_b)

        # 模拟战斗
        start = time.perf_counter()
        simulator = BattleSimulator(board_a, board_b, random_seed=42)
        result = simulator.simulate()
        elapsed = (time.perf_counter() - start) * 1000

        return elapsed

    async def test_100_battles_sequential(self) -> PerformanceMetrics:
        """测试100场战斗（顺序执行）"""
        latencies = []
        start = time.perf_counter()

        for i in range(100):
            elapsed = await self.test_single_battle()
            latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics("100场战斗(顺序)", latencies, total_time)

    async def test_1000_battles_concurrent(self, batch_size: int = 100) -> PerformanceMetrics:
        """测试1000场战斗（并发执行）"""
        latencies = []
        total_ops = 1000
        start = time.perf_counter()

        for batch_start in range(0, total_ops, batch_size):
            batch_end = min(batch_start + batch_size, total_ops)
            tasks = [self.test_single_battle() for _ in range(batch_end - batch_start)]
            batch_results = await asyncio.gather(*tasks)
            latencies.extend(batch_results)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics("1000场战斗(并发)", latencies, total_time)

    async def test_large_battle(self, hero_count: int = 20) -> PerformanceMetrics:
        """测试大规模战斗（每方20个英雄）"""
        latencies = []
        iterations = 50

        for _ in range(iterations):
            heroes_a = [create_test_hero(f"hero_a_{i}", f"英雄A{i}") for i in range(hero_count)]
            heroes_b = [create_test_hero(f"hero_b_{i}", f"英雄B{i}") for i in range(hero_count)]

            board_a = create_test_board("player_a", heroes_a)
            board_b = create_test_board("player_b", heroes_b)

            start = time.perf_counter()
            simulator = BattleSimulator(board_a, board_b, random_seed=42)
            simulator.simulate()
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        return self._calculate_metrics(f"大规模战斗({hero_count}v{hero_count})", latencies)

    def _calculate_metrics(
        self,
        name: str,
        latencies: list[float],
        total_time_ms: float | None = None,
    ) -> PerformanceMetrics:
        """计算性能指标"""
        if not latencies:
            return PerformanceMetrics(
                name=name,
                total_time_ms=0,
                operations=0,
                ops_per_second=0,
                avg_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
            )

        sorted_latencies = sorted(latencies)
        total_time = total_time_ms or sum(latencies)

        return PerformanceMetrics(
            name=name,
            total_time_ms=total_time,
            operations=len(latencies),
            ops_per_second=len(latencies) / (total_time / 1000) if total_time > 0 else 0,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_ms=sorted_latencies[int(len(sorted_latencies) * 0.5)],
            p95_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        )

    async def run_all(self) -> list[PerformanceMetrics]:
        """运行所有测试"""
        print("\n=== 战斗模拟器压力测试 ===")

        print("测试单场战斗...")
        single_time = await self.test_single_battle()
        print(f"  单场战斗耗时: {single_time:.2f}ms")

        print("测试100场顺序战斗...")
        result1 = await self.test_100_battles_sequential()
        self.results.append(result1)
        print(
            f"  总耗时: {result1.total_time_ms:.2f}ms, 吞吐量: {result1.ops_per_second:.2f} ops/s"
        )

        print("测试1000场并发战斗...")
        result2 = await self.test_1000_battles_concurrent()
        self.results.append(result2)
        print(
            f"  总耗时: {result2.total_time_ms:.2f}ms, 吞吐量: {result2.ops_per_second:.2f} ops/s"
        )

        print("测试大规模战斗...")
        result3 = await self.test_large_battle()
        self.results.append(result3)
        print(f"  平均耗时: {result3.avg_latency_ms:.2f}ms")

        return self.results


class MatchQueueStressTest:
    """匹配队列压力测试"""

    def __init__(self) -> None:
        self.results: list[PerformanceMetrics] = []

    async def test_join_queue(self, queue: MatchQueue, count: int) -> PerformanceMetrics:
        """测试加入队列性能"""
        latencies = []
        start = time.perf_counter()

        for i in range(count):
            player_id = f"player_{i}"
            rating = PlayerRating(
                player_id=player_id,
                tier=random.choice(list(Tier)),
                stars=random.randint(0, 100),
            )
            elo_score = random.randint(1000, 2000)

            join_start = time.perf_counter()
            await queue.join(player_id, rating, elo_score)
            elapsed = (time.perf_counter() - join_start) * 1000
            latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(f"加入队列({count}玩家)", latencies, total_time)

    async def test_match_processing(
        self, queue: MatchQueue, player_count: int
    ) -> PerformanceMetrics:
        """测试匹配处理性能"""
        # 先加入玩家
        for i in range(player_count):
            player_id = f"match_player_{i}"
            rating = PlayerRating(
                player_id=player_id,
                tier=random.choice(list(Tier)),
                stars=random.randint(0, 100),
            )
            await queue.join(player_id, rating, random.randint(1000, 2000))

        # 测试匹配处理
        latencies = []
        iterations = 100

        for _ in range(iterations):
            start = time.perf_counter()
            matches = await queue._process_matches()
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        return self._calculate_metrics(f"匹配处理({player_count}玩家)", latencies)

    async def test_concurrent_operations(self, player_count: int = 500) -> PerformanceMetrics:
        """测试并发操作"""
        config = QueueConfig(max_queue_size=2000)
        queue = MatchQueue(config)

        latencies = []
        start = time.perf_counter()

        # 并发加入
        async def join_player(i: int):
            player_id = f"concurrent_player_{i}"
            rating = PlayerRating(
                player_id=player_id,
                tier=random.choice(list(Tier)),
                stars=random.randint(0, 100),
            )
            join_start = time.perf_counter()
            await queue.join(player_id, rating, random.randint(1000, 2000))
            return (time.perf_counter() - join_start) * 1000

        # 分批执行
        batch_size = 50
        for batch_start in range(0, player_count, batch_size):
            batch_end = min(batch_start + batch_size, player_count)
            tasks = [join_player(i) for i in range(batch_start, batch_end)]
            batch_latencies = await asyncio.gather(*tasks)
            latencies.extend(batch_latencies)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(f"并发加入({player_count}玩家)", latencies, total_time)

    def _calculate_metrics(
        self,
        name: str,
        latencies: list[float],
        total_time_ms: float | None = None,
    ) -> PerformanceMetrics:
        """计算性能指标"""
        if not latencies:
            return PerformanceMetrics(
                name=name,
                total_time_ms=0,
                operations=0,
                ops_per_second=0,
                avg_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
            )

        sorted_latencies = sorted(latencies)
        total_time = total_time_ms or sum(latencies)

        return PerformanceMetrics(
            name=name,
            total_time_ms=total_time,
            operations=len(latencies),
            ops_per_second=len(latencies) / (total_time / 1000) if total_time > 0 else 0,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_ms=sorted_latencies[int(len(sorted_latencies) * 0.5)],
            p95_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        )

    async def run_all(self) -> list[PerformanceMetrics]:
        """运行所有测试"""
        print("\n=== 匹配队列压力测试 ===")

        config = QueueConfig(max_queue_size=2000)
        queue = MatchQueue(config)

        print("测试加入队列(1000玩家)...")
        result1 = await self.test_join_queue(queue, 1000)
        self.results.append(result1)
        print(
            f"  总耗时: {result1.total_time_ms:.2f}ms, 吞吐量: {result1.ops_per_second:.2f} ops/s"
        )

        # 清空队列
        await queue.clear()

        print("测试并发操作(500玩家)...")
        result2 = await self.test_concurrent_operations(500)
        self.results.append(result2)
        print(f"  总耗时: {result2.total_time_ms:.2f}ms, P95延迟: {result2.p95_ms:.2f}ms")

        print("测试匹配处理(100玩家)...")
        result3 = await self.test_match_processing(queue, 100)
        self.results.append(result3)
        print(f"  平均处理时间: {result3.avg_latency_ms:.4f}ms")

        return self.results


class HeroPoolStressTest:
    """英雄池性能测试"""

    def __init__(self) -> None:
        self.results: list[PerformanceMetrics] = []

    def test_shop_refresh(self, iterations: int = 1000) -> PerformanceMetrics:
        """测试商店刷新性能"""
        config_loader = HeroConfigLoader()
        config_loader.load_from_dict(SAMPLE_HEROES_CONFIG)

        hero_pool = SharedHeroPool(config_loader, seed=42)
        shop_manager = ShopManager(hero_pool, player_level=5)

        latencies = []
        start = time.perf_counter()

        for _ in range(iterations):
            refresh_start = time.perf_counter()
            shop_manager.refresh_shop()
            elapsed = (time.perf_counter() - refresh_start) * 1000
            latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(f"商店刷新({iterations}次)", latencies, total_time)

    def test_hero_draw(self, iterations: int = 5000) -> PerformanceMetrics:
        """测试英雄抽取性能"""
        config_loader = HeroConfigLoader()
        config_loader.load_from_dict(SAMPLE_HEROES_CONFIG)

        hero_pool = SharedHeroPool(config_loader, seed=42)

        latencies = []
        start = time.perf_counter()

        for _ in range(iterations):
            cost = random.randint(1, 5)
            draw_start = time.perf_counter()
            hero_pool.draw_random_hero(cost)
            elapsed = (time.perf_counter() - draw_start) * 1000
            latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(f"英雄抽取({iterations}次)", latencies, total_time)

    def _calculate_metrics(
        self,
        name: str,
        latencies: list[float],
        total_time_ms: float | None = None,
    ) -> PerformanceMetrics:
        """计算性能指标"""
        if not latencies:
            return PerformanceMetrics(
                name=name,
                total_time_ms=0,
                operations=0,
                ops_per_second=0,
                avg_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
            )

        sorted_latencies = sorted(latencies)
        total_time = total_time_ms or sum(latencies)

        return PerformanceMetrics(
            name=name,
            total_time_ms=total_time,
            operations=len(latencies),
            ops_per_second=len(latencies) / (total_time / 1000) if total_time > 0 else 0,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_ms=sorted_latencies[int(len(sorted_latencies) * 0.5)],
            p95_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        )

    def run_all(self) -> list[PerformanceMetrics]:
        """运行所有测试"""
        print("\n=== 英雄池性能测试 ===")

        print("测试商店刷新(1000次)...")
        result1 = self.test_shop_refresh(1000)
        self.results.append(result1)
        print(
            f"  平均耗时: {result1.avg_latency_ms:.4f}ms, 吞吐量: {result1.ops_per_second:.2f} ops/s"
        )

        print("测试英雄抽取(5000次)...")
        result2 = self.test_hero_draw(5000)
        self.results.append(result2)
        print(
            f"  平均耗时: {result2.avg_latency_ms:.4f}ms, 吞吐量: {result2.ops_per_second:.2f} ops/s"
        )

        return self.results


class SpectatorStressTest:
    """观战系统负载测试"""

    def __init__(self) -> None:
        self.results: list[PerformanceMetrics] = []

    async def test_create_sessions(
        self, game_count: int = 100, spectators_per_game: int = 10
    ) -> PerformanceMetrics:
        """测试创建观战会话"""
        manager = SpectatorManager()

        # 创建对局
        for i in range(game_count):
            manager.create_spectatable_game(f"game_{i}")

        latencies = []
        start = time.perf_counter()

        for g in range(game_count):
            for s in range(spectators_per_game):
                spectator_id = f"spectator_{g}_{s}"
                create_start = time.perf_counter()
                manager.create_session(spectator_id, f"game_{g}", "player_1")
                elapsed = (time.perf_counter() - create_start) * 1000
                latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(
            f"创建观战会话({game_count}x{spectators_per_game})", latencies, total_time
        )

    async def test_state_updates(
        self, game_count: int = 100, updates: int = 50
    ) -> PerformanceMetrics:
        """测试状态更新"""
        manager = SpectatorManager()

        # 创建对局
        for i in range(game_count):
            manager.create_spectatable_game(f"game_{i}")

        latencies = []
        start = time.perf_counter()

        for _ in range(updates):
            for g in range(game_count):
                push_start = time.perf_counter()
                manager.push_game_state(
                    f"game_{g}",
                    round_num=1,
                    phase="battle",
                    player_states={"player_1": {"hp": 100}},
                )
                elapsed = (time.perf_counter() - push_start) * 1000
                latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(f"状态更新({game_count}x{updates})", latencies, total_time)

    async def test_chat_messages(
        self, game_count: int = 50, messages_per_game: int = 100
    ) -> PerformanceMetrics:
        """测试弹幕系统"""
        manager = SpectatorManager()

        # 创建对局
        for i in range(game_count):
            manager.create_spectatable_game(f"game_{i}")

        latencies = []
        start = time.perf_counter()

        for g in range(game_count):
            for m in range(messages_per_game):
                send_start = time.perf_counter()
                manager.send_chat(f"game_{g}", f"sender_{m}", f"用户{m}", f"测试消息 {m}")
                elapsed = (time.perf_counter() - send_start) * 1000
                latencies.append(elapsed)

        total_time = (time.perf_counter() - start) * 1000

        return self._calculate_metrics(
            f"弹幕消息({game_count}x{messages_per_game})", latencies, total_time
        )

    def _calculate_metrics(
        self,
        name: str,
        latencies: list[float],
        total_time_ms: float | None = None,
    ) -> PerformanceMetrics:
        """计算性能指标"""
        if not latencies:
            return PerformanceMetrics(
                name=name,
                total_time_ms=0,
                operations=0,
                ops_per_second=0,
                avg_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
            )

        sorted_latencies = sorted(latencies)
        total_time = total_time_ms or sum(latencies)

        return PerformanceMetrics(
            name=name,
            total_time_ms=total_time,
            operations=len(latencies),
            ops_per_second=len(latencies) / (total_time / 1000) if total_time > 0 else 0,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_ms=sorted_latencies[int(len(sorted_latencies) * 0.5)],
            p95_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        )

    async def run_all(self) -> list[PerformanceMetrics]:
        """运行所有测试"""
        print("\n=== 观战系统负载测试 ===")

        print("测试创建观战会话(100对局 x 10观众)...")
        result1 = await self.test_create_sessions(100, 10)
        self.results.append(result1)
        print(
            f"  总耗时: {result1.total_time_ms:.2f}ms, 吞吐量: {result1.ops_per_second:.2f} ops/s"
        )

        print("测试状态更新(100对局 x 50次)...")
        result2 = await self.test_state_updates(100, 50)
        self.results.append(result2)
        print(f"  总耗时: {result2.total_time_ms:.2f}ms, P95延迟: {result2.p95_ms:.4f}ms")

        print("测试弹幕系统(50对局 x 100消息)...")
        result3 = await self.test_chat_messages(50, 100)
        self.results.append(result3)
        print(
            f"  总耗时: {result3.total_time_ms:.2f}ms, 吞吐量: {result3.ops_per_second:.2f} msgs/s"
        )

        return self.results


async def run_comprehensive_test() -> dict[str, Any]:
    """运行综合压力测试"""
    print("\n" + "=" * 60)
    print("王者之奕 - 综合压力测试")
    print("=" * 60)

    start_time = time.time()
    all_results = {}

    # 1. 战斗模拟器测试
    battle_test = BattleSimulatorStressTest()
    all_results["battle_simulator"] = [r.to_dict() for r in await battle_test.run_all()]

    # 2. 匹配队列测试
    match_test = MatchQueueStressTest()
    all_results["match_queue"] = [r.to_dict() for r in await match_test.run_all()]

    # 3. 英雄池测试
    hero_pool_test = HeroPoolStressTest()
    all_results["hero_pool"] = [r.to_dict() for r in hero_pool_test.run_all()]

    # 4. 观战系统测试
    spectator_test = SpectatorStressTest()
    all_results["spectator"] = [r.to_dict() for r in await spectator_test.run_all()]

    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print(f"测试完成! 总耗时: {total_time:.2f}秒")
    print("=" * 60)

    return {
        "total_time_seconds": total_time,
        "results": all_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


if __name__ == "__main__":
    results = asyncio.run(run_comprehensive_test())
    print("\n结果:", results)
