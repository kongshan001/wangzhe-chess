"""
王者之奕 - FastAPI 应用入口

提供 HTTP API 和 WebSocket 服务
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.server.db.database import DatabaseConfig, close_db, init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("Starting WangZhe Chess server...", version="0.1.0")
    try:
        db_config = DatabaseConfig(
            database_url=settings.database.url,
            pool_size=settings.database.POOL_SIZE,
            max_overflow=settings.database.MAX_OVERFLOW,
            pool_timeout=settings.database.POOL_TIMEOUT,
            pool_recycle=settings.database.POOL_RECYCLE,
            echo=settings.database.ECHO,
        )
        await init_db(db_config)
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running without database.")

    yield

    logger.info("Shutting down server...")
    try:
        await close_db()
    except Exception:
        pass
    logger.info("Server stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="王者之奕",
    description="自走棋游戏服务器",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
cors_config = settings.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)


# ============================================================================
# HTTP 路由
# ============================================================================


@app.get("/")
async def root() -> dict:
    """根路径"""
    return {
        "name": "王者之奕",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict:
    """健康检查"""
    return {"status": "healthy"}


# ============================================================================
# WebSocket 路由
# ============================================================================

from src.server.ws.handler import ws_handler
from src.shared.protocol import MessageType


def register_handlers():
    """注册所有消息处理器"""
    # 导入各处理器
    from src.server.ws.consumable_ws import ConsumableWSHandler
    from src.server.ws.emote_ws import EmoteWSHandler
    from src.server.ws.lineup_ws import LineupWSHandler
    from src.server.ws.spectator_ws import SpectatorWSHandler
    from src.server.ws.voting_ws import VotingWSHandler

    # 创建处理器实例
    consumable_handler = ConsumableWSHandler()
    emote_handler = EmoteWSHandler()
    lineup_handler = LineupWSHandler()
    spectator_handler = SpectatorWSHandler()
    voting_handler = VotingWSHandler()

    # 注册 consumable 处理器
    ws_handler._handlers[MessageType.GET_CONSUMABLES] = consumable_handler.handle_get_consumables
    ws_handler._handlers[MessageType.GET_PLAYER_CONSUMABLES] = consumable_handler.handle_get_player_consumables
    ws_handler._handlers[MessageType.BUY_CONSUMABLE] = consumable_handler.handle_buy_consumable

    # 注册 emote 处理器
    ws_handler._handlers[MessageType.GET_EMOTES] = emote_handler.handle_get_emotes
    ws_handler._handlers[MessageType.SEND_EMOTE] = emote_handler.handle_send_emote

    # 注册 lineup 处理器
    ws_handler._handlers[MessageType.LINEUP_SAVE] = lineup_handler.handle_save
    ws_handler._handlers[MessageType.LINEUP_LOAD] = lineup_handler.handle_load

    # 注册 spectator 处理器
    ws_handler._handlers[MessageType.GET_SPECTATABLE_GAMES] = spectator_handler.handle_get_spectatable_games

    # 注册 voting 处理器
    ws_handler._handlers[MessageType.GET_VOTING_LIST] = voting_handler.handle_get_voting_list

    print(f"✅ 已注册 {len(ws_handler._handlers) - 4} 个业务消息处理器, 当前共 {len(ws_handler._handlers)} 个")


# 注册处理器
register_handlers()


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str) -> None:
    """WebSocket 连接端点"""
    await ws_handler.handle_connection(websocket)


# ============================================================================
# API 路由
# ============================================================================

# from src.server.api import players, matches
# app.include_router(players.router, prefix="/api/players", tags=["players"])
# app.include_router(matches.router, prefix="/api/matches", tags=["matches"])


def main() -> None:
    """启动服务器"""
    import uvicorn

    uvicorn.run(
        "src.server.main:app",
        host=settings.server.HOST,
        port=settings.server.PORT,
        reload=settings.DEBUG,
        log_config=None,
    )


if __name__ == "__main__":
    main()
