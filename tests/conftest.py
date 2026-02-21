"""
王者之奕 - pytest 配置和共享 fixtures

本模块提供测试所需的通用 fixtures，包括：
- 测试用英雄数据
- 测试用玩家数据
- 测试用棋盘数据
- 各种模拟对象
"""

import sys
from pathlib import Path
from typing import Any

import pytest

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from shared.constants import (
    BASE_INCOME_PER_ROUND,
    BENCH_SIZE,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    HERO_POOL_COUNTS,
    INITIAL_PLAYER_HP,
    INTEREST_INCREMENT,
    LEVEL_UP_EXP,
    MAX_HERO_COST,
    MAX_HERO_STAR,
    MAX_INTEREST_GOLD,
    MAX_PLAYER_LEVEL,
    MIN_HERO_COST,
    REFRESH_PROBABILITY,
    SHOP_SLOT_COUNT,
)
from shared.models import (
    ActiveSynergy,
    BattleResult,
    Board,
    DamageEvent,
    DamageType,
    DeathEvent,
    Hero,
    HeroState,
    HeroTemplate,
    Player,
    PlayerState,
    Position,
    Shop,
    ShopSlot,
    Skill,
    SkillEvent,
    Synergy,
    SynergyLevel,
    SynergyType,
)
from server.game.battle.simulator import BattleSimulator, BattleUnit, DeterministicRNG
from server.game.economy import EconomyManager, EconomyState, IncomeBreakdown
from server.game.hero_pool import (
    HeroConfigLoader,
    HeroFactory,
    SharedHeroPool,
    ShopManager,
    SAMPLE_HEROES_CONFIG,
)
from server.game.synergy import SynergyManager, RACE_SYNERGIES, PROFESSION_SYNERGIES


# ============================================================================
# 基础配置
# ============================================================================

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "deterministic: mark test as requiring deterministic behavior"
    )


# ============================================================================
# 英雄相关 fixtures
# ============================================================================

@pytest.fixture
def sample_skill() -> Skill:
    """创建示例技能"""
    return Skill(
        name="火球术",
        description="发射一枚火球",
        mana_cost=50,
        damage=100,
        damage_type=DamageType.MAGICAL,
        target_type="single",
    )


@pytest.fixture
def sample_hero_template(sample_skill: Skill) -> HeroTemplate:
    """创建示例英雄模板"""
    return HeroTemplate(
        hero_id="test_hero_001",
        name="测试英雄",
        cost=1,
        race="人族",
        profession="战士",
        base_hp=500,
        base_attack=50,
        base_defense=30,
        attack_speed=0.7,
        skill=sample_skill,
    )


@pytest.fixture
def sample_hero_templates() -> list[HeroTemplate]:
    """创建多个示例英雄模板（不同费用）"""
    templates = []
    for cost in range(1, 6):
        template = HeroTemplate(
            hero_id=f"test_hero_cost_{cost}",
            name=f"测试英雄{cost}费",
            cost=cost,
            race=["人族", "神族", "魔种", "亡灵", "龙族"][cost - 1],
            profession=["战士", "法师", "刺客", "射手", "坦克"][cost - 1],
            base_hp=400 + cost * 100,
            base_attack=40 + cost * 15,
            base_defense=20 + cost * 10,
            attack_speed=0.6 + cost * 0.05,
            skill=Skill(
                name=f"技能{cost}",
                description=f"测试技能{cost}",
                mana_cost=40 + cost * 10,
                damage=80 + cost * 50,
                damage_type=DamageType.MAGICAL,
                target_type="single",
            ),
        )
        templates.append(template)
    return templates


@pytest.fixture
def sample_hero(sample_hero_template: HeroTemplate) -> Hero:
    """创建示例英雄实例"""
    return Hero.create_from_template(
        sample_hero_template,
        instance_id="test_instance_001",
        star=1,
    )


@pytest.fixture
def sample_heroes(sample_hero_templates: list[HeroTemplate]) -> list[Hero]:
    """创建多个示例英雄实例"""
    heroes = []
    for i, template in enumerate(sample_hero_templates):
        hero = Hero.create_from_template(
            template,
            instance_id=f"test_instance_{i:03d}",
            star=1,
        )
        heroes.append(hero)
    return heroes


@pytest.fixture
def two_star_hero(sample_hero_template: HeroTemplate) -> Hero:
    """创建2星英雄"""
    return Hero.create_from_template(
        sample_hero_template,
        instance_id="test_instance_2star",
        star=2,
    )


@pytest.fixture
def three_star_hero(sample_hero_template: HeroTemplate) -> Hero:
    """创建3星英雄"""
    return Hero.create_from_template(
        sample_hero_template,
        instance_id="test_instance_3star",
        star=3,
    )


# ============================================================================
# 棋盘相关 fixtures
# ============================================================================

