# 王者之奕 - 自走棋游戏技术分析

## 1. 游戏核心机制分析

### 1.1 棋盘系统
- **规格**: 标准8x8或6x7六边形棋盘
- **格子类型**: 普通格子、特殊格子（如加成格）
- **部署区域**: 玩家准备区域 vs 战斗区域

### 1.2 英雄系统
- **星级系统**: 1-3星（3个同名1星=1个2星）
- **属性**: HP、攻击力、防御力、攻速、技能
- **职业/种族**: 决定羁绊效果
- **费用**: 1-5费，影响购买价格和刷新概率

### 1.3 羁绊系统
- **种族羁绊**: 同种族英雄达到数量触发
- **职业羁绊**: 同职业英雄达到数量触发
- **效果类型**: 属性加成、特殊技能、被动效果

### 1.4 经济系统
- **金币来源**: 回合基础收入、连胜/连败奖励、利息（最高5金币）
- **金币用途**: 购买英雄(1-5金币)、刷新商店(2金币)、购买经验(4金币)
- **等级系统**: 影响上场英雄数量和刷新概率

### 1.5 战斗系统
- **战斗模式**: 自动战斗，英雄自动寻敌攻击
- **技能释放**: 蓝条满后自动释放
- **伤害计算**: 物理伤害、法术伤害、真实伤害
- **胜负判定**: 存活英雄数量决定伤害

### 1.6 游戏流程
1. 准备阶段（30秒）：购买、部署、升级
2. 战斗阶段（自动）：与其他玩家对战
3. 结算阶段：计算伤害、发放奖励
4. 循环直到最后存活

---

## 2. 帧同步 vs 状态同步技术选择

### 2.1 帧同步 (Frame Synchronization)
**原理**: 所有客户端只发送操作指令，本地模拟游戏逻辑

**优点**:
- 网络流量小（只传输操作）
- 服务器负载低
- 回放功能易实现

**缺点**:
- 浮点数精度问题（需定点数）
- 需要确保所有客户端确定性
- 网络抖动影响大

### 2.2 状态同步 (State Synchronization)
**原理**: 服务器计算游戏状态，广播给客户端

**优点**:
- 安全性高（逻辑在服务器）
- 易于防作弊
- 客户端简单

**缺点**:
- 网络流量大
- 服务器负载高
- 延迟敏感

### 2.3 推荐方案: 混合同步
- **准备阶段**: 状态同步（玩家操作不频繁）
- **战斗阶段**: 帧同步（自动战斗，输入确定）
- **关键状态**: 服务器校验和存储

**理由**:
1. 自走棋战斗阶段输入确定性高
2. 准备阶段需要实时同步其他玩家状态
3. 减少服务器计算压力
4. 便于反作弊

---

## 3. 服务器架构设计

### 3.1 整体架构
```
                    ┌─────────────┐
                    │   Gateway   │ WebSocket/API Gateway
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐      ┌────▼────┐
   │ Match   │       │  Room     │      │  Game   │
   │ Service │       │  Service  │      │ Service │
   └────┬────┘       └─────┬─────┘      └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐      ┌────▼────┐
   │  Redis  │       │  MySQL    │      │  MQ     │
   │ (缓存)  │       │ (持久化)  │      │(消息队列)│
   └─────────┘       └───────────┘      └─────────┘
```

### 3.2 匹配系统 (Match Service)
**功能**:
- 玩家排队匹配
- ELO/段位匹配
- 房间分配

**数据结构**:
```python
class MatchQueue:
    queue: List[Player]  # 按段位排序
    match_config: MatchConfig  # 匹配配置
```

**算法**:
- 分段位队列
- 扩大搜索范围机制
- 超时保护（AI填充）

### 3.3 房间管理 (Room Service)
**功能**:
- 8人房间管理
- 玩家状态同步
- 回合控制

**状态机**:
```
WAITING → PREPARING → BATTLING → SETTLING → [GAME_OVER | PREPARING]
```

**数据结构**:
```python
class Room:
    room_id: str
    players: List[Player]
    state: RoomState
    current_round: int
    shop_pool: List[Hero]  # 共享英雄池
```

### 3.4 游戏服务 (Game Service)
**功能**:
- 战斗逻辑模拟
- 羁绊计算
- 伤害结算

**核心类**:
```python
class BattleSimulator:
    def simulate(self, board_a: Board, board_b: Board) -> BattleResult:
        # 确定性战斗模拟
        pass

class SynergyCalculator:
    def calculate(self, heroes: List[Hero]) -> List[Buff]:
        # 计算激活的羁绊
        pass
```

### 3.5 广播机制
**WebSocket事件**:
```python
# 房间事件
ROOM_JOIN, ROOM_LEAVE, ROOM_STATE_CHANGE

# 游戏事件
ROUND_START, ROUND_END, SHOP_REFRESH
HERO_BUY, HERO_SELL, HERO_PLACE
BATTLE_START, BATTLE_UPDATE, BATTLE_END

# 系统事件
PLAYER_DAMAGE, PLAYER_DIE, GAME_OVER
```

---

## 4. 微信小游戏技术限制与优化

