# 部署文档

> 王者之奕生产环境部署指南

## 目录

- [系统要求](#系统要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [部署命令](#部署命令)
- [健康检查](#健康检查)
- [升级与回滚](#升级与回滚)
- [性能优化](#性能优化)
- [安全加固](#安全加固)

---

## 系统要求

### 硬件要求

#### 最低配置（开发/测试环境）

- **CPU**: 2 核
- **内存**: 4 GB
- **存储**: 20 GB SSD
- **网络**: 10 Mbps

#### 推荐配置（生产环境）

- **CPU**: 4 核或更多
- **内存**: 8 GB 或更多
- **存储**: 50 GB SSD（建议 100 GB）
- **网络**: 100 Mbps 或更高

### 软件要求

#### 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Docker | >= 24.0 | 容器运行时 |
| Docker Compose | >= 2.20 | 容器编排工具 |
| Git | >= 2.30 | 版本控制 |

#### 可选软件

| 软件 | 用途 |
|------|------|
| Nginx | 反向代理、负载均衡 |
| Certbot | SSL 证书管理 |
| Prometheus | 监控指标收集 |
| Grafana | 监控可视化 |
| ELK Stack | 日志收集和分析 |

### 操作系统支持

- **Linux**: Ubuntu 22.04+、CentOS 8+、Debian 11+
- **macOS**: 12+ (仅开发环境)
- **Windows**: Windows 10+ with WSL2 (仅开发环境)

### 网络要求

#### 端口配置

| 端口 | 服务 | 访问级别 | 说明 |
|------|------|---------|------|
| 8000 | Game Server | 公网 | HTTP/WebSocket 服务 |
| 3306 | MySQL | 内网 | 数据库服务（不暴露公网）|
| 6379 | Redis | 内网 | 缓存服务（不暴露公网）|

#### 防火墙规则

```bash
# 开放游戏服务器端口
sudo ufw allow 8000/tcp

# 允许 Docker 内部通信
sudo ufw allow from 172.16.0.0/12
sudo ufw allow from 192.168.0.0/16

# 启用防火墙
sudo ufw enable
```

---

## 安装步骤

### 1. 环境准备

#### 1.1 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户加入 docker 组
sudo usermod -aG docker $USER

# 重新登录使权限生效
exit
# 重新登录

# 验证安装
docker --version
docker compose version
```

#### 1.2 安装 Git

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install git -y

# 验证安装
git --version
```

### 2. 获取代码

```bash
# 克隆代码仓库
git clone https://github.com/your-org/wangzhe-chess.git
cd wangzhe-chess

# 查看最新版本
git tag

# 切换到稳定版本（推荐）
git checkout v0.1.0
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

#### 必须修改的配置项

```bash
# 应用密钥（必须修改！）
SECRET_KEY=your-secret-key-min-32-chars-change-me

# 数据库密码（必须修改！）
DB_PASSWORD=your-secure-db-password
MYSQL_ROOT_PASSWORD=your-secure-root-password

# Redis 密码（生产环境建议设置）
REDIS_PASSWORD=your-redis-password

# 运行环境
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

#### 生成安全密钥

```bash
# 生成 SECRET_KEY
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 24
```

### 4. 初始化数据库

```bash
# 首次部署需要初始化数据库
# Docker Compose 会自动创建数据库和表结构

# 如需手动执行数据库迁移
docker compose exec game-server alembic upgrade head
```

### 5. 启动服务

```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f game-server
```

---

## 配置说明

### 环境变量配置

详见 [配置文档](./configuration.md)

### Docker Compose 配置

#### 生产环境配置

`docker-compose.yml` 已针对生产环境优化：

- **健康检查**: 自动检测服务健康状态
- **资源限制**: 防止资源耗尽
- **日志轮转**: 自动清理旧日志
- **安全配置**: 最小权限原则
- **重启策略**: 自动重启失败服务

#### 开发环境配置

使用 `docker-compose.dev.yml`:

```bash
# 启动开发环境（包含调试工具）
docker compose -f docker-compose.dev.yml up -d
```

### 数据库配置

#### MySQL 配置优化

编辑 `docker/mysql/conf.d/my.cnf`:

```ini
[mysqld]
# 连接配置
max_connections = 500
wait_timeout = 600

# 缓冲池配置（建议设置为可用内存的 70-80%）
innodb_buffer_pool_size = 1G
innodb_buffer_pool_instances = 4

# 日志配置
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 慢查询日志
slow_query_log = 1
long_query_time = 2
```

#### Redis 配置优化

在 `docker-compose.yml` 中已配置:

```yaml
command: >
  redis-server
  --appendonly yes
  --appendfsync everysec
  --maxmemory 256mb
  --maxmemory-policy allkeys-lru
```

---

## 部署命令

### 基础命令

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启服务
docker compose restart

# 重启单个服务
docker compose restart game-server

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f [service-name]
```

### 部署流程

#### 首次部署

```bash
# 1. 拉取代码
git clone https://github.com/your-org/wangzhe-chess.git
cd wangzhe-chess

# 2. 配置环境变量
cp .env.example .env
vim .env  # 修改必要配置

# 3. 构建并启动
docker compose up -d --build

# 4. 验证服务
curl http://localhost:8000/health

# 5. 查看日志
docker compose logs -f game-server
```

#### 更新部署

```bash
# 1. 备份数据（重要！）
docker compose exec mysql mysqldump -u root -p wangzhe > backup-$(date +%Y%m%d-%H%M%S).sql

# 2. 拉取最新代码
git pull origin main
# 或切换到指定版本
git checkout v0.2.0

# 3. 重新构建并启动
docker compose up -d --build

# 4. 执行数据库迁移（如有）
docker compose exec game-server alembic upgrade head

# 5. 验证服务
curl http://localhost:8000/health

# 6. 查看日志确认正常
docker compose logs -f game-server
```

#### 滚动更新（零停机）

```bash
# 1. 构建新镜像
docker compose build game-server

# 2. 逐个更新容器
docker compose up -d --no-deps --build game-server

# 3. 等待健康检查通过
# Docker 会自动等待新容器健康后才停止旧容器
```

---

## 健康检查

### 自动健康检查

Docker Compose 已配置健康检查，自动监控服务状态：

- **game-server**: 每 30 秒检查 `/health` 端点
- **mysql**: 每 10 秒执行 `mysqladmin ping`
- **redis**: 每 10 秒执行 `redis-cli ping`

### 手动健康检查

#### 检查服务状态

```bash
# 查看所有服务健康状态
docker compose ps

# 输出示例：
# NAME                STATUS
# wangzhe-server      Up 2 hours (healthy)
# wangzhe-mysql       Up 2 hours (healthy)
# wangzhe-redis       Up 2 hours (healthy)
```

#### 检查应用健康

```bash
# HTTP 健康检查
curl http://localhost:8000/health

# 预期响应：
# {"status":"healthy","timestamp":"2024-01-01T12:00:00Z","services":{"database":"ok","redis":"ok"}}

# 检查 API 版本
curl http://localhost:8000/api/v1/version
```

#### 检查数据库连接

```bash
# MySQL 连接检查
docker compose exec mysql mysql -uwangzhe -p -e "SELECT 1"

# Redis 连接检查
docker compose exec redis redis-cli ping
# 预期响应: PONG
```

#### 检查 WebSocket 连接

```bash
# 使用 wscat 测试 WebSocket 连接
npm install -g wscat
wscat -c ws://localhost:8000/ws

# 或使用 Python
python3 << EOF
import websocket
ws = websocket.create_connection("ws://localhost:8000/ws")
print("WebSocket connected!")
ws.close()
EOF
```

### 监控脚本

创建健康检查脚本 `scripts/health-check.sh`:

```bash
#!/bin/bash
set -e

echo "=== 王者之奕健康检查 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# 检查 Docker 服务
echo "1. 检查 Docker 服务..."
if docker compose ps | grep -q "Up"; then
    echo "✅ Docker 服务运行中"
else
    echo "❌ Docker 服务未运行"
    exit 1
fi

# 检查应用健康
echo "2. 检查应用健康..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 应用健康"
else
    echo "❌ 应用不健康"
    exit 1
fi

# 检查数据库
echo "3. 检查数据库..."
if docker compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} > /dev/null 2>&1; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 数据库连接失败"
    exit 1
fi

# 检查 Redis
echo "4. 检查 Redis..."
if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis 连接正常"
else
    echo "❌ Redis 连接失败"
    exit 1
fi

echo
echo "✅ 所有检查通过！"
```

使用方式：

```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

---

## 升级与回滚

### 版本升级

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取新版本代码
git fetch --tags
git checkout v0.2.0

# 3. 查看变更日志
cat CHANGELOG.md

# 4. 更新配置（如有新配置项）
vim .env

# 5. 重新部署
docker compose up -d --build

# 6. 执行数据库迁移
docker compose exec game-server alembic upgrade head

# 7. 验证升级
curl http://localhost:8000/health
docker compose logs -f game-server
```

### 版本回滚

```bash
# 1. 停止当前服务
docker compose down

# 2. 切换到旧版本
git checkout v0.1.0

# 3. 恢复数据库（如需要）
docker compose up -d mysql redis
sleep 10
docker compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} wangzhe < backup-20240101.sql

# 4. 启动服务
docker compose up -d

# 5. 验证回滚
curl http://localhost:8000/health
```

---

## 性能优化

### 应用层优化

1. **调整 Worker 数量**

   ```bash
   # .env
   SERVER_WORKERS=4  # 建议: 2 * CPU 核心数
   ```

2. **启用 Gzip 压缩**

   在应用代码中已默认启用

3. **调整连接池**

   ```bash
   # .env
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40
   REDIS_MAX_CONNECTIONS=100
   ```

### 数据库优化

1. **调整缓冲池**

   ```ini
   # my.cnf
   innodb_buffer_pool_size = 2G  # 设置为可用内存的 70-80%
   innodb_buffer_pool_instances = 4
   ```

2. **优化查询**

   - 添加必要的索引
   - 使用 EXPLAIN 分析慢查询
   - 定期优化表

3. **连接池配置**

   ```bash
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40
   DB_POOL_RECYCLE=3600
   ```

### Redis 优化

1. **内存管理**

   ```bash
   # .env
   REDIS_MAXMEMORY=512mb
   ```

2. **持久化策略**

   ```yaml
   # docker-compose.yml
   command: >
     redis-server
     --appendonly yes
     --appendfsync everysec
   ```

### 系统层优化

1. **增加文件描述符限制**

   ```bash
   # /etc/security/limits.conf
   * soft nofile 65536
   * hard nofile 65536
   ```

2. **调整内核参数**

   ```bash
   # /etc/sysctl.conf
   net.core.somaxconn = 65535
   net.ipv4.tcp_max_syn_backlog = 65535
   net.ipv4.ip_local_port_range = 1024 65535
   ```

---

## 安全加固

### 网络安全

1. **配置防火墙**

   ```bash
   # 仅开放必要端口
   sudo ufw default deny incoming
   sudo ufw allow ssh
   sudo ufw allow 8000/tcp
   sudo ufw enable
   ```

2. **启用 HTTPS**

   使用 Nginx 反向代理：

   ```nginx
   server {
       listen 443 ssl http2;
       server_name game.example.com;

       ssl_certificate /etc/letsencrypt/live/game.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/game.example.com/privkey.pem;

       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **隐藏内部服务**

   不要暴露 MySQL 和 Redis 端口到公网

### 应用安全

1. **使用强密钥**

   ```bash
   # 生成强密钥
   openssl rand -hex 32
   ```

2. **定期更新依赖**

   ```bash
   # 检查安全更新
   docker compose run --rm game-server pip-audit

   # 更新依赖
   pip install --upgrade package-name
   docker compose build --no-cache game-server
   ```

3. **启用速率限制**

   ```bash
   # .env
   RATE_LIMIT_PER_MINUTE=60
   ```

### 数据安全

1. **定期备份**

   ```bash
   # 设置每日自动备份
   crontab -e
   # 添加：
   0 2 * * * /path/to/wangzhe-chess/scripts/backup.sh
   ```

2. **加密备份**

   ```bash
   # 加密备份文件
   gpg -c backup-$(date +%Y%m%d).sql
   ```

3. **敏感信息管理**

   - 使用 Docker Secrets
   - 或使用 HashiCorp Vault
   - 不要在代码中硬编码密钥

### 容器安全

1. **使用非 root 用户**

   Dockerfile 中已配置 `USER wangzhe`

2. **只读文件系统**（可选）

   ```yaml
   # docker-compose.yml
   read_only: true
   tmpfs:
     - /tmp
   ```

3. **限制能力**

   ```yaml
   # docker-compose.yml
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE
   ```

---

## 常见问题

### 1. 服务启动失败

**症状**: `docker compose up -d` 后服务无法启动

**排查步骤**:

```bash
# 查看详细日志
docker compose logs game-server

# 检查配置文件
docker compose config

# 检查端口占用
netstat -tlnp | grep 8000

# 检查环境变量
docker compose exec game-server env | grep -E 'DB_|REDIS_|SECRET'
```

### 2. 数据库连接失败

**症状**: 应用日志显示数据库连接错误

**排查步骤**:

```bash
# 检查 MySQL 容器状态
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 测试数据库连接
docker compose exec mysql mysql -uwangzhe -p -e "SELECT 1"

# 检查网络连通性
docker compose exec game-server ping mysql
```

### 3. 健康检查失败

**症状**: `docker compose ps` 显示 "unhealthy"

**排查步骤**:

```bash
# 手动执行健康检查命令
docker compose exec game-server curl -f http://localhost:8000/health

# 查看应用日志
docker compose logs --tail 100 game-server

# 检查资源使用
docker stats wangzhe-server
```

### 4. 性能问题

**症状**: 响应慢、超时

**排查步骤**:

```bash
# 检查资源使用
docker stats

# 检查数据库慢查询
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST"

# 检查 Redis 内存使用
docker compose exec redis redis-cli info memory

# 查看应用日志中的性能指标
docker compose logs game-server | grep -E 'duration|latency|slow'
```

---

## 附录

### 有用的命令速查

```bash
# 查看服务日志（最近 100 行）
docker compose logs --tail 100 game-server

# 进入容器调试
docker compose exec game-server bash

# 重启单个服务
docker compose restart game-server

# 查看资源使用
docker stats

# 清理无用镜像
docker image prune -a

# 查看容器网络
docker network inspect wangzhe-network

# 导出日志
docker compose logs --no-color > logs-$(date +%Y%m%d).log

# 备份数据卷
docker run --rm -v wangzhe-mysql-data:/data -v $(pwd):/backup alpine tar czf /backup/mysql-backup.tar.gz /data
```

### 联系支持

- **文档**: [https://docs.example.com](https://docs.example.com)
- **问题反馈**: [https://github.com/your-org/wangzhe-chess/issues](https://github.com/your-org/wangzhe-chess/issues)
- **社区讨论**: [Discord](https://discord.gg/example)

---

**最后更新**: 2024-01-01  
**版本**: v0.1.0