@pytest.fixture
def empty_board() -> Board:
    """创建空棋盘"""
    return Board.create_empty(owner_id="test_player")


@pytest.fixture
def sample_board(sample_heroes: list[Hero]) -> Board:
    """创建带有英雄的棋盘"""
    board = Board.create_empty(owner_id="test_player")
    positions = [
        Position(x=0, y=0),
        Position(x=1, y=0),
        Position(x=2, y=0),
        Position(x=0, y=1),
        Position(x=1, y=1),
    ]
    for hero, pos in zip(sample_heroes[:5], positions):
        board.place_hero(hero, pos)
    return board


@pytest.fixture
def battle_board() -> tuple[Board, Board]:
    """创建用于战斗测试的两个棋盘"""
    # 创建玩家A的棋盘
    hero_a = Hero(
        instance_id="hero_a_001",
        template_id="template_a",
        name="英雄A",
        cost=1,
        star=1,
        race="人族",
        profession="战士",
        max_hp=500,
        hp=500,
        attack=50,
        defense=30,
        attack_speed=0.7,
        skill=Skill(name="技能A", mana_cost=50, damage=100),
        position=Position(x=0, y=0),
    )
    board_a = Board.create_empty(owner_id="player_a")
    board_a.place_hero(hero_a, Position(x=0, y=0))

    # 创建玩家B的棋盘
    hero_b = Hero(
        instance_id="hero_b_001",
        template_id="template_b",
        name="英雄B",
        cost=1,
        star=1,
        race="魔种",
        profession="刺客",
        max_hp=400,
        hp=400,
        attack=60,
        defense=20,
        attack_speed=0.8,
        skill=Skill(name="技能B", mana_cost=40, damage=80),
        position=Position(x=7, y=7),
    )
    board_b = Board.create_empty(owner_id="player_b")
    board_b.place_hero(hero_b, Position(x=7, y=7))

    return board_a, board_b


# ============================================================================
# 玩家相关 fixtures
# ============================================================================

@pytest.fixture
def sample_player() -> Player:
    """创建示例玩家"""
    return Player(
        player_id="test_player_001",
        hp=INITIAL_PLAYER_HP,
        gold=10,
        level=1,
        exp=0,
    )


@pytest.fixture
def sample_players() -> list[Player]:
    """创建多个示例玩家（模拟8人游戏）"""
    players = []
    for i in range(8):
        player = Player(
            player_id=f"player_{i:03d}",
            hp=INITIAL_PLAYER_HP,
            gold=10,
            level=1,
        )
        players.append(player)
    return players


@pytest.fixture
def player_with_heroes(sample_player: Player, sample_heroes: list[Hero]) -> Player:
    """创建拥有英雄的玩家"""
    # 添加英雄到备战席
    for hero in sample_heroes[:3]:
        sample_player.add_to_bench(hero)
    
    # 放置英雄到棋盘
    if len(sample_heroes) > 3:
        sample_player.board.place_hero(sample_heroes[3], Position(x=0, y=0))
        sample_player.board.place_hero(sample_heroes[4], Position(x=1, y=0))
    
    return sample_player


# ============================================================================
# 英雄池相关 fixtures
# ============================================================================

@pytest.fixture
def hero_config_loader() -> HeroConfigLoader:
    """创建英雄配置加载器（使用示例配置）"""
    loader = HeroConfigLoader()
    loader.load_from_dict(SAMPLE_HEROES_CONFIG)
    return loader


@pytest.fixture
def shared_hero_pool(hero_config_loader: HeroConfigLoader) -> SharedHeroPool:
    """创建共享英雄池（固定种子用于测试）"""
    return SharedHeroPool(hero_config_loader, seed=42)


@pytest.fixture
def hero_factory(hero_config_loader: HeroConfigLoader) -> HeroFactory:
    """创建英雄工厂"""
    return HeroFactory(hero_config_loader)


@pytest.fixture
def shop_manager(shared_hero_pool: SharedHeroPool) -> ShopManager:
    """创建商店管理器"""
    return ShopManager(shared_hero_pool, player_level=1, seed=42)


# ============================================================================
# 羁绊相关 fixtures
# ============================================================================

@pytest.fixture
def synergy_manager() -> SynergyManager:
    """创建羁绊管理器"""
    return SynergyManager()


@pytest.fixture
def sample_synergies() -> list[Synergy]:
    """创建示例羁绊"""
    return [
        Synergy(
            name="人族",
            synergy_type=SynergyType.RACE,
            description="人族羁绊",
            levels=[
                SynergyLevel(required_count=2, effect_description="2人族"),
                SynergyLevel(required_count=4, effect_description="4人族"),
            ],
        ),
        Synergy(
            name="战士",
            synergy_type=SynergyType.CLASS,
            description="战士羁绊",
            levels=[
                SynergyLevel(required_count=2, effect_description="2战士"),
                SynergyLevel(required_count=4, effect_description="4战士"),
            ],
        ),
    ]


