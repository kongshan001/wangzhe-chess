# 配置文档

> 王者之奕系统配置详解

## 目录

- [环境变量说明](#环境变量说明)
- [配置文件详解](#配置文件详解)
- [调优参数](#调优参数)
- [配置最佳实践](#配置最佳实践)
- [配置验证](#配置验证)

---

## 环境变量说明

### 应用基础配置

| 变量名 | 类型 | 默认值 | 必需 | 说明 |
|--------|------|--------|------|------|
| `APP_ENV` | string | `development` | 是 | 运行环境: development, staging, production, testing |
| `DEBUG` | boolean | `true` | 是 | 调试模式（生产环境必须为 false） |
| `APP_NAME` | string | `王者之奕` | 否 | 应用名称 |
| `APP_VERSION` | string | `0.1.0` | 否 | 应用版本 |

**使用示例**:

```bash
# 开发环境
APP_ENV=development
DEBUG=true

# 生产环境
APP_ENV=production
DEBUG=false
```

**注意事项**:

- 生产环境 `DEBUG` 必须设置为 `false`，否则会暴露敏感信息
- `APP_ENV` 影响日志级别、错误处理等行为
- 不同环境应使用不同的配置文件

---

### 服务器配置

| 变量名 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| `SERVER_HOST` | string | `0.0.0.0` | - | 服务器绑定地址 |
| `SERVER_PORT` | integer | `8000` | 1-65535 | 服务器端口 |
| `SERVER_WORKERS` | integer | `2` | 1-64 | 工作进程数 |
| `SERVER_TIMEOUT` | integer | `120` | 1-3600 | 请求超时时间（秒） |
| `KEEP_ALIVE` | integer | `5` | 0-60 | Keep-Alive 超时（秒） |

**性能调优**:

```bash
# CPU 密集型任务
SERVER_WORKERS=2  # 建议: CPU 核心数 + 1

# I/O 密集型任务（数据库、网络请求多）
SERVER_WORKERS=8  # 建议: 2 * CPU 核心数

# 高并发场景
SERVER_WORKERS=16
SERVER_TIMEOUT=60
KEEP_ALIVE=10
```

**注意事项**:

- Worker 数量过多会增加内存消耗
- 超时时间设置过短会导致长请求失败
- Keep-Alive 过长会占用连接资源

---

### 安全配置

| 变量名 | 类型 | 默认值 | 必需 | 说明 |
|--------|------|--------|------|------|
| `SECRET_KEY` | string | - | **是** | 应用密钥，用于签名 Token |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `30` | 否 | 访问令牌过期时间（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | integer | `7` | 否 | 刷新令牌过期时间（天） |
| `CORS_ORIGINS` | string | `*` | 否 | 允许的跨域来源（逗号分隔） |
| `RATE_LIMIT_PER_MINUTE` | integer | `60` | 否 | 每分钟请求限制（0 表示不限制） |

**密钥生成**:

```bash
# 生成安全的 SECRET_KEY
openssl rand -hex 32

# 输出示例
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**CORS 配置**:

```bash
# 允许所有来源（开发环境）
CORS_ORIGINS=*

# 允许特定域名（生产环境）
CORS_ORIGINS=https://example.com,https://app.example.com

# 允许多个子域名
CORS_ORIGINS=https://*.example.com
```

**速率限制**:

```bash
# 开发环境不限制
RATE_LIMIT_PER_MINUTE=0

# 生产环境适度限制
RATE_LIMIT_PER_MINUTE=60

# 高安全要求场景
RATE_LIMIT_PER_MINUTE=30
```

---

### MySQL 数据库配置

| 变量名 | 类型 | 默认值 | 必需 | 说明 |
|--------|------|--------|------|------|
| `DB_HOST` | string | `mysql` | 是 | 数据库主机地址 |
| `DB_PORT` | integer | `3306` | 否 | 数据库端口 |
| `DB_NAME` | string | `wangzhe` | 是 | 数据库名称 |
| `DB_USER` | string | `wangzhe` | 是 | 数据库用户名 |
| `DB_PASSWORD` | string | - | **是** | 数据库密码 |
| `MYSQL_ROOT_PASSWORD` | string | - | **是** | MySQL root 密码（初始化用） |
| `DB_POOL_SIZE` | integer | `10` | 否 | 连接池大小 |
| `DB_MAX_OVERFLOW` | integer | `20` | 否 | 最大溢出连接数 |
| `DB_POOL_RECYCLE` | integer | `3600` | 否 | 连接回收时间（秒） |
| `DB_POOL_PRE_PING` | boolean | `true` | 否 | 连接前测试可用性 |
| `DB_ECHO` | boolean | `false` | 否 | 打印 SQL 语句（调试用） |

**连接池配置**:

```bash
# 小型应用
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# 中型应用
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# 大型应用
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

**连接池大小计算**:

```
连接池大小 = (核心数 * 2) + 有效磁盘数

示例（4 核 CPU）:
DB_POOL_SIZE = (4 * 2) + 1 = 9 ≈ 10
```

**注意事项**:

- 连接池大小过小会导致等待，过大浪费资源
- `DB_POOL_PRE_PING` 建议开启，避免使用失效连接
- `DB_POOL_RECYCLE` 应小于数据库 `wait_timeout`

---

### Redis 配置

| 变量名 | 类型 | 默认值 | 必需 | 说明 |
|--------|------|--------|------|------|
| `REDIS_HOST` | string | `redis` | 是 | Redis 主机地址 |
| `REDIS_PORT` | integer | `6379` | 否 | Redis 端口 |
| `REDIS_PASSWORD` | string | - | 否 | Redis 密码（生产环境建议设置） |
| `REDIS_DB` | integer | `0` | 0-15 | Redis 数据库编号 |
| `REDIS_MAX_CONNECTIONS` | integer | `50` | 否 | 最大连接数 |
| `REDIS_SOCKET_TIMEOUT` | integer | `5` | 否 | Socket 超时（秒） |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | integer | `5` | 否 | 连接超时（秒） |

**连接池配置**:

```bash
# 低并发场景
REDIS_MAX_CONNECTIONS=20

# 中等并发
REDIS_MAX_CONNECTIONS=50

# 高并发场景
REDIS_MAX_CONNECTIONS=100
```

**注意事项**:

- 连接池大小应与数据库连接池协调
- 生产环境建议设置密码
- 不同服务使用不同 `REDIS_DB` 隔离数据

---

### 游戏配置

| 变量名 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| `GAME_MAX_PLAYERS_PER_ROOM` | integer | `8` | 2-8 | 每个房间最大玩家数 |
| `GAME_TICK_RATE` | integer | `30` | 10-60 | 游戏帧率（FPS） |
| `GAME_ROUND_DURATION_SECONDS` | integer | `30` | 10-120 | 回合持续时间（秒） |
| `GAME_BUY_PHASE_DURATION` | integer | `30` | 15-60 | 购买阶段时长（秒） |
| `GAME_BATTLE_PHASE_DURATION` | integer | `60` | 30-120 | 战斗阶段时长（秒） |
| `GAME_STARTING_GOLD` | integer | `10` | 5-20 | 初始金币 |
| `GAME_STARTING_HEALTH` | integer | `100` | 50-200 | 初始生命值 |

**游戏平衡调整**:

```bash
# 快节奏模式
GAME_BUY_PHASE_DURATION=20
GAME_BATTLE_PHASE_DURATION=40

# 标准模式
GAME_BUY_PHASE_DURATION=30
GAME_BATTLE_PHASE_DURATION=60

# 慢节奏模式（新手友好）
GAME_BUY_PHASE_DURATION=45
GAME_BATTLE_PHASE_DURATION=90
```

**帧率影响**:

```bash
# 低帧率（节省资源）
GAME_TICK_RATE=20

# 标准帧率
GAME_TICK_RATE=30

# 高帧率（流畅体验）
GAME_TICK_RATE=60
```

---

### 日志配置

| 变量名 | 类型 | 默认值 | 可选值 | 说明 |
|--------|------|--------|--------|------|
| `LOG_LEVEL` | string | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL | 日志级别 |
| `LOG_FORMAT` | string | `text` | text, json | 日志格式 |
| `LOG_FILE` | string | `logs/app.log` | - | 日志文件路径 |
| `LOG_MAX_SIZE` | integer | `10` | 1-100 | 单文件最大大小（MB） |
| `LOG_BACKUP_COUNT` | integer | `5` | 1-20 | 日志备份数量 |

**日志级别选择**:

```bash
# 开发环境
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# 测试环境
LOG_LEVEL=INFO
LOG_FORMAT=text

# 生产环境
LOG_LEVEL=WARNING
LOG_FORMAT=json

# 故障排查
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

**注意事项**:

- 生产环境不要使用 DEBUG 级别，会影响性能
- JSON 格式便于日志收集和分析
- 合理设置文件大小和备份数量

---

## 配置文件详解

### Docker Compose 配置

#### 生产环境配置

`docker-compose.yml` 关键配置说明：

```yaml
services:
  game-server:
    # 环境变量
    environment:
      - APP_ENV=${APP_ENV:-production}
      # 使用 ${VAR:-default} 语法提供默认值
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s   # 检查间隔
      timeout: 10s    # 超时时间
      retries: 3      # 重试次数
      start_period: 10s  # 启动等待时间
    
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2'       # 最大 CPU
          memory: 1G      # 最大内存
        reservations:
          cpus: '0.5'     # 预留 CPU
          memory: 256M    # 预留内存
    
    # 日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"   # 单文件最大 10MB
        max-file: "5"     # 保留 5 个文件
```

#### 开发环境配置

`docker-compose.dev.yml` 添加开发工具：

```yaml
services:
  # Adminer - 数据库管理工具
  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
  
  # Redis Commander - Redis 管理工具
  redis-commander:
    image: rediscommander/redis-commander:latest
    environment:
      - REDIS_HOSTS=local:redis:6379
    ports:
      - "8081:8081"
```

### MySQL 配置文件

`docker/mysql/conf.d/my.cnf`:

```ini
[mysqld]
# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 连接配置
max_connections = 500
wait_timeout = 600
interactive_timeout = 600

# InnoDB 配置
innodb_buffer_pool_size = 1G
innodb_buffer_pool_instances = 4
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 查询缓存（MySQL 8.0 前版本）
query_cache_type = 1
query_cache_size = 64M

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/lib/mysql/slow.log
long_query_time = 2

# 二进制日志（用于主从复制和备份）
log_bin = mysql-bin
binlog_format = ROW
expire_logs_days = 7

[client]
default-character-set = utf8mb4
```

**配置说明**:

- `innodb_buffer_pool_size`: 设置为可用内存的 70-80%
- `innodb_flush_log_at_trx_commit`: 
  - `0`: 每秒刷新（性能好，可能丢数据）
  - `1`: 每次提交刷新（安全，性能差）
  - `2`: 每次提交写入 OS 缓存（平衡）

### Nginx 配置

如需反向代理，配置示例：

```nginx
upstream game_backend {
    least_conn;
    server game-server-1:8000 weight=5;
    server game-server-2:8000 weight=5;
    keepalive 32;
}

server {
    listen 80;
    server_name game.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name game.example.com;

    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/game.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/game.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 客户端配置
    client_max_body_size 10M;

    # 代理配置
    location / {
        proxy_pass http://game_backend;
        proxy_http_version 1.1;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 其他头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://game_backend/health;
        access_log off;
    }
}
```

### 日志配置

应用日志配置（Python structlog）：

```python
# src/server/core/logging.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # JSON 或控制台格式
            structlog.processors.JSONRenderer()
            if os.getenv("LOG_FORMAT") == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

---

## 调优参数

### 应用层调优

#### 1. Worker 数量优化

```bash
# CPU 密集型
SERVER_WORKERS = CPU_CORES + 1

# I/O 密集型
SERVER_WORKERS = 2 * CPU_CORES + 1

# 示例（4 核 CPU）
SERVER_WORKERS=9
```

#### 2. 连接池优化

**数据库连接池**:

```bash
# 公式
DB_POOL_SIZE = (CPU_CORES * 2) + DISK_COUNT

# 示例（4 核 CPU，1 块磁盘）
DB_POOL_SIZE=9
DB_MAX_OVERFLOW=18

# 生产环境建议
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

**Redis 连接池**:

```bash
# 建议：DB_POOL_SIZE * 1.5
REDIS_MAX_CONNECTIONS=30
```

#### 3. 超时时间优化

```bash
# 快速响应场景
SERVER_TIMEOUT=30
DB_POOL_TIMEOUT=10
REDIS_SOCKET_TIMEOUT=3

# 标准场景
SERVER_TIMEOUT=60
DB_POOL_TIMEOUT=30
REDIS_SOCKET_TIMEOUT=5

# 长连接场景
SERVER_TIMEOUT=120
DB_POOL_TIMEOUT=60
REDIS_SOCKET_TIMEOUT=10
```

### 数据库调优

#### 1. InnoDB 缓冲池

```ini
# 物理内存的 70-80%
innodb_buffer_pool_size = 2G

# 大缓冲池应设置多个实例
innodb_buffer_pool_instances = 4

# 日志文件大小（缓冲池的 25%）
innodb_log_file_size = 512M
```

#### 2. 连接数配置

```ini
# 最大连接数
max_connections = 500

# 用户连接限制
max_user_connections = 400

# 临时连接数（管理用）
extra_max_connections = 100
```

#### 3. 查询优化

```ini
# 排序缓冲
sort_buffer_size = 2M

# Join 缓冲
join_buffer_size = 2M

# 读缓冲
read_buffer_size = 1M
read_rnd_buffer_size = 1M
```

### Redis 调优

#### 1. 内存管理

```bash
# 最大内存
maxmemory 1gb

# 淘汰策略
# allkeys-lru: 淘汰最少使用的键
# volatile-lru: 淘汰最少使用的有过期时间的键
# allkeys-random: 随机淘汰
# volatile-random: 随机淘汰有过期时间的键
maxmemory-policy allkeys-lru
```

#### 2. 持久化策略

```bash
# RDB 快照
save 900 1      # 900 秒内至少 1 次修改
save 300 10     # 300 秒内至少 10 次修改
save 60 10000   # 60 秒内至少 10000 次修改

# AOF 持久化
appendonly yes
appendfsync everysec  # 每秒同步

# 混合持久化（Redis 4.0+）
aof-use-rdb-preamble yes
```

#### 3. 性能优化

```bash
# 最大连接数
maxclients 10000

# 超时时间
timeout 300

# TCP 配置
tcp-keepalive 60
tcp-backlog 511
```

### 系统调优

#### 1. 文件描述符

```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536

# 查看当前限制
ulimit -n
```

#### 2. 内核参数

```bash
# /etc/sysctl.conf
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# 文件系统
fs.file-max = 65535

# 应用
sysctl -p
```

#### 3. 磁盘 I/O

```bash
# 调整 I/O 调度器
echo noop > /sys/block/sda/queue/scheduler

# SSD 使用 deadline 或 noop
# HDD 使用 cfq
```

---

## 配置最佳实践

### 1. 分环境配置

```bash
# 开发环境
.env.development
docker-compose.dev.yml

# 测试环境
.env.testing
docker-compose.test.yml

# 生产环境
.env.production
docker-compose.yml
```

### 2. 敏感信息管理

#### 使用 Docker Secrets

```yaml
# docker-compose.yml
services:
  game-server:
    secrets:
      - db_password
      - redis_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
```

#### 使用 Vault

```bash
# 从 Vault 读取密钥
export DB_PASSWORD=$(vault kv get -field=password secret/wangzhe/db)
```

### 3. 配置验证

#### 启动前检查

```bash
# 检查必需的环境变量
./scripts/check-config.sh
```

创建 `scripts/check-config.sh`:

```bash
#!/bin/bash
# 配置验证脚本

set -e

echo "检查配置..."

# 必需的环境变量
required_vars=(
    "SECRET_KEY"
    "DB_PASSWORD"
    "MYSQL_ROOT_PASSWORD"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ 缺少必需的环境变量:"
    printf '  - %s\n' "${missing_vars[@]}"
    exit 1
fi

# 检查 SECRET_KEY 长度
if [ ${#SECRET_KEY} -lt 32 ]; then
    echo "❌ SECRET_KEY 长度必须至少 32 个字符"
    exit 1
fi

# 检查生产环境配置
if [ "$APP_ENV" = "production" ]; then
    if [ "$DEBUG" = "true" ]; then
        echo "❌ 生产环境不能启用 DEBUG 模式"
        exit 1
    fi
    
    if [ "$SECRET_KEY" = "your-secret-key-change-in-production-min-32-chars!!" ]; then
        echo "❌ 生产环境必须修改默认 SECRET_KEY"
        exit 1
    fi
fi

echo "✅ 配置检查通过"
```

### 4. 配置文档化

#### 创建配置清单

`docs/config-checklist.md`:

```markdown
# 配置清单

## 开发环境

- [ ] 复制 .env.example 到 .env
- [ ] 设置 DEBUG=true
- [ ] 设置 APP_ENV=development

## 测试环境

- [ ] 设置 APP_ENV=testing
- [ ] 设置独立的数据库
- [ ] 配置测试数据

## 生产环境

- [ ] 生成强密钥
- [ ] 设置 APP_ENV=production
- [ ] 设置 DEBUG=false
- [ ] 配置 HTTPS
- [ ] 配置防火墙
- [ ] 配置监控告警
```

---

## 配置验证

### 自动化验证脚本

创建 `scripts/validate-config.py`:

```python
#!/usr/bin/env python3
"""配置验证脚本"""

import os
import sys
from typing import Dict, List, Tuple

class ConfigValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> bool:
        """运行所有验证"""
        self.check_required_vars()
        self.check_secret_key()
        self.check_database_config()
        self.check_redis_config()
        self.check_game_config()
        self.check_production_config()
        
        return len(self.errors) == 0
    
    def check_required_vars(self):
        """检查必需的环境变量"""
        required = [
            'SECRET_KEY',
            'DB_PASSWORD',
            'MYSQL_ROOT_PASSWORD',
        ]
        
        for var in required:
            if not os.getenv(var):
                self.errors.append(f"缺少必需的环境变量: {var}")
    
    def check_secret_key(self):
        """检查 SECRET_KEY"""
        secret_key = os.getenv('SECRET_KEY', '')
        
        if len(secret_key) < 32:
            self.errors.append("SECRET_KEY 长度必须至少 32 个字符")
        
        if secret_key in ['your-secret-key', 'test', 'dev']:
            self.warnings.append("SECRET_KEY 过于简单")
    
    def check_database_config(self):
        """检查数据库配置"""
        pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        
        if pool_size < 1 or pool_size > 100:
            self.errors.append(f"DB_POOL_SIZE 范围应为 1-100，当前: {pool_size}")
        
        if max_overflow < 0 or max_overflow > 200:
            self.errors.append(f"DB_MAX_OVERFLOW 范围应为 0-200，当前: {max_overflow}")
    
    def check_redis_config(self):
        """检查 Redis 配置"""
        redis_db = int(os.getenv('REDIS_DB', '0'))
        
        if redis_db < 0 or redis_db > 15:
            self.errors.append(f"REDIS_DB 范围应为 0-15，当前: {redis_db}")
    
    def check_game_config(self):
        """检查游戏配置"""
        tick_rate = int(os.getenv('GAME_TICK_RATE', '30'))
        players = int(os.getenv('GAME_MAX_PLAYERS_PER_ROOM', '8'))
        
        if tick_rate not in [10, 20, 30, 60]:
            self.warnings.append(f"GAME_TICK_RATE 建议 10/20/30/60，当前: {tick_rate}")
        
        if players < 2 or players > 8:
            self.errors.append(f"GAME_MAX_PLAYERS_PER_ROOM 范围应为 2-8，当前: {players}")
    
    def check_production_config(self):
        """检查生产环境配置"""
        app_env = os.getenv('APP_ENV', 'development')
        
        if app_env == 'production':
            debug = os.getenv('DEBUG', 'false').lower()
            if debug == 'true':
                self.errors.append("生产环境不能启用 DEBUG 模式")
            
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            if log_level == 'DEBUG':
                self.warnings.append("生产环境建议不使用 DEBUG 日志级别")
    
    def print_results(self):
        """打印验证结果"""
        if self.errors:
            print("❌ 配置错误:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("⚠️  配置警告:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ 配置验证通过")

def main():
    validator = ConfigValidator()
    is_valid = validator.validate()
    validator.print_results()
    
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
```

使用方式：

```bash
python scripts/validate-config.py
```

---

## 常见配置问题

### 1. 数据库连接失败

**原因**:
- 密码错误
- 网络不通
- 防火墙阻止
- 连接数耗尽

**解决**:

```bash
# 测试连接
docker compose exec mysql mysql -uwangzhe -p -e "SELECT 1"

# 检查连接数
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST"

# 检查防火墙
sudo iptables -L -n | grep 3306
```

### 2. Redis 连接超时

**原因**:
- Redis 未启动
- 密码错误
- 内存不足
- 网络问题

**解决**:

```bash
# 测试连接
docker compose exec redis redis-cli ping

# 检查内存
docker compose exec redis redis-cli info memory

# 查看慢查询
docker compose exec redis redis-cli slowlog get 10
```

### 3. 应用启动失败

**原因**:
- 环境变量未设置
- 端口被占用
- 依赖服务未启动

**解决**:

```bash
# 检查环境变量
docker compose config

# 检查端口
netstat -tlnp | grep 8000

# 查看日志
docker compose logs game-server
```

---

## 附录

### 环境变量完整清单

详见 `.env.example` 文件

### 配置模板

- `.env.development.template`
- `.env.production.template`
- `docker-compose.override.yml.template`

### 配置变更流程

1. 修改配置文件
2. 运行验证脚本
3. 在测试环境验证
4. 应用到生产环境
5. 监控服务状态
6. 记录配置变更

---

**最后更新**: 2024-01-01  
**版本**: v0.1.0
