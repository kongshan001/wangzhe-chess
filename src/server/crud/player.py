"""
王者之奕 - 玩家 CRUD 操作

本模块提供玩家数据的增删改查操作：
- 创建玩家
- 查询玩家
- 更新玩家信息
- 删除玩家
- 统计数据管理

所有操作都是异步的，需要配合 async session 使用。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional, List

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.player import PlayerDB, PlayerStatsDB

logger = logging.getLogger(__name__)


class PlayerCRUD:
    """
    玩家 CRUD 操作类
    
    提供玩家数据的所有数据库操作方法。
    所有方法都是类方法，无需实例化。
    
    Example:
        async with get_session() as session:
            player = await PlayerCRUD.get_by_user_id(session, "user123")
    """
    
    # ========================================================================
    # 创建操作 (Create)
    # ========================================================================
    
    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: str,
        nickname: str,
        avatar: Optional[str] = None,
        **kwargs: Any,
    ) -> PlayerDB:
        """
        创建新玩家
        
        同时创建玩家记录和关联的统计记录。
        
        Args:
            session: 数据库会话
            user_id: 用户唯一标识
            nickname: 玩家昵称
            avatar: 头像URL
            **kwargs: 其他可选字段
            
        Returns:
            创建的玩家对象
            
        Raises:
            IntegrityError: 如果 user_id 已存在
            
        Example:
            player = await PlayerCRUD.create(
                session,
                user_id="abc123",
                nickname="玩家1",
                avatar="https://example.com/avatar.png",
            )
        """
        # 创建玩家
        player = PlayerDB(
            user_id=user_id,
            nickname=nickname,
            avatar=avatar,
            **kwargs,
        )
        session.add(player)
        
        # 刷新以获取生成的ID
        await session.flush()
        
        # 创建关联的统计数据
        stats = PlayerStatsDB(player_id=player.id)
        session.add(stats)
        
        await session.flush()
        await session.refresh(player, ["stats"])
        
        logger.info(f"创建玩家: user_id={user_id}, nickname={nickname}")
        return player
    
    @classmethod
    async def create_with_stats(
        cls,
        session: AsyncSession,
        player_data: dict[str, Any],
    ) -> PlayerDB:
        """
        使用数据字典创建玩家
        
        Args:
            session: 数据库会话
            player_data: 玩家数据字典
            
        Returns:
            创建的玩家对象
        """
        return await cls.create(session, **player_data)
    
    # ========================================================================
    # 查询操作 (Read)
    # ========================================================================
    
    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        player_id: int,
    ) -> Optional[PlayerDB]:
        """
        根据ID获取玩家
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            
        Returns:
            玩家对象，如果不存在返回 None
            
        Example:
            player = await PlayerCRUD.get_by_id(session, 1)
        """
        result = await session.execute(
            select(PlayerDB)
            .options(selectinload(PlayerDB.stats))
            .where(PlayerDB.id == player_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_user_id(
        cls,
        session: AsyncSession,
        user_id: str,
    ) -> Optional[PlayerDB]:
        """
        根据用户ID获取玩家
        
        Args:
            session: 数据库会话
            user_id: 用户唯一标识
            
        Returns:
            玩家对象，如果不存在返回 None
            
        Example:
            player = await PlayerCRUD.get_by_user_id(session, "abc123")
        """
        result = await session.execute(
            select(PlayerDB)
            .options(selectinload(PlayerDB.stats))
            .where(PlayerDB.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_nickname(
        cls,
        session: AsyncSession,
        nickname: str,
    ) -> Optional[PlayerDB]:
        """
        根据昵称获取玩家
        
        Args:
            session: 数据库会话
            nickname: 玩家昵称
            
        Returns:
            玩家对象，如果不存在返回 None
        """
        result = await session.execute(
            select(PlayerDB)
            .options(selectinload(PlayerDB.stats))
            .where(PlayerDB.nickname == nickname)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_multi(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        online_only: bool = False,
    ) -> List[PlayerDB]:
        """
        获取玩家列表
        
        支持分页和在线过滤。
        
        Args:
            session: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            online_only: 是否只返回在线玩家
            
        Returns:
            玩家对象列表
            
        Example:
            players = await PlayerCRUD.get_multi(session, skip=0, limit=10)
        """
        query = select(PlayerDB).options(selectinload(PlayerDB.stats))
        
        if online_only:
            query = query.where(PlayerDB.is_online == True)
        
        query = query.offset(skip).limit(limit).order_by(PlayerDB.id.desc())
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_level(
        cls,
        session: AsyncSession,
        level: int,
        limit: int = 100,
    ) -> List[PlayerDB]:
        """
        获取指定等级的玩家列表
        
        Args:
            session: 数据库会话
            level: 玩家等级
            limit: 返回的最大记录数
            
        Returns:
            玩家对象列表
        """
        result = await session.execute(
            select(PlayerDB)
            .options(selectinload(PlayerDB.stats))
            .where(PlayerDB.level == level)
            .limit(limit)
            .order_by(PlayerDB.exp.desc())
        )
        return list(result.scalars().all())
    
    @classmethod
    async def count(
        cls,
        session: AsyncSession,
        online_only: bool = False,
    ) -> int:
        """
        统计玩家数量
        
        Args:
            session: 数据库会话
            online_only: 是否只统计在线玩家
            
        Returns:
            玩家数量
        """
        query = select(func.count(PlayerDB.id))
        if online_only:
            query = query.where(PlayerDB.is_online == True)
        
        result = await session.execute(query)
        return result.scalar_one()
    
    @classmethod
    async def exists(
        cls,
        session: AsyncSession,
        user_id: str,
    ) -> bool:
        """
        检查玩家是否存在
        
        Args:
            session: 数据库会话
            user_id: 用户唯一标识
            
        Returns:
            是否存在
        """
        result = await session.execute(
            select(func.count(PlayerDB.id)).where(PlayerDB.user_id == user_id)
        )
        return result.scalar_one() > 0
    
    # ========================================================================
    # 更新操作 (Update)
    # ========================================================================
    
    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        player_id: int,
        **kwargs: Any,
    ) -> Optional[PlayerDB]:
        """
        更新玩家信息
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的玩家对象，如果不存在返回 None
            
        Example:
            player = await PlayerCRUD.update(
                session, 
                player_id=1, 
                nickname="新昵称",
                gold=1000,
            )
        """
        player = await cls.get_by_id(session, player_id)
        if player is None:
            return None
        
        for key, value in kwargs.items():
            if hasattr(player, key):
                setattr(player, key, value)
        
        await session.flush()
        await session.refresh(player)
        
        logger.debug(f"更新玩家: id={player_id}, fields={list(kwargs.keys())}")
        return player
    
    @classmethod
    async def update_by_user_id(
        cls,
        session: AsyncSession,
        user_id: str,
        **kwargs: Any,
    ) -> Optional[PlayerDB]:
        """
        根据用户ID更新玩家信息
        
        Args:
            session: 数据库会话
            user_id: 用户唯一标识
            **kwargs: 要更新的字段
            
        Returns:
            更新后的玩家对象，如果不存在返回 None
        """
        player = await cls.get_by_user_id(session, user_id)
        if player is None:
            return None
        
        return await cls.update(session, player.id, **kwargs)
    
    @classmethod
    async def add_gold(
        cls,
        session: AsyncSession,
        player_id: int,
        amount: int,
    ) -> Optional[PlayerDB]:
        """
        增加玩家金币
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            amount: 增加的金币数量（可以为负数表示扣除）
            
        Returns:
            更新后的玩家对象
        """
        player = await cls.get_by_id(session, player_id)
        if player is None:
            return None
        
        player.gold = max(0, player.gold + amount)
        await session.flush()
        await session.refresh(player)
        
        return player
    
    @classmethod
    async def add_exp(
        cls,
        session: AsyncSession,
        player_id: int,
        amount: int,
    ) -> Optional[PlayerDB]:
        """
        增加玩家经验值
        
        自动处理升级逻辑。
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            amount: 增加的经验值
            
        Returns:
            更新后的玩家对象
        """
        from ...shared.constants import LEVEL_UP_EXP, MAX_PLAYER_LEVEL
        
        player = await cls.get_by_id(session, player_id)
        if player is None:
            return None
        
        player.exp += amount
        
        # 检查升级
        while player.level < MAX_PLAYER_LEVEL:
            exp_needed = LEVEL_UP_EXP.get(player.level + 1, 999)
            if player.exp >= exp_needed:
                player.exp -= exp_needed
                player.level += 1
                logger.info(f"玩家升级: id={player_id}, level={player.level}")
            else:
                break
        
        await session.flush()
        await session.refresh(player)
        
        return player
    
    @classmethod
    async def set_online(
        cls,
        session: AsyncSession,
        player_id: int,
        is_online: bool = True,
    ) -> Optional[PlayerDB]:
        """
        设置玩家在线状态
        
        同时更新登录/登出时间。
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            is_online: 是否在线
            
        Returns:
            更新后的玩家对象
        """
        now = datetime.utcnow()
        update_data = {"is_online": is_online}
        
        if is_online:
            update_data["last_login_at"] = now
        else:
            update_data["last_logout_at"] = now
        
        return await cls.update(session, player_id, **update_data)
    
    # ========================================================================
    # 删除操作 (Delete)
    # ========================================================================
    
    @classmethod
    async def delete(
        cls,
        session: AsyncSession,
        player_id: int,
    ) -> bool:
        """
        删除玩家
        
        同时删除关联的统计数据（级联删除）。
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            
        Returns:
            是否成功删除
        """
        player = await cls.get_by_id(session, player_id)
        if player is None:
            return False
        
        await session.delete(player)
        await session.flush()
        
        logger.info(f"删除玩家: id={player_id}")
        return True
    
    @classmethod
    async def delete_by_user_id(
        cls,
        session: AsyncSession,
        user_id: str,
    ) -> bool:
        """
        根据用户ID删除玩家
        
        Args:
            session: 数据库会话
            user_id: 用户唯一标识
            
        Returns:
            是否成功删除
        """
        result = await session.execute(
            delete(PlayerDB).where(PlayerDB.user_id == user_id)
        )
        deleted = result.rowcount > 0
        
        if deleted:
            logger.info(f"删除玩家: user_id={user_id}")
        
        return deleted


class PlayerStatsCRUD:
    """
    玩家统计数据 CRUD 操作类
    
    提供玩家统计数据的数据库操作方法。
    """
    
    @classmethod
    async def get_by_player_id(
        cls,
        session: AsyncSession,
        player_id: int,
    ) -> Optional[PlayerStatsDB]:
        """
        根据玩家ID获取统计数据
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            
        Returns:
            统计数据对象
        """
        result = await session.execute(
            select(PlayerStatsDB).where(PlayerStatsDB.player_id == player_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def update_after_match(
        cls,
        session: AsyncSession,
        player_id: int,
        rank: int,
        is_win: bool,
        **game_stats: Any,
    ) -> Optional[PlayerStatsDB]:
        """
        对局结束后更新统计数据
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            rank: 本局排名
            is_win: 是否获胜
            **game_stats: 游戏统计数据
            
        Returns:
            更新后的统计数据对象
        """
        stats = await cls.get_by_player_id(session, player_id)
        if stats is None:
            return None
        
        stats.update_after_match(
            rank=rank,
            is_win=is_win,
            **game_stats,
        )
        
        await session.flush()
        await session.refresh(stats)
        
        return stats
    
    @classmethod
    async def get_top_players(
        cls,
        session: AsyncSession,
        limit: int = 10,
        order_by: str = "wins",
    ) -> List[PlayerStatsDB]:
        """
        获取排行榜玩家
        
        Args:
            session: 数据库会话
            limit: 返回数量
            order_by: 排序字段（wins, total_matches, first_place_count）
            
        Returns:
            统计数据列表
        """
        order_column = getattr(PlayerStatsDB, order_by, PlayerStatsDB.wins)
        
        result = await session.execute(
            select(PlayerStatsDB)
            .order_by(order_column.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def increment_play_time(
        cls,
        session: AsyncSession,
        player_id: int,
        seconds: int,
    ) -> Optional[PlayerStatsDB]:
        """
        增加游戏时长
        
        Args:
            session: 数据库会话
            player_id: 玩家ID
            seconds: 增加的秒数
            
        Returns:
            更新后的统计数据对象
        """
        stats = await cls.get_by_player_id(session, player_id)
        if stats is None:
            return None
        
        stats.total_play_time_seconds += seconds
        await session.flush()
        await session.refresh(stats)
        
        return stats
