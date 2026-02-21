"""
王者之奕 - 战斗模块

本模块包含战斗相关的子模块：
- simulator: 确定性战斗模拟器
"""

from .simulator import (
    BattleSimulator,
    BattleUnit,
    DeterministicRNG,
    create_test_board,
    create_test_hero,
    simulate_battle,
)

__all__ = [
    "BattleSimulator",
    "BattleUnit",
    "DeterministicRNG",
    "simulate_battle",
    "create_test_board",
    "create_test_hero",
]