# ============================================================================
# 经济相关 fixtures
# ============================================================================

@pytest.fixture
def economy_manager() -> EconomyManager:
    """创建经济管理器"""
    return EconomyManager(initial_gold=10)


@pytest.fixture
def economy_state() -> EconomyState:
    """创建经济状态"""
    return EconomyState(
        gold=20,
        level=3,
        exp=5,
        win_streak=3,
        lose_streak=0,
    )


# ============================================================================
# 战斗相关 fixtures
# ============================================================================

@pytest.fixture
def deterministic_rng() -> DeterministicRNG:
    """创建确定性随机数生成器"""
    return DeterministicRNG(seed=42)


@pytest.fixture
def battle_unit(sample_hero: Hero) -> BattleUnit:
    """创建战斗单元"""
    return BattleUnit(hero=sample_hero, team=0)


@pytest.fixture
def battle_simulator(battle_board: tuple[Board, Board]) -> BattleSimulator:
    """创建战斗模拟器"""
    board_a, board_b = battle_board
    return BattleSimulator(board_a, board_b, random_seed=42)


# ============================================================================
# 房间相关 fixtures（模拟房间类）
# ============================================================================

class MockRoom:
    """
    模拟房间类（用于测试）
    
    由于当前项目没有房间管理模块，这里创建一个模拟类用于测试。
    """
    
    def __init__(self, room_id: str, max_players: int = 8):
        self.room_id = room_id
        self.max_players = max_players
        self.players: dict[str, Player] = {}
        self.state = "waiting"
        self.current_round = 0
        self._round_results: dict[str, Any] = {}
    
    def add_player(self, player: Player) -> bool:
        if len(self.players) >= self.max_players:
            return False
        if player.player_id in self.players:
            return False
        self.players[player.player_id] = player
        return True
    
    def remove_player(self, player_id: str) -> bool:
        if player_id not in self.players:
            return False
        del self.players[player_id]
        return True
    
    def get_player_count(self) -> int:
        return len(self.players)
    
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players
    
    def can_start(self) -> bool:
        return len(self.players) >= 2
    
    def start_game(self) -> bool:
        if not self.can_start():
            return False
        self.state = "preparing"
        self.current_round = 1
        return True
    
    def next_round(self) -> bool:
        if self.state == "game_over":
            return False
        self.current_round += 1
        return True
    
    def end_game(self) -> None:
        self.state = "game_over"
    
    def get_alive_players(self) -> list[Player]:
        return [p for p in self.players.values() if p.is_alive()]


@pytest.fixture
def mock_room() -> MockRoom:
    """创建模拟房间"""
    return MockRoom(room_id="test_room_001")


@pytest.fixture
def mock_room_with_players(sample_players: list[Player]) -> MockRoom:
    """创建带有玩家的模拟房间"""
    room = MockRoom(room_id="test_room_full")
    for player in sample_players[:8]:
        room.add_player(player)
    return room


# ============================================================================
# 辅助函数 fixtures
# ============================================================================

@pytest.fixture
def create_test_hero():
    """创建测试英雄的工厂函数"""
    def _create(
        instance_id: str,
        name: str = "测试英雄",
        hp: int = 500,
        attack: int = 50,
        defense: int = 30,
        attack_speed: float = 1.0,
        mana_cost: int = 50,
        skill_damage: int = 100,
        race: str = "人族",
        profession: str = "战士",
        star: int = 1,
    ) -> Hero:
        skill = Skill(
            name=f"{name}技能",
            description="测试技能",
            mana_cost=mana_cost,
            damage=skill_damage,
            damage_type=DamageType.MAGICAL,
            target_type="single",
        )
        template = HeroTemplate(
            hero_id=f"template_{name}",
            name=name,
            cost=1,
            race=race,
            profession=profession,
            base_hp=hp,
            base_attack=attack,
            base_defense=defense,
            attack_speed=attack_speed,
            skill=skill,
        )
        star_multiplier = {1: 1.0, 2: 1.8, 3: 3.24}.get(star, 1.0)
        return Hero(
            instance_id=instance_id,
            template_id=template.hero_id,
            name=name,
            cost=template.cost,
            star=star,
            race=race,
            profession=profession,
            max_hp=int(hp * star_multiplier),
            hp=int(hp * star_multiplier),
            attack=int(attack * star_multiplier),
            defense=int(defense * star_multiplier),
            attack_speed=attack_speed,
            skill=skill,
        )
    return _create


@pytest.fixture
def create_test_board():
    """创建测试棋盘的工厂函数"""
    def _create(owner_id: str, heroes: list[Hero] = None) -> Board:
        board = Board.create_empty(owner_id)
        if heroes:
            for i, hero in enumerate(heroes):
                x = i % 4
                y = i // 4
                pos = Position(x=x, y=y)
                board.place_hero(hero, pos)
        return board
    return _create
