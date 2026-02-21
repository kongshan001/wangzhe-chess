"""
王者之奕 - 天赋系统测试
"""

import pytest
from server.game.talent import Talent, TalentManager, PlayerTalents, TalentEffectApplier


class TestTalent:
    """天赋类测试"""
    
    def test_create_talent(self):
        """测试天赋创建"""
        talent = Talent(
            talent_id="talent_eco_1",
            name="财富积累",
            category="economy",
            tier=1,
            max_points=1,
            required_points=0,
            effect_description="利息上限+1"
        )
        assert talent.talent_id == "talent_eco_1"
        assert talent.tier == 1
    
    def test_is_unlocked_no_requirements(self):
        """测试无要求天赋解锁"""
        talent = Talent(
            talent_id="test_1",
            name="测试",
            category="economy",
            tier=1,
            max_points=1,
            required_points=0,
            effect_description="测试"
        )
        assert talent.is_unlocked([], 0) is True
    
    def test_is_unlocked_with_requirements(self):
        """测试有要求天赋解锁"""
        talent = Talent(
            talent_id="test_2",
            name="测试2",
            category="economy",
            tier=2,
            max_points=1,
            required_points=3,
            required_talents=["test_1"],
            effect_description="测试2"
        )
        # 有前置天赋，点数足够
        assert talent.is_unlocked(["test_1"], 3) is True
        # 没有前置天赋
        assert talent.is_unlocked([], 3) is False
        # 点数不足
        assert talent.is_unlocked(["test_1"], 2) is False


class TestPlayerTalents:
    """玩家天赋测试"""
    
    def test_create_player_talents(self):
        """测试创建玩家天赋"""
        pt = PlayerTalents(player_id="player_1", talent_points=10)
        assert pt.player_id == "player_1"
        assert pt.talent_points == 10
        assert len(pt.unlocked_talents) == 0
    
    def test_add_points(self):
        """测试增加天赋点"""
        pt = PlayerTalents(player_id="player_1", talent_points=0)
        added = pt.add_points(5)
        assert added == 5
        assert pt.talent_points == 5
        assert pt.total_points_earned == 5
    
    def test_unlock_talent_success(self):
        """测试成功解锁天赋"""
        pt = PlayerTalents(player_id="player_1", talent_points=5)
        talent = Talent(
            talent_id="test_talent",
            name="测试",
            category="economy",
            tier=1,
            max_points=1,
            required_points=3,
            effect_description="测试"
        )
        success = pt.unlock(talent)
        assert success is True
        assert "test_talent" in pt.unlocked_talents
        # 注意：required_points 是解锁门槛，不是消耗的点数
        # 点数不会被扣除，只是需要达到门槛才能解锁
    
    def test_unlock_talent_not_enough_points(self):
        """测试点数不足"""
        pt = PlayerTalents(player_id="player_1", talent_points=2)
        talent = Talent(
            talent_id="test_talent",
            name="测试",
            category="economy",
            tier=1,
            max_points=1,
            required_points=3,
            effect_description="测试"
        )
        success = pt.unlock(talent)
        assert success is False
        assert "test_talent" not in pt.unlocked_talents
        assert pt.talent_points == 2  # 未扣点数


class TestTalentEffectApplier:
    """天赋效果应用测试"""
    
    def test_apply_economy_talent(self):
        """测试应用经济天赋"""
        # 需要实际的 Player 对象
        effect = {"interest_cap_bonus": 1}
        # player = Player(...)
        # TalentEffectApplier._apply_economy_talent(effect, player)
        # 验证效果应用
        pass
    
    def test_apply_battle_talent(self):
        """测试应用战斗天赋"""
        effect = {"hp_bonus_percent": 0.05, "attack_bonus_percent": 0.05}
        # player = Player(...)
        # TalentEffectApplier._apply_battle_talent(effect, player)
        # 验证所有英雄属性增加
        pass


class TestTalentManager:
    """天赋管理器测试"""
    
    def test_create_manager(self):
        """测试创建管理器"""
        manager = TalentManager()
        assert len(manager.talents) == 0
        assert len(manager.player_talents) == 0
    
    def test_load_from_dict(self):
        """测试从字典加载"""
        data = {
            "talent_tree": {
                "economy": [
                    {
                        "talent_id": "talent_eco_1",
                        "name": "财富积累",
                        "tier": 1,
                        "required_points": 0,
                        "effect_description": "利息上限+1"
                    }
                ]
            }
        }
        manager = TalentManager()
        manager.load_from_dict(data)
        assert "talent_eco_1" in manager.talents
    
    def test_unlock_talent_through_manager(self):
        """测试通过管理器解锁"""
        manager = TalentManager()
        # 加载配置...
        # pt = manager.create_player_talents("player_1", initial_points=10)
        # success = manager.unlock_talent("player_1", "talent_eco_1")
        # assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
