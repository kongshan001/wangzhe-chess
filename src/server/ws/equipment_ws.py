"""
王者之奕 - 装备系统 WebSocket 处理器

处理装备相关的 WebSocket 消息，包括：
- 装备穿戴
- 装备卸下
- 装备合成
- 获取装备背包
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ..game.equipment import (
    CraftResult,
    EquipmentErrorCode,
    EquipResult,
    UnequipResult,
    create_equipment_service,
)
from ...shared.protocol.messages import (
    BaseMessage,
    CraftEquipmentMessage,
    EquipItemMessage,
    EquipmentBagDataMessage,
    EquipmentCraftedMessage,
    EquipmentInstanceData,
    ErrorMessage,
    GetEquipmentBagMessage,
    HeroData,
    ItemEquippedMessage,
    ItemUnequippedMessage,
    MessageType,
    UnequipItemMessage,
)

if TYPE_CHECKING:
    from server.ws.handler import Session


class EquipmentWSHandler:
    """
    装备系统 WebSocket 处理器

    处理装备相关的所有 WebSocket 消息。
    """

    def __init__(self) -> None:
        """初始化装备 WebSocket 处理器"""
        self.equipment_service = create_equipment_service()

    async def handle_equip_item(
        self,
        session: Session,
        message: EquipItemMessage,
        player_data: dict[str, Any],
    ) -> BaseMessage | None:
        """
        处理装备穿戴请求

        Args:
            session: WebSocket 会话
            message: 穿戴装备消息
            player_data: 玩家数据

        Returns:
            响应消息
        """
        # 获取玩家数据
        equipment_bag = player_data.get("equipment_bag", [])
        heroes = self._get_all_heroes(player_data)

        # 执行穿戴操作
        result: EquipResult = self.equipment_service.equip_item(
            player_equipment_bag=equipment_bag,
            heroes=heroes,
            equipment_instance_id=message.equipment_instance_id,
            hero_instance_id=message.hero_instance_id,
        )

        if not result.success:
            return self._create_error_message(
                result.error_code,
                result.error_message,
                message.seq,
            )

        # 构建响应
        hero_data = self._hero_to_data(result.hero) if result.hero else None
        if hero_data is None:
            return self._create_error_message(
                EquipmentErrorCode.HERO_NOT_FOUND,
                "英雄数据无效",
                message.seq,
            )

        return ItemEquippedMessage(
            type=MessageType.ITEM_EQUIPPED,
            seq=message.seq,
            timestamp=int(time.time() * 1000),
            equipment_instance_id=message.equipment_instance_id,
            hero_instance_id=message.hero_instance_id,
            hero=hero_data,
        )

    async def handle_unequip_item(
        self,
        session: Session,
        message: UnequipItemMessage,
        player_data: dict[str, Any],
    ) -> BaseMessage | None:
        """
        处理装备卸下请求

        Args:
            session: WebSocket 会话
            message: 卸下装备消息
            player_data: 玩家数据

        Returns:
            响应消息
        """
        # 获取玩家数据
        equipment_bag = player_data.get("equipment_bag", [])
        heroes = self._get_all_heroes(player_data)

        # 执行卸下操作
        result: UnequipResult = self.equipment_service.unequip_item(
            player_equipment_bag=equipment_bag,
            heroes=heroes,
            equipment_instance_id=message.equipment_instance_id,
        )

        if not result.success:
            return self._create_error_message(
                result.error_code,
                result.error_message,
                message.seq,
            )

        # 构建响应
        hero_data = self._hero_to_data(result.hero) if result.hero else None
        if hero_data is None:
            return self._create_error_message(
                EquipmentErrorCode.HERO_NOT_FOUND,
                "英雄数据无效",
                message.seq,
            )

        equipment_data = None
        if result.equipment_instance:
            equipment_data = EquipmentInstanceData(
                instance_id=result.equipment_instance.instance_id,
                equipment_id=result.equipment_instance.equipment_id,
                equipped_to=result.equipment_instance.equipped_to,
                acquired_at=result.equipment_instance.acquired_at,
            )

        return ItemUnequippedMessage(
            type=MessageType.ITEM_UNEQUIPPED,
            seq=message.seq,
            timestamp=int(time.time() * 1000),
            equipment_instance_id=message.equipment_instance_id,
            hero_instance_id=result.hero.instance_id if result.hero else "",
            hero=hero_data,
            equipment=equipment_data
            or EquipmentInstanceData(
                instance_id="",
                equipment_id="",
            ),
        )

    async def handle_craft_equipment(
        self,
        session: Session,
        message: CraftEquipmentMessage,
        player_data: dict[str, Any],
    ) -> BaseMessage | None:
        """
        处理装备合成请求

        Args:
            session: WebSocket 会话
            message: 合成装备消息
            player_data: 玩家数据

        Returns:
            响应消息
        """
        # 获取玩家数据
        equipment_bag = player_data.get("equipment_bag", [])

        # 执行合成操作
        result: CraftResult = self.equipment_service.craft_equipment(
            player_equipment_bag=equipment_bag,
            equipment_instance_ids=message.equipment_instance_ids,
        )

        if not result.success:
            return self._create_error_message(
                result.error_code,
                result.error_message,
                message.seq,
            )

        # 构建响应
        new_equipment_data = None
        if result.new_equipment:
            new_equipment_data = EquipmentInstanceData(
                instance_id=result.new_equipment.instance_id,
                equipment_id=result.new_equipment.equipment_id,
                equipped_to=result.new_equipment.equipped_to,
                acquired_at=result.new_equipment.acquired_at,
            )

        return EquipmentCraftedMessage(
            type=MessageType.EQUIPMENT_CRAFTED,
            seq=message.seq,
            timestamp=int(time.time() * 1000),
            consumed_ids=result.consumed_ids,
            new_equipment=new_equipment_data
            or EquipmentInstanceData(
                instance_id="",
                equipment_id="",
            ),
        )

    async def handle_get_equipment_bag(
        self,
        session: Session,
        message: GetEquipmentBagMessage,
        player_data: dict[str, Any],
    ) -> BaseMessage | None:
        """
        处理获取装备背包请求

        Args:
            session: WebSocket 会话
            message: 获取装备背包消息
            player_data: 玩家数据

        Returns:
            响应消息
        """
        # 获取装备背包
        equipment_bag = player_data.get("equipment_bag", [])

        # 转换为响应格式
        equipment_list = []
        for eq_data in equipment_bag:
            equipment_list.append(
                EquipmentInstanceData(
                    instance_id=eq_data.get("instance_id", ""),
                    equipment_id=eq_data.get("equipment_id", ""),
                    equipped_to=eq_data.get("equipped_to"),
                    acquired_at=eq_data.get("acquired_at", 0),
                )
            )

        return EquipmentBagDataMessage(
            type=MessageType.EQUIPMENT_BAG_DATA,
            seq=message.seq,
            timestamp=int(time.time() * 1000),
            equipment=equipment_list,
        )

    def _get_all_heroes(self, player_data: dict[str, Any]) -> list:
        """
        获取玩家所有英雄（场上 + 备战席）

        Args:
            player_data: 玩家数据

        Returns:
            英雄列表
        """
        from shared.models import Hero

        heroes = []

        # 从棋盘获取英雄
        board_data = player_data.get("board", {})
        board_heroes = board_data.get("heroes", {})
        for hero_data in board_heroes.values():
            try:
                heroes.append(Hero.from_dict(hero_data))
            except Exception:
                pass

        # 从备战席获取英雄
        bench_data = player_data.get("bench", [])
        for hero_data in bench_data:
            try:
                heroes.append(Hero.from_dict(hero_data))
            except Exception:
                pass

        return heroes

    def _hero_to_data(self, hero) -> HeroData | None:
        """
        将 Hero 对象转换为 HeroData

        Args:
            hero: 英雄对象

        Returns:
            HeroData 或 None
        """
        if hero is None:
            return None

        from shared.protocol.messages import PositionData

        position_data = None
        if hero.position:
            position_data = PositionData(x=hero.position.x, y=hero.position.y)

        return HeroData(
            instance_id=hero.instance_id,
            template_id=hero.template_id,
            name=hero.name,
            cost=hero.cost,
            star=hero.star,
            race=hero.race,
            profession=hero.profession,
            max_hp=hero.max_hp,
            hp=hero.hp,
            attack=hero.attack,
            defense=hero.defense,
            attack_speed=hero.attack_speed,
            mana=hero.mana,
            position=position_data,
        )

    def _create_error_message(
        self,
        error_code: int,
        error_message: str,
        seq: int | None = None,
    ) -> ErrorMessage:
        """
        创建错误消息

        Args:
            error_code: 错误码
            error_message: 错误描述
            seq: 消息序列号

        Returns:
            ErrorMessage
        """
        return ErrorMessage(
            type=MessageType.ERROR,
            seq=seq,
            timestamp=int(time.time() * 1000),
            code=error_code,
            message=error_message,
        )


# 消息处理器注册表
EQUIPMENT_HANDLERS = {
    MessageType.EQUIP_ITEM: "handle_equip_item",
    MessageType.UNEQUIP_ITEM: "handle_unequip_item",
    MessageType.CRAFT_EQUIPMENT: "handle_craft_equipment",
    MessageType.GET_EQUIPMENT_BAG: "handle_get_equipment_bag",
}
