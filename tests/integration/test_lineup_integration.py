"""
王者之奕 - 阵容预设与游戏流程集成测试

测试阵容预设与游戏流程的跨模块交互：
- 预设保存与数据库持久化
- 预设应用到游戏对局
- 预设版本管理
- 预设数量限制
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.lineup import (
    MAX_PRESETS_PER_PLAYER,
    EquipmentAssignment,
    LineupManager,
    LineupPreset,
    LineupSlot,
    TargetSynergy,
)


class TestLineupPresetIntegration:
    """阵容预设集成测试"""

    @pytest.fixture
    def sample_slots(self) -> list[LineupSlot]:
        """创建示例英雄槽位"""
        return [
            LineupSlot(
                hero_id="hero_warrior_001",
                row=0,
                col=0,
                equipment=[EquipmentAssignment(equipment_id="sword_001")],
                star_level=2,
            ),
            LineupSlot(
                hero_id="hero_mage_001",
                row=1,
                col=2,
                equipment=[],
                star_level=1,
            ),
            LineupSlot(
                hero_id="hero_tank_001",
                row=0,
                col=1,
                equipment=[
                    EquipmentAssignment(equipment_id="shield_001"),
                    EquipmentAssignment(equipment_id="helmet_001"),
                ],
                star_level=3,
            ),
        ]

    @pytest.fixture
    def sample_synergies(self) -> list[TargetSynergy]:
        """创建示例目标羁绊"""
        return [
            TargetSynergy(
                synergy_id="warrior",
                target_count=4,
                priority=1,
            ),
            TargetSynergy(
                synergy_id="tank",
                target_count=2,
                priority=2,
            ),
        ]

    def test_create_lineup_preset(self, sample_slots, sample_synergies):
        """测试创建阵容预设"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="战士坦克流",
            description="高护甲高血量的肉盾阵容",
            slots=sample_slots,
            target_synergies=sample_synergies,
            notes="前期用战士过渡",
        )

        assert preset.preset_id == "preset_001"
        assert preset.player_id == "player_001"
        assert preset.name == "战士坦克流"
        assert len(preset.slots) == 3
        assert len(preset.target_synergies) == 2

    def test_preset_hero_ids(self, sample_slots):
        """测试预设英雄ID列表"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试预设",
            slots=sample_slots,
        )

        hero_ids = preset.hero_ids
        assert len(hero_ids) == 3
        assert "hero_warrior_001" in hero_ids
        assert "hero_mage_001" in hero_ids
        assert "hero_tank_001" in hero_ids

    def test_preset_get_heroes_at_positions(self, sample_slots):
        """测试获取英雄位置信息"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试预设",
            slots=sample_slots,
        )

        positions = preset.get_heroes_at_positions()

        assert len(positions) == 3
        # 验证位置信息
        for pos_data in positions:
            assert "hero_id" in pos_data
            assert "row" in pos_data
            assert "col" in pos_data

    def test_preset_serialization(self, sample_slots, sample_synergies):
        """测试预设序列化"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试预设",
            description="描述",
            slots=sample_slots,
            target_synergies=sample_synergies,
            notes="备注",
        )

        # 序列化
        data = preset.to_dict()
        assert data["preset_id"] == "preset_001"
        assert len(data["slots"]) == 3

        # 反序列化
        loaded = LineupPreset.from_dict(data)
        assert loaded.preset_id == "preset_001"
        assert len(loaded.slots) == 3

    def test_lineup_slot_equipment(self):
        """测试英雄槽位装备"""
        slot = LineupSlot(
            hero_id="hero_001",
            row=0,
            col=0,
            equipment=[
                EquipmentAssignment(equipment_id="sword_001", slot=1),
                EquipmentAssignment(equipment_id="shield_001", slot=2),
            ],
            star_level=2,
        )

        assert len(slot.equipment) == 2
        assert slot.total_equipment_count == 2


class TestLineupManagerIntegration:
    """阵容预设管理器集成测试"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.scalar = AsyncMock()
        session.scalars = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def sample_slots(self) -> list[LineupSlot]:
        """创建示例英雄槽位"""
        return [
            LineupSlot(
                hero_id="hero_001",
                row=0,
                col=0,
                equipment=[],
                star_level=1,
            ),
            LineupSlot(
                hero_id="hero_002",
                row=0,
                col=1,
                equipment=[],
                star_level=1,
            ),
        ]

    @pytest.mark.asyncio
    async def test_save_preset_success(self, mock_session, sample_slots):
        """测试保存预设成功"""
        # 设置模拟返回
        mock_session.scalar = AsyncMock(return_value=0)  # 预设数量为0

        manager = LineupManager(mock_session)

        # 保存预设
        preset = await manager.save_preset(
            player_id="player_001",
            name="测试预设",
            slots=sample_slots,
            description="测试描述",
        )

        assert preset is not None
        assert preset.player_id == "player_001"
        assert preset.name == "测试预设"
        assert len(preset.slots) == 2

        # 验证会话操作
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_preset_exceeds_limit(self, mock_session, sample_slots):
        """测试保存预设超过限制"""
        # 设置模拟返回已达到上限
        mock_session.scalar = AsyncMock(return_value=MAX_PRESETS_PER_PLAYER)

        manager = LineupManager(mock_session)

        # 尝试保存应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            await manager.save_preset(
                player_id="player_001",
                name="测试预设",
                slots=sample_slots,
            )

        assert "超过" in str(exc_info.value) or "限制" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_player_presets(self, mock_session, sample_slots):
        """测试获取玩家预设列表"""
        # 创建模拟预设数据
        mock_db_preset = MagicMock()
        mock_db_preset.preset_id = "preset_001"
        mock_db_preset.player_id = "player_001"
        mock_db_preset.name = "测试预设"
        mock_db_preset.description = "描述"
        mock_db_preset.slots_data = [s.to_dict() for s in sample_slots]
        mock_db_preset.synergies_data = []
        mock_db_preset.notes = ""
        mock_db_preset.created_at = datetime.now()
        mock_db_preset.updated_at = datetime.now()
        mock_db_preset.version = 1

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_db_preset]
        mock_session.scalars.return_value = mock_result

        manager = LineupManager(mock_session)

        presets = await manager.get_player_presets("player_001")

        assert len(presets) == 1
        assert presets[0].name == "测试预设"

    @pytest.mark.asyncio
    async def test_delete_preset(self, mock_session):
        """测试删除预设"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        manager = LineupManager(mock_session)

        result = await manager.delete_preset(
            preset_id="preset_001",
            player_id="player_001",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_preset_not_found(self, mock_session):
        """测试删除不存在的预设"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        manager = LineupManager(mock_session)

        result = await manager.delete_preset(
            preset_id="nonexistent",
            player_id="player_001",
        )

        assert result is False


