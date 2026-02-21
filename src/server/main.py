"""
王者之奕 - FastAPI 应用入口

提供 HTTP API 和 WebSocket 服务
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from config.settings import settings
from src.server.db.database import init_db, close_db


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting WangZhe Chess server...", version="0.1.0")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # 关闭时
    logger.info("Shutting down server...")
    await close_db()
    logger.info("Server stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="王者之奕",
    description="自走棋游戏服务器",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

from fastapi import WebSocket, WebSocketDisconnect
from src.server.ws.handler import WebSocketHandler

ws_handler = WebSocketHandler()


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str) -> None:
    """
    WebSocket 连接端点
    
    Args:
        websocket: WebSocket 连接
        player_id: 玩家ID
    """
    await ws_handler.connect(websocket, player_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_handler.handle_message(player_id, data)
    except WebSocketDisconnect:
        await ws_handler.disconnect(player_id)


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
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # 使用 structlog
    )


if __name__ == "__main__":
    main()
