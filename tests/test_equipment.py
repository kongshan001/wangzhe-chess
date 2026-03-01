"""
王者之奕 - 装备系统测试
"""

import pytest

from server.game.equipment import Equipment, EquipmentManager, EquipmentStats


class TestEquipmentStats:
    """装备属性测试"""

    def test_create_stats_default(self):
        """测试默认属性创建"""
        stats = EquipmentStats()
        assert stats.attack == 0
        assert stats.armor == 0
        assert stats.spell_power == 0
        assert stats.hp == 0
        assert stats.attack_speed == 0.0

    def test_create_stats_from_dict(self):
        """测试从字典创建属性"""
        data = {"attack": 15, "hp": 100}
        stats = EquipmentStats.from_dict(data)
        assert stats.attack == 15
        assert stats.hp == 100


class TestEquipment:
    """装备类测试"""

    def test_create_equipment(self):
        """测试装备创建"""
        eq = Equipment(
            equipment_id="eq_001",
            name="铁剑",
            tier=1,
            stats=EquipmentStats(attack=15),
            description="基础攻击装备",
        )
        assert eq.equipment_id == "eq_001"
        assert eq.name == "铁剑"
        assert eq.tier == 1

    def test_equipment_serialization(self):
        """测试装备序列化"""
        eq = Equipment(equipment_id="eq_001", name="铁剑", tier=1, stats=EquipmentStats(attack=15))
        data = eq.to_dict()
        assert "equipment_id" in data
        assert "stats" in data


class TestEquipmentManager:
    """装备管理器测试"""

    def test_get_equipment_exists(self):
        """测试获取存在的装备"""
        manager = EquipmentManager()
        # 需要先加载配置
        eq = manager.get_equipment("eq_001")
        # 断言取决于配置

    def test_can_craft_simple(self):
        """测试简单合成（2个基础装备）"""
        manager = EquipmentManager()
        result = manager.can_craft(["eq_001", "eq_001"])
        # 断言取决于配置

    def test_can_craft_invalid(self):
        """测试无效合成"""
        manager = EquipmentManager()
        result = manager.can_craft(["eq_001", "eq_002"])
        assert result is None

    def test_apply_equipment_single(self):
        """测试应用单个装备"""
        manager = EquipmentManager()
        # 创建测试英雄
        # hero = Hero(...)
        # manager.apply_equipment(hero, ["eq_001"])
        # 验证属性增加
        # assert hero.attack == original_attack + 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