### 4.1 技术限制
- **包大小**: 主包4MB，总分包20MB
- **内存**: iOS 2GB限制，Android设备差异大
- **网络**: 需使用wx.request，WebSocket有连接数限制
- **渲染**: Canvas/WebGL性能受限
- **存储**: 本地存储10MB限制

### 4.2 优化策略

**资源优化**:
- 图片压缩、图集打包
- 音频压缩、按需加载
- 资源远程加载

**渲染优化**:
- 对象池复用
- 脏矩形渲染
- LOD（细节层次）
- 遮挡剔除

**网络优化**:
- 协议压缩（Protobuf）
- 增量同步
- 预测回滚

**内存优化**:
- 资源卸载
- 分帧加载
- 内存监控

---

## 5. 生产环境组件

### 5.1 数据库设计 (MySQL)

**核心表**:
```sql
-- 玩家表
CREATE TABLE players (
    id BIGINT PRIMARY KEY,
    openid VARCHAR(64) UNIQUE,
    nickname VARCHAR(64),
    avatar VARCHAR(256),
    elo INT DEFAULT 1000,
    level INT DEFAULT 1,
    exp INT DEFAULT 0,
    gold INT DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 对局记录
CREATE TABLE matches (
    id BIGINT PRIMARY KEY,
    room_id VARCHAR(64),
    players JSON,  -- 玩家快照
    result JSON,   -- 对局结果
    duration INT,
    created_at TIMESTAMP
);

-- 英雄配置
CREATE TABLE heroes (
    id INT PRIMARY KEY,
    name VARCHAR(64),
    cost INT,
    race VARCHAR(64),
    profession VARCHAR(64),
    hp INT,
    attack INT,
    defense INT,
    attack_speed DECIMAL(3,2),
    skill JSON,
    created_at TIMESTAMP
);
```

### 5.2 缓存设计 (Redis)

**缓存结构**:
```
# 玩家在线状态
player:online:{player_id} → timestamp (TTL: 5min)

# 玩家数据缓存
player:data:{player_id} → JSON (TTL: 1hour)

# 房间状态
room:{room_id}:state → JSON
room:{room_id}:players → SET

# 匹配队列
match:queue:{tier} → ZSET (score: timestamp)

# 全局英雄池
game:hero_pool → SET
```

### 5.3 消息队列 (可选)

**用途**:
- 异步任务（结算、奖励发放）
- 事件广播
- 日志收集

**队列设计**:
```
match.result → 对局结果处理
player.reward → 奖励发放
analytics.event → 数据分析
```

### 5.4 监控告警

**指标监控**:
- 在线人数
- 匹配成功率/时间
- 房间创建/销毁速率
- 服务器CPU/内存
- 网络延迟
- 错误率

**工具选择**:
- Prometheus + Grafana
- 日志: ELK / Loki
- 告警: AlertManager

---

## 6. Python技术栈选择

### 6.1 推荐技术栈

**后端框架**: FastAPI
- 异步支持好
- 类型提示
- 自动文档
- 性能优秀

**WebSocket**: python-socketio / fastapi-websocket
- 房间管理
- 命名空间
- 断线重连

**数据库**:
- ORM: SQLAlchemy 2.0 (async)
- 迁移: Alembic

**缓存**: aioredis / redis-py

**序列化**: Pydantic + Protobuf

**测试**: pytest + pytest-asyncio

### 6.2 项目结构
```
wangzhe-chess/
├── src/
│   ├── server/
│   │   ├── api/          # REST API
│   │   ├── ws/           # WebSocket handlers
│   │   ├── game/         # 游戏逻辑
│   │   │   ├── battle/   # 战斗系统
│   │   │   ├── hero/     # 英雄系统
│   │   │   ├── synergy/  # 羁绊系统
│   │   │   └── economy/  # 经济系统
│   │   ├── room/         # 房间管理
│   │   ├── match/        # 匹配系统
│   │   └── models/       # 数据模型
│   ├── shared/
│   │   ├── protocol/     # 通信协议
│   │   └── constants/    # 常量定义
│   └── client/           # 客户端（可选）
├── tests/
├── docs/
├── scripts/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 7. 实现优先级

### Phase 1: 核心游戏逻辑 (MVP)
1. 英雄数据模型和配置
2. 棋盘和部署系统
3. 羁绊计算
4. 战斗模拟器（确定性）
5. 经济系统

### Phase 2: 网络层
1. WebSocket服务器
2. 房间管理
3. 匹配系统
4. 状态同步

### Phase 3: 持久化
1. 数据库设计
2. 玩家数据存储
3. 对局记录

### Phase 4: 生产化
1. Docker化
2. 监控集成
3. 负载测试
4. 安全加固

---

## 8. 关键技术难点

### 8.1 确定性战斗模拟
- 使用定点数或整数运算
- 随机数种子同步
- 状态快照对比

### 8.2 断线重连
- 状态快照保存
- 快进机制
- 数据差异同步

### 8.3 防作弊
- 服务端校验关键操作
- 行为分析
- 异常检测

### 8.4 性能优化
- 战斗模拟并行化
- 缓存策略
- 连接池管理
