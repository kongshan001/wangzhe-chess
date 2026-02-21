# API 接口文档

本目录包含王者之奕项目的所有 API 接口文档。

## 目录

- [HTTP API](./http-api.md) - RESTful HTTP 接口
- [WebSocket 协议](./websocket-protocol.md) - WebSocket 消息协议

## 基础信息

- **Base URL**: `http://localhost:8000`
- **WebSocket URL**: `ws://localhost:8000/ws/{player_id}`
- **Content-Type**: `application/json`
- **认证方式**: Token 认证（Header: `Authorization: Bearer <token>`）

## 响应格式

### 成功响应

```json
{
  "id": 1,
  "nickname": "棋圣",
  "avatar": "https://example.com/avatar.png"
}
```

### 错误响应

```json
{
  "detail": "错误描述",
  "code": "ERROR_CODE"
}
```

## 通用错误码

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
