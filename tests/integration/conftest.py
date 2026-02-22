"""
王者之奕 - 集成测试配置

本模块提供集成测试所需的通用 fixtures：
- 测试数据库配置
- 跨模块测试工具
- 共享测试数据
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime

import pytest
import pytest_asyncio

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# 测试数据库配置
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)


# ============================================================================
# 事件循环
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# 数据库 Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_db_session():
    """创建测试数据库会话"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_engine():
    """创建测试数据库引擎"""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    
    yield engine
    
    await engine.dispose()


# ============================================================================
# 玩家 Fixtures
# ============================================================================

@pytest.fixture
def sample_player_id() -> str:
    """示例玩家ID"""
    return "test_player_001"


@pytest.fixture
def sample_friend_id() -> str:
    """示例好友ID"""
    return "test_friend_001"


@pytest.fixture
def sample_players() -> list[dict]:
    """创建多个测试玩家"""
    return [
        {
            "player_id": f"test_player_{i:03d}",
            "nickname": f"测试玩家{i}",
            "avatar": f"avatar_{i}.png",
            "tier": "bronze",
            "stars": 0,
        }
        for i in range(8)
    ]


# ============================================================================
# 英雄 Fixtures
# ============================================================================

@pytest.fixture
def sample_hero_config() -> dict:
    """示例英雄配置"""
    return {
        "hero_test_001": {
            "hero_id": "hero_test_001",
            "name": "测试战士",
            "cost": 1,
            "race": "人族",
            "profession": "战士",
            "base_hp": 500,
            "base_attack": 50,
            "base_defense": 30,
            "attack_speed": 0.7,
        },
        "hero_test_002": {
            "hero_id": "hero_test_002",
            "name": "测试法师",
            "cost": 2,
            "race": "神族",
            "profession": "法师",
            "base_hp": 400,
            "base_attack": 40,
            "base_defense": 20,
            "attack_speed": 0.8,
        },
        "hero_test_003": {
            "hero_id": "hero_test_003",
            "name": "测试刺客",
            "cost": 3,
            "race": "魔种",
            "profession": "刺客",
            "base_hp": 350,
            "base_attack": 70,
            "base_defense": 15,
            "attack_speed": 1.0,
        },
        "hero_test_004": {
            "hero_id": "hero_test_004",
            "name": "测试射手",
            "cost": 4,
            "race": "精灵",
            "profession": "射手",
            "base_hp": 380,
            "base_attack": 60,
            "base_defense": 20,
            "attack_speed": 0.9,
        },
        "hero_test_005": {
            "hero_id": "hero_test_005",
            "name": "测试坦克",
            "cost": 5,
            "race": "机械",
            "profession": "坦克",
            "base_hp": 800,
            "base_attack": 30,
            "base_defense": 50,
            "attack_speed": 0.5,
        },
    }


# ============================================================================
# 管理器 Fixtures
# ============================================================================

@pytest.fixture
def friendship_manager():
    """创建好友管理器"""
    from src.server.friendship import FriendshipManager
    return FriendshipManager()


@pytest.fixture
def crafting_manager():
    """创建装备合成管理器"""
    from src.server.game.crafting.manager import CraftingManager
    return CraftingManager()


@pytest.fixture
def checkin_manager():
    """创建签到管理器"""
    from src.server.checkin.manager import CheckinManager
    manager = CheckinManager()
    manager.clear_cache()
    return manager


@pytest.fixture
def leaderboard_manager():
    """创建排行榜管理器"""
    from src.server.leaderboard.manager import LeaderboardManager
    return LeaderboardManager()


