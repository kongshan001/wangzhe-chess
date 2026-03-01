"""
王者之奕 - 阵容预设系统测试

本模块测试阵容预设系统的核心功能：
- 数据模型转换
- 预设保存和加载
- 预设删除和重命名
- 预设数量限制
- 应用预设
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.lineup import (
    MAX_EQUIPMENT_PER_HERO,
    MAX_HEROES_PER_PRESET,
    MAX_PRESETS_PER_PLAYER,
    EquipmentAssignment,
    LineupManager,
    LineupPreset,
    LineupSlot,
    TargetSynergy,
)
from src.server.lineup.models import (
    EquipmentAssignment,
    LineupPreset,
    LineupSlot,
    TargetSynergy,
)

# ============================================================================
# 数据模型测试
# ============================================================================


class TestEquipmentAssignment:
    """装备分配模型测试"""

    def test_create_equipment(self):
        """测试创建装备分配"""
        eq = EquipmentAssignment(equipment_id="sword_001", slot=0)
        assert eq.equipment_id == "sword_001"
        assert eq.slot == 0

    def test_equipment_to_dict(self):
        """测试装备转换为字典"""
        eq = EquipmentAssignment(equipment_id="sword_001", slot=1)
        data = eq.to_dict()

        assert data["equipment_id"] == "sword_001"
        assert data["slot"] == 1

    def test_equipment_from_dict(self):
        """测试从字典创建装备"""
        data = {"equipment_id": "armor_001", "slot": 2}
        eq = EquipmentAssignment.from_dict(data)

        assert eq.equipment_id == "armor_001"
        assert eq.slot == 2


class TestLineupSlot:
    """英雄槽位模型测试"""

    def test_create_slot(self):
        """测试创建英雄槽位"""
        slot = LineupSlot(
            hero_id="hero_001",
            row=3,
            col=2,
            star_level=2,
        )

        assert slot.hero_id == "hero_001"
        assert slot.row == 3
        assert slot.col == 2
        assert slot.star_level == 2
        assert slot.equipment == []

    def test_slot_with_equipment(self):
        """测试带装备的英雄槽位"""
        equipment = [
            EquipmentAssignment("sword_001", 0),
            EquipmentAssignment("armor_001", 1),
        ]
        slot = LineupSlot(
            hero_id="hero_001",
            row=0,
            col=0,
            equipment=equipment,
        )

        assert len(slot.equipment) == 2
        assert slot.equipment[0].equipment_id == "sword_001"

    def test_add_equipment(self):
        """测试添加装备"""
        slot = LineupSlot(hero_id="hero_001", row=0, col=0)

        # 添加装备
        assert slot.add_equipment("sword_001", 0) is True
        assert len(slot.equipment) == 1

        # 添加第二件装备
        assert slot.add_equipment("armor_001", 1) is True
        assert len(slot.equipment) == 2

        # 添加第三件装备
        assert slot.add_equipment("boots_001", 2) is True
        assert len(slot.equipment) == 3

        # 超过上限
        assert slot.add_equipment("ring_001", 3) is False
        assert len(slot.equipment) == 3

    def test_add_equipment_duplicate_slot(self):
        """测试重复槽位"""
        slot = LineupSlot(hero_id="hero_001", row=0, col=0)

        slot.add_equipment("sword_001", 0)

        # 同一槽位
        assert slot.add_equipment("sword_002", 0) is False
        assert len(slot.equipment) == 1

    def test_remove_equipment(self):
        """测试移除装备"""
        slot = LineupSlot(hero_id="hero_001", row=0, col=0)
        slot.add_equipment("sword_001", 0)

        # 移除装备
        assert slot.remove_equipment("sword_001") is True
        assert len(slot.equipment) == 0

        # 移除不存在的装备
        assert slot.remove_equipment("not_exist") is False

    def test_slot_to_dict(self):
        """测试槽位转换为字典"""
        slot = LineupSlot(
            hero_id="hero_001",
            row=3,
            col=2,
            star_level=2,
        )
        slot.add_equipment("sword_001", 0)

        data = slot.to_dict()

        assert data["hero_id"] == "hero_001"
        assert data["row"] == 3
        assert data["col"] == 2
        assert data["star_level"] == 2
        assert len(data["equipment"]) == 1

    def test_slot_from_dict(self):
        """测试从字典创建槽位"""
        data = {
            "hero_id": "hero_002",
            "row": 4,
            "col": 3,
            "star_level": 3,
            "equipment": [
                {"equipment_id": "sword_001", "slot": 0},
                {"equipment_id": "armor_001", "slot": 1},
            ],
        }

        slot = LineupSlot.from_dict(data)

        assert slot.hero_id == "hero_002"
        assert slot.row == 4
        assert slot.col == 3
        assert slot.star_level == 3
        assert len(slot.equipment) == 2


class TestTargetSynergy:
    """目标羁绊模型测试"""

    def test_create_synergy(self):
        """测试创建目标羁绊"""
        synergy = TargetSynergy(
            synergy_id="warrior",
            target_count=6,
            priority=5,
            note="前排坦克",
        )

        assert synergy.synergy_id == "warrior"
        assert synergy.target_count == 6
        assert synergy.priority == 5
        assert synergy.note == "前排坦克"

    def test_synergy_to_dict(self):
        """测试羁绊转换为字典"""
        synergy = TargetSynergy(
            synergy_id="mage",
            target_count=4,
            priority=4,
        )

        data = synergy.to_dict()

        assert data["synergy_id"] == "mage"
        assert data["target_count"] == 4
        assert data["priority"] == 4
        assert data["note"] == ""

    def test_synergy_from_dict(self):
        """测试从字典创建羁绊"""
        data = {
            "synergy_id": "assassin",
            "target_count": 3,
            "priority": 3,
            "note": "切后排",
        }

        synergy = TargetSynergy.from_dict(data)

        assert synergy.synergy_id == "assassin"
        assert synergy.target_count == 3
        assert synergy.priority == 3
        assert synergy.note == "切后排"


class TestLineupPreset:
    """阵容预设模型测试"""

    def test_create_preset(self):
        """测试创建预设"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="战士流",
            description="前排战士坦克阵容",
        )

        assert preset.preset_id == "preset_001"
        assert preset.player_id == "player_001"
        assert preset.name == "战士流"
        assert preset.description == "前排战士坦克阵容"
        assert preset.slots == []
        assert preset.target_synergies == []
        assert preset.created_at is not None
        assert preset.updated_at is not None

    def test_add_slot(self):
        """测试添加英雄槽位"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        slot1 = LineupSlot(hero_id="hero_001", row=0, col=0)
        slot2 = LineupSlot(hero_id="hero_002", row=0, col=1)

        assert preset.add_slot(slot1) is True
        assert preset.add_slot(slot2) is True
        assert preset.hero_count == 2

    def test_add_slot_limit(self):
        """测试添加英雄超过上限"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        # 添加9个英雄
        for i in range(9):
            slot = LineupSlot(hero_id=f"hero_{i:03d}", row=i // 4, col=i % 4)
            assert preset.add_slot(slot) is True

        assert preset.hero_count == 9

        # 尝试添加第10个
        slot = LineupSlot(hero_id="hero_009", row=2, col=0)
        assert preset.add_slot(slot) is False
        assert preset.hero_count == 9

    def test_remove_slot(self):
        """测试移除英雄槽位"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        slot = LineupSlot(hero_id="hero_001", row=0, col=0)
        preset.add_slot(slot)

        assert preset.remove_slot("hero_001") is True
        assert preset.hero_count == 0

        assert preset.remove_slot("not_exist") is False

    def test_update_slot(self):
        """测试更新英雄槽位"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        slot = LineupSlot(hero_id="hero_001", row=0, col=0, star_level=1)
        preset.add_slot(slot)

        # 更新星级
        assert preset.update_slot("hero_001", star_level=2, row=1) is True

        updated = preset.get_slot("hero_001")
        assert updated.star_level == 2
        assert updated.row == 1

    def test_get_slot(self):
        """测试获取英雄槽位"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        slot = LineupSlot(hero_id="hero_001", row=0, col=0)
        preset.add_slot(slot)

        found = preset.get_slot("hero_001")
        assert found is not None
        assert found.hero_id == "hero_001"

        not_found = preset.get_slot("not_exist")
        assert not_found is None

    def test_add_target_synergy(self):
        """测试添加目标羁绊"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        synergy = TargetSynergy(synergy_id="warrior", target_count=6)
        preset.add_target_synergy(synergy)

        assert len(preset.target_synergies) == 1

    def test_remove_target_synergy(self):
        """测试移除目标羁绊"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        synergy = TargetSynergy(synergy_id="warrior", target_count=6)
        preset.add_target_synergy(synergy)

        assert preset.remove_target_synergy("warrior") is True
        assert len(preset.target_synergies) == 0

        assert preset.remove_target_synergy("not_exist") is False

    def test_hero_ids_property(self):
        """测试hero_ids属性"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0))
        preset.add_slot(LineupSlot(hero_id="hero_002", row=0, col=1))
        preset.add_slot(LineupSlot(hero_id="hero_003", row=0, col=2))

        assert preset.hero_ids == ["hero_001", "hero_002", "hero_003"]

    def test_get_heroes_at_positions(self):
        """测试获取位置映射"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0))
        preset.add_slot(LineupSlot(hero_id="hero_002", row=1, col=2))

        positions = preset.get_heroes_at_positions()

        assert positions[(0, 0)] == "hero_001"
        assert positions[(1, 2)] == "hero_002"

    def test_is_valid(self):
        """测试阵容有效性验证"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )

        # 有效阵容
        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0))
        preset.add_slot(LineupSlot(hero_id="hero_002", row=1, col=1))
        assert preset.is_valid() is True

        # 位置超出范围
        invalid_preset = LineupPreset(
            preset_id="preset_002",
            player_id="player_001",
            name="无效阵容",
        )
        invalid_preset.add_slot(LineupSlot(hero_id="hero_001", row=10, col=0))
        assert invalid_preset.is_valid() is False

    def test_preset_to_dict(self):
        """测试预设转换为字典"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="战士流",
            description="前排坦克",
        )
        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0))

        data = preset.to_dict()

        assert data["preset_id"] == "preset_001"
        assert data["player_id"] == "player_001"
        assert data["name"] == "战士流"
        assert data["description"] == "前排坦克"
        assert len(data["slots"]) == 1

    def test_preset_from_dict(self):
        """测试从字典创建预设"""
        data = {
            "preset_id": "preset_002",
            "player_id": "player_002",
            "name": "法师流",
            "description": "法术爆发",
            "slots": [
                {
                    "hero_id": "hero_001",
                    "row": 0,
                    "col": 0,
                    "star_level": 2,
                    "equipment": [],
                }
            ],
            "target_synergies": [
                {
                    "synergy_id": "mage",
                    "target_count": 6,
                    "priority": 5,
                    "note": "",
                }
            ],
            "notes": "注意站位",
            "version": 2,
        }

        preset = LineupPreset.from_dict(data)

        assert preset.preset_id == "preset_002"
        assert preset.player_id == "player_002"
        assert preset.name == "法师流"
        assert len(preset.slots) == 1
        assert len(preset.target_synergies) == 1
        assert preset.notes == "注意站位"
        assert preset.version == 2


# ============================================================================
# 管理器测试
# ============================================================================


class TestLineupManager:
    """阵容预设管理器测试"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        session = AsyncMock()
        session.flush = AsyncMock()
        session.scalar = AsyncMock()
        session.scalars = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def manager(self, mock_session):
        """创建管理器实例"""
        return LineupManager(mock_session)

    def test_generate_preset_id(self, manager):
        """测试生成预设ID"""
        preset_id = manager._generate_preset_id()

        assert preset_id.startswith("preset_")
        assert len(preset_id) > 7

    def test_apply_preset_to_board(self, manager):
        """测试应用预设到棋盘"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="战士流",
        )
        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0, star_level=2))
        preset.add_slot(LineupSlot(hero_id="hero_002", row=0, col=1, star_level=1))
        preset.add_target_synergy(TargetSynergy(synergy_id="warrior", target_count=6))

        result = manager.apply_preset_to_board(preset)

        assert result["preset_id"] == "preset_001"
        assert result["preset_name"] == "战士流"
        assert len(result["slots"]) == 2
        assert len(result["target_synergies"]) == 1

    def test_apply_preset_with_current_board(self, manager):
        """测试应用预设（带当前棋盘）"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试阵容",
        )
        preset.add_slot(LineupSlot(hero_id="hero_001", row=0, col=0))
        preset.add_slot(LineupSlot(hero_id="hero_002", row=0, col=1))

        current_board = {"slots": [{"hero_id": "hero_001"}]}

        result = manager.apply_preset_to_board(preset, current_board)

        assert "hero_002" in result["heroes_to_buy"]
        assert "hero_001" not in result["heroes_to_buy"]


