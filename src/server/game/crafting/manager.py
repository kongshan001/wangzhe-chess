"""
王者之奕 - 装备合成管理器
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .models import (
    CraftingHistoryEntry,
    CraftingMaterial,
    CraftingRecipe,
    CraftingResult,
    Rarity,
    SpecialEffect,
)


@dataclass
class PlayerInventory:
    """玩家装备背包"""
    equipment: Dict[str, int] = field(default_factory=dict)  # equipment_id -> count
    gold: int = 0
    
    def add_equipment(self, equipment_id: str, count: int = 1) -> None:
        """添加装备"""
        self.equipment[equipment_id] = self.equipment.get(equipment_id, 0) + count
    
    def remove_equipment(self, equipment_id: str, count: int = 1) -> bool:
        """
        移除装备
        
        Returns:
            是否成功移除
        """
        current = self.equipment.get(equipment_id, 0)
        if current < count:
            return False
        self.equipment[equipment_id] = current - count
        if self.equipment[equipment_id] <= 0:
            del self.equipment[equipment_id]
        return True
    
    def get_equipment_count(self, equipment_id: str) -> int:
        """获取装备数量"""
        return self.equipment.get(equipment_id, 0)
    
    def has_equipment(self, equipment_id: str, count: int = 1) -> bool:
        """检查是否拥有足够装备"""
        return self.get_equipment_count(equipment_id) >= count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipment": dict(self.equipment),
            "gold": self.gold,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlayerInventory:
        return cls(
            equipment=data.get("equipment", {}),
            gold=data.get("gold", 0),
        )


class CraftingManager:
    """
    装备合成管理器
    
    负责管理合成配方、执行合成操作、记录合成历史
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化合成管理器
        
        Args:
            config_path: 合成配方配置文件路径
        """
        self.recipes: Dict[str, CraftingRecipe] = {}  # recipe_id -> recipe
        self._material_index: Dict[str, List[str]] = {}  # 装备ID -> 可用配方ID列表
        self._history: List[CraftingHistoryEntry] = []
        
        if config_path:
            self.load_recipes(config_path)
    
    def load_recipes(self, config_path: str) -> None:
        """从JSON文件加载合成配方"""
        path = Path(config_path)
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for recipe_data in data.get("recipes", []):
            recipe = CraftingRecipe.from_dict(recipe_data)
            self.add_recipe(recipe)
    
    def add_recipe(self, recipe: CraftingRecipe) -> None:
        """添加合成配方"""
        self.recipes[recipe.recipe_id] = recipe
        
        # 更新材料索引
        for material in recipe.materials:
            if material.equipment_id not in self._material_index:
                self._material_index[material.equipment_id] = []
            if recipe.recipe_id not in self._material_index[material.equipment_id]:
                self._material_index[material.equipment_id].append(recipe.recipe_id)
    
    def get_recipe(self, recipe_id: str) -> Optional[CraftingRecipe]:
        """获取配方"""
        return self.recipes.get(recipe_id)
    
    def get_all_recipes(self) -> List[CraftingRecipe]:
        """获取所有配方"""
        return list(self.recipes.values())
    
    def find_matching_recipes(self, equipment_ids: List[str]) -> List[CraftingRecipe]:
        """
        查找匹配所提供装备的配方
        
        Args:
            equipment_ids: 装备ID列表
            
        Returns:
            匹配的配方列表
        """
        matches = []
        for recipe in self.recipes.values():
            if recipe.matches_materials(equipment_ids):
                matches.append(recipe)
        return matches
    
    def find_recipes_using_equipment(self, equipment_id: str) -> List[CraftingRecipe]:
        """
        查找使用指定装备的所有配方
        
        Args:
            equipment_id: 装备ID
            
        Returns:
            使用该装备的配方列表
        """
        recipe_ids = self._material_index.get(equipment_id, [])
        return [self.recipes[rid] for rid in recipe_ids if rid in self.recipes]
    
    def can_craft(
        self,
        recipe: CraftingRecipe,
        inventory: PlayerInventory
    ) -> tuple[bool, str]:
        """
        检查是否可以执行合成
        
        Args:
            recipe: 合成配方
            inventory: 玩家背包
            
        Returns:
            (是否可以合成, 错误信息)
        """
        # 检查材料
        for material in recipe.materials:
            if not inventory.has_equipment(material.equipment_id, material.quantity):
                return False, f"缺少材料: {material.equipment_id}"
        
        # 检查金币
        if inventory.gold < recipe.gold_cost:
            return False, f"金币不足: 需要{recipe.gold_cost}, 当前{inventory.gold}"
        
        return True, ""
    
    def get_craftable_recipes(self, inventory: PlayerInventory) -> List[CraftingRecipe]:
        """
        获取玩家当前可合成的所有配方
        
        Args:
            inventory: 玩家背包
            
        Returns:
            可合成的配方列表
        """
        craftable = []
        for recipe in self.recipes.values():
            can_craft, _ = self.can_craft(recipe, inventory)
            if can_craft:
                craftable.append(recipe)
        return craftable
    
    def craft(
        self,
        recipe: CraftingRecipe,
        inventory: PlayerInventory
    ) -> CraftingResult:
        """
        执行装备合成
        
        Args:
            recipe: 合成配方
            inventory: 玩家背包（会被修改）
            
        Returns:
            合成结果
        """
        # 检查是否可以合成
        can_craft, error_msg = self.can_craft(recipe, inventory)
        if not can_craft:
            return CraftingResult(
                success=False,
                error_message=error_msg
            )
        
        # 消耗材料
        consumed = []
        for material in recipe.materials:
            for _ in range(material.quantity):
                if inventory.remove_equipment(material.equipment_id, 1):
                    consumed.append(material.equipment_id)
        
        # 消耗金币
        inventory.gold -= recipe.gold_cost
        
        # 执行合成（考虑成功率）
        import random
        if random.random() > recipe.success_rate:
            # 合成失败（材料消耗但不产出装备）
            entry = CraftingHistoryEntry(
                recipe_id=recipe.recipe_id,
                result_id="",
                materials=consumed,
                gold_cost=recipe.gold_cost,
                timestamp=time.time(),
                success=False
            )
            self._history.append(entry)
            return CraftingResult(
                success=False,
                gold_spent=recipe.gold_cost,
                materials_consumed=consumed,
                error_message="合成失败！"
            )
        
        # 添加合成结果
        inventory.add_equipment(recipe.result_id, 1)
        
        # 记录历史
        entry = CraftingHistoryEntry(
            recipe_id=recipe.recipe_id,
            result_id=recipe.result_id,
            materials=consumed,
            gold_cost=recipe.gold_cost,
            timestamp=time.time(),
            success=True
        )
        self._history.append(entry)
        
        return CraftingResult(
            success=True,
            result_equipment_id=recipe.result_id,
            gold_spent=recipe.gold_cost,
            materials_consumed=consumed
        )
    
    def craft_with_equipment_ids(
        self,
        equipment_ids: List[str],
        inventory: PlayerInventory
    ) -> CraftingResult:
        """
        使用装备ID列表进行合成（自动匹配配方）
        
        Args:
            equipment_ids: 要合成的装备ID列表
            inventory: 玩家背包
            
        Returns:
            合成结果
        """
        # 查找匹配的配方
        matching = self.find_matching_recipes(equipment_ids)
        
        if not matching:
            return CraftingResult(
                success=False,
                error_message="没有找到匹配的合成配方"
            )
        
        if len(matching) > 1:
            # 多个配方匹配，选择第一个
            pass
        
        recipe = matching[0]
        
        # 再次检查背包是否拥有这些装备
        from collections import Counter
        counts = Counter(equipment_ids)
        for eq_id, needed in counts.items():
            if not inventory.has_equipment(eq_id, needed):
                return CraftingResult(
                    success=False,
                    error_message=f"缺少装备: {eq_id}"
                )
        
        return self.craft(recipe, inventory)
    
    def get_history(self, limit: int = 100) -> List[CraftingHistoryEntry]:
        """获取合成历史"""
        return self._history[-limit:]
    
    def clear_history(self) -> None:
        """清空合成历史"""
        self._history.clear()
    
    def get_recipe_count(self) -> int:
        """获取配方数量"""
        return len(self.recipes)


def create_crafting_manager(config_path: Optional[str] = None) -> CraftingManager:
    """
    创建合成管理器的工厂函数
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        合成管理器实例
    """
    if config_path is None:
        # 尝试使用默认配置路径
        default_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "crafting-recipes.json"
        if default_path.exists():
            config_path = str(default_path)
    
    return CraftingManager(config_path=config_path)
