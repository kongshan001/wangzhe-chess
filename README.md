# 王者之奕 - 生产级自走棋游戏

> 🎮 生产级自走棋游戏 Python 实现 | 87,600+ 行代码 | 支持 8 人在线对战

## 🎮 项目简介

王者之奕是一个**生产级**的自走棋（Auto Chess）游戏服务端实现，灵感来自王者荣耀的王者模拟战。项目采用 Python + FastAPI 技术栈，实现了完整的游戏逻辑和网络通信，支持 8 人在线对战。

### 项目亮点

- 🏗️ **完整的游戏系统** - 涵盖战斗、经济、羁绊、天赋、装备等核心玩法
- 🎯 **确定性战斗** - 可重现的战斗过程，支持回放和调试
- 🌐 **实时对战** - WebSocket 实现的流畅实时通信
- 📈 **可扩展架构** - 模块化设计，易于扩展和维护
- 📚 **完善文档** - 14+ 篇技术文档，详细的代码注释

### 核心特性

- 🎯 **确定性战斗模拟** - 保证相同输入产生相同输出，支持回放
- 🔄 **帧同步架构** - 混合帧同步与状态同步，优化网络传输
- 🏠 **房间管理** - 支持 8 人房间、观战、自定义房间
- 🎭 **羁绊系统** - 完整的种族/职业羁绊计算和效果应用
- 💰 **经济系统** - 连胜/连败奖励、利息机制、经验系统
- 📦 **共享英雄池** - 8 人共享英雄池抽取机制
- ⚔️ **天赋与装备** - 完整的天赋系统和装备合成系统
- 🎮 **实时对战** - WebSocket 支持的实时通信和观战
- 📊 **MMR 匹配** - 基于评分的智能匹配系统

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Gateway (WebSocket)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼───┐           ┌─────▼─────┐         ┌─────▼─────┐
│ Match │           │   Room    │         │   Game    │
│Service│           │  Service  │         │  Service  │
└───┬───┘           └─────┬─────┘         └─────┬─────┘
    │                     │                     │
    └─────────────────────┼─────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼───┐           ┌─────▼─────┐         ┌─────▼─────┐
│ Redis │           │   MySQL   │         │   MQ      │
│(缓存) │           │ (持久化)  │         │(消息队列) │
└───────┘           └───────────┘         └───────────┘
```

### 技术栈

#### 后端

- **框架**: FastAPI + Uvicorn
- **WebSocket**: python-socketio
- **数据库**: MySQL 8.0 + SQLAlchemy + Alembic
- **缓存**: Redis 7.2
- **消息队列**: 内置队列（可扩展为 RabbitMQ）
- **日志**: structlog（结构化日志）
- **测试**: pytest + pytest-asyncio

#### 基础设施

- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx（可选）
- **监控**: Prometheus + Grafana（推荐）
- **日志收集**: ELK Stack（可选）

### 核心模块

#### 1. 游戏引擎

- **战斗系统**: 确定性战斗模拟，支持回放
- **英雄池**: 8 人共享英雄池，支持抽卡和刷新
- **羁绊系统**: 种族/职业羁绊计算和效果应用
- **经济系统**: 连胜/连败、利息、经验系统

#### 2. 网络层

- **帧同步**: 混合帧同步与状态同步
- **房间管理**: 支持 8 人房间、观战、回放
- **匹配系统**: 基于 MMR 的智能匹配

#### 3. 持久化

- **数据库设计**: 优化的表结构和索引
- **缓存策略**: 多层缓存，减少数据库压力
- **数据迁移**: 使用 Alembic 管理数据库版本

## 📦 项目结构

```
wangzhe-chess/
├── src/
│   ├── server/                 # 服务端代码
│   │   ├── api/               # REST API
│   │   ├── ws/                # WebSocket handlers
│   │   ├── game/              # 游戏逻辑
│   │   │   ├── battle/        # 战斗系统
│   │   │   ├── hero_pool.py   # 英雄池管理
│   │   │   ├── synergy.py     # 羁绊系统
│   │   │   └── economy.py     # 经济系统
│   │   ├── room/              # 房间管理
│   │   ├── match/             # 匹配系统
│   │   └── models/            # 数据模型
│   ├── shared/                 # 共享代码
│   │   ├── protocol/          # 通信协议
│   │   ├── constants.py       # 常量定义
│   │   └── models.py          # 数据模型
│   └── client/                 # 客户端（可选）
├── tests/                      # 测试代码
├── docs/                       # 文档
│   └── technical-analysis.md   # 技术分析
├── pyproject.toml              # 项目配置
└── README.md                   # 本文件
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/wangzhe-chess.git
cd wangzhe-chess
```

#### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置（必须修改密钥和密码）
vim .env
```

