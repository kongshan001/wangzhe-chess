"""
王者之奕 - 装备合成与背包集成测试

测试装备合成系统与背包的跨模块交互：
- 合成操作与背包状态更新
- 材料消耗与金币消耗
- 合成失败处理
- 背包容量管理
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import tempfile

from src.server.game.crafting.manager import (
    CraftingManager,
    PlayerInventory,
    create_crafting_manager,
)
from src.server.game.crafting.models import (
    CraftingRecipe,
    CraftingMaterial,
    CraftingResult,
    Rarity,
    SpecialEffect,
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
        inventory = PlayerInventory(
            equipment={"sword_001": 5, "shield_001": 2},
            gold=1000
        )
        
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
            name="合成大剑",
            description="合成一把大剑",
            materials=[
                CraftingMaterial(equipment_id="iron_001", quantity=2),
                CraftingMaterial(equipment_id="wood_001", quantity=1),
            ],
            result_id="sword_002",
            result_name="大剑",
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
            name="合成大剑",
            description="合成一把大剑",
            materials=[
                CraftingMaterial(equipment_id="iron_001", quantity=2),
            ],
            result_id="sword_002",
            result_name="大剑",
            gold_cost=100,
            success_rate=0.9,
            rarity=Rarity.EPIC,
            special_effects=[SpecialEffect(name="暴击", value=10)],
        )
        
        # 序列化
        data = recipe.to_dict()
        assert data["recipe_id"] == "recipe_001"
        assert data["rarity"] == "epic"
        
        # 反序列化
        loaded = CraftingRecipe.from_dict(data)
        assert loaded.recipe_id == "recipe_001"
        assert loaded.rarity == Rarity.EPIC


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
                name="铁剑合成",
                description="合成铁剑",
                materials=[
                    CraftingMaterial(equipment_id="iron", quantity=2),
                ],
                result_id="iron_sword",
                result_name="铁剑",
                gold_cost=50,
                success_rate=1.0,
            ),
            CraftingRecipe(
                recipe_id="recipe_shield",
                name="铁盾合成",
                description="合成铁盾",
                materials=[
                    CraftingMaterial(equipment_id="iron", quantity=3),
                ],
                result_id="iron_shield",
                result_name="铁盾",
                gold_cost=100,
                success_rate=1.0,
            ),
            CraftingRecipe(
                recipe_id="recipe_legendary",
                name="传说武器",
                description="合成传说武器",
                materials=[
                    CraftingMaterial(equipment_id="iron_sword", quantity=1),
                    CraftingMaterial(equipment_id="iron_shield", quantity=1),
                    CraftingMaterial(equipment_id="gem", quantity=2),
                ],
                result_id="legendary_weapon",
                result_name="传说武器",
                gold_cost=500,
                success_rate=0.8,
                rarity=Rarity.LEGENDARY,
            ),
        ]
        
        for recipe in recipes:
            manager.add_recipe(recipe)
        
        return manager

    def test_add_recipe(self, manager_with_recipes):
        """测试添加配方"""
        manager = manager_with_recipes
        
        assert manager.get_recipe_count() == 3
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

    def test_find_recipes_using_equipment(self, manager_with_recipes):
        """测试查找使用指定装备的配方"""
        manager = manager_with_recipes
        
        # 查找使用 iron 的配方
        recipes = manager.find_recipes_using_equipment("iron")
        assert len(recipes) == 2  # 铁剑和铁盾
        
        # 查找使用 iron_sword 的配方
        recipes = manager.find_recipes_using_equipment("iron_sword")
        assert len(recipes) == 1  # 传说武器
        assert recipes[0].recipe_id == "recipe_legendary"

    def test_can_craft_success(self, manager_with_recipes):
        """测试检查是否可合成 - 成功"""
        manager = manager_with_recipes
        
        recipe = manager.get_recipe("recipe_sword")
        inventory = PlayerInventory(
            equipment={"iron": 5},
            gold=100
        )
        
        can_craft, error = manager.can_craft(recipe, inventory)
        assert can_craft is True
        assert error == ""

    def test_can_craft_missing_material(self, manager_with_recipes):
        """测试检查是否可合成 - 缺少材料"""
        manager = manager_with_recipes
        
        recipe = manager.get_recipe("recipe_sword")
        inventory = PlayerInventory(
            equipment={"iron": 1},
            gold=100
        )
        
        can_craft, error = manager.can_craft(recipe, inventory)
        assert can_craft is False
        assert "缺少材料" in error

    def test_can_craft_insufficient_gold(self, manager_with_recipes):
        """测试检查是否可合成 - 金币不足"""
        manager = manager_with_recipes
        
        recipe = manager.get_recipe("recipe_shield")
        inventory = PlayerInventory(
            equipment={"iron": 5},
            gold=50  # 需要100
        )
        
        can_craft, error = manager.can_craft(recipe, inventory)
        assert can_craft is False
        assert "金币不足" in error

    def test_craft_success(self, manager_with_recipes):
        """测试合成成功"""
        manager = manager_with_recipes
        
        recipe = manager.get_recipe("recipe_sword")
        inventory = PlayerInventory(
            equipment={"iron": 5},
            gold=100
        )
        
        # 执行合成（成功率100%）
        result = manager.craft(recipe, inventory)
        
        assert result.success is True
        assert result.result_equipment_id == "iron_sword"
        assert result.gold_spent == 50
        assert len(result.materials_consumed) == 2
        
        # 验证背包更新
        assert inventory.get_equipment_count("iron") == 3
        assert inventory.get_equipment_count("iron_sword") == 1
        assert inventory.gold == 50

    def test_craft_failure(self, manager_with_recipes):
        """测试合成失败"""
        manager = manager_with_recipes
        
        # 使用传说武器配方（80%成功率）
        recipe = manager.get_recipe("recipe_legendary")
        inventory = PlayerInventory(
            equipment={"iron_sword": 1, "iron_shield": 1, "gem": 2},
            gold=1000
        )
        
        # 多次尝试，验证失败情况
        with patch('random.random', return_value=0.9):  # 模拟失败
            result = manager.craft(recipe, inventory)
        
        assert result.success is False
        assert "合成失败" in result.error_message
        assert result.gold_spent == 500  # 金币仍然消耗

    def test_craft_with_equipment_ids(self, manager_with_recipes):
        """测试使用装备ID列表合成"""
        manager = manager_with_recipes
        
        inventory = PlayerInventory(
            equipment={"iron": 5},
            gold=100
        )
        
        result = manager.craft_with_equipment_ids(
            equipment_ids=["iron", "iron"],
            inventory=inventory
        )
        
        assert result.success is True
        assert result.result_equipment_id == "iron_sword"

    def test_get_craftable_recipes(self, manager_with_recipes):
        """测试获取可合成配方列表"""
        manager = manager_with_recipes
        
        # 足够材料合成铁剑
        inventory1 = PlayerInventory(
            equipment={"iron": 2},
            gold=100
        )
        craftable = manager.get_craftable_recipes(inventory1)
        assert len(craftable) == 1
        assert craftable[0].recipe_id == "recipe_sword"
        
        # 足够材料合成两个配方
        inventory2 = PlayerInventory(
            equipment={"iron": 5},
            gold=200
        )
        craftable = manager.get_craftable_recipes(inventory2)
        assert len(craftable) == 2

    def test_crafting_history(self, manager_with_recipes):
        """测试合成历史记录"""
        manager = manager_with_recipes
        
        recipe = manager.get_recipe("recipe_sword")
        inventory = PlayerInventory(
            equipment={"iron": 10},
            gold=500
        )
        
        # 执行多次合成
        for _ in range(3):
            manager.craft(recipe, inventory)
        
        # 获取历史
        history = manager.get_history()
        assert len(history) == 3
        
        # 验证历史记录内容
        for entry in history:
            assert entry.recipe_id == "recipe_sword"
            assert entry.success is True

    def test_crafting_chain(self, manager_with_recipes):
        """测试合成链（基础材料 -> 中级装备 -> 高级装备）"""
        manager = manager_with_recipes
        
        # 初始材料
        inventory = PlayerInventory(
            equipment={"iron": 10, "gem": 5},
            gold=1000
        )
        
        # 第一阶段：合成铁剑
        recipe1 = manager.get_recipe("recipe_sword")
        result1 = manager.craft(recipe1, inventory)
        assert result1.success is True
        assert inventory.get_equipment_count("iron_sword") == 1
        
        # 第一阶段：合成铁盾
        recipe2 = manager.get_recipe("recipe_shield")
        result2 = manager.craft(recipe2, inventory)
        assert result2.success is True
        assert inventory.get_equipment_count("iron_shield") == 1
        
        # 第二阶段：合成传说武器
        recipe3 = manager.get_recipe("recipe_legendary")
        with patch('random.random', return_value=0.5):  # 确保成功
            result3 = manager.craft(recipe3, inventory)
        
        assert result3.success is True
        assert inventory.get_equipment_count("legendary_weapon") == 1
        assert inventory.get_equipment_count("iron_sword") == 0
        assert inventory.get_equipment_count("iron_shield") == 0


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
                    "name": "数据库配方",
                    "description": "从数据库加载的配方",
                    "materials": [
                        {"equipment_id": "mat_001", "quantity": 2}
                    ],
                    "result_id": "result_001",
                    "result_name": "合成结果",
                    "gold_cost": 100,
                    "success_rate": 1.0,
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
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
        assert recipe.name == "数据库配方"


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

    def test_concurrent_crafting_safety(self):
        """测试连续合成的安全性"""
        manager = CraftingManager()
        manager.add_recipe(CraftingRecipe(
            recipe_id="test_recipe",
            name="测试",
            description="测试",
            materials=[CraftingMaterial(equipment_id="mat", quantity=1)],
            result_id="result",
            result_name="结果",
            gold_cost=10,
            success_rate=1.0,
        ))
        
        inventory = PlayerInventory(equipment={"mat": 5}, gold=100)
        recipe = manager.get_recipe("test_recipe")
        
        # 连续合成5次
        for i in range(5):
            result = manager.craft(recipe, inventory)
            assert result.success is True, f"合成失败于第{i+1}次"
        
        # 验证最终状态
        assert inventory.get_equipment_count("mat") == 0
        assert inventory.get_equipment_count("result") == 5
        assert inventory.gold == 50
