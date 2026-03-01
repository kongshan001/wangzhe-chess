"""
王者之奕 - 皮肤系统测试

测试皮肤系统的核心功能：
- 皮肤配置加载
- 皮肤管理器
- 皮肤获取、装备、购买
- 属性加成计算
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.server.skin.manager import SkinManager
from src.server.skin.models import (
    PlayerSkin,
    Skin,
    SkinEffect,
    SkinEffectType,
    SkinPrice,
    SkinRarity,
    SkinStatBonus,
    SkinType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_skin_normal() -> Skin:
    """创建一个普通皮肤"""
    return Skin(
        skin_id="test_normal_skin",
        hero_id="yase",
        name="普通测试皮肤",
        description="这是一个普通测试皮肤",
        rarity=SkinRarity.NORMAL,
        skin_type=SkinType.DEFAULT,
        preview_image="test.png",
    )


@pytest.fixture
def sample_skin_rare() -> Skin:
    """创建一个稀有皮肤（+5%攻击）"""
    return Skin(
        skin_id="test_rare_skin",
        hero_id="yase",
        name="稀有测试皮肤",
        description="这是一个稀有测试皮肤",
        rarity=SkinRarity.RARE,
        skin_type=SkinType.SHOP,
        price=SkinPrice(gold=2000, diamond=200),
        stat_bonuses=[SkinStatBonus(stat_name="attack", bonus_percent=5)],
        effects=[
            SkinEffect(
                effect_type=SkinEffectType.MODEL, effect_id="rare_model", description="稀有造型"
            ),
        ],
        preview_image="test_rare.png",
    )


@pytest.fixture
def sample_skin_epic() -> Skin:
    """创建一个史诗皮肤（+5%多属性 + 特效）"""
    return Skin(
        skin_id="test_epic_skin",
        hero_id="libai",
        name="史诗测试皮肤",
        description="这是一个史诗测试皮肤",
        rarity=SkinRarity.EPIC,
        skin_type=SkinType.SHOP,
        price=SkinPrice(gold=5000, diamond=500),
        stat_bonuses=[
            SkinStatBonus(stat_name="attack", bonus_percent=5),
            SkinStatBonus(stat_name="attack_speed", bonus_percent=5),
        ],
        effects=[
            SkinEffect(
                effect_type=SkinEffectType.MODEL, effect_id="epic_model", description="史诗造型"
            ),
            SkinEffect(
                effect_type=SkinEffectType.SKILL, effect_id="epic_skill", description="技能特效"
            ),
        ],
        preview_image="test_epic.png",
    )


@pytest.fixture
def sample_skin_legendary() -> Skin:
    """创建一个传说皮肤（+8%多属性 + 全新特效）"""
    return Skin(
        skin_id="test_legendary_skin",
        hero_id="libai",
        name="传说测试皮肤",
        description="这是一个传说测试皮肤",
        rarity=SkinRarity.LEGENDARY,
        skin_type=SkinType.SHOP,
        price=SkinPrice(diamond=1000),
        stat_bonuses=[
            SkinStatBonus(stat_name="attack", bonus_percent=8),
            SkinStatBonus(stat_name="attack_speed", bonus_percent=8),
            SkinStatBonus(stat_name="hp", bonus_percent=8),
        ],
        effects=[
            SkinEffect(
                effect_type=SkinEffectType.MODEL,
                effect_id="legendary_model",
                description="传说造型",
            ),
            SkinEffect(
                effect_type=SkinEffectType.SKILL,
                effect_id="legendary_skill",
                description="全新技能特效",
            ),
            SkinEffect(
                effect_type=SkinEffectType.SOUND,
                effect_id="legendary_sound",
                description="专属音效",
            ),
            SkinEffect(
                effect_type=SkinEffectType.PARTICLE,
                effect_id="legendary_particle",
                description="专属粒子",
            ),
        ],
        preview_image="test_legendary.png",
    )


@pytest.fixture
def skin_manager() -> SkinManager:
    """创建皮肤管理器"""
    return SkinManager()


@pytest.fixture
def populated_skin_manager(
    skin_manager: SkinManager,
    sample_skin_normal: Skin,
    sample_skin_rare: Skin,
    sample_skin_epic: Skin,
    sample_skin_legendary: Skin,
) -> SkinManager:
    """创建包含测试皮肤的皮肤管理器"""
    for skin in [sample_skin_normal, sample_skin_rare, sample_skin_epic, sample_skin_legendary]:
        skin_manager.skins[skin.skin_id] = skin
        if skin.hero_id not in skin_manager.hero_skins:
            skin_manager.hero_skins[skin.hero_id] = []
        skin_manager.hero_skins[skin.hero_id].append(skin)
    return skin_manager


# ============================================================================
# 模型测试
# ============================================================================


class TestSkinModels:
    """测试皮肤数据模型"""

    def test_skin_rarity_enum(self):
        """测试皮肤稀有度枚举"""
        assert SkinRarity.NORMAL.value == "normal"
        assert SkinRarity.RARE.value == "rare"
        assert SkinRarity.EPIC.value == "epic"
        assert SkinRarity.LEGENDARY.value == "legendary"

    def test_skin_rarity_display_name(self):
        """测试稀有度显示名称"""
        assert SkinRarity.get_display_name("normal") == "普通"
        assert SkinRarity.get_display_name("rare") == "稀有"
        assert SkinRarity.get_display_name("epic") == "史诗"
        assert SkinRarity.get_display_name("legendary") == "传说"

    def test_skin_rarity_bonus_percent(self):
        """测试稀有度属性加成"""
        assert SkinRarity.get_bonus_percent("normal") == 0
        assert SkinRarity.get_bonus_percent("rare") == 5
        assert SkinRarity.get_bonus_percent("epic") == 5
        assert SkinRarity.get_bonus_percent("legendary") == 8

    def test_skin_rarity_color(self):
        """测试稀有度颜色"""
        assert SkinRarity.get_color("normal") == "#FFFFFF"
        assert SkinRarity.get_color("rare") == "#1EFF00"
        assert SkinRarity.get_color("epic") == "#A335EE"
        assert SkinRarity.get_color("legendary") == "#FF8000"

    def test_skin_stat_bonus(self):
        """测试皮肤属性加成"""
        bonus = SkinStatBonus(stat_name="attack", bonus_percent=5)
        assert bonus.apply_bonus(100) == 105.0
        assert bonus.apply_bonus(200) == 210.0

    def test_skin_price_gold(self):
        """测试金币价格"""
        price = SkinPrice(gold=2000, diamond=200)
        assert price.can_afford(gold=3000, diamond=0) is True
        assert price.can_afford(gold=1000, diamond=0) is False
        assert price.can_afford(gold=0, diamond=300) is True

    def test_skin_price_cheapest(self):
        """测试最便宜的购买方式"""
        price = SkinPrice(gold=2000, diamond=200)
        currency, cost = price.get_cheapest_option()
        assert currency == "gold"
        assert cost == 2000

    def test_skin_to_dict(self, sample_skin_legendary: Skin):
        """测试皮肤转换为字典"""
        data = sample_skin_legendary.to_dict()
        assert data["skin_id"] == "test_legendary_skin"
        assert data["hero_id"] == "libai"
        assert data["rarity"] == "legendary"
        assert len(data["stat_bonuses"]) == 3
        assert len(data["effects"]) == 4

    def test_skin_from_dict(self, sample_skin_legendary: Skin):
        """测试从字典创建皮肤"""
        data = sample_skin_legendary.to_dict()
        skin = Skin.from_dict(data)
        assert skin.skin_id == sample_skin_legendary.skin_id
        assert skin.hero_id == sample_skin_legendary.hero_id
        assert skin.rarity == sample_skin_legendary.rarity

    def test_skin_apply_stat_bonuses(self, sample_skin_legendary: Skin):
        """测试应用属性加成"""
        base_stats = {
            "hp": 1000,
            "attack": 100,
            "attack_speed": 1.0,
            "armor": 50,
        }
        result = sample_skin_legendary.apply_stat_bonuses(base_stats)
        assert result["hp"] == 1080  # +8%
        assert result["attack"] == 108.0  # +8%
        assert result["attack_speed"] == 1.08  # +8%
        assert result["armor"] == 50  # 无加成

    def test_skin_has_effect(self, sample_skin_legendary: Skin):
        """测试检查特效"""
        assert sample_skin_legendary.has_effect(SkinEffectType.SKILL) is True
        assert sample_skin_legendary.has_effect(SkinEffectType.EMOTE) is False

    def test_skin_get_effects_by_type(self, sample_skin_legendary: Skin):
        """测试获取指定类型的特效"""
        skill_effects = sample_skin_legendary.get_effects_by_type(SkinEffectType.SKILL)
        assert len(skill_effects) == 1
        assert skill_effects[0].description == "全新技能特效"


# ============================================================================
# 皮肤管理器测试
# ============================================================================


class TestSkinManager:
    """测试皮肤管理器"""

    def test_get_skin(self, populated_skin_manager: SkinManager):
        """测试获取皮肤"""
        skin = populated_skin_manager.get_skin("test_normal_skin")
        assert skin is not None
        assert skin.name == "普通测试皮肤"

    def test_get_skin_not_found(self, skin_manager: SkinManager):
        """测试获取不存在的皮肤"""
        skin = skin_manager.get_skin("nonexistent")
        assert skin is None

    def test_get_skins_by_hero(self, populated_skin_manager: SkinManager):
        """测试按英雄获取皮肤"""
        skins = populated_skin_manager.get_skins_by_hero("yase")
        assert len(skins) == 2  # normal + rare

        skins = populated_skin_manager.get_skins_by_hero("libai")
        assert len(skins) == 2  # epic + legendary

    def test_get_skins_by_rarity(self, populated_skin_manager: SkinManager):
        """测试按稀有度获取皮肤"""
        rare_skins = populated_skin_manager.get_skins_by_rarity(SkinRarity.RARE)
        assert len(rare_skins) == 1

        legendary_skins = populated_skin_manager.get_skins_by_rarity(SkinRarity.LEGENDARY)
        assert len(legendary_skins) == 1

    def test_has_skin(self, populated_skin_manager: SkinManager):
        """测试检查玩家是否拥有皮肤"""
        player_id = "test_player"
        assert populated_skin_manager.has_skin(player_id, "test_normal_skin") is False

        # 添加皮肤
        player_skin = PlayerSkin(
            player_id=player_id,
            skin_id="test_normal_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
        )
        populated_skin_manager.player_skins[player_id] = {"test_normal_skin": player_skin}

        assert populated_skin_manager.has_skin(player_id, "test_normal_skin") is True

    def test_equip_skin(self, populated_skin_manager: SkinManager):
        """测试装备皮肤"""
        player_id = "test_player"
        skin_id = "test_rare_skin"

        # 先解锁皮肤
        populated_skin_manager.unlock_skin(player_id, skin_id)

        # 装备皮肤
        success, error = populated_skin_manager.equip_skin(player_id, skin_id)
        assert success is True
        assert error is None

        # 检查装备状态
        equipped = populated_skin_manager.get_equipped_skin(player_id, "yase")
        assert equipped == skin_id

    def test_equip_skin_not_owned(self, populated_skin_manager: SkinManager):
        """测试装备未拥有的皮肤"""
        player_id = "test_player"

        success, error = populated_skin_manager.equip_skin(player_id, "test_rare_skin")
        assert success is False
        assert "未拥有" in error

    def test_unequip_skin(self, populated_skin_manager: SkinManager):
        """测试卸下皮肤"""
        player_id = "test_player"
        skin_id = "test_rare_skin"

        # 先解锁并装备
        populated_skin_manager.unlock_skin(player_id, skin_id)
        populated_skin_manager.equip_skin(player_id, skin_id)

        # 卸下皮肤
        success, error = populated_skin_manager.unequip_skin(player_id, "yase")
        assert success is True
        assert error is None

        # 检查装备状态
        equipped = populated_skin_manager.get_equipped_skin(player_id, "yase")
        assert equipped is None

    def test_buy_skin(self, populated_skin_manager: SkinManager):
        """测试购买皮肤"""
        player_id = "test_player"
        skin_id = "test_rare_skin"

        # 购买皮肤
        player_skin, currency, cost, error = populated_skin_manager.buy_skin(
            player_id=player_id,
            skin_id=skin_id,
            gold=3000,
            diamond=0,
        )

        assert player_skin is not None
        assert currency == "gold"
        assert cost == 2000
        assert error is None

    def test_buy_skin_insufficient_gold(self, populated_skin_manager: SkinManager):
        """测试金币不足购买皮肤"""
        player_id = "test_player"
        skin_id = "test_rare_skin"

        player_skin, currency, cost, error = populated_skin_manager.buy_skin(
            player_id=player_id,
            skin_id=skin_id,
            gold=1000,
            diamond=0,
        )

        assert player_skin is None
        assert "金币不足" in error

    def test_buy_skin_already_owned(self, populated_skin_manager: SkinManager):
        """测试购买已拥有的皮肤"""
        player_id = "test_player"
        skin_id = "test_rare_skin"

        # 先解锁
        populated_skin_manager.unlock_skin(player_id, skin_id)

        # 尝试购买
        player_skin, currency, cost, error = populated_skin_manager.buy_skin(
            player_id=player_id,
            skin_id=skin_id,
            gold=3000,
            diamond=0,
        )

        assert player_skin is None
        assert "已拥有" in error

    def test_unlock_skin(self, populated_skin_manager: SkinManager):
        """测试解锁皮肤"""
        player_id = "test_player"
        skin_id = "test_epic_skin"

        player_skin, error = populated_skin_manager.unlock_skin(player_id, skin_id, "reward")

        assert player_skin is not None
        assert error is None
        assert player_skin.acquire_type == "reward"

    def test_unlock_skin_already_owned(self, populated_skin_manager: SkinManager):
        """测试解锁已拥有的皮肤"""
        player_id = "test_player"
        skin_id = "test_epic_skin"

        # 先解锁
        populated_skin_manager.unlock_skin(player_id, skin_id)

        # 再次解锁
        player_skin, error = populated_skin_manager.unlock_skin(player_id, skin_id)

        assert player_skin is None
        assert "已拥有" in error


# ============================================================================
# 属性加成计算测试
# ============================================================================


class TestStatBonusCalculation:
    """测试属性加成计算"""

    def test_calculate_stat_bonuses_no_skin(self, populated_skin_manager: SkinManager):
        """测试无皮肤时的属性加成"""
        player_id = "test_player"
        hero_id = "yase"
        base_stats = {"hp": 1000, "attack": 100, "armor": 50}

        result = populated_skin_manager.calculate_stat_bonuses(player_id, hero_id, base_stats)

        assert result == base_stats  # 无变化

    def test_calculate_stat_bonuses_rare_skin(self, populated_skin_manager: SkinManager):
        """测试稀有皮肤属性加成"""
        player_id = "test_player"
        hero_id = "yase"
        skin_id = "test_rare_skin"
        base_stats = {"hp": 1000, "attack": 100, "armor": 50}

        # 解锁并装备皮肤
        populated_skin_manager.unlock_skin(player_id, skin_id)
        populated_skin_manager.equip_skin(player_id, skin_id)

        result = populated_skin_manager.calculate_stat_bonuses(player_id, hero_id, base_stats)

        assert result["hp"] == 1000  # 无变化
        assert result["attack"] == 105  # +5%
        assert result["armor"] == 50  # 无变化

    def test_calculate_stat_bonuses_legendary_skin(self, populated_skin_manager: SkinManager):
        """测试传说皮肤属性加成"""
        player_id = "test_player"
        hero_id = "libai"
        skin_id = "test_legendary_skin"
        base_stats = {"hp": 1000, "attack": 100, "attack_speed": 1.0, "armor": 50}

        # 解锁并装备皮肤
        populated_skin_manager.unlock_skin(player_id, skin_id)
        populated_skin_manager.equip_skin(player_id, skin_id)

        result = populated_skin_manager.calculate_stat_bonuses(player_id, hero_id, base_stats)

        assert result["hp"] == 1080  # +8%
        assert result["attack"] == 108  # +8%
        assert result["attack_speed"] == 1.08  # +8%
        assert result["armor"] == 50  # 无变化

    def test_get_stat_bonus_description(self, populated_skin_manager: SkinManager):
        """测试获取属性加成描述"""
        # 稀有皮肤
        desc = populated_skin_manager.get_stat_bonus_description("test_rare_skin")
        assert "攻击力+5%" in desc

        # 传说皮肤
        desc = populated_skin_manager.get_stat_bonus_description("test_legendary_skin")
        assert "生命值+8%" in desc
        assert "攻击力+8%" in desc
        assert "攻击速度+8%" in desc

    def test_get_effect_description(self, populated_skin_manager: SkinManager):
        """测试获取特效描述"""
        # 普通皮肤
        desc = populated_skin_manager.get_effect_description("test_normal_skin")
        assert desc == "无特效"

        # 传说皮肤
        desc = populated_skin_manager.get_effect_description("test_legendary_skin")
        assert "模型" in desc
        assert "技能" in desc


# ============================================================================
# 玩家皮肤数据测试
# ============================================================================


class TestPlayerSkin:
    """测试玩家皮肤数据"""

    def test_player_skin_creation(self):
        """测试创建玩家皮肤"""
        ps = PlayerSkin(
            player_id="test_player",
            skin_id="test_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
            acquire_type="buy",
        )

        assert ps.is_equipped is False
        assert ps.equipped_at is None

    def test_player_skin_equip(self):
        """测试玩家皮肤装备"""
        ps = PlayerSkin(
            player_id="test_player",
            skin_id="test_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
        )

        ps.equip()

        assert ps.is_equipped is True
        assert ps.equipped_at is not None

    def test_player_skin_unequip(self):
        """测试玩家皮肤卸下"""
        ps = PlayerSkin(
            player_id="test_player",
            skin_id="test_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
        )

        ps.equip()
        ps.unequip()

        assert ps.is_equipped is False
        assert ps.equipped_at is None

    def test_player_skin_to_dict(self):
        """测试玩家皮肤转换为字典"""
        ps = PlayerSkin(
            player_id="test_player",
            skin_id="test_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
            acquire_type="reward",
        )

        data = ps.to_dict()

        assert data["player_id"] == "test_player"
        assert data["skin_id"] == "test_skin"
        assert data["hero_id"] == "yase"
        assert data["acquire_type"] == "reward"

    def test_player_skin_from_dict(self):
        """测试从字典创建玩家皮肤"""
        ps = PlayerSkin(
            player_id="test_player",
            skin_id="test_skin",
            hero_id="yase",
            acquired_at=datetime.now(),
            is_equipped=True,
        )

        data = ps.to_dict()
        new_ps = PlayerSkin.from_dict(data)

        assert new_ps.player_id == ps.player_id
        assert new_ps.skin_id == ps.skin_id
        assert new_ps.is_equipped == ps.is_equipped


# ============================================================================
# 集成测试
# ============================================================================


class TestSkinIntegration:
    """皮肤系统集成测试"""

    def test_full_skin_workflow(self, populated_skin_manager: SkinManager):
        """测试完整的皮肤获取和使用流程"""
        player_id = "test_player"
        hero_id = "libai"
        skin_id = "test_legendary_skin"

        # 1. 检查初始状态
        assert not populated_skin_manager.has_skin(player_id, skin_id)

        # 2. 购买皮肤
        player_skin, currency, cost, error = populated_skin_manager.buy_skin(
            player_id=player_id,
            skin_id=skin_id,
            gold=0,
            diamond=1500,
        )

        assert player_skin is not None
        assert currency == "diamond"
        assert cost == 1000

        # 3. 检查是否拥有
        assert populated_skin_manager.has_skin(player_id, skin_id)

        # 4. 装备皮肤
        success, error = populated_skin_manager.equip_skin(player_id, skin_id)
        assert success is True

        # 5. 检查装备状态
        equipped = populated_skin_manager.get_equipped_skin(player_id, hero_id)
        assert equipped == skin_id

        # 6. 计算属性加成
        base_stats = {"hp": 800, "attack": 95, "attack_speed": 0.85}
        result = populated_skin_manager.calculate_stat_bonuses(player_id, hero_id, base_stats)

        assert result["hp"] == 864  # +8%
        assert abs(result["attack"] - 102.6) < 0.01  # +8% (浮点精度)
        assert abs(result["attack_speed"] - 0.918) < 0.001  # +8%

        # 7. 卸下皮肤
        success, error = populated_skin_manager.unequip_skin(player_id, hero_id)
        assert success is True

        # 8. 检查装备状态
        equipped = populated_skin_manager.get_equipped_skin(player_id, hero_id)
        assert equipped is None

        # 9. 再次计算属性（应该无加成）
        result = populated_skin_manager.calculate_stat_bonuses(player_id, hero_id, base_stats)
        assert result == base_stats


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
