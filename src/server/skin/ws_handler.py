"""
王者之奕 - 皮肤系统 WebSocket 处理器

本模块实现皮肤系统的 WebSocket 消息处理：
- 获取皮肤列表
- 装备/卸下皮肤
- 购买皮肤
- 解锁皮肤
- 收藏皮肤
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.shared.protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
)
from src.shared.protocol.messages import (
    BuySkinMessage,
    EquipSkinMessage,
    GetHeroSkinsMessage,
    GetOwnedSkinsMessage,
    GetSkinsMessage,
    HeroSkinsListMessage,
    OwnedSkinsListMessage,
    SetFavoriteSkinMessage,
    SkinBoughtMessage,
    SkinData,
    SkinEquippedMessage,
    SkinFavoriteSetMessage,
    SkinUnlockedMessage,
    SkinUnequippedMessage,
    SkinsListMessage,
    UnequipSkinMessage,
    PlayerSkinData,
)
from .manager import SkinManager, get_skin_manager
from .models import Skin, SkinRarity

if TYPE_CHECKING:
    from src.server.ws.handler import Session

import structlog

logger = structlog.get_logger()


class SkinWSHandler:
    """
    皮肤系统 WebSocket 处理器
    
    处理所有皮肤相关的 WebSocket 消息。
    
    Attributes:
        skin_manager: 皮肤管理器
        player_currencies: 玩家货币缓存（实际应从数据库获取）
    """
    
    def __init__(self, skin_manager: Optional[SkinManager] = None):
        """
        初始化皮肤 WebSocket 处理器
        
        Args:
            skin_manager: 皮肤管理器（可选，默认使用全局单例）
        """
        self.skin_manager = skin_manager or get_skin_manager()
        # 玩家货币缓存（临时实现，实际应从数据库或玩家管理器获取）
        self.player_currencies: Dict[str, Dict[str, int]] = {}
    
    def set_player_currency(self, player_id: str, gold: int, diamond: int) -> None:
        """
        设置玩家货币（用于测试或初始化）
        
        Args:
            player_id: 玩家ID
            gold: 金币数量
            diamond: 钻石数量
        """
        self.player_currencies[player_id] = {"gold": gold, "diamond": diamond}
    
    def get_player_currency(self, player_id: str) -> tuple[int, int]:
        """
        获取玩家货币
        
        Args:
            player_id: 玩家ID
            
        Returns:
            (金币, 钻石)
        """
        currency = self.player_currencies.get(player_id, {"gold": 0, "diamond": 0})
        return currency.get("gold", 0), currency.get("diamond", 0)
    
    def update_player_currency(self, player_id: str, currency_type: str, amount: int) -> None:
        """
        更新玩家货币
        
        Args:
            player_id: 玩家ID
            currency_type: 货币类型
            amount: 新数量
        """
        if player_id not in self.player_currencies:
            self.player_currencies[player_id] = {"gold": 0, "diamond": 0}
        self.player_currencies[player_id][currency_type] = amount
    
    async def handle_get_skins(
        self,
        session: Session,
        message: GetSkinsMessage,
    ) -> SkinsListMessage:
        """
        处理获取皮肤列表请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            皮肤列表响应
        """
        player_id = session.player_id
        
        # 获取所有皮肤
        all_skins = self.skin_manager.get_all_skins()
        
        # 按稀有度筛选
        if message.rarity_filter:
            try:
                rarity = SkinRarity(message.rarity_filter)
                all_skins = [s for s in all_skins if s.rarity == rarity]
            except ValueError:
                pass
        
        # 排序：传说 > 史诗 > 稀有 > 普通
        rarity_order = {
            SkinRarity.LEGENDARY: 0,
            SkinRarity.EPIC: 1,
            SkinRarity.RARE: 2,
            SkinRarity.NORMAL: 3,
        }
        all_skins.sort(key=lambda s: (rarity_order.get(s.rarity, 99), s.name))
        
        # 分页
        total_count = len(all_skins)
        page = message.page
        page_size = message.page_size
        start = (page - 1) * page_size
        end = start + page_size
        page_skins = all_skins[start:end]
        
        # 转换为 SkinData
        skin_data_list = []
        for skin in page_skins:
            is_owned = self.skin_manager.has_skin(player_id, skin.skin_id)
            is_equipped = (
                self.skin_manager.get_equipped_skin(player_id, skin.hero_id) == skin.skin_id
            )
            
            skin_data = self._skin_to_data(skin, is_owned, is_equipped)
            skin_data_list.append(skin_data)
        
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return SkinsListMessage(
            skins=skin_data_list,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            seq=message.seq,
        )
    
    async def handle_get_hero_skins(
        self,
        session: Session,
        message: GetHeroSkinsMessage,
    ) -> HeroSkinsListMessage:
        """
        处理获取英雄皮肤列表请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            英雄皮肤列表响应
        """
        player_id = session.player_id
        hero_id = message.hero_id
        
        # 获取英雄的皮肤
        hero_skins = self.skin_manager.get_skins_by_hero(hero_id)
        
        # 获取当前装备的皮肤
        equipped_skin_id = self.skin_manager.get_equipped_skin(player_id, hero_id)
        
        # 转换为 SkinData
        skin_data_list = []
        for skin in hero_skins:
            is_owned = self.skin_manager.has_skin(player_id, skin.skin_id)
            is_equipped = (skin.skin_id == equipped_skin_id)
            
            skin_data = self._skin_to_data(skin, is_owned, is_equipped)
            skin_data_list.append(skin_data)
        
        # 获取英雄名称（从第一个皮肤或默认皮肤获取）
        hero_name = ""
        if hero_skins:
            hero_name = hero_skins[0].name
        
        return HeroSkinsListMessage(
            hero_id=hero_id,
            hero_name=hero_name,
            skins=skin_data_list,
            equipped_skin_id=equipped_skin_id,
            seq=message.seq,
        )
    
    async def handle_get_owned_skins(
        self,
        session: Session,
        message: GetOwnedSkinsMessage,
    ) -> OwnedSkinsListMessage:
        """
        处理获取已拥有皮肤请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            已拥有皮肤列表响应
        """
        player_id = session.player_id
        hero_id = message.hero_id
        
        # 获取玩家拥有的皮肤
        if hero_id:
            player_skins = self.skin_manager.get_player_skins_by_hero(player_id, hero_id)
        else:
            player_skins = self.skin_manager.get_player_skins(player_id)
        
        # 转换为 PlayerSkinData
        skin_data_list = []
        for ps in player_skins:
            skin = self.skin_manager.get_skin(ps.skin_id)
            if not skin:
                continue
            
            skin_data = PlayerSkinData(
                skin_id=ps.skin_id,
                hero_id=ps.hero_id,
                hero_name=skin.name,
                skin_name=skin.name,
                rarity=skin.rarity.value,
                is_equipped=ps.is_equipped,
                is_favorite=ps.is_equipped,  # 暂时用 is_equipped 替代
                acquired_at=ps.acquired_at.isoformat() if ps.acquired_at else None,
                acquire_type=ps.acquire_type,
            )
            skin_data_list.append(skin_data)
        
        return OwnedSkinsListMessage(
            skins=skin_data_list,
            total_count=len(skin_data_list),
            seq=message.seq,
        )
    
    async def handle_equip_skin(
        self,
        session: Session,
        message: EquipSkinMessage,
    ) -> BaseMessage:
        """
        处理装备皮肤请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            装备成功响应或错误消息
        """
        player_id = session.player_id
        skin_id = message.skin_id
        
        # 装备皮肤
        success, error = self.skin_manager.equip_skin(player_id, skin_id)
        
        if not success:
            return ErrorMessage(
                code=4001,
                message=error or "装备失败",
                seq=message.seq,
            )
        
        # 获取皮肤信息
        skin = self.skin_manager.get_skin(skin_id)
        if not skin:
            return ErrorMessage(
                code=4002,
                message="皮肤不存在",
                seq=message.seq,
            )
        
        # 获取属性加成描述
        stat_bonuses = self.skin_manager.get_stat_bonus_description(skin_id)
        effects = self.skin_manager.get_effect_description(skin_id)
        
        logger.info(
            "Skin equipped",
            player_id=player_id,
            skin_id=skin_id,
            hero_id=skin.hero_id,
        )
        
        return SkinEquippedMessage(
            skin_id=skin_id,
            hero_id=skin.hero_id,
            skin_name=skin.name,
            stat_bonuses=stat_bonuses,
            effects=effects,
            seq=message.seq,
        )
    
    async def handle_unequip_skin(
        self,
        session: Session,
        message: UnequipSkinMessage,
    ) -> BaseMessage:
        """
        处理卸下皮肤请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            卸下成功响应或错误消息
        """
        player_id = session.player_id
        hero_id = message.hero_id
        
        # 获取当前装备的皮肤
        previous_skin_id = self.skin_manager.get_equipped_skin(player_id, hero_id)
        
        # 卸下皮肤
        success, error = self.skin_manager.unequip_skin(player_id, hero_id)
        
        if not success:
            return ErrorMessage(
                code=4003,
                message=error or "卸下失败",
                seq=message.seq,
            )
        
        logger.info(
            "Skin unequipped",
            player_id=player_id,
            hero_id=hero_id,
            previous_skin_id=previous_skin_id,
        )
        
        return SkinUnequippedMessage(
            hero_id=hero_id,
            previous_skin_id=previous_skin_id,
            seq=message.seq,
        )
    
    async def handle_buy_skin(
        self,
        session: Session,
        message: BuySkinMessage,
    ) -> BaseMessage:
        """
        处理购买皮肤请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            购买成功响应或错误消息
        """
        player_id = session.player_id
        skin_id = message.skin_id
        currency = message.currency
        
        # 获取玩家货币
        gold, diamond = self.get_player_currency(player_id)
        
        # 购买皮肤
        player_skin, used_currency, cost, error = self.skin_manager.buy_skin(
            player_id=player_id,
            skin_id=skin_id,
            gold=gold,
            diamond=diamond,
            use_currency=currency,
        )
        
        if error:
            return ErrorMessage(
                code=4004,
                message=error,
                seq=message.seq,
            )
        
        # 扣除货币
        if used_currency == "gold":
            gold -= cost
            self.update_player_currency(player_id, "gold", gold)
            remaining = gold
        else:
            diamond -= cost
            self.update_player_currency(player_id, "diamond", diamond)
            remaining = diamond
        
        # 获取皮肤信息
        skin = self.skin_manager.get_skin(skin_id)
        if not skin:
            return ErrorMessage(
                code=4002,
                message="皮肤不存在",
                seq=message.seq,
            )
        
        logger.info(
            "Skin bought",
            player_id=player_id,
            skin_id=skin_id,
            currency=used_currency,
            cost=cost,
        )
        
        return SkinBoughtMessage(
            skin_id=skin_id,
            hero_id=skin.hero_id,
            skin_name=skin.name,
            currency=used_currency,
            cost=cost,
            remaining_balance=remaining,
            seq=message.seq,
        )
    
    async def handle_set_favorite_skin(
        self,
        session: Session,
        message: SetFavoriteSkinMessage,
    ) -> SkinFavoriteSetMessage:
        """
        处理设置收藏皮肤请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            设置成功响应
        """
        player_id = session.player_id
        skin_id = message.skin_id
        is_favorite = message.is_favorite
        
        # 检查是否拥有皮肤
        if not self.skin_manager.has_skin(player_id, skin_id):
            return SkinFavoriteSetMessage(
                skin_id=skin_id,
                is_favorite=False,
                seq=message.seq,
            )
        
        # TODO: 实现收藏逻辑（需要在 PlayerSkin 模型中添加 is_favorite 字段）
        # 这里暂时返回成功
        
        logger.info(
            "Skin favorite set",
            player_id=player_id,
            skin_id=skin_id,
            is_favorite=is_favorite,
        )
        
        return SkinFavoriteSetMessage(
            skin_id=skin_id,
            is_favorite=is_favorite,
            seq=message.seq,
        )
    
    def _skin_to_data(
        self,
        skin: Skin,
        is_owned: bool = False,
        is_equipped: bool = False,
    ) -> SkinData:
        """
        将皮肤对象转换为 SkinData
        
        Args:
            skin: 皮肤对象
            is_owned: 是否已拥有
            is_equipped: 是否已装备
            
        Returns:
            SkinData 对象
        """
        return SkinData(
            skin_id=skin.skin_id,
            hero_id=skin.hero_id,
            name=skin.name,
            description=skin.description,
            rarity=skin.rarity.value,
            rarity_name=SkinRarity.get_display_name(skin.rarity.value),
            skin_type=skin.skin_type.value,
            price=skin.price.to_dict() if skin.price else None,
            stat_bonuses=[b.to_dict() for b in skin.stat_bonuses],
            effects=[e.to_dict() for e in skin.effects],
            preview_image=skin.preview_image,
            is_available=skin.is_available and not skin.is_expired(),
            is_owned=is_owned,
            is_equipped=is_equipped,
            is_favorite=False,  # TODO: 从玩家皮肤数据获取
        )


def register_skin_handlers(ws_handler: Any) -> None:
    """
    注册皮肤系统的 WebSocket 处理器
    
    Args:
        ws_handler: WebSocket 处理器实例
    """
    skin_handler = SkinWSHandler()
    
    @ws_handler.on_message(MessageType.GET_SKINS)
    async def handle_get_skins(session: Session, message: GetSkinsMessage):
        return await skin_handler.handle_get_skins(session, message)
    
    @ws_handler.on_message(MessageType.GET_HERO_SKINS)
    async def handle_get_hero_skins(session: Session, message: GetHeroSkinsMessage):
        return await skin_handler.handle_get_hero_skins(session, message)
    
    @ws_handler.on_message(MessageType.GET_OWNED_SKINS)
    async def handle_get_owned_skins(session: Session, message: GetOwnedSkinsMessage):
        return await skin_handler.handle_get_owned_skins(session, message)
    
    @ws_handler.on_message(MessageType.EQUIP_SKIN)
    async def handle_equip_skin(session: Session, message: EquipSkinMessage):
        return await skin_handler.handle_equip_skin(session, message)
    
    @ws_handler.on_message(MessageType.UNEQUIP_SKIN)
    async def handle_unequip_skin(session: Session, message: UnequipSkinMessage):
        return await skin_handler.handle_unequip_skin(session, message)
    
    @ws_handler.on_message(MessageType.BUY_SKIN)
    async def handle_buy_skin(session: Session, message: BuySkinMessage):
        return await skin_handler.handle_buy_skin(session, message)
    
    @ws_handler.on_message(MessageType.SET_FAVORITE_SKIN)
    async def handle_set_favorite_skin(session: Session, message: SetFavoriteSkinMessage):
        return await skin_handler.handle_set_favorite_skin(session, message)
    
    logger.info("Skin WebSocket handlers registered")
