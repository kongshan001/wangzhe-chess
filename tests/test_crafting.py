"""
王者之奕 - 装备合成系统测试
"""

from pathlib import Path

import pytest

from server.game.crafting import (
    CraftingManager,
    CraftingMaterial,
    CraftingRecipe,
    PlayerInventory,
    Rarity,
    SpecialEffect,
    SpecialEffectType,
)

# ============================================================================
# 测试固件
# ============================================================================


@pytest.fixture
def sample_recipe() -> CraftingRecipe:
    """创建示例合成配方"""
    return CraftingRecipe(
        recipe_id="test_recipe_001",
        result_id="eq_011",
        materials=[
            CraftingMaterial(equipment_id="eq_006", quantity=2),
        ],
        gold_cost=50,
        success_rate=1.0,
    )


@pytest.fixture
def sample_inventory() -> PlayerInventory:
    """创建示例玩家背包"""
    inventory = PlayerInventory()
    inventory.add_equipment("eq_006", 3)  # 暴风大剑 x3
    inventory.add_equipment("eq_007", 2)  # 锁子甲 x2
    inventory.gold = 200
    return inventory


@pytest.fixture
def crafting_manager() -> CraftingManager:
    """创建合成管理器"""
    config_path = Path(__file__).parent.parent / "config" / "crafting-recipes.json"
    if config_path.exists():
        return CraftingManager(config_path=str(config_path))
    return CraftingManager()


# ============================================================================
# CraftingMaterial 测试
# ============================================================================


class TestCraftingMaterial:
    """合成材料测试"""

    def test_create_material(self):
        """测试创建材料"""
        material = CraftingMaterial(equipment_id="eq_001", quantity=2)
        assert material.equipment_id == "eq_001"
        assert material.quantity == 2

    def test_material_serialization(self):
        """测试材料序列化"""
        material = CraftingMaterial(equipment_id="eq_001", quantity=3)
        data = material.to_dict()
        assert data["equipment_id"] == "eq_001"
        assert data["quantity"] == 3

        # 反序列化
        restored = CraftingMaterial.from_dict(data)
        assert restored.equipment_id == material.equipment_id
        assert restored.quantity == material.quantity


# ============================================================================
# CraftingRecipe 测试
# ============================================================================


class TestCraftingRecipe:
    """合成配方测试"""

    def test_create_recipe(self, sample_recipe):
        """测试创建配方"""
        assert sample_recipe.recipe_id == "test_recipe_001"
        assert sample_recipe.result_id == "eq_011"
        assert sample_recipe.gold_cost == 50
        assert len(sample_recipe.materials) == 1

    def test_get_material_ids(self, sample_recipe):
        """测试获取材料ID列表"""
        ids = sample_recipe.get_material_ids()
        assert ids == ["eq_006", "eq_006"]

    def test_matches_materials_success(self, sample_recipe):
        """测试材料匹配 - 成功"""
        assert sample_recipe.matches_materials(["eq_006", "eq_006"]) is True
        assert sample_recipe.matches_materials(["eq_006"]) is False

    def test_matches_materials_different_order(self, sample_recipe):
        """测试材料匹配 - 不同顺序"""
        # 排序后应该匹配
        recipe = CraftingRecipe(
            recipe_id="test_multi",
            result_id="eq_012",
            materials=[
                CraftingMaterial(equipment_id="eq_006", quantity=1),
                CraftingMaterial(equipment_id="eq_007", quantity=1),
            ],
        )
        assert recipe.matches_materials(["eq_006", "eq_007"]) is True
        assert recipe.matches_materials(["eq_007", "eq_006"]) is True  # 顺序不重要

    def test_recipe_serialization(self, sample_recipe):
        """测试配方序列化"""
        data = sample_recipe.to_dict()
        assert "recipe_id" in data
        assert "result_id" in data
        assert "materials" in data

        restored = CraftingRecipe.from_dict(data)
        assert restored.recipe_id == sample_recipe.recipe_id
        assert restored.result_id == sample_recipe.result_id


# ============================================================================
# PlayerInventory 测试
# ============================================================================