**必须修改的配置**:
```bash
SECRET_KEY=your-secret-key-min-32-chars-change-me
DB_PASSWORD=your-secure-db-password
MYSQL_ROOT_PASSWORD=your-secure-root-password
```

#### 3. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f game-server
```

#### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{"status":"healthy","timestamp":"2024-01-01T12:00:00Z"}
```

### 方式二：本地开发

#### 1. 安装依赖

```bash
# 使用 uv (推荐)
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

#### 2. 启动依赖服务

```bash
# 启动 MySQL 和 Redis
docker compose up -d mysql redis
```

#### 3. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head
```

#### 4. 启动开发服务器

```bash
# 开发模式（热重载）
uvicorn src.server.main:app --reload --port 8000

# 或使用项目命令
wangzhe-server
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_game.py -v
```

### 访问应用

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

## 🎯 游戏机制

### 英雄系统

- **星级**: 1-3 星，3 个同名低星英雄可合成 1 个高星英雄
- **费用**: 1-5 金币，影响购买价格和刷新概率
- **属性**: HP、攻击力、防御力、攻速、技能

### 羁绊系统

- **种族羁绊**: 人族、神族、魔种、亡灵、精灵、兽族、机械、龙族、妖精
- **职业羁绊**: 战士、法师、刺客、射手、坦克、辅助、游侠、术士
- **效果**: 属性加成、特殊技能、被动效果

### 经济系统

- **基础收入**: 每回合 5 金币
- **利息**: 每 10 金币获得 1 利息（最高 5 金币）
- **连胜/连败奖励**: 最高 +3 金币
- **刷新商店**: 2 金币
- **购买经验**: 4 金币 = 4 经验

## 📖 部署指南

### 生产环境部署

详细的部署文档请参考: [docs/deployment.md](docs/deployment.md)

#### 系统要求

- **CPU**: 2 核以上（推荐 4 核）
- **内存**: 4 GB 以上（推荐 8 GB）
- **存储**: 20 GB SSD 以上
- **软件**: Docker >= 24.0, Docker Compose >= 2.20

#### 快速部署

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 修改必需配置

# 2. 构建并启动
docker compose up -d --build

# 3. 验证部署
curl http://localhost:8000/health

# 4. 查看日志
docker compose logs -f game-server
```

#### 生产环境配置清单

- [ ] 修改 `SECRET_KEY`（使用强密钥）
- [ ] 修改数据库密码
- [ ] 设置 `APP_ENV=production`
- [ ] 设置 `DEBUG=false`
- [ ] 配置 HTTPS（Nginx + Let's Encrypt）
- [ ] 配置防火墙规则
- [ ] 设置监控和告警
- [ ] 配置定时备份

### 运维手册

详细的运维指南请参考: [docs/operations.md](docs/operations.md)

#### 日常运维

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f game-server

# 重启服务
docker compose restart game-server

# 备份数据库
docker compose exec mysql mysqldump -uroot -p wangzhe > backup.sql

# 健康检查
curl http://localhost:8000/health
```

#### 监控指标

