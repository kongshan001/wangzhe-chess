"""
王者之奕 - 集成测试模块

本模块包含所有集成测试：
- test_friendship_integration: 好友系统 + 组队 + 私聊
- test_crafting_integration: 装备合成系统与背包
- test_lineup_integration: 阵容预设与游戏流程
- test_daily_task_integration: 每日任务与对局
- test_leaderboard_integration: 排行榜数据更新
- test_checkin_integration: 签到系统与数据库
- test_synergypedia_integration: 羁绊图鉴与英雄池
- test_tutorial_integration: 新手引导与游戏流程
- test_custom_room_integration: 自定义房间与匹配系统

运行集成测试：
    pytest tests/integration -v

运行特定测试文件：
    pytest tests/integration/test_friendship_integration.py -v

运行带覆盖率：
    pytest tests/integration --cov=src --cov-report=html
"""

import pytest

# 标记所有集成测试
pytestmark = pytest.mark.integration
