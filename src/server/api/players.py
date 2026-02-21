"""
王者之奕 - 玩家 API 模块

本模块提供玩家相关的 RESTful API：
- GET /api/players/{id} - 获取玩家信息
- PUT /api/players/{id} - 更新玩家信息
- GET /api/players/{id}/stats - 获取玩家统计
- GET /api/players/{id}/rank - 获取玩家段位
- GET /api/players/{id}/inventory - 获取玩家背包
- GET /api/players - 搜索玩家列表

所有接口都包含：
- 完整的类型注解
- 详细的中文文档
- 请求/响应模型
- 错误处理
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_session
from ..crud.player import PlayerCRUD
from ..models.player import RankTier


# ============================================================================
# 请求/响应模型
# ============================================================================

class PlayerResponse(BaseModel):
    """
    玩家信息响应模型
    
    包含玩家的基本信息，不包含敏感信息。
    """
    
    id: int = Field(..., description="玩家ID")
    user_id: str = Field(..., description="用户唯一标识")
    nickname: str = Field(..., description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": "user_abc123",
                "nickname": "棋圣",
                "avatar": "https://example.com/avatar.png",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "last_login_at": "2024-01-15T12:00:00",
            }
        }
    }


class PlayerUpdateRequest(BaseModel):
    """
    玩家信息更新请求
    
    可更新的字段：昵称、头像
    """
    
    nickname: Optional[str] = Field(None, min_length=2, max_length=20, description="新昵称")
    avatar: Optional[str] = Field(None, max_length=500, description="新头像URL")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nickname": "新昵称",
                "avatar": "https://example.com/new-avatar.png",
            }
        }
    }


class PlayerRankResponse(BaseModel):
    """
    玩家段位响应模型
    """
    
    tier: str = Field(..., description="段位")
    sub_tier: int = Field(..., description="子段位(1-5)")
    stars: int = Field(..., description="当前星数")
    points: int = Field(..., description="当前积分")
    max_tier: str = Field(..., description="历史最高段位")
    max_points: int = Field(..., description="历史最高积分")
    display_rank: str = Field(..., description="段位显示文本")
    is_placed: bool = Field(..., description="是否完成定位赛")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "tier": "gold",
                "sub_tier": 3,
                "stars": 2,
                "points": 1500,
                "max_tier": "platinum",
                "max_points": 1800,
                "display_rank": "gold3 2星",
                "is_placed": True,
            }
        }
    }


class PlayerStatsResponse(BaseModel):
    """
    玩家统计响应模型
    """
    
    total_matches: int = Field(..., description="总对局数")
    total_wins: int = Field(..., description="总胜场")
    total_top4: int = Field(..., description="总前四场数")
    win_rate: float = Field(..., description="胜率(%)")
    top4_rate: float = Field(..., description="前四率(%)")
    avg_rank: float = Field(..., description="平均排名")
    total_damage_dealt: int = Field(..., description="总造成伤害")
    total_kills: int = Field(..., description="总击杀数")
    total_gold_earned: int = Field(..., description="总获得金币")
    max_win_streak: int = Field(..., description="最大连胜")
    fastest_win_round: int = Field(..., description="最快获胜回合")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "total_matches": 100,
                "total_wins": 20,
                "total_top4": 50,
                "win_rate": 20.0,
                "top4_rate": 50.0,
                "avg_rank": 3.5,
                "total_damage_dealt": 50000,
                "total_kills": 1000,
                "total_gold_earned": 10000,
                "max_win_streak": 5,
                "fastest_win_round": 15,
            }
        }
    }


class PlayerDetailResponse(BaseModel):
    """
    玩家详情响应模型
    
    包含玩家的所有信息：基本信息、段位、统计
    """
    
    id: int = Field(..., description="玩家ID")
    user_id: str = Field(..., description="用户唯一标识")
    nickname: str = Field(..., description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    rank: Optional[PlayerRankResponse] = Field(None, description="段位信息")
    stats: Optional[PlayerStatsResponse] = Field(None, description="统计信息")
    
    model_config = {
        "from_attributes": True,
    }


class PlayerListItem(BaseModel):
    """
    玩家列表项
    
    用于玩家搜索结果中的简化信息
    """
    
    id: int = Field(..., description="玩家ID")
    nickname: str = Field(..., description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    
    model_config = {
        "from_attributes": True,
    }


class PlayerListResponse(BaseModel):
    """
    玩家列表响应
    """
    
    total: int = Field(..., description="总数")
    items: List[PlayerListItem] = Field(..., description="玩家列表")


class InventoryItemResponse(BaseModel):
    """
    背包物品响应
    """
    
    id: int = Field(..., description="物品记录ID")
    item_type: str = Field(..., description="物品类型")
    item_id: str = Field(..., description="物品ID")
    quantity: int = Field(..., description="数量")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_expired: bool = Field(..., description="是否已过期")
    
    model_config = {
        "from_attributes": True,
    }


class ErrorResponse(BaseModel):
    """
    错误响应模型
    """
    
    detail: str = Field(..., description="错误信息")
    code: str = Field(..., description="错误代码")


# ============================================================================
# API 路由
# ============================================================================

router = APIRouter(
    prefix="/players",
    tags=["players"],
    responses={
        404: {"model": ErrorResponse, "description": "玩家不存在"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
    },
)


@router.get(
    "/{player_id}",
    response_model=PlayerDetailResponse,
    summary="获取玩家信息",
    description="""
    获取指定玩家的详细信息，包括：
    - 基本信息（ID、昵称、头像等）
    - 段位信息（当前段位、积分等）
    - 统计信息（胜率、场次等）
    """,
    responses={
        200: {
            "description": "玩家信息",
            "model": PlayerDetailResponse,
        },
        404: {
            "description": "玩家不存在",
            "model": ErrorResponse,
        },
    },
)
async def get_player(
    player_id: int,
    session: AsyncSession = Depends(get_session),
) -> PlayerDetailResponse:
    """
    获取玩家信息
    
    通过玩家ID获取玩家的详细信息。
    
    Args:
        player_id: 玩家ID
        
    Returns:
        玩家详情，包含段位和统计信息
        
    Raises:
        HTTPException: 玩家不存在时返回404
    """
    crud = PlayerCRUD(session)
    player = await crud.get_by_id(player_id)
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )
    
    # 构建响应
    response = PlayerDetailResponse(
        id=player.id,
        user_id=player.user_id,
        nickname=player.nickname,
        avatar=player.avatar,
        is_active=player.is_active,
        created_at=player.created_at,
        last_login_at=player.last_login_at,
    )
    
    # 添加段位信息
    if player.rank:
        response.rank = PlayerRankResponse(
            tier=player.rank.tier,
            sub_tier=player.rank.sub_tier,
            stars=player.rank.stars,
            points=player.rank.points,
            max_tier=player.rank.max_tier,
            max_points=player.rank.max_points,
            display_rank=player.rank.display_rank,
            is_placed=player.rank.is_placed,
        )
    
    # 添加统计信息
    if player.stats:
        response.stats = PlayerStatsResponse(
            total_matches=player.stats.total_matches,
            total_wins=player.stats.total_wins,
            total_top4=player.stats.total_top4,
            win_rate=player.stats.win_rate,
            top4_rate=player.stats.top4_rate,
            avg_rank=player.stats.avg_rank,
            total_damage_dealt=player.stats.total_damage_dealt,
            total_kills=player.stats.total_kills,
            total_gold_earned=player.stats.total_gold_earned,
            max_win_streak=player.stats.max_win_streak,
            fastest_win_round=player.stats.fastest_win_round,
        )
    
    return response


@router.put(
    "/{player_id}",
    response_model=PlayerResponse,
    summary="更新玩家信息",
    description="""
    更新指定玩家的信息。
    
    可更新的字段：
    - nickname: 昵称（2-20个字符）
    - avatar: 头像URL
    """,
    responses={
        200: {
            "description": "更新成功",
            "model": PlayerResponse,
        },
        404: {
            "description": "玩家不存在",
            "model": ErrorResponse,
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse,
        },
    },
)
async def update_player(
    player_id: int,
    data: PlayerUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> PlayerResponse:
    """
    更新玩家信息
    
    更新指定玩家的昵称或头像。
    
    Args:
        player_id: 玩家ID
        data: 更新数据
        
    Returns:
        更新后的玩家信息
        
    Raises:
        HTTPException: 玩家不存在时返回404
    """
    crud = PlayerCRUD(session)
    
    # 检查是否有需要更新的字段
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要更新的字段",
        )
    
    player = await crud.update(player_id, **update_data)
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )
    
    return PlayerResponse(
        id=player.id,
        user_id=player.user_id,
        nickname=player.nickname,
        avatar=player.avatar,
        is_active=player.is_active,
        created_at=player.created_at,
        last_login_at=player.last_login_at,
    )


@router.get(
    "/{player_id}/stats",
    response_model=PlayerStatsResponse,
    summary="获取玩家统计",
    description="""
    获取指定玩家的游戏统计数据。
    
    包括：
    - 对局统计（场次、胜率等）
    - 战斗统计（伤害、击杀等）
    - 经济统计（金币等）
    """,
    responses={
        200: {
            "description": "统计数据",
            "model": PlayerStatsResponse,
        },
        404: {
            "description": "玩家不存在或无统计数据",
            "model": ErrorResponse,
        },
    },
)
async def get_player_stats(
    player_id: int,
    session: AsyncSession = Depends(get_session),
) -> PlayerStatsResponse:
    """
    获取玩家统计
    
    获取指定玩家的游戏统计数据。
    
    Args:
        player_id: 玩家ID
        
    Returns:
        玩家统计数据
        
    Raises:
        HTTPException: 玩家不存在时返回404
    """
    crud = PlayerCRUD(session)
    stats = await crud.get_stats(player_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家统计数据不存在: {player_id}",
        )
    
    return PlayerStatsResponse(
        total_matches=stats.total_matches,
        total_wins=stats.total_wins,
        total_top4=stats.total_top4,
        win_rate=stats.win_rate,
        top4_rate=stats.top4_rate,
        avg_rank=stats.avg_rank,
        total_damage_dealt=stats.total_damage_dealt,
        total_kills=stats.total_kills,
        total_gold_earned=stats.total_gold_earned,
        max_win_streak=stats.max_win_streak,
        fastest_win_round=stats.fastest_win_round,
    )


@router.get(
    "/{player_id}/rank",
    response_model=PlayerRankResponse,
    summary="获取玩家段位",
    description="""
    获取指定玩家的段位信息。
    
    包括：
    - 当前段位和积分
    - 历史最高段位
    - 定位赛状态
    """,
    responses={
        200: {
            "description": "段位信息",
            "model": PlayerRankResponse,
        },
        404: {
            "description": "玩家不存在或无段位数据",
            "model": ErrorResponse,
        },
    },
)
async def get_player_rank(
    player_id: int,
    session: AsyncSession = Depends(get_session),
) -> PlayerRankResponse:
    """
    获取玩家段位
    
    获取指定玩家的段位信息。
    
    Args:
        player_id: 玩家ID
        
    Returns:
        玩家段位信息
        
    Raises:
        HTTPException: 玩家不存在时返回404
    """
    crud = PlayerCRUD(session)
    rank = await crud.get_rank(player_id)
    
    if not rank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家段位数据不存在: {player_id}",
        )
    
    return PlayerRankResponse(
        tier=rank.tier,
        sub_tier=rank.sub_tier,
        stars=rank.stars,
        points=rank.points,
        max_tier=rank.max_tier,
        max_points=rank.max_points,
        display_rank=rank.display_rank,
        is_placed=rank.is_placed,
    )


@router.get(
    "/{player_id}/inventory",
    response_model=List[InventoryItemResponse],
    summary="获取玩家背包",
    description="""
    获取指定玩家的背包物品列表。
    
    支持按物品类型筛选。
    """,
    responses={
        200: {
            "description": "背包物品列表",
            "model": List[InventoryItemResponse],
        },
        404: {
            "description": "玩家不存在",
            "model": ErrorResponse,
        },
    },
)
async def get_player_inventory(
    player_id: int,
    item_type: Optional[str] = Query(None, description="物品类型筛选"),
    session: AsyncSession = Depends(get_session),
) -> List[InventoryItemResponse]:
    """
    获取玩家背包
    
    获取指定玩家的背包物品列表。
    
    Args:
        player_id: 玩家ID
        item_type: 物品类型筛选（可选）
        
    Returns:
        背包物品列表
        
    Raises:
        HTTPException: 玩家不存在时返回404
    """
    crud = PlayerCRUD(session)
    
    # 先检查玩家是否存在
    if not await crud.exists(player_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )
    
    items = await crud.get_inventory(player_id, item_type)
    
    return [
        InventoryItemResponse(
            id=item.id,
            item_type=item.item_type,
            item_id=item.item_id,
            quantity=item.quantity,
            extra_data=item.extra_data,
            expires_at=item.expires_at,
            is_expired=item.is_expired,
        )
        for item in items
    ]


@router.get(
    "/",
    response_model=PlayerListResponse,
    summary="搜索玩家",
    description="""
    搜索玩家列表。
    
    支持通过昵称或用户名搜索。
    返回匹配的玩家列表（简化信息）。
    """,
)
async def search_players(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    session: AsyncSession = Depends(get_session),
) -> PlayerListResponse:
    """
    搜索玩家
    
    通过昵称或用户名搜索玩家。
    
    Args:
        query: 搜索关键词
        limit: 返回数量限制
        
    Returns:
        匹配的玩家列表
    """
    crud = PlayerCRUD(session)
    players = await crud.search(query, limit)
    
    items = [
        PlayerListItem(
            id=p.id,
            nickname=p.nickname,
            avatar=p.avatar,
        )
        for p in players
    ]
    
    return PlayerListResponse(
        total=len(items),
        items=items,
    )