- HTTP 请求成功率和延迟
- WebSocket 连接数
- 数据库连接池使用率
- Redis 内存使用率
- 系统资源（CPU、内存、磁盘）

### 配置文档

详细的配置说明请参考: [docs/configuration.md](docs/configuration.md)

#### 核心配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | 应用密钥 | - |
| `DB_PASSWORD` | 数据库密码 | - |
| `SERVER_WORKERS` | 工作进程数 | 2 |
| `DB_POOL_SIZE` | 数据库连接池大小 | 10 |
| `REDIS_MAX_CONNECTIONS` | Redis 最大连接数 | 50 |

## 📊 项目统计

- **代码规模**: ~87,600 行 Python 代码
- **文件数量**: 1,593 个 Python 文件
- **文档数量**: 14+ 个技术文档
- **测试覆盖**: 持续完善中

## 🔧 开发状态

### ✅ 已完成

#### 核心游戏系统
- [x] 技术架构设计
- [x] 核心数据模型
- [x] 英雄池管理 (hero_pool.py)
- [x] 羁绊系统 (synergy.py) - 完整的种族/职业羁绊计算
- [x] 经济系统 (economy.py) - 连胜/连败、利息、经验
- [x] 天赋系统 (talent.py)
- [x] 装备系统 (equipment.py)
- [x] 合成系统 (crafting/)
- [x] 战斗模拟器 (battle/simulator.py) - 确定性战斗

#### 网络与通信
- [x] WebSocket 服务器 (ws/handler.py)
  - 自定义房间 (custom_room_ws.py)
  - 观战系统 (spectator_ws.py)
  - 表情系统 (emote_ws.py)
  - 排行榜 (leaderboard_ws.py)
  - 阵容推荐 (lineup_ws.py)
  - 羁绊图鉴 (synergypedia_ws.py)
  - 投票系统 (voting_ws.py)
  - 消耗品 (consumable_ws.py)

#### 房间与匹配
- [x] 房间管理 (room/manager.py, room/game_room.py)
- [x] 匹配系统 (match/queue.py)
- [x] MMR 评分系统 (match/elo.py, match/rating.py)

#### 基础设施
- [x] Docker 容器化配置
- [x] 完整的项目文档
  - [架构文档](docs/architecture.md)
  - [核心类说明](docs/core-classes.md)
  - [API 文档](docs/api/)
  - [部署指南](docs/deployment.md)
  - [配置说明](docs/configuration.md)
  - [性能报告](docs/performance-report.md)

### 🚧 进行中

- [ ] 测试覆盖率提升
- [ ] 性能优化
- [ ] 生产环境部署测试

### 📋 规划中

- [ ] 数据库持久化（部分完成）
- [ ] 监控告警系统
- [ ] 回放系统增强
- [ ] AI 对战机器人

## 📄 License

MIT License

## 📚 文档

### 核心文档
- [架构文档](docs/architecture.md) - 系统架构设计详解
- [核心类说明](docs/core-classes.md) - 核心类职责和方法
- [技术分析](docs/technical-analysis.md) - 技术架构分析
- [性能报告](docs/performance-report.md) - 性能测试和优化

### API 与协议
- [API 文档](docs/api/) - API 接口文档
  - [WebSocket 协议](docs/api/websocket-protocol.md)
  - [HTTP API](docs/api/http-api.md)

### 部署与运维
- [部署文档](docs/deployment.md) - 生产环境部署指南
- [配置文档](docs/configuration.md) - 环境变量和配置详解

### 游戏设计
- [游戏设计](docs/game-design.md) - 游戏机制设计
- [英雄设计](docs/hero-design.md) - 英雄属性和技能
- [平衡分析](docs/balance-analysis.md) - 游戏平衡性分析

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/your-org/wangzhe-chess/issues)
- **功能建议**: [GitHub Discussions](https://github.com/your-org/wangzhe-chess/discussions)
- **文档**: [在线文档](https://docs.example.com)

---

**Made with ❤️ by OpenClaw Team**
