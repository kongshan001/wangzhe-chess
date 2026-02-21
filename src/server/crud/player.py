"""
王者之奕 - 玩家 CRUD 操作

本模块提供玩家相关的数据库 CRUD 操作：
- 玩家基本信息的增删改查
- 段位信息管理
- 统计数据管理
- 登录记录管理

使用方式:
    from src.server.crud.player import PlayerCRUD
    
    async with get_session() as session:
        crud = PlayerCRUD(session)
        player = await crud.get_by_username("test")
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.player import (
    Player,
    PlayerInventory,
    PlayerLoginLog,
    PlayerRank,
    PlayerStats,
    RankTier,
)

logger = logging.getLogger(__name__)


class CacheMixin:
    """
    缓存混入类
    
    提供简单的内存缓存支持，可用于热数据缓存。
    """
    
    _cache: dict[str, tuple[Any, float]] = {}
    _cache_ttl: int = 300  # 默认缓存5分钟
    
    @classmethod
    def _get_cache_key(cls, *args: Any) -> str:
        """生成缓存键"""
        return ":".join(str(arg) for arg in args)
    
    @classmethod
    def _get_from_cache(cls, key: str) -> Any | None:
        """从缓存获取数据"""
        if key in cls._cache:
            value, expire_at = cls._cache[key]
            if datetime.now().timestamp() < expire_at:
                return value
            del cls._cache[key]
        return None
    
    @classmethod
    def _set_to_cache(cls, key: str, value: Any, ttl: int | None = None) -> None:
        """设置缓存"""
        ttl = ttl or cls._cache_ttl
        expire_at = datetime.now().timestamp() + ttl
        cls._cache[key] = (value, expire_at)
    
    @classmethod
    def _invalidate_cache(cls, key: str) -> None:
        """使缓存失效"""
        cls._cache.pop(key, None)


class PlayerCRUD(CacheMixin):
    """
    玩家 CRUD 操作类
    
    提供玩家相关的所有数据库操作。
    
    Attributes:
        session: 异步数据库会话
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        初始化 CRUD 实例
        
        Args:
            session: 异步数据库会话
        """
        self.session = session
    
    # ========================================================================
    # 创建操作
    # ========================================================================
    
    async def create(
        self,
        username: str,
        nickname: str,
        password: str | None = None,
        **kwargs: Any,
    ) -> Player:
        """
        创建新玩家
        
        Args:
            username: 用户名
            nickname: 昵称
            password: 密码（可选，用于账号密码登录）
            **kwargs: 其他字段
            
        Returns:
            创建的玩家实例
        """
        # 密码哈希
        password_hash = None
        if password:
            password_hash = self._hash_password(password)
        
        player = Player(
            username=username,
            nickname=nickname,
            password_hash=password_hash,
            **kwargs,
        )
        
        self.session.add(player)
        await self.session.flush()
        
        # 创建关联的段位和统计记录
        rank = PlayerRank(player_id=player.id)
        stats = PlayerStats(player_id=player.id)
        
        self.session.add(rank)
        self.session.add(stats)
        
        await self.session.flush()
        await self.session.refresh(player)
        
        logger.info(f"创建新玩家: {username}")
        return player
    
    async def create_with_device(
        self,
        device_id: str,
        nickname: str,
    ) -> Player:
        """
        通过设备ID创建玩家（游客登录）
        
        Args:
            device_id: 设备ID
            nickname: 昵称
            
        Returns:
            创建的玩家实例
        """
        # 生成随机用户名
        username = f"guest_{secrets.token_hex(8)}"
        
        return await self.create(
            username=username,
            nickname=nickname,
            device_id=device_id,
        )
    
    # ========================================================================
    # 读取操作
    # ========================================================================
    
    async def get_by_id(self, player_id: int) -> Player | None:
        """
        通过ID获取玩家
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家实例，如果不存在返回None
        """
        cache_key = self._get_cache_key("player", player_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        stmt = (
            select(Player)
            .options(selectinload(Player.rank), selectinload(Player.stats))
            .where(Player.id == player_id)
        )
        result = await self.session.scalar(stmt)
        
        if result:
            self._set_to_cache(cache_key, result)
        
        return result
    
    async def get_by_username(self, username: str) -> Player | None:
        """
        通过用户名获取玩家
        
        Args:
            username: 用户名
            
        Returns:
            玩家实例
        """
        stmt = (
            select(Player)
            .options(selectinload(Player.rank), selectinload(Player.stats))
            .where(Player.username == username)
        )
        return await self.session.scalar(stmt)
    
    async def get_by_device_id(self, device_id: str) -> Player | None:
        """
        通过设备ID获取玩家
        
        Args:
            device_id: 设备ID
            
        Returns:
            玩家实例
        """
        stmt = (
            select(Player)
            .options(selectinload(Player.rank), selectinload(Player.stats))
            .where(Player.device_id == device_id)
        )
        return await self.session.scalar(stmt)
    
    async def get_multi(
        self,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Player]:
        """
        获取多个玩家
        
        Args:
            offset: 偏移量
            limit: 数量限制
            is_active: 是否只获取活跃玩家
            
        Returns:
            玩家列表
        """
        stmt = select(Player).offset(offset).limit(limit)
        
        if is_active is not None:
            stmt = stmt.where(Player.is_active == is_active)
        
        stmt = stmt.order_by(desc(Player.id))
        
        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Player]:
        """
        搜索玩家
        
        Args:
            query: 搜索关键词（匹配用户名或昵称）
            limit: 数量限制
            
        Returns:
            匹配的玩家列表
        """
        stmt = (
            select(Player)
            .where(
                or_(
                    Player.username.contains(query),
                    Player.nickname.contains(query),
                )
            )
            .limit(limit)
            .order_by(desc(Player.id))
        )
        
        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def exists(self, player_id: int) -> bool:
        """
        检查玩家是否存在
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否存在
        """
        stmt = select(func.count()).select_from(Player).where(Player.id == player_id)
        count = await self.session.scalar(stmt)
        return count > 0
    
    async def username_exists(self, username: str) -> bool:
        """
        检查用户名是否已存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        stmt = select(func.count()).select_from(Player).where(Player.username == username)
        count = await self.session.scalar(stmt)
        return count > 0
    
    # ========================================================================
    # 更新操作
    # ========================================================================
    
    async def update(
        self,
        player_id: int,
        **kwargs: Any,
    ) -> Player | None:
        """
        更新玩家信息
        
        Args:
            player_id: 玩家ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的玩家实例
        """
        player = await self.get_by_id(player_id)
        if not player:
            return None
        
        # 过滤不允许更新的字段
        protected_fields = {"id", "created_at", "username"}
        for key in protected_fields:
            kwargs.pop(key, None)
        
        player.update_from_dict(kwargs)
        await self.session.flush()
        await self.session.refresh(player)
        
        # 使缓存失效
        self._invalidate_cache(self._get_cache_key("player", player_id))
        
        return player
    
    async def update_last_login(
        self,
        player_id: int,
        ip_address: str | None = None,
    ) -> None:
        """
        更新最后登录信息
        
        Args:
            player_id: 玩家ID
            ip_address: 登录IP
        """
        stmt = (
            update(Player)
            .where(Player.id == player_id)
            .values(
                last_login_at=datetime.now(),
                last_login_ip=ip_address,
            )
        )
        await self.session.execute(stmt)
        
        # 使缓存失效
        self._invalidate_cache(self._get_cache_key("player", player_id))
    
    async def update_nickname(self, player_id: int, nickname: str) -> Player | None:
        """
        更新昵称
        
        Args:
            player_id: 玩家ID
            nickname: 新昵称
            
        Returns:
            更新后的玩家实例
        """
        return await self.update(player_id, nickname=nickname)
    
    async def update_password(
        self,
        player_id: int,
        new_password: str,
    ) -> bool:
        """
        更新密码
        
        Args:
            player_id: 玩家ID
            new_password: 新密码
            
        Returns:
            是否成功
        """
        password_hash = self._hash_password(new_password)
        result = await self.update(player_id, password_hash=password_hash)
        return result is not None
    
    async def ban_player(
        self,
        player_id: int,
        until: datetime | None = None,
    ) -> bool:
        """
        封禁玩家
        
        Args:
            player_id: 玩家ID
            until: 封禁截止时间（None表示永久）
            
        Returns:
            是否成功
        """
        result = await self.update(
            player_id,
            is_banned=True,
            ban_until=until,
        )
        return result is not None
    
    async def unban_player(self, player_id: int) -> bool:
        """
        解封玩家
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功
        """
        result = await self.update(
            player_id,
            is_banned=False,
            ban_until=None,
        )
        return result is not None
    
    # ========================================================================
    # 删除操作
    # ========================================================================
    
    async def delete(self, player_id: int) -> bool:
        """
        删除玩家（软删除）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功
        """
        result = await self.update(player_id, is_active=False)
        return result is not None
    
    async def hard_delete(self, player_id: int) -> bool:
        """
        硬删除玩家（真正删除）
        
        警告：此操作不可逆！
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功
        """
        player = await self.get_by_id(player_id)
        if not player:
            return False
        
        await self.session.delete(player)
        await self.session.flush()
        
        # 使缓存失效
        self._invalidate_cache(self._get_cache_key("player", player_id))
        
        return True
    
    # ========================================================================
    # 认证操作
    # ========================================================================
    
    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> Player | None:
        """
        验证玩家登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回玩家实例，否则返回None
        """
        player = await self.get_by_username(username)
        
        if not player:
            return None
        
        if not player.is_active:
            return None
        
        if player.is_banned:
            if player.ban_until and player.ban_until < datetime.now():
                # 封禁已过期，自动解封
                await self.unban_player(player.id)
            else:
                return None
        
        if not self._verify_password(password, player.password_hash or ""):
            return None
        
        return player
    
    # ========================================================================
    # 段位操作
    # ========================================================================
    
    async def get_rank(self, player_id: int) -> PlayerRank | None:
        """
        获取玩家段位信息
        
        Args:
            player_id: 玩家ID
            
        Returns:
            段位信息
        """
        stmt = select(PlayerRank).where(PlayerRank.player_id == player_id)
        return await self.session.scalar(stmt)
    
    async def update_rank(
        self,
        player_id: int,
        point_change: int,
        rank_up: bool = False,
        new_tier: str | None = None,
    ) -> PlayerRank | None:
        """
        更新玩家段位
        
        Args:
            player_id: 玩家ID
            point_change: 积分变化（正数为增加）
            rank_up: 是否升段
            new_tier: 新段位（升段时使用）
            
        Returns:
            更新后的段位信息
        """
        rank = await self.get_rank(player_id)
        if not rank:
            return None
        
        rank.points += point_change
        
        if rank_up and new_tier:
            rank.tier = new_tier
            rank.sub_tier = 5  # 新段位从5开始
        
        # 更新历史最高
        if rank.points > rank.max_points:
            rank.max_points = rank.points
            # 比较段位顺序
            tier_order = [t.value for t in RankTier]
            if tier_order.index(rank.tier) > tier_order.index(rank.max_tier):
                rank.max_tier = rank.tier
        
        await self.session.flush()
        await self.session.refresh(rank)
        
        return rank
    
    # ========================================================================
    # 统计操作
    # ========================================================================
    
    async def get_stats(self, player_id: int) -> PlayerStats | None:
        """
        获取玩家统计数据
        
        Args:
            player_id: 玩家ID
            
        Returns:
            统计数据
        """
        stmt = select(PlayerStats).where(PlayerStats.player_id == player_id)
        return await self.session.scalar(stmt)
    
    async def update_stats_after_match(
        self,
        player_id: int,
        rank: int,
        damage: int,
        survivors: int,
        kills: int,
        gold: int,
        win_streak: int,
        round_num: int,
    ) -> PlayerStats | None:
        """
        对局结束后更新统计数据
        
        Args:
            player_id: 玩家ID
            rank: 本局排名
            damage: 造成伤害
            survivors: 存活英雄数
            kills: 击杀数
            gold: 获得金币
            win_streak: 连胜场次
            round_num: 回合数
            
        Returns:
            更新后的统计数据
        """
        stats = await self.get_stats(player_id)
        if not stats:
            return None
        
        # 更新对局统计
        old_total = stats.total_matches
        stats.total_matches += 1
        
        if rank == 1:
            stats.total_wins += 1
            if stats.fastest_win_round == 0 or round_num < stats.fastest_win_round:
                stats.fastest_win_round = round_num
        
        if rank <= 4:
            stats.total_top4 += 1
        
        # 重新计算平均排名
        stats.avg_rank = (stats.avg_rank * old_total + rank) / stats.total_matches
        
        # 更新战斗统计
        stats.avg_damage = (stats.avg_damage * old_total + damage) / stats.total_matches
        stats.avg_survivors = (stats.avg_survivors * old_total + survivors) / stats.total_matches
        stats.total_kills += kills
        
        # 更新经济统计
        stats.total_gold_earned += gold
        
        # 更新连胜记录
        if win_streak > stats.longest_win_streak:
            stats.longest_win_streak = win_streak
        
        await self.session.flush()
        await self.session.refresh(stats)
        
        return stats
    
    # ========================================================================
    # 登录记录操作
    # ========================================================================
    
    async def create_login_log(
        self,
        player_id: int,
        ip_address: str | None = None,
        device_id: str | None = None,
        device_type: str | None = None,
        client_version: str | None = None,
        location: str | None = None,
    ) -> PlayerLoginLog:
        """
        创建登录记录
        
        Args:
            player_id: 玩家ID
            ip_address: 登录IP
            device_id: 设备ID
            device_type: 设备类型
            client_version: 客户端版本
            location: 登录地点
            
        Returns:
            登录记录
        """
        login_log = PlayerLoginLog(
            player_id=player_id,
            login_ip=ip_address,
            device_id=device_id,
            device_type=device_type,
            client_version=client_version,
            location=location,
        )
        
        self.session.add(login_log)
        await self.session.flush()
        
        return login_log
    
    async def logout(self, log_id: int) -> bool:
        """
        记录登出时间
        
        Args:
            log_id: 登录记录ID
            
        Returns:
            是否成功
        """
        stmt = (
            update(PlayerLoginLog)
            .where(PlayerLoginLog.id == log_id)
            .values(logout_time=datetime.now())
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    # ========================================================================
    # 背包操作
    # ========================================================================
    
    async def get_inventory(
        self,
        player_id: int,
        item_type: str | None = None,
    ) -> list[PlayerInventory]:
        """
        获取玩家背包
        
        Args:
            player_id: 玩家ID
            item_type: 物品类型过滤
            
        Returns:
            物品列表
        """
        stmt = select(PlayerInventory).where(PlayerInventory.player_id == player_id)
        
        if item_type:
            stmt = stmt.where(PlayerInventory.item_type == item_type)
        
        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def add_item(
        self,
        player_id: int,
        item_type: str,
        item_id: str,
        quantity: int = 1,
        expires_at: datetime | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> PlayerInventory:
        """
        添加物品到背包
        
        Args:
            player_id: 玩家ID
            item_type: 物品类型
            item_id: 物品ID
            quantity: 数量
            expires_at: 过期时间
            extra_data: 额外数据
            
        Returns:
            背包物品记录
        """
        # 检查是否已存在
        stmt = select(PlayerInventory).where(
            and_(
                PlayerInventory.player_id == player_id,
                PlayerInventory.item_type == item_type,
                PlayerInventory.item_id == item_id,
            )
        )
        existing = await self.session.scalar(stmt)
        
        if existing:
            existing.quantity += quantity
            if expires_at:
                existing.expires_at = expires_at
            if extra_data:
                existing.extra_data = extra_data
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        
        inventory_item = PlayerInventory(
            player_id=player_id,
            item_type=item_type,
            item_id=item_id,
            quantity=quantity,
            expires_at=expires_at,
            extra_data=extra_data,
        )
        
        self.session.add(inventory_item)
        await self.session.flush()
        await self.session.refresh(inventory_item)
        
        return inventory_item
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        密码哈希
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        salt = secrets.token_hex(16)
        hash_value = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${hash_value}"
    
    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed: 哈希后的密码
            
        Returns:
            是否匹配
        """
        try:
            salt, hash_value = hashed.split("$")
            new_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return secrets.compare_digest(hash_value, new_hash)
        except ValueError:
            return False
