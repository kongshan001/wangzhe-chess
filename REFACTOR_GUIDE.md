# wangzhe-chess 修复建议

## 问题1: Pydantic Enum 序列化失败

### 问题描述
`RankTier` (StrEnum) 直接用 `json.dumps()` 会失败:
```python
# 错误写法
return json.dumps(player_data)  # ❌ TypeError

# 正确写法
return json.dumps(player_data, default=lambda x: x.value if isinstance(x, StrEnum) else x)
```

### 修复代码 (src/server/models/player.py)

```python
import json
from enum import StrEnum

class RankTier(StrEnum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    MASTER = "master"
    GRANDMASTER = "grandmaster"
    KING = "king"

def enum_encoder(obj):
    """JSON 序列化编码器，支持 StrEnum"""
    if isinstance(obj, StrEnum):
        return obj.value
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# 使用方式
json.dumps(data, default=enum_encoder)

# 或使用 Pydantic 内置方法
from pydantic import BaseModel
class PlayerResponse(BaseModel):
    rank: RankTier
    
    class Config:
        json_encoders = {RankTier: lambda x: x.value}
```

---

## 问题2: WebSocket 重连逻辑缺失

### 问题描述
WebSocket 断开后无自动重连，无指数退避

### 修复代码 (src/server/game/gateway.py)

```python
import asyncio
import websockets

class GameGateway:
    def __init__(self, url: str):
        self.url = url
        self.ws = None
        self.reconnect_delay = 1  # 初始重连延迟(秒)
        self.max_reconnect_delay = 30  # 最大重连延迟
        self.max_retries = 10
        self.retry_count = 0
        
    async def connect(self):
        while self.retry_count < self.max_retries:
            try:
                self.ws = await websockets.connect(self.url)
                self.retry_count = 0
                self.reconnect_delay = 1
                print(f"Connected to {self.url}")
                return True
            except Exception as e:
                print(f"Connection failed: {e}")
                await self._handle_disconnect()
        return False
    
    async def _handle_disconnect(self):
        # 指数退避
        await asyncio.sleep(self.reconnect_delay)
        self.reconnect_delay = min(
            self.reconnect_delay * 2,  # 指数增长
            self.max_reconnect_delay
        )
        self.retry_count += 1
        print(f"Reconnecting in {self.reconnect_delay}s... (attempt {self.retry_count})")
```

---

## 问题3: 路由响应格式不统一

### 问题描述
部分 API 返回 JSON，部分返回字符串

### 修复代码 (src/server/api/players.py)

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class ApiResponse(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Any = None

    def to_json_response(self):
        return JSONResponse(
            content=self.model_dump(),
            status_code=self.code
        )

@router.get("/player/info")
async def get_player_info(player_id: int):
    player = get_player(player_id)
    if not player:
        return ApiResponse(
            code=404, 
            message="Player not found"
        ).to_json_response()
    
    return ApiResponse(
        data=player.to_dict()
    ).to_json_response()

# 全局异常处理
@router.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": str(exc), "data": None}
    )
```

---

## 总结

| 问题 | 修复方式 | 文件位置 |
|------|----------|----------|
| Enum 序列化 | 添加 `default` 编码器 | `src/server/models/player.py` |
| WebSocket 重连 | 指数退避重连 | `src/server/game/gateway.py` |
| 响应格式不统一 | 统一 ApiResponse 包装 | `src/server/api/players.py` |