# ============================================================================
# 常量测试
# ============================================================================


class TestConstants:
    """常量测试"""

    def test_max_presets(self):
        """测试最大预设数量"""
        assert MAX_PRESETS_PER_PLAYER == 5

    def test_max_heroes(self):
        """测试最大英雄数量"""
        assert MAX_HEROES_PER_PRESET == 9

    def test_max_equipment(self):
        """测试最大装备数量"""
        assert MAX_EQUIPMENT_PER_HERO == 3


# ============================================================================
# WebSocket 消息测试
# ============================================================================


class TestLineupMessages:
    """阵容预设消息测试"""

    def test_lineup_slot_data(self):
        """测试阵容槽位数据模型"""
        from src.shared.protocol import LineupSlotData

        slot = LineupSlotData(
            hero_id="hero_001",
            row=3,
            col=2,
            equipment=["sword_001", "armor_001"],
            star_level=2,
        )

        assert slot.hero_id == "hero_001"
        assert slot.row == 3
        assert slot.col == 2
        assert slot.equipment == ["sword_001", "armor_001"]
        assert slot.star_level == 2

    def test_lineup_synergy_data(self):
        """测试目标羁绊数据模型"""
        from src.shared.protocol import LineupSynergyData

        synergy = LineupSynergyData(
            synergy_id="warrior",
            target_count=6,
            priority=5,
        )

        assert synergy.synergy_id == "warrior"
        assert synergy.target_count == 6
        assert synergy.priority == 5

    def test_lineup_preset_data(self):
        """测试预设数据模型"""
        from src.shared.protocol import LineupPresetData, LineupSlotData

        preset = LineupPresetData(
            preset_id="preset_001",
            name="战士流",
            description="前排坦克",
            slots=[
                LineupSlotData(hero_id="hero_001", row=0, col=0),
            ],
        )

        assert preset.preset_id == "preset_001"
        assert preset.name == "战士流"
        assert len(preset.slots) == 1

    def test_lineup_save_message(self):
        """测试保存预设消息"""
        from src.shared.protocol import LineupSaveMessage, LineupSlotData

        msg = LineupSaveMessage(
            name="新阵容",
            description="测试阵容",
            slots=[
                LineupSlotData(hero_id="hero_001", row=0, col=0),
            ],
        )

        assert msg.type == "lineup_save"
        assert msg.name == "新阵容"
        assert len(msg.slots) == 1

    def test_lineup_saved_message(self):
        """测试保存成功消息"""
        from src.shared.protocol import LineupPresetData, LineupSavedMessage

        msg = LineupSavedMessage(
            preset=LineupPresetData(
                preset_id="preset_001",
                name="新阵容",
            )
        )

        assert msg.type == "lineup_saved"
        assert msg.preset.preset_id == "preset_001"

    def test_lineup_list_result_message(self):
        """测试预设列表结果消息"""
        from src.shared.protocol import (
            LineupListResultMessage,
            LineupPresetData,
        )

        msg = LineupListResultMessage(
            presets=[
                LineupPresetData(preset_id="preset_001", name="阵容1"),
                LineupPresetData(preset_id="preset_002", name="阵容2"),
            ],
            max_presets=5,
        )

        assert msg.type == "lineup_list_result"
        assert len(msg.presets) == 2
        assert msg.max_presets == 5


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