class TestPlayerInventory:
    """玩家背包测试"""

    def test_empty_inventory(self):
        """测试空背包"""
        inventory = PlayerInventory()
        assert inventory.gold == 0
        assert len(inventory.equipment) == 0

    def test_add_equipment(self):
        """测试添加装备"""
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 1)
        assert inventory.get_equipment_count("eq_001") == 1

        inventory.add_equipment("eq_001", 2)
        assert inventory.get_equipment_count("eq_001") == 3

    def test_remove_equipment(self):
        """测试移除装备"""
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 3)

        assert inventory.remove_equipment("eq_001", 1) is True
        assert inventory.get_equipment_count("eq_001") == 2

        assert inventory.remove_equipment("eq_001", 2) is True
        assert inventory.get_equipment_count("eq_001") == 0
        assert "eq_001" not in inventory.equipment

    def test_remove_equipment_insufficient(self):
        """测试移除装备 - 数量不足"""
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 1)

        assert inventory.remove_equipment("eq_001", 2) is False
        assert inventory.get_equipment_count("eq_001") == 1

    def test_has_equipment(self):
        """测试检查装备"""
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 3)

        assert inventory.has_equipment("eq_001", 1) is True
        assert inventory.has_equipment("eq_001", 3) is True
        assert inventory.has_equipment("eq_001", 4) is False
        assert inventory.has_equipment("eq_002", 1) is False

    def test_inventory_serialization(self):
        """测试背包序列化"""
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 2)
        inventory.add_equipment("eq_002", 1)
        inventory.gold = 100

        data = inventory.to_dict()
        restored = PlayerInventory.from_dict(data)

        assert restored.gold == 100
        assert restored.get_equipment_count("eq_001") == 2
        assert restored.get_equipment_count("eq_002") == 1


# ============================================================================
# CraftingManager 测试
# ============================================================================


class TestCraftingManager:
    """合成管理器测试"""

    def test_create_manager(self):
        """测试创建管理器"""
        manager = CraftingManager()
        assert manager.get_recipe_count() == 0

    def test_add_recipe(self, sample_recipe):
        """测试添加配方"""
        manager = CraftingManager()
        manager.add_recipe(sample_recipe)

        assert manager.get_recipe_count() == 1
        assert manager.get_recipe("test_recipe_001") == sample_recipe

    def test_find_matching_recipes(self, sample_recipe):
        """测试查找匹配配方"""
        manager = CraftingManager()
        manager.add_recipe(sample_recipe)

        matches = manager.find_matching_recipes(["eq_006", "eq_006"])
        assert len(matches) == 1
        assert matches[0].recipe_id == "test_recipe_001"

        no_matches = manager.find_matching_recipes(["eq_007"])
        assert len(no_matches) == 0

    def test_find_recipes_using_equipment(self, sample_recipe):
        """测试查找使用特定装备的配方"""
        manager = CraftingManager()
        manager.add_recipe(sample_recipe)

        recipes = manager.find_recipes_using_equipment("eq_006")
        assert len(recipes) == 1

        no_recipes = manager.find_recipes_using_equipment("eq_999")
        assert len(no_recipes) == 0

    def test_can_craft_success(self, sample_recipe, sample_inventory):
        """测试检查可合成 - 成功"""
        manager = CraftingManager()
        can_craft, msg = manager.can_craft(sample_recipe, sample_inventory)
        assert can_craft is True
        assert msg == ""

    def test_can_craft_missing_material(self, sample_recipe):
        """测试检查可合成 - 缺少材料"""
        manager = CraftingManager()
        inventory = PlayerInventory()
        inventory.gold = 100

        can_craft, msg = manager.can_craft(sample_recipe, inventory)
        assert can_craft is False
        assert "缺少材料" in msg

    def test_can_craft_insufficient_gold(self, sample_recipe):
        """测试检查可合成 - 金币不足"""
        manager = CraftingManager()
        inventory = PlayerInventory()
        inventory.add_equipment("eq_006", 2)
        inventory.gold = 10  # 需要50

        can_craft, msg = manager.can_craft(sample_recipe, inventory)
        assert can_craft is False
        assert "金币不足" in msg

    def test_get_craftable_recipes(self, sample_recipe, sample_inventory):
        """测试获取可合成配方列表"""
        manager = CraftingManager()
        manager.add_recipe(sample_recipe)

        craftable = manager.get_craftable_recipes(sample_inventory)
        assert len(craftable) == 1

    def test_craft_success(self, sample_recipe, sample_inventory):
        """测试执行合成 - 成功"""
        manager = CraftingManager()
        result = manager.craft(sample_recipe, sample_inventory)

        assert result.success is True
        assert result.result_equipment_id == "eq_011"
        assert result.gold_spent == 50
        assert len(result.materials_consumed) == 2

        # 验证背包变化
        assert sample_inventory.gold == 150  # 200 - 50
        assert sample_inventory.get_equipment_count("eq_006") == 1  # 3 - 2
        assert sample_inventory.get_equipment_count("eq_011") == 1  # 新增

    def test_craft_failure_insufficient_material(self, sample_recipe):
        """测试执行合成 - 材料不足"""
        manager = CraftingManager()
        inventory = PlayerInventory()
        inventory.add_equipment("eq_006", 1)  # 只有1个，需要2个
        inventory.gold = 100

        result = manager.craft(sample_recipe, inventory)
        assert result.success is False
        assert "缺少材料" in result.error_message

    def test_craft_history(self, sample_recipe, sample_inventory):
        """测试合成历史记录"""
        manager = CraftingManager()
        manager.craft(sample_recipe, sample_inventory)

        history = manager.get_history()
        assert len(history) == 1
        assert history[0].recipe_id == "test_recipe_001"
        assert history[0].success is True

    def test_craft_with_equipment_ids(self, sample_recipe, sample_inventory):
        """测试使用装备ID列表合成"""
        manager = CraftingManager()
        manager.add_recipe(sample_recipe)

        result = manager.craft_with_equipment_ids(["eq_006", "eq_006"], sample_inventory)

        assert result.success is True
        assert result.result_equipment_id == "eq_011"