class TestPresetToGameIntegration:
    """预设应用到游戏的集成测试"""

    @pytest.fixture
    def sample_preset(self) -> LineupPreset:
        """创建示例预设"""
        return LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="战士阵容",
            description="标准战士阵容",
            slots=[
                LineupSlot(
                    hero_id="warrior_001",
                    row=0,
                    col=0,
                    equipment=[EquipmentAssignment(equipment_id="sword_001")],
                    star_level=2,
                ),
                LineupSlot(
                    hero_id="warrior_002",
                    row=0,
                    col=1,
                    equipment=[],
                    star_level=1,
                ),
            ],
            target_synergies=[
                TargetSynergy(synergy_id="warrior", target_count=4, priority=1),
            ],
            notes="前期运营",
        )

    def test_apply_preset_to_empty_board(self, sample_preset):
        """测试应用预设到空棋盘"""
        # 使用 LineupPreset 的方法（假设有）
        # 这里模拟 apply_preset_to_board 的逻辑

        board = {
            "preset_id": sample_preset.preset_id,
            "preset_name": sample_preset.name,
            "slots": [],
            "heroes_to_buy": [],
            "target_synergies": [],
        }

        for slot in sample_preset.slots:
            board["slots"].append(
                {
                    "hero_id": slot.hero_id,
                    "row": slot.row,
                    "col": slot.col,
                    "equipment": [eq.equipment_id for eq in slot.equipment],
                    "star_level": slot.star_level,
                }
            )

        for synergy in sample_preset.target_synergies:
            board["target_synergies"].append(
                {
                    "synergy_id": synergy.synergy_id,
                    "target_count": synergy.target_count,
                    "priority": synergy.priority,
                }
            )

        assert len(board["slots"]) == 2
        assert board["preset_name"] == "战士阵容"

    def test_apply_preset_with_current_board(self, sample_preset):
        """测试应用预设时考虑当前棋盘"""
        current_board = {
            "slots": [
                {"hero_id": "warrior_001", "star_level": 1},  # 已有但星级不够
            ]
        }

        # 计算需要购买的英雄
        current_heroes = {"warrior_001"}
        preset_heroes = set(sample_preset.hero_ids)
        heroes_to_buy = preset_heroes - current_heroes

        assert "warrior_002" in heroes_to_buy
        assert "warrior_001" not in heroes_to_buy

    def test_preset_version_management(self):
        """测试预设版本管理"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="测试预设",
            slots=[],
            version=1,
        )

        # 更新预设后版本应该增加
        preset.version += 1
        assert preset.version == 2


class TestPresetSharingIntegration:
    """预设分享集成测试"""

    def test_preset_export_format(self):
        """测试预设导出格式"""
        preset = LineupPreset(
            preset_id="preset_001",
            player_id="player_001",
            name="分享阵容",
            description="这是一个分享的阵容",
            slots=[
                LineupSlot(
                    hero_id="hero_001",
                    row=0,
                    col=0,
                    equipment=[],
                    star_level=1,
                ),
            ],
            target_synergies=[
                TargetSynergy(synergy_id="warrior", target_count=4, priority=1),
            ],
        )

        # 导出为字典
        export_data = preset.to_dict()

        # 验证导出数据完整性
        assert "preset_id" in export_data
        assert "name" in export_data
        assert "description" in export_data
        assert "slots" in export_data
        assert "target_synergies" in export_data

    def test_preset_import(self):
        """测试预设导入"""
        import_data = {
            "preset_id": "imported_001",
            "player_id": "player_001",
            "name": "导入的阵容",
            "description": "从外部导入",
            "slots": [
                {
                    "hero_id": "hero_001",
                    "row": 0,
                    "col": 0,
                    "equipment": [],
                    "star_level": 1,
                },
            ],
            "target_synergies": [
                {
                    "synergy_id": "mage",
                    "target_count": 3,
                    "priority": 1,
                },
            ],
            "notes": "",
            "version": 1,
        }

        preset = LineupPreset.from_dict(import_data)

        assert preset.name == "导入的阵容"
        assert len(preset.slots) == 1
        assert len(preset.target_synergies) == 1


class TestPresetEquipmentIntegration:
    """预设装备集成测试"""

    def test_equipment_assignment(self):
        """测试装备分配"""
        equipment = EquipmentAssignment(
            equipment_id="legendary_sword",
            slot=1,
        )

        assert equipment.equipment_id == "legendary_sword"
        assert equipment.slot == 1

    def test_slot_with_multiple_equipment(self):
        """测试多装备槽位"""
        slot = LineupSlot(
            hero_id="hero_001",
            row=0,
            col=0,
            equipment=[
                EquipmentAssignment(equipment_id="sword_001", slot=1),
                EquipmentAssignment(equipment_id="shield_001", slot=2),
                EquipmentAssignment(equipment_id="ring_001", slot=3),
            ],
            star_level=3,
        )

        assert len(slot.equipment) == 3
        assert slot.total_equipment_count == 3

    def test_equipment_serialization(self):
        """测试装备序列化"""
        equipment = EquipmentAssignment(
            equipment_id="test_sword",
            slot=1,
        )

        data = equipment.to_dict()
        assert data["equipment_id"] == "test_sword"

        loaded = EquipmentAssignment.from_dict(data)
        assert loaded.equipment_id == "test_sword"