@pytest.fixture
def tutorial_manager():
    """创建新手引导管理器"""
    from src.server.tutorial.manager import TutorialManager
    # 创建临时配置文件
    import json
    import tempfile
    
    config_data = {
        "version": "1.0.0",
        "tutorials": [
            {
                "tutorial_id": "tutorial_test_001",
                "name": "基础操作",
                "description": "学习游戏的基本操作",
                "tutorial_type": "basic",
                "required": True,
                "enabled": True,
                "sort_order": 1,
                "recommended_level": 1,
                "steps": [
                    {
                        "step_id": "step_001",
                        "order": 1,
                        "title": "移动英雄",
                        "description": "将英雄放置到棋盘上",
                        "action_type": "place_hero",
                        "action_target": "any",
                    },
                    {
                        "step_id": "step_002",
                        "order": 2,
                        "title": "购买英雄",
                        "description": "从商店购买一个英雄",
                        "action_type": "buy_hero",
                        "action_target": "any",
                    },
                ],
                "completion_reward": {
                    "reward_id": "tutorial_reward_001",
                    "gold": 100,
                    "exp": 50,
                },
            },
            {
                "tutorial_id": "tutorial_test_002",
                "name": "羁绊系统",
                "description": "了解羁绊如何工作",
                "tutorial_type": "synergy",
                "required": False,
                "enabled": True,
                "sort_order": 2,
                "recommended_level": 3,
                "prerequisites": ["tutorial_test_001"],
                "steps": [
                    {
                        "step_id": "step_003",
                        "order": 1,
                        "title": "收集英雄",
                        "description": "收集两个相同种族的英雄",
                        "action_type": "collect_synergy",
                        "action_target": "race_2",
                    },
                ],
                "completion_reward": {
                    "reward_id": "tutorial_reward_002",
                    "gold": 200,
                    "exp": 100,
                },
            },
        ],
    }
    
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    ) as f:
        json.dump(config_data, f, ensure_ascii=False)
        temp_path = f.name
    
    manager = TutorialManager(config_path=temp_path)
    yield manager
    
    # 清理
    os.unlink(temp_path)


@pytest.fixture
def synergypedia_manager(sample_hero_config):
    """创建羁绊图鉴管理器"""
    from src.server.synergypedia.manager import SynergypediaManager
    from src.server.game.synergy import SynergyManager
    
    # 创建英雄配置对象
    hero_configs = {}
    for hero_id, config in sample_hero_config.items():
        hero_configs[hero_id] = MagicMock(
            hero_id=hero_id,
            name=config["name"],
            cost=config["cost"],
            race=config["race"],
            profession=config["profession"],
            base_hp=config["base_hp"],
            base_attack=config["base_attack"],
            base_defense=config["base_defense"],
            attack_speed=config["attack_speed"],
        )
    
    manager = SynergypediaManager(
        synergy_manager=SynergyManager(),
        hero_configs=hero_configs,
    )
    return manager


@pytest.fixture
def custom_room_manager():
    """创建自定义房间管理器"""
    from src.server.custom_room.manager import CustomRoomManager
    return CustomRoomManager()


@pytest.fixture
def daily_task_manager():
    """创建每日任务管理器"""
    from src.server.daily_task.manager import DailyTaskManager
    return DailyTaskManager()


# ============================================================================
# 辅助函数
# ============================================================================

@pytest.fixture
def create_test_friendship(friendship_manager):
    """创建测试好友关系"""
    def _create(player1_id: str, player2_id: str):
        # 发送好友请求
        request = friendship_manager.send_friend_request(
            from_player_id=player1_id,
            to_player_id=player2_id,
            message="测试好友请求",
        )
        if request:
            friendship_manager.accept_friend_request(request.request_id)
        return friendship_manager.is_friend(player1_id, player2_id)
    return _create


@pytest.fixture
def create_test_inventory(crafting_manager):
    """创建测试装备背包"""
    def _create(equipment: dict[str, int], gold: int = 1000):
        from src.server.game.crafting.manager import PlayerInventory
        inventory = PlayerInventory(equipment=equipment.copy(), gold=gold)
        return inventory
    return _create


# ============================================================================
# 异步测试标记
# ============================================================================

def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "db: mark test requiring database"
    )