# ============================================================================
# 集成测试 - 使用配置文件
# ============================================================================


class TestCraftingIntegration:
    """集成测试"""

    def test_load_recipes_from_config(self, crafting_manager):
        """测试从配置文件加载配方"""
        # 如果配置文件存在，应该有配方
        count = crafting_manager.get_recipe_count()
        assert count > 0, "应该从配置文件加载到配方"

    def test_basic_sword_recipe(self, crafting_manager):
        """测试基础剑合成配方"""
        recipe = crafting_manager.get_recipe("recipe_basic_sword")
        if recipe:
            assert recipe.result_id == "eq_006"
            assert len(recipe.materials) == 1
            assert recipe.materials[0].equipment_id == "eq_001"
            assert recipe.materials[0].quantity == 2

    def test_epic_recipes(self, crafting_manager):
        """测试史诗装备合成配方"""
        # 破军配方
        recipe = crafting_manager.get_recipe("recipe_sword_sword")
        if recipe:
            assert recipe.result_id == "eq_011"
            assert recipe.gold_cost == 50

        # 博学者之怒配方
        recipe = crafting_manager.get_recipe("recipe_staff_staff")
        if recipe:
            assert recipe.result_id == "eq_013"

    def test_full_crafting_workflow(self, crafting_manager):
        """测试完整合成流程"""
        # 创建一个有基础材料的背包
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 4)  # 4个铁剑
        inventory.gold = 100

        # 第一次合成：铁剑 -> 暴风大剑
        recipe = crafting_manager.get_recipe("recipe_basic_sword")
        if recipe:
            result = crafting_manager.craft(recipe, inventory)
            assert result.success is True
            assert inventory.get_equipment_count("eq_001") == 2
            assert inventory.get_equipment_count("eq_006") == 1

        # 第二次合成：再合成一把暴风大剑
        if recipe:
            result = crafting_manager.craft(recipe, inventory)
            assert result.success is True
            assert inventory.get_equipment_count("eq_006") == 2

        # 第三次合成：暴风大剑 + 暴风大剑 -> 破军
        epic_recipe = crafting_manager.get_recipe("recipe_sword_sword")
        if epic_recipe:
            result = crafting_manager.craft(epic_recipe, inventory)
            assert result.success is True
            assert inventory.get_equipment_count("eq_006") == 0
            assert inventory.get_equipment_count("eq_011") == 1


# ============================================================================
# 稀有度和特殊效果测试
# ============================================================================


