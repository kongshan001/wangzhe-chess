"""
王者之奕 - 装备合成与背包集成测试

测试装备合成系统与背包的跨模块交互：
- 合成操作与背包状态更新
- 材料消耗与金币消耗
- 合成失败处理
- 背包容量管理
"""

import json
import tempfile

import pytest

from src.server.game.crafting.manager import (
    CraftingManager,
    PlayerInventory,
)
from src.server.game.crafting.models import (
    CraftingMaterial,
    CraftingRecipe,
    CraftingResult,
    SpecialEffect,
    SpecialEffectType,
)


class TestPlayerInventoryIntegration:
    """玩家背包集成测试"""

    def test_add_equipment(self):
        """测试添加装备"""
        inventory = PlayerInventory()

        # 添加装备
        inventory.add_equipment("sword_001", 1)
        assert inventory.get_equipment_count("sword_001") == 1

        # 添加多件
        inventory.add_equipment("sword_001", 3)
        assert inventory.get_equipment_count("sword_001") == 4

        # 添加不同装备
        inventory.add_equipment("shield_001", 2)
        assert inventory.get_equipment_count("shield_001") == 2

    def test_remove_equipment(self):
        """测试移除装备"""
        inventory = PlayerInventory(equipment={"sword_001": 5}, gold=100)

        # 移除装备
        result = inventory.remove_equipment("sword_001", 2)
        assert result is True
        assert inventory.get_equipment_count("sword_001") == 3

        # 移除超过拥有数量
        result = inventory.remove_equipment("sword_001", 10)
        assert result is False
        assert inventory.get_equipment_count("sword_001") == 3

    def test_remove_equipment_clears_zero_count(self):
        """测试移除最后一件装备后清除记录"""
        inventory = PlayerInventory(equipment={"sword_001": 2})

        result = inventory.remove_equipment("sword_001", 2)
        assert result is True
        assert "sword_001" not in inventory.equipment

    def test_has_equipment(self):
        """测试检查装备拥有"""
        inventory = PlayerInventory(equipment={"sword_001": 5})

        assert inventory.has_equipment("sword_001", 1) is True
        assert inventory.has_equipment("sword_001", 5) is True
        assert inventory.has_equipment("sword_001", 6) is False
        assert inventory.has_equipment("shield_001", 1) is False

    def test_inventory_serialization(self):
        """测试背包序列化"""
        inventory = PlayerInventory(equipment={"sword_001": 5, "shield_001": 2}, gold=1000)

        # 序列化
        data = inventory.to_dict()
        assert data["equipment"]["sword_001"] == 5
        assert data["gold"] == 1000

        # 反序列化
        loaded = PlayerInventory.from_dict(data)
        assert loaded.get_equipment_count("sword_001") == 5
        assert loaded.gold == 1000


class TestCraftingRecipeIntegration:
    """合成配方集成测试"""

    def test_recipe_matches_materials(self):
        """测试配方材料匹配"""
        recipe = CraftingRecipe(
            recipe_id="recipe_001",
            result_id="sword_002",
            materials=[
                CraftingMaterial(equipment_id="iron_001", quantity=2),
                CraftingMaterial(equipment_id="wood_001", quantity=1),
            ],
            gold_cost=100,
            success_rate=1.0,
        )

        # 完全匹配
        assert recipe.matches_materials(["iron_001", "iron_001", "wood_001"]) is True

        # 部分匹配
        assert recipe.matches_materials(["iron_001", "wood_001"]) is False

        # 多余材料
        assert recipe.matches_materials(["iron_001", "iron_001", "wood_001", "gem_001"]) is False

    def test_recipe_serialization(self):
        """测试配方序列化"""
        recipe = CraftingRecipe(
            recipe_id="recipe_001",
            result_id="sword_002",
            materials=[
                CraftingMaterial(equipment_id="iron_001", quantity=2),
            ],
            gold_cost=100,
            success_rate=0.9,
        )

        # 序列化
        data = recipe.to_dict()
        assert data["recipe_id"] == "recipe_001"

        # 反序列化
        loaded = CraftingRecipe.from_dict(data)
        assert loaded.recipe_id == "recipe_001"


