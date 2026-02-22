"""
王者之奕 - 新手引导管理器

本模块提供新手引导系统的管理功能：
- TutorialManager: 引导管理器类
- 加载引导配置
- 管理引导进度
- 发放引导奖励
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    PlayerTutorialProgress,
    Tutorial,
    TutorialReward,
    TutorialType,
)

logger = logging.getLogger(__name__)


class TutorialManager:
    """
    新手引导管理器
    
    负责管理所有引导相关的操作：
    - 引导配置加载
    - 引导进度管理
    - 引导奖励发放
    - 引导统计查询
    
    Attributes:
        tutorials: 所有引导配置 (tutorial_id -> Tutorial)
        player_progress: 玩家引导进度 (player_id + tutorial_id -> PlayerTutorialProgress)
        config_path: 配置文件路径
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化引导管理器
        
        Args:
            config_path: 引导配置文件路径
        """
        self.tutorials: Dict[str, Tutorial] = {}
        self.player_progress: Dict[str, PlayerTutorialProgress] = {}  # key: f"{player_id}_{tutorial_id}"
        self.config_path = config_path
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
        else:
            self._init_default_tutorials()
        
        logger.info(f"TutorialManager initialized with {len(self.tutorials)} tutorials")
    
    def _init_default_tutorials(self) -> None:
        """初始化默认引导配置"""
        # 默认引导会在 load_config 时从 JSON 加载
        # 这里只创建一个最基础的结构
        pass
    
    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载引导
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Tutorial config file not found: {config_path}")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tutorials_data = data.get("tutorials", [])
            for tutorial_data in tutorials_data:
                tutorial = Tutorial.from_dict(tutorial_data)
                self.tutorials[tutorial.tutorial_id] = tutorial
            
            logger.info(f"Loaded {len(self.tutorials)} tutorials from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load tutorial config: {e}")
            raise
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存引导配置到文件
        
        Args:
            config_path: 配置文件路径（默认使用初始化时的路径）
        """
        path = Path(config_path or self.config_path)
        if not path:
            logger.warning("No config path specified for saving")
            return
        
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "tutorials": [t.to_dict() for t in self.tutorials.values()],
            }
            
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(self.tutorials)} tutorials to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save tutorial config: {e}")
    
    # ========== 引导查询 ==========
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """
        获取指定引导
        
        Args:
            tutorial_id: 引导ID
            
        Returns:
            引导对象，不存在返回None
        """
        return self.tutorials.get(tutorial_id)
    
    def get_all_tutorials(self) -> List[Tutorial]:
        """
        获取所有引导列表
        
        Returns:
            引导列表
        """
        return list(self.tutorials.values())
    
    def get_tutorials_by_type(self, tutorial_type: TutorialType) -> List[Tutorial]:
        """
        获取指定类型的引导
        
        Args:
            tutorial_type: 引导类型
            
        Returns:
            该类型的引导列表
        """
        return [t for t in self.tutorials.values() if t.tutorial_type == tutorial_type]
    
    def get_tutorials_for_player(
        self,
        player_id: str,
        include_completed: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        获取玩家的引导列表
        
        Args:
            player_id: 玩家ID
            include_completed: 是否包含已完成的
            
        Returns:
            引导列表（包含进度信息）
        """
        result = []
        
        for tutorial in sorted(
            self.tutorials.values(),
            key=lambda t: (t.sort_order, t.recommended_level)
        ):
            if not tutorial.enabled:
                continue
            
            progress = self.get_player_progress(player_id, tutorial.tutorial_id)
            
            # 筛选已完成
            if not include_completed and progress and progress.completed:
                continue
            
            # 检查前置条件
            unlocked = self._check_prerequisites(player_id, tutorial)
            
            tutorial_data = tutorial.to_dict()
            tutorial_data["unlocked"] = unlocked
            tutorial_data["progress"] = progress.to_dict() if progress else None
            tutorial_data["progress_percent"] = (
                len(progress.completed_steps) / tutorial.total_steps * 100
                if progress and tutorial.total_steps > 0
                else 0
            )
            
            result.append(tutorial_data)
        
        return result
    
    # ========== 进度管理 ==========
    
    def get_player_progress(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[PlayerTutorialProgress]:
        """
        获取玩家引导进度
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            玩家引导进度，不存在返回None
        """
        key = f"{player_id}_{tutorial_id}"
        return self.player_progress.get(key)
    
    def get_or_create_progress(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> PlayerTutorialProgress:
        """
        获取或创建玩家引导进度
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            玩家引导进度
        """
        key = f"{player_id}_{tutorial_id}"
        if key not in self.player_progress:
            self.player_progress[key] = PlayerTutorialProgress(
                player_id=player_id,
                tutorial_id=tutorial_id,
            )
        return self.player_progress[key]
    
    def _check_prerequisites(
        self,
        player_id: str,
        tutorial: Tutorial,
    ) -> bool:
        """
        检查前置条件
        
        Args:
            player_id: 玩家ID
            tutorial: 引导对象
            
        Returns:
            是否满足前置条件
        """
        if not tutorial.prerequisites:
            return True
        
        for prereq_id in tutorial.prerequisites:
            progress = self.get_player_progress(player_id, prereq_id)
            if not progress or not (progress.completed or progress.skipped):
                return False
        
        return True
    
    # ========== 引导操作 ==========
    
    def start_tutorial(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        开始引导
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            引导信息（包含步骤），无法开始返回None
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            logger.warning(f"Tutorial not found: {tutorial_id}")
            return None
        
        if not tutorial.enabled:
            logger.warning(f"Tutorial is disabled: {tutorial_id}")
            return None
        
        # 检查前置条件
        if not self._check_prerequisites(player_id, tutorial):
            logger.warning(f"Prerequisites not met for tutorial: {tutorial_id}")
            return None
        
        # 获取或创建进度
        progress = self.get_or_create_progress(player_id, tutorial_id)
        
        # 如果已完成、已跳过或已经开始，不允许重新开始
        if progress.completed or progress.skipped:
            logger.warning(f"Tutorial already completed or skipped: {tutorial_id}")
            return None
        
        # 如果已经开始但未完成，返回当前进度
        if progress.started_at:
            logger.info(f"Tutorial already started: {tutorial_id}")
            current_step = tutorial.get_step_by_order(progress.current_step)
            return {
                "tutorial": tutorial.to_dict(),
                "progress": progress.to_dict(),
                "current_step": current_step.to_dict() if current_step else None,
            }
        
        # 开始引导
        progress.start()
        
        # 获取第一步
        first_step = tutorial.get_step_by_order(1)
        if first_step:
            progress.current_step_id = first_step.step_id
        
        logger.info(f"Player {player_id} started tutorial: {tutorial.name}")
        
        return {
            "tutorial": tutorial.to_dict(),
            "progress": progress.to_dict(),
            "current_step": first_step.to_dict() if first_step else None,
        }
    
    def get_current_step(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取当前步骤
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            当前步骤信息
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            return None
        
        progress = self.get_player_progress(player_id, tutorial_id)
        if not progress:
            return None
        
        if progress.completed or progress.skipped:
            return None
        
        current_step = tutorial.get_step_by_order(progress.current_step)
        
        return {
            "tutorial": tutorial.to_dict(),
            "progress": progress.to_dict(),
            "current_step": current_step.to_dict() if current_step else None,
        }
    
    def update_progress(
        self,
        player_id: str,
        tutorial_id: str,
        step_id: str,
        action_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        更新引导进度
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            step_id: 完成的步骤ID
            action_data: 动作数据（用于验证）
            
        Returns:
            更新后的进度信息
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            logger.warning(f"Tutorial not found: {tutorial_id}")
            return None
        
        progress = self.get_player_progress(player_id, tutorial_id)
        if not progress:
            logger.warning(f"Progress not found for tutorial: {tutorial_id}")
            return None
        
        if progress.completed or progress.skipped:
            logger.warning(f"Tutorial already completed or skipped: {tutorial_id}")
            return None
        
        # 验证步骤
        step = tutorial.get_step(step_id)
        if not step:
            logger.warning(f"Step not found: {step_id}")
            return None
        
        # 推进步骤
        if not progress.advance_step(step_id):
            return None
        
        logger.info(
            f"Player {player_id} completed step {step.order}/{tutorial.total_steps} "
            f"in tutorial: {tutorial.name}"
        )
        
        # 检查是否完成
        if progress.current_step > tutorial.total_steps:
            progress.complete()
            logger.info(
                f"Player {player_id} completed tutorial: {tutorial.name}"
            )
        
        # 更新当前步骤ID
        current_step = tutorial.get_step_by_order(progress.current_step)
        if current_step:
            progress.current_step_id = current_step.step_id
        
        return {
            "tutorial": tutorial.to_dict(),
            "progress": progress.to_dict(),
            "current_step": current_step.to_dict() if current_step else None,
            "just_completed": progress.completed,
        }
    
    def complete_tutorial(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        完成引导
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            完成信息，无法完成返回None
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            return None
        
        progress = self.get_player_progress(player_id, tutorial_id)
        if not progress:
            return None
        
        if progress.completed:
            return {
                "tutorial": tutorial.to_dict(),
                "progress": progress.to_dict(),
                "reward": None,  # 已经领取过了
            }
        
        # 完成引导
        progress.complete()
        
        logger.info(
            f"Player {player_id} manually completed tutorial: {tutorial.name}"
        )
        
        return {
            "tutorial": tutorial.to_dict(),
            "progress": progress.to_dict(),
            "reward": tutorial.completion_reward.to_dict(),
        }
    
    def skip_tutorial(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        跳过引导
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            跳过信息，无法跳过返回None
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            return None
        
        # 必须完成的引导不能跳过
        if tutorial.required:
            logger.warning(f"Cannot skip required tutorial: {tutorial_id}")
            return None
        
        progress = self.get_or_create_progress(player_id, tutorial_id)
        
        if progress.completed or progress.skipped:
            logger.warning(f"Tutorial already completed or skipped: {tutorial_id}")
            return None
        
        # 跳过引导
        progress.skip()
        
        logger.info(
            f"Player {player_id} skipped tutorial: {tutorial.name}"
        )
        
        return {
            "tutorial": tutorial.to_dict(),
            "progress": progress.to_dict(),
            "reward": None,  # 跳过没有奖励
        }
    
    # ========== 奖励管理 ==========
    
    def claim_reward(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> Optional[TutorialReward]:
        """
        领取引导奖励
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            奖励内容，无法领取返回None
        """
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            return None
        
        progress = self.get_player_progress(player_id, tutorial_id)
        if not progress:
            return None
        
        # 跳过的引导没有奖励
        if progress.skipped:
            logger.warning(f"Skipped tutorials have no rewards: {tutorial_id}")
            return None
        
        if not progress.is_claimable:
            logger.warning(f"Reward not claimable for tutorial: {tutorial_id}")
            return None
        
        # 领取奖励
        progress.claim()
        
        logger.info(
            f"Player {player_id} claimed reward for tutorial: {tutorial.name}"
        )
        
        return tutorial.completion_reward
    
    # ========== 统计查询 ==========
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """
        获取玩家引导统计
        
        Args:
            player_id: 玩家ID
            
        Returns:
            统计数据字典
        """
        total = len([t for t in self.tutorials.values() if t.enabled])
        completed = 0
        skipped = 0
        in_progress = 0
        by_type: Dict[str, Dict[str, int]] = {}
        
        for tutorial in self.tutorials.values():
            if not tutorial.enabled:
                continue
            
            type_key = tutorial.tutorial_type.value
            if type_key not in by_type:
                by_type[type_key] = {
                    "total": 0,
                    "completed": 0,
                    "skipped": 0,
                }
            
            by_type[type_key]["total"] += 1
            
            progress = self.get_player_progress(player_id, tutorial.tutorial_id)
            
            if progress:
                if progress.completed:
                    completed += 1
                    by_type[type_key]["completed"] += 1
                elif progress.skipped:
                    skipped += 1
                    by_type[type_key]["skipped"] += 1
                elif progress.started_at:
                    in_progress += 1
        
        return {
            "player_id": player_id,
            "total_tutorials": total,
            "completed_tutorials": completed,
            "skipped_tutorials": skipped,
            "in_progress_tutorials": in_progress,
            "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
            "by_type": by_type,
        }
    
    def get_unclaimed_rewards(
        self,
        player_id: str,
    ) -> List[Dict[str, Any]]:
        """
        获取未领取的奖励列表
        
        Args:
            player_id: 玩家ID
            
        Returns:
            未领取奖励列表
        """
        unclaimed = []
        
        for tutorial in self.tutorials.values():
            if not tutorial.enabled:
                continue
            
            progress = self.get_player_progress(player_id, tutorial.tutorial_id)
            
            if progress and progress.is_claimable:
                unclaimed.append({
                    "tutorial_id": tutorial.tutorial_id,
                    "tutorial_name": tutorial.name,
                    "reward": tutorial.completion_reward.to_dict(),
                })
        
        return unclaimed
    
    def reset_progress(
        self,
        player_id: str,
        tutorial_id: str,
    ) -> bool:
        """
        重置引导进度
        
        Args:
            player_id: 玩家ID
            tutorial_id: 引导ID
            
        Returns:
            是否成功重置
        """
        progress = self.get_player_progress(player_id, tutorial_id)
        if not progress:
            return False
        
        progress.reset()
        
        logger.info(
            f"Player {player_id} reset progress for tutorial: {tutorial_id}"
        )
        
        return True


# 全局单例
_tutorial_manager: Optional[TutorialManager] = None


def get_tutorial_manager(config_path: Optional[str] = None) -> TutorialManager:
    """
    获取引导管理器单例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        引导管理器实例
    """
    global _tutorial_manager
    if _tutorial_manager is None:
        _tutorial_manager = TutorialManager(config_path)
    return _tutorial_manager
