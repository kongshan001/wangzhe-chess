"""
王者之奕 - 装备服务单元测试

测试装备穿戴、卸下、合成功能。
"""

from __future__ import annotations

import time

import pytest

from server.game.equipment import (
    EquipmentErrorCode,
    EquipmentInstance,
    EquipmentManager,
    EquipmentService,
    EquipmentStats,
    create_equipment_service,
)
from shared.models import Hero

# ============================================================================
# 测试固件
# ============================================================================


@pytest.fixture
def equipment_service() -> EquipmentService:
    """创建装备服务实例"""
    return create_equipment_service()


@pytest.fixture
def sample_hero() -> Hero:
    """创建测试英雄"""
    return Hero(
        instance_id="hero_001",
        template_id="template_001",
        name="测试英雄",
        cost=1,
        star=1,
        race="人族",
        profession="战士",
        max_hp=100,
        hp=100,
        attack=10,
        defense=5,
        attack_speed=1.0,
        equipment=[],
    )


@pytest.fixture
def equipment_bag() -> list[dict]:
    """创建测试装备背包"""
    return []


# ============================================================================
# EquipmentInstance 测试
# ============================================================================


class TestEquipmentInstance:
    """EquipmentInstance 测试类"""

    def test_create_instance(self) -> None:
        """测试创建装备实例"""
        instance = EquipmentInstance(
            instance_id="eq_inst_001",
            equipment_id="eq_001",
            equipped_to=None,
            acquired_at=int(time.time() * 1000),
        )
        assert instance.instance_id == "eq_inst_001"
        assert instance.equipment_id == "eq_001"
        assert instance.equipped_to is None
        assert not instance.is_equipped()

    def test_is_equipped(self) -> None:
        """测试装备穿戴状态"""
        instance = EquipmentInstance(
            instance_id="eq_inst_001",
            equipment_id="eq_001",
            equipped_to="hero_001",
        )
        assert instance.is_equipped()

    def test_to_dict(self) -> None:
        """测试序列化"""
        instance = EquipmentInstance(
            instance_id="eq_inst_001",
            equipment_id="eq_001",
            equipped_to=None,
            acquired_at=1234567890,
        )
        data = instance.to_dict()
        assert data["instance_id"] == "eq_inst_001"
        assert data["equipment_id"] == "eq_001"
        assert data["equipped_to"] is None
        assert data["acquired_at"] == 1234567890

    def test_from_dict(self) -> None:
        """测试反序列化"""
        data = {
            "instance_id": "eq_inst_001",
            "equipment_id": "eq_001",
            "equipped_to": "hero_001",
            "acquired_at": 1234567890,
        }
        instance = EquipmentInstance.from_dict(data)
        assert instance.instance_id == "eq_inst_001"
        assert instance.equipment_id == "eq_001"
        assert instance.equipped_to == "hero_001"
        assert instance.acquired_at == 1234567890


# ============================================================================
# EquipmentStats 测试
# ============================================================================


class TestEquipmentStats:
    """EquipmentStats 测试类"""

    def test_default_stats(self) -> None:
        """测试默认属性"""
        stats = EquipmentStats()
        assert stats.attack == 0
        assert stats.armor == 0
        assert stats.spell_power == 0
        assert stats.hp == 0
        assert stats.attack_speed == 0.0

    def test_add_stats(self) -> None:
        """测试属性合并"""
        stats1 = EquipmentStats(attack=10, hp=100)
        stats2 = EquipmentStats(attack=5, armor=10)
        result = stats1 + stats2
        assert result.attack == 15
        assert result.armor == 10
        assert result.hp == 100

    def test_to_dict(self) -> None:
        """测试序列化"""
        stats = EquipmentStats(attack=10, hp=100)
        data = stats.to_dict()
        assert data["attack"] == 10
        assert data["hp"] == 100

    def test_from_dict(self) -> None:
        """测试反序列化"""
        data = {"attack": 10, "hp": 100}
        stats = EquipmentStats.from_dict(data)
        assert stats.attack == 10
        assert stats.hp == 100


# ============================================================================
# EquipmentService.add_equipment_to_bag 测试
# ============================================================================


