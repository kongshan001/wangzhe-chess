"""
王者之奕 - FastAPI 应用入口

提供 HTTP API 和 WebSocket 服务
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import structlog

from config.settings import settings
from src.server.db.database import init_db, close_db, DatabaseConfig


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
    from src.server.ws.consumable_ws import ConsumableWSHandler
    
    handler = ConsumableWSHandler()
    
    # 注册 consumable 处理器 (使用MessageType枚举)
    ws_handler._handlers[MessageType.GET_CONSUMABLES] = handler.handle_get_consumables
    ws_handler._handlers[MessageType.GET_PLAYER_CONSUMABLES] = handler.handle_get_player_consumables
    ws_handler._handlers[MessageType.BUY_CONSUMABLE] = handler.handle_buy_consumable
    
    print(f"✅ 已注册 3 个消息处理器, 当前共 {len(ws_handler._handlers)} 个")


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