class TestCraftingManagerIntegration:
    """合成管理器集成测试"""

    @pytest.fixture
    def manager_with_recipes(self):
        """创建带有配方的合成管理器"""
        manager = CraftingManager()

        # 添加测试配方
        recipes = [
            CraftingRecipe(
                recipe_id="recipe_sword",
                result_id="iron_sword",
                materials=[
                    CraftingMaterial(equipment_id="iron", quantity=2),
                ],
                gold_cost=50,
                success_rate=1.0,
            ),
            CraftingRecipe(
                recipe_id="recipe_shield",
                result_id="iron_shield",
                materials=[
                    CraftingMaterial(equipment_id="iron", quantity=3),
                ],
                gold_cost=100,
                success_rate=1.0,
            ),
        ]

        for recipe in recipes:
            manager.add_recipe(recipe)

        return manager

    def test_add_recipe(self, manager_with_recipes):
        """测试添加配方"""
        manager = manager_with_recipes

        assert manager.get_recipe_count() == 2
        assert manager.get_recipe("recipe_sword") is not None

    def test_find_matching_recipes(self, manager_with_recipes):
        """测试查找匹配配方"""
        manager = manager_with_recipes

        # 查找铁剑配方
        matches = manager.find_matching_recipes(["iron", "iron"])
        assert len(matches) == 1
        assert matches[0].recipe_id == "recipe_sword"

        # 无匹配
        matches = manager.find_matching_recipes(["unknown"])
        assert len(matches) == 0


class TestCraftingWithDatabaseIntegration:
    """合成与数据库集成测试"""

    @pytest.fixture
    def config_file(self):
        """创建临时配置文件"""
        config_data = {
            "version": "1.0.0",
            "recipes": [
                {
                    "recipe_id": "db_recipe_001",
                    "result_id": "result_001",
                    "materials": [{"equipment_id": "mat_001", "quantity": 2}],
                    "gold_cost": 100,
                    "success_rate": 1.0,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_data, f)
            temp_path = f.name

        yield temp_path

        import os

        os.unlink(temp_path)

    def test_load_recipes_from_file(self, config_file):
        """测试从配置文件加载配方"""
        manager = CraftingManager(config_path=config_file)

        assert manager.get_recipe_count() == 1
        recipe = manager.get_recipe("db_recipe_001")
        assert recipe is not None


class TestInventoryLimits:
    """背包限制测试"""

    def test_inventory_gold_operations(self):
        """测试金币操作"""
        inventory = PlayerInventory(gold=1000)

        # 直接操作金币
        inventory.gold -= 500
        assert inventory.gold == 500

        inventory.gold += 300
        assert inventory.gold == 800

    def test_multiple_equipment_types(self):
        """测试多种装备类型"""
        inventory = PlayerInventory()

        # 添加多种装备
        equipment_types = {
            "sword_001": 5,
            "shield_001": 3,
            "helmet_001": 2,
            "boots_001": 4,
            "ring_001": 1,
        }

        for eq_id, count in equipment_types.items():
            inventory.add_equipment(eq_id, count)

        # 验证所有装备
        for eq_id, count in equipment_types.items():
            assert inventory.get_equipment_count(eq_id) == count

    def test_special_effect_creation(self):
        """测试特殊效果创建"""
        effect = SpecialEffect(
            effect_type=SpecialEffectType.BURN,
            value=10.0,
            duration=3.0,
        )

        assert effect.effect_type == SpecialEffectType.BURN
        assert effect.value == 10.0

    def test_special_effect_serialization(self):
        """测试特殊效果序列化"""
        effect = SpecialEffect(
            effect_type=SpecialEffectType.LIFESTEAL,
            value=15.0,
            duration=5.0,
            trigger_chance=0.5,
        )

        data = effect.to_dict()
        assert data["effect_type"] == "lifesteal"
        assert data["value"] == 15.0

        loaded = SpecialEffect.from_dict(data)
        assert loaded.effect_type == SpecialEffectType.LIFESTEAL
        assert loaded.value == 15.0


class TestCraftingResult:
    """合成结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = CraftingResult(
            success=True,
            result_equipment_id="sword_001",
            gold_spent=100,
            materials_consumed=["iron", "iron"],
        )

        assert result.success is True
        assert result.result_equipment_id == "sword_001"

    def test_failure_result(self):
        """测试失败结果"""
        result = CraftingResult(
            success=False,
            error_message="合成失败",
            gold_spent=100,
        )

        assert result.success is False
        assert "失败" in result.error_message

    def test_result_serialization(self):
        """测试结果序列化"""
        result = CraftingResult(
            success=True,
            result_equipment_id="sword_001",
            gold_spent=100,
            materials_consumed=["iron", "iron"],
        )

        data = result.to_dict()
        assert data["success"] is True
        assert data["result_equipment_id"] == "sword_001"