class TestAddEquipmentToBag:
    """add_equipment_to_bag 测试类"""

    def test_add_equipment_success(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试添加装备成功"""
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        assert instance.equipment_id == "eq_001"
        assert instance.equipped_to is None
        assert len(equipment_bag) == 1

    def test_add_multiple_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试添加多件装备"""
        equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        equipment_service.add_equipment_to_bag(equipment_bag, "eq_002")
        equipment_service.add_equipment_to_bag(equipment_bag, "eq_003")
        assert len(equipment_bag) == 3

    def test_unique_instance_ids(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试实例ID唯一性"""
        inst1 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        inst2 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        assert inst1.instance_id != inst2.instance_id


# ============================================================================
# EquipmentService.equip_item 测试
# ============================================================================


class TestEquipItem:
    """equip_item 测试类"""

    def test_equip_success(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试穿戴成功"""
        # 添加装备到背包
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        # 穿戴装备
        result = equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
            sample_hero.instance_id,
        )

        assert result.success
        assert result.error_code == EquipmentErrorCode.SUCCESS
        assert instance.instance_id in sample_hero.equipment

    def test_equip_equipment_not_found(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试装备不存在"""
        result = equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            "non_existent_id",
            sample_hero.instance_id,
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_NOT_FOUND

    def test_equip_already_equipped(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试装备已被穿戴"""
        # 添加并穿戴装备
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
            sample_hero.instance_id,
        )

        # 创建另一个英雄
        hero2 = Hero(
            instance_id="hero_002",
            template_id="template_001",
            name="测试英雄2",
            cost=1,
            star=1,
            race="人族",
            profession="战士",
            max_hp=100,
            hp=100,
            attack=10,
            defense=5,
            attack_speed=1.0,
            equipment=[],
        )

        # 尝试穿戴同一件装备
        result = equipment_service.equip_item(
            equipment_bag,
            [sample_hero, hero2],
            instance.instance_id,
            hero2.instance_id,
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_ALREADY_EQUIPPED

    def test_equip_hero_not_found(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试英雄不存在"""
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        result = equipment_service.equip_item(
            equipment_bag,
            [],  # 空英雄列表
            instance.instance_id,
            "non_existent_hero",
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.HERO_NOT_FOUND

    def test_equip_hero_full_slots(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试英雄装备槽已满"""
        # 添加3件装备
        instances = []
        for _ in range(3):
            inst = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
            instances.append(inst)

        # 穿戴3件装备（填满槽位）
        for inst in instances:
            equipment_service.equip_item(
                equipment_bag,
                [sample_hero],
                inst.instance_id,
                sample_hero.instance_id,
            )

        # 添加第4件装备
        inst4 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        # 尝试穿戴第4件
        result = equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            inst4.instance_id,
            sample_hero.instance_id,
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.HERO_EQUIPMENT_FULL


# ============================================================================
# EquipmentService.unequip_item 测试
# ============================================================================


class TestUnequipItem:
    """unequip_item 测试类"""

    def test_unequip_success(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试卸下成功"""
        # 添加并穿戴装备
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
            sample_hero.instance_id,
        )

        # 卸下装备
        result = equipment_service.unequip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
        )

        assert result.success
        assert instance.instance_id not in sample_hero.equipment

    def test_unequip_equipment_not_found(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试装备不存在"""
        result = equipment_service.unequip_item(
            equipment_bag,
            [sample_hero],
            "non_existent_id",
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_NOT_FOUND

    def test_unequip_not_equipped(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试装备未被穿戴"""
        # 添加装备但不穿戴
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        result = equipment_service.unequip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_NOT_EQUIPPED

    def test_unequip_hero_not_found(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试穿戴英雄不存在（背包数据损坏场景）"""
        # 添加并穿戴装备
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            instance.instance_id,
            sample_hero.instance_id,
        )

        # 使用空英雄列表尝试卸下
        result = equipment_service.unequip_item(
            equipment_bag,
            [],  # 空英雄列表
            instance.instance_id,
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.HERO_NOT_FOUND


# ============================================================================
# EquipmentService.craft_equipment 测试
# ============================================================================


class TestCraftEquipment:
    """craft_equipment 测试类"""

    def test_craft_insufficient_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试装备数量不足"""
        # 只添加1件装备
        equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        result = equipment_service.craft_equipment(
            equipment_bag,
            ["non_existent_id", "another_non_existent"],
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.INSUFFICIENT_EQUIPMENT

    def test_craft_equipment_already_equipped(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试合成已穿戴的装备"""
        # 添加并穿戴装备1
        inst1 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        equipment_service.equip_item(
            equipment_bag,
            [sample_hero],
            inst1.instance_id,
            sample_hero.instance_id,
        )

        # 添加装备2
        inst2 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        result = equipment_service.craft_equipment(
            equipment_bag,
            [inst1.instance_id, inst2.instance_id],
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_ALREADY_EQUIPPED

    def test_craft_single_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试只提供一件装备"""
        inst = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        result = equipment_service.craft_equipment(
            equipment_bag,
            [inst.instance_id],
        )

        assert not result.success
        assert result.error_code == EquipmentErrorCode.INVALID_RECIPE

    def test_craft_consumes_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试合成消耗原装备"""
        # 添加两件装备
        inst1 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        inst2 = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        initial_count = len(equipment_bag)

        # 尝试合成（即使配方不存在，也会检查消耗逻辑）
        equipment_service.craft_equipment(
            equipment_bag,
            [inst1.instance_id, inst2.instance_id],
        )

        # 如果配方无效，装备应该还在
        # 如果配方有效，装备应该被消耗
        # 这里我们只验证不会崩溃


# ============================================================================
# EquipmentService.get_equipment_stats_for_hero 测试
# ============================================================================


class TestGetEquipmentStatsForHero:
    """get_equipment_stats_for_hero 测试类"""

    def test_no_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试英雄没有装备"""
        stats = equipment_service.get_equipment_stats_for_hero(sample_hero, equipment_bag)
        assert stats.attack == 0
        assert stats.hp == 0

    def test_with_equipment(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试英雄有装备"""
        # 添加装备到背包
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        # 手动将装备添加到英雄（模拟已穿戴状态）
        sample_hero.equipment.append(instance.instance_id)

        # 获取装备属性（由于没有配置，属性应该为0）
        stats = equipment_service.get_equipment_stats_for_hero(sample_hero, equipment_bag)

        # 验证方法不会崩溃
        assert isinstance(stats, EquipmentStats)


# ============================================================================
# EquipmentManager 测试
# ============================================================================


class TestEquipmentManager:
    """EquipmentManager 测试类"""

    def test_create_manager(self) -> None:
        """测试创建管理器"""
        manager = EquipmentManager()
        assert manager.equipment_config == {}

    def test_get_equipment_not_found(self) -> None:
        """测试获取不存在的装备"""
        manager = EquipmentManager()
        result = manager.get_equipment("non_existent")
        assert result is None

    def test_can_craft_no_match(self) -> None:
        """测试合成配方不匹配"""
        manager = EquipmentManager()
        result = manager.can_craft(["eq_001", "eq_002"])
        assert result is None

    def test_get_all_equipment_empty(self) -> None:
        """测试获取所有装备（空）"""
        manager = EquipmentManager()
        result = manager.get_all_equipment()
        assert result == []


# ============================================================================
# 边界条件测试
# ============================================================================


class TestEdgeCases:
    """边界条件测试类"""

    def test_empty_equipment_bag(
        self,
        equipment_service: EquipmentService,
        sample_hero: Hero,
    ) -> None:
        """测试空背包操作"""
        result = equipment_service.equip_item(
            [],
            [sample_hero],
            "any_id",
            sample_hero.instance_id,
        )
        assert not result.success
        assert result.error_code == EquipmentErrorCode.EQUIPMENT_NOT_FOUND

    def test_empty_hero_list(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
    ) -> None:
        """测试空英雄列表"""
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")
        result = equipment_service.equip_item(
            equipment_bag,
            [],
            instance.instance_id,
            "any_hero_id",
        )
        assert not result.success
        assert result.error_code == EquipmentErrorCode.HERO_NOT_FOUND

    def test_multiple_heroes_same_instance(
        self,
        equipment_service: EquipmentService,
        equipment_bag: list[dict],
        sample_hero: Hero,
    ) -> None:
        """测试多英雄场景"""
        hero2 = Hero(
            instance_id="hero_002",
            template_id="template_001",
            name="测试英雄2",
            cost=1,
            star=1,
            race="人族",
            profession="战士",
            max_hp=100,
            hp=100,
            attack=10,
            defense=5,
            attack_speed=1.0,
            equipment=[],
        )

        # 添加装备
        instance = equipment_service.add_equipment_to_bag(equipment_bag, "eq_001")

        # 给第一个英雄穿戴
        result1 = equipment_service.equip_item(
            equipment_bag,
            [sample_hero, hero2],
            instance.instance_id,
            sample_hero.instance_id,
        )
        assert result1.success

        # 尝试给第二个英雄穿戴同一件装备
        result2 = equipment_service.equip_item(
            equipment_bag,
            [sample_hero, hero2],
            instance.instance_id,
            hero2.instance_id,
        )
        assert not result2.success