class TestRarityAndEffects:
    """稀有度和特殊效果测试"""

    def test_rarity_values(self):
        """测试稀有度枚举值"""
        assert Rarity.COMMON.value == "common"
        assert Rarity.RARE.value == "rare"
        assert Rarity.EPIC.value == "epic"
        assert Rarity.LEGENDARY.value == "legendary"

    def test_rarity_colors(self):
        """测试稀有度颜色"""
        assert Rarity.COMMON.get_color_code() == "#FFFFFF"
        assert Rarity.RARE.get_color_code() == "#1EFF00"
        assert Rarity.EPIC.get_color_code() == "#A335EE"
        assert Rarity.LEGENDARY.get_color_code() == "#FF8000"

    def test_special_effect_types(self):
        """测试特殊效果类型"""
        assert SpecialEffectType.BURN.value == "burn"
        assert SpecialEffectType.FREEZE.value == "freeze"
        assert SpecialEffectType.CRIT.value == "crit"

    def test_special_effect_creation(self):
        """测试特殊效果创建"""
        effect = SpecialEffect(
            effect_type=SpecialEffectType.BURN, value=20, duration=3.0, trigger_chance=0.25
        )
        assert effect.effect_type == SpecialEffectType.BURN
        assert effect.value == 20
        assert effect.duration == 3.0
        assert effect.trigger_chance == 0.25

    def test_special_effect_serialization(self):
        """测试特殊效果序列化"""
        effect = SpecialEffect(effect_type=SpecialEffectType.FREEZE, value=0.2, duration=2.0)
        data = effect.to_dict()
        restored = SpecialEffect.from_dict(data)

        assert restored.effect_type == effect.effect_type
        assert restored.value == effect.value


# ============================================================================
# 边界情况测试
# ============================================================================


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_inventory_operations(self):
        """测试空背包操作"""
        inventory = PlayerInventory()
        assert inventory.has_equipment("eq_001", 0) is True
        assert inventory.has_equipment("eq_001", 1) is False
        assert inventory.remove_equipment("eq_001", 1) is False

    def test_recipe_with_single_material(self):
        """测试单个材料的配方"""
        recipe = CraftingRecipe(
            recipe_id="single_mat",
            result_id="eq_999",
            materials=[CraftingMaterial(equipment_id="eq_001", quantity=1)],
            gold_cost=0,
        )
        assert recipe.matches_materials(["eq_001"]) is True

    def test_recipe_with_many_materials(self):
        """测试多个材料的配方"""
        recipe = CraftingRecipe(
            recipe_id="multi_mat",
            result_id="eq_999",
            materials=[
                CraftingMaterial(equipment_id="eq_001", quantity=3),
                CraftingMaterial(equipment_id="eq_002", quantity=2),
            ],
            gold_cost=0,
        )
        assert recipe.matches_materials(["eq_001", "eq_001", "eq_001", "eq_002", "eq_002"]) is True
        assert recipe.matches_materials(["eq_001", "eq_002"]) is False

    def test_zero_gold_recipe(self):
        """测试免费配方"""
        recipe = CraftingRecipe(
            recipe_id="free",
            result_id="eq_999",
            materials=[CraftingMaterial(equipment_id="eq_001", quantity=1)],
            gold_cost=0,
        )
        inventory = PlayerInventory()
        inventory.add_equipment("eq_001", 1)
        inventory.gold = 0

        manager = CraftingManager()
        can_craft, _ = manager.can_craft(recipe, inventory)
        assert can_craft is True

    def test_multiple_matching_recipes(self):
        """测试多个配方匹配同一材料组合"""
        manager = CraftingManager()

        # 添加两个使用相同材料的配方
        recipe1 = CraftingRecipe(
            recipe_id="r1",
            result_id="eq_100",
            materials=[CraftingMaterial(equipment_id="eq_001", quantity=1)],
            gold_cost=10,
        )
        recipe2 = CraftingRecipe(
            recipe_id="r2",
            result_id="eq_101",
            materials=[CraftingMaterial(equipment_id="eq_001", quantity=1)],
            gold_cost=20,
        )
        manager.add_recipe(recipe1)
        manager.add_recipe(recipe2)

        matches = manager.find_matching_recipes(["eq_001"])
        assert len(matches) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
