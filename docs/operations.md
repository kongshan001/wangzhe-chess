# 运维手册

> 王者之奕生产环境运维指南

## 目录

- [监控指标](#监控指标)
- [日志管理](#日志管理)
- [故障排查](#故障排查)
- [数据库维护](#数据库维护)
- [备份恢复](#备份恢复)
- [性能调优](#性能调优)
- [安全运维](#安全运维)
- [应急响应](#应急响应)

---

## 监控指标

### 核心监控指标

#### 应用层指标

| 指标名称 | 说明 | 告警阈值 | 采集方式 |
|---------|------|---------|---------|
| HTTP 请求成功率 | 2xx 响应占比 | < 99% | `/metrics` 端点 |
| HTTP 请求延迟 (P95) | 95% 请求响应时间 | > 500ms | `/metrics` 端点 |
| WebSocket 连接数 | 活跃连接数 | > 5000 | `/metrics` 端点 |
| 房间数量 | 活跃游戏房间数 | - | `/metrics` 端点 |
| 在线玩家数 | 当前在线玩家 | - | `/metrics` 端点 |
| 游戏对局数 | 进行中的对局数 | - | `/metrics` 端点 |

#### 系统层指标

| 指标名称 | 说明 | 告警阈值 |
|---------|------|---------|
| CPU 使用率 | 容器 CPU 使用百分比 | > 80% 持续 5 分钟 |
| 内存使用率 | 容器内存使用百分比 | > 85% 持续 5 分钟 |
| 磁盘使用率 | 数据卷磁盘使用百分比 | > 85% |
| 网络流量 | 进出流量速率 | > 带宽 80% |
| 进程数 | 运行的进程数量 | 异常增长 |

#### 数据库指标

| 指标名称 | 说明 | 告警阈值 |
|---------|------|---------|
| 连接数 | 活跃数据库连接 | > 80% max_connections |
| 慢查询数 | 执行时间 > 2s 的查询 | > 10/分钟 |
| 查询延迟 | 平均查询响应时间 | > 100ms |
| 死锁次数 | 发生死锁的次数 | > 0 |
| 主从延迟 | 主从复制延迟（如使用） | > 10s |

#### Redis 指标

| 指标名称 | 说明 | 告警阈值 |
|---------|------|---------|
| 内存使用率 | Redis 内存使用百分比 | > 90% |
| 连接数 | 活跃连接数 | > 80% maxclients |
| 命令延迟 | 平均命令执行时间 | > 10ms |
| 键驱逐次数 | 因内存不足被驱逐的键 | > 0 |
| 阻塞客户端 | 被阻塞的客户端数 | > 10 |

### Prometheus 监控配置

#### 1. 安装 Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'wangzhe-chess'
    static_configs:
      - targets: ['game-server:8000']
    metrics_path: '/metrics'
```

#### 2. 配置告警规则

```yaml
# alert_rules.yml
groups:
  - name: wangzhe-chess
    rules:
      # HTTP 错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率告警"
          description: "HTTP 5xx 错误率超过 5%"

      # 响应时间告警
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高延迟告警"
          description: "P95 延迟超过 500ms"

      # 容器资源告警
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{name="wangzhe-server"}[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高"
          description: "容器 CPU 使用率超过 80%"

      # 数据库连接数告警
      - alert: HighDBConnections
        expr: mysql_global_status_threads_connected / mysql_global_variables_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接数过高"
          description: "数据库连接使用率超过 80%"

      # Redis 内存告警
      - alert: HighRedisMemory
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Redis 内存不足"
          description: "Redis 内存使用率超过 90%"
```

#### 3. Grafana 仪表板

导入 Grafana 仪表板 ID: `12345` (示例)

**推荐仪表板面板**:

- HTTP 请求概览（QPS、错误率、延迟）
- WebSocket 连接统计
- 系统资源使用（CPU、内存、磁盘、网络）
- 数据库性能（查询数、慢查询、连接池）
- Redis 性能（内存、命中率、命令统计）
- 游戏业务指标（在线人数、房间数、对局数）

### 自定义监控脚本

创建 `scripts/monitor.sh`:

```bash
#!/bin/bash
# 王者之奕监控脚本

# 配置
PROMETHEUS_URL="http://localhost:9090"
ALERT_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 获取指标
get_metric() {
    local query=$1
    curl -s "${PROMETHEUS_URL}/api/v1/query?query=${query}" | jq -r '.data.result[0].value[1]'
}

# 检查错误率
check_error_rate() {
    local error_rate=$(get_metric 'rate(http_requests_total{status=~"5.."}[5m])')
    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        send_alert "高错误率: ${error_rate}"
    fi
}

# 检查延迟
check_latency() {
    local latency=$(get_metric 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))')
    if (( $(echo "$latency > 0.5" | bc -l) )); then
        send_alert "高延迟: ${latency}s"
    fi
}

# 发送告警
send_alert() {
    local message=$1
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"【王者之奕告警】${message}\"}" \
         "$ALERT_WEBHOOK"
}

# 主循环
while true; do
    check_error_rate
    check_latency
    sleep 60
done
```

---

## 日志管理

### 日志格式

#### 应用日志格式（JSON）

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "wangzhe.server.game",
  "message": "Player joined room",
  "context": {
    "player_id": "12345",
    "room_id": "room-67890",
    "request_id": "req-abc123"
  },
  "extra": {
    "user_agent": "Mozilla/5.0",
    "ip": "192.168.1.100"
  }
}
```

#### 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 调试信息 | 变量值、函数调用 |
| INFO | 常规信息 | 请求处理、用户操作 |
| WARNING | 警告信息 | 性能下降、资源接近上限 |
| ERROR | 错误信息 | 请求失败、异常 |
| CRITICAL | 严重错误 | 服务不可用、数据丢失 |

### 日志收集

#### 使用 Docker 日志驱动

```yaml
# docker-compose.yml
services:
  game-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"    # 单文件最大 10MB
        max-file: "5"       # 保留 5 个文件
        labels: "service,environment"
        tag: "{{.Name}}/{{.ID}}"
```

#### 集中日志收集（ELK Stack）

1. **安装 Filebeat**

   ```yaml
   # filebeat.yml
   filebeat.inputs:
     - type: container
       paths:
         - /var/lib/docker/containers/*/*.log
       processors:
         - add_docker_metadata: ~
   
   output.elasticsearch:
     hosts: ["elasticsearch:9200"]
     index: "wangzhe-chess-%{+yyyy.MM.dd}"
   ```

2. **Logstash 配置**

   ```ruby
   # logstash.conf
   input {
     beats {
       port => 5044
     }
   }
   
   filter {
     json {
       source => "message"
     }
     
     if [level] == "ERROR" {
       mutate {
         add_tag => ["error"]
       }
     }
   }
   
   output {
     elasticsearch {
       hosts => ["elasticsearch:9200"]
       index => "wangzhe-chess-%{+YYYY.MM.dd}"
     }
   }
   ```

3. **Kibana 仪表板**

   - 创建索引模式: `wangzhe-chess-*`
   - 配置可视化图表
   - 设置告警规则

### 日志查询

#### 常用查询命令

```bash
# 查看实时日志
docker compose logs -f game-server

# 查看最近 100 行日志
docker compose logs --tail 100 game-server

# 查看特定时间段的日志
docker compose logs --since 2024-01-01T10:00:00 --until 2024-01-01T12:00:00 game-server

# 过滤错误日志
docker compose logs game-server | grep -i error

# 过滤特定用户的操作日志
docker compose logs game-server | grep "player_id\":\"12345"

# 导出日志到文件
docker compose logs --no-color game-server > app-$(date +%Y%m%d).log

# 使用 jq 解析 JSON 日志
docker compose logs game-server | jq 'select(.level == "ERROR")'

# 统计错误数量
docker compose logs game-server | jq -r 'select(.level == "ERROR") | .message' | wc -l
```

#### Kibana 查询示例

```
# 查询错误日志
level: "ERROR"

# 查询特定玩家的操作
context.player_id: "12345"

# 查询特定房间的事件
context.room_id: "room-67890"

# 查询慢请求
context.duration_ms: >500

# 组合查询
level: "ERROR" AND context.room_id: "room-67890"
```

### 日志轮转与清理

#### 自动清理脚本

创建 `scripts/clean-logs.sh`:

```bash
#!/bin/bash
# 清理旧日志文件

LOG_DIR="/var/log/wangzhe"
RETENTION_DAYS=30

# 删除 30 天前的日志
find "$LOG_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete

# 压缩 7 天前的日志
find "$LOG_DIR" -name "*.log" -mtime +7 -exec gzip {} \;

echo "日志清理完成: $(date)"
```

设置定时任务:

```bash
crontab -e
# 每天凌晨 3 点执行
0 3 * * * /path/to/wangzhe-chess/scripts/clean-logs.sh
```

---

## 故障排查

### 常见故障场景

#### 1. 服务无法启动

**症状**:
- `docker compose up -d` 失败
- 容器启动后立即退出

**排查步骤**:

```bash
# 1. 查看容器日志
docker compose logs game-server

# 2. 查看容器退出代码
docker compose ps -a

# 3. 检查配置文件
docker compose config

# 4. 检查端口占用
netstat -tlnp | grep 8000

# 5. 检查环境变量
docker compose exec game-server env

# 6. 检查依赖服务
docker compose ps mysql redis
```

**常见原因及解决**:

| 原因 | 解决方法 |
|------|---------|
| 端口被占用 | 停止占用端口的进程或修改端口 |
| 环境变量未设置 | 检查 .env 文件，确保必需变量已设置 |
| 数据库连接失败 | 检查数据库服务状态和网络连接 |
| 权限问题 | 检查文件权限，确保容器用户有访问权限 |
| 镜像构建失败 | 检查 Dockerfile，重新构建镜像 |

#### 2. 数据库连接失败

**症状**:
- 应用日志显示数据库连接错误
- 请求返回 500 错误

**排查步骤**:

```bash
# 1. 检查 MySQL 服务状态
docker compose ps mysql
docker compose logs mysql

# 2. 测试数据库连接
docker compose exec mysql mysql -uwangzhe -p -e "SELECT 1"

# 3. 检查网络连通性
docker compose exec game-server ping mysql
docker compose exec game-server telnet mysql 3306

# 4. 检查用户权限
docker compose exec mysql mysql -uroot -p -e "SHOW GRANTS FOR 'wangzhe'@'%'"

# 5. 检查连接数
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST"

# 6. 检查防火墙
sudo iptables -L -n | grep 3306
```

**解决方案**:

```bash
# 重启 MySQL
docker compose restart mysql

# 修改用户权限
docker compose exec mysql mysql -uroot -p << EOF
GRANT ALL PRIVILEGES ON wangzhe.* TO 'wangzhe'@'%';
FLUSH PRIVILEGES;
EOF

# 检查配置
docker compose exec mysql mysql -uroot -p -e "SHOW VARIABLES LIKE 'max_connections'"
```

#### 3. Redis 连接问题

**症状**:
- 缓存失效
- 会话丢失
- 性能下降

**排查步骤**:

```bash
# 1. 检查 Redis 服务
docker compose ps redis
docker compose logs redis

# 2. 测试连接
docker compose exec redis redis-cli ping

# 3. 检查内存使用
docker compose exec redis redis-cli info memory

# 4. 检查连接数
docker compose exec redis redis-cli info clients

# 5. 检查慢查询
docker compose exec redis redis-cli slowlog get 10

# 6. 监控实时命令
docker compose exec redis redis-cli monitor
```

**解决方案**:

```bash
# 重启 Redis
docker compose restart redis

# 清理内存
docker compose exec redis redis-cli flushall

# 调整内存限制
# 修改 docker-compose.yml 中的 maxmemory 配置
```

#### 4. 性能下降

**症状**:
- 响应时间变长
- 请求超时
- 用户体验差

**排查步骤**:

```bash
# 1. 检查系统资源
docker stats

# 2. 检查应用性能
curl -w "Time: %{time_total}s\n" http://localhost:8000/health

# 3. 检查数据库性能
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST"
docker compose exec mysql mysql -uroot -p -e "SELECT * FROM information_schema.innodb_trx"

# 4. 检查慢查询
docker compose exec mysql mysql -uroot -p -e "SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10"

# 5. 检查 Redis 性能
docker compose exec redis redis-cli --latency

# 6. 分析应用日志
docker compose logs game-server | grep -E "duration|latency|slow"
```

**解决方案**:

```bash
# 增加资源限制
# 修改 docker-compose.yml 中的 deploy.resources

# 优化数据库查询
# 添加索引、优化 SQL

# 调整连接池
# 修改 .env 中的 DB_POOL_SIZE 和 REDIS_MAX_CONNECTIONS

# 启用缓存
# 优化缓存策略，减少数据库访问
```

#### 5. 内存泄漏

**症状**:
- 内存持续增长
- 容器被 OOM 杀死

**排查步骤**:

```bash
# 1. 监控内存使用
watch -n 1 'docker stats wangzhe-server --no-stream'

# 2. 生成内存快照
docker compose exec game-server python -m cProfile -o profile.stats src/server/main.py

# 3. 分析内存使用
docker compose exec game-server python -c "
import tracemalloc
tracemalloc.start()
# 运行一段时间
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"

# 4. 检查数据库连接
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST" | wc -l

# 5. 检查 Redis 连接
docker compose exec redis redis-cli client list | wc -l
```

**解决方案**:

```bash
# 重启服务
docker compose restart game-server

# 修复代码中的内存泄漏
# - 释放不再使用的对象
# - 关闭数据库连接
# - 限制缓存大小
```

### 故障排查工具箱

#### 诊断脚本

创建 `scripts/diagnose.sh`:

```bash
#!/bin/bash
# 综合诊断脚本

echo "=== 王者之奕系统诊断 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# 1. 系统资源
echo "【系统资源】"
echo "CPU 使用率:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}'
echo "内存使用:"
free -h | grep Mem
echo "磁盘使用:"
df -h | grep -E '^/dev'
echo

# 2. Docker 服务
echo "【Docker 服务】"
docker compose ps
echo

# 3. 网络连接
echo "【网络连接】"
echo "监听端口:"
netstat -tlnp | grep -E '8000|3306|6379'
echo

# 4. 应用健康
echo "【应用健康】"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 应用健康"
    curl -s http://localhost:8000/health | jq .
else
    echo "❌ 应用不健康"
fi
echo

# 5. 数据库连接
echo "【数据库连接】"
if docker compose exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
    echo "✅ MySQL 连接正常"
    docker compose exec -T mysql mysql -uwangzhe -p${DB_PASSWORD} -e "SELECT COUNT(*) as connections FROM information_schema.processlist"
else
    echo "❌ MySQL 连接失败"
fi
echo

# 6. Redis 连接
echo "【Redis 连接】"
if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis 连接正常"
    docker compose exec -T redis redis-cli info memory | grep -E "used_memory_human|maxmemory_human"
else
    echo "❌ Redis 连接失败"
fi
echo

# 7. 最近错误
echo "【最近错误日志】"
docker compose logs --tail 20 game-server | grep -i error
echo

echo "=== 诊断完成 ==="
```

---

## 数据库维护

### 日常维护任务

#### 1. 定期优化表

```bash
# 优化所有表（释放空间、重建索引）
docker compose exec mysql mysql -uroot -p -e "
USE wangzhe;
OPTIMIZE TABLE players;
OPTIMIZE TABLE rooms;
OPTIMIZE TABLE games;
"

# 或使用脚本
docker compose exec mysql mysqlcheck -uroot -p --optimize wangzhe
```

#### 2. 分析表统计信息

```bash
# 更新表统计信息（优化查询计划）
docker compose exec mysql mysql -uroot -p -e "
USE wangzhe;
ANALYZE TABLE players;
ANALYZE TABLE rooms;
ANALYZE TABLE games;
"
```

#### 3. 检查表完整性

```bash
# 检查表是否有错误
docker compose exec mysql mysqlcheck -uroot -p --check wangzhe

# 修复损坏的表
docker compose exec mysql mysqlcheck -uroot -p --repair wangzhe
```

### 索引管理

#### 查看索引使用情况

```sql
-- 查看表的索引
SHOW INDEX FROM players;

-- 查看未使用的索引
SELECT *
FROM sys.schema_unused_indexes
WHERE object_schema = 'wangzhe';

-- 查看冗余索引
SELECT *
FROM sys.schema_redundant_indexes
WHERE table_schema = 'wangzhe';
```

#### 添加索引

```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_players_created_at ON players(created_at);
CREATE INDEX idx_games_room_id ON games(room_id, created_at);

-- 复合索引
CREATE INDEX idx_rooms_status_created ON rooms(status, created_at);
```

### 慢查询优化

#### 识别慢查询

```bash
# 查看慢查询日志配置
docker compose exec mysql mysql -uroot -p -e "
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
"

# 查看最近的慢查询
docker compose exec mysql mysql -uroot -p -e "
SELECT * FROM mysql.slow_log
ORDER BY start_time DESC
LIMIT 10;
"
```

#### 分析查询执行计划

```sql
-- 使用 EXPLAIN 分析查询
EXPLAIN SELECT * FROM players WHERE username = 'test';

-- 使用 EXPLAIN ANALYZE（MySQL 8.0.18+）
EXPLAIN ANALYZE SELECT * FROM players WHERE username = 'test';
```

#### 优化建议

1. **避免 SELECT ***: 只查询需要的字段
2. **使用索引**: 确保 WHERE、JOIN、ORDER BY 使用索引
3. **避免函数索引**: 不要在索引列上使用函数
4. **优化 JOIN**: 小表驱动大表
5. **分页优化**: 使用游标分页代替 LIMIT offset

### 数据库监控

#### 关键监控指标

```sql
-- 连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW VARIABLES LIKE 'max_connections';

-- 查询统计
SHOW STATUS LIKE 'Queries';
SHOW STATUS LIKE 'Slow_queries';

-- 缓冲池命中率
SHOW STATUS LIKE 'Innodb_buffer_pool_read%';
-- 命中率 = 1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)

-- 锁等待
SHOW STATUS LIKE 'Innodb_row_lock%';

-- 死锁
SHOW ENGINE INNODB STATUS;
```

#### 监控脚本

创建 `scripts/db-monitor.sh`:

```bash
#!/bin/bash
# 数据库监控脚本

MYSQL_CMD="docker compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD}"

# 连接数
connections=$($MYSQL_CMD -e "SHOW STATUS LIKE 'Threads_connected'" | tail -1 | awk '{print $2}')
max_conn=$($MYSQL_CMD -e "SHOW VARIABLES LIKE 'max_connections'" | tail -1 | awk '{print $2}')
conn_pct=$(echo "scale=2; $connections / $max_conn * 100" | bc)

echo "数据库连接: $connections / $max_conn (${conn_pct}%)"

# 缓冲池命中率
pool_reads=$($MYSQL_CMD -e "SHOW STATUS LIKE 'Innodb_buffer_pool_reads'" | tail -1 | awk '{print $2}')
pool_requests=$($MYSQL_CMD -e "SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'" | tail -1 | awk '{print $2}')
hit_rate=$(echo "scale=2; (1 - $pool_reads / $pool_requests) * 100" | bc)

echo "缓冲池命中率: ${hit_rate}%"

# 慢查询数
slow_queries=$($MYSQL_CMD -e "SHOW STATUS LIKE 'Slow_queries'" | tail -1 | awk '{print $2}')
echo "慢查询数: $slow_queries"
```

---

## 备份恢复

### 备份策略

#### 备份类型

| 类型 | 频率 | 保留时间 | 大小 | 恢复时间 |
|------|------|---------|------|---------|
| 完整备份 | 每日 | 30 天 | 大 | 慢 |
| 增量备份 | 每小时 | 7 天 | 小 | 快 |
| 二进制日志 | 实时 | 7 天 | 中 | 最快 |

#### 推荐备份策略

- **每日完整备份**: 凌晨 2 点执行
- **每小时增量备份**: 保留 7 天
- **实时二进制日志**: 用于时间点恢复
- **异地备份**: 每周同步到远程存储

### 备份脚本

#### 完整备份脚本

创建 `scripts/backup.sh`:

```bash
#!/bin/bash
# 数据库完整备份脚本

set -e

# 配置
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/wangzhe-full-${DATE}.sql"
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "开始备份: $(date)"

# 执行备份
docker compose exec -T mysql mysqldump \
  -u root \
  -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --flush-logs \
  --master-data=2 \
  wangzhe > "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"

# 加密备份（可选）
# gpg -c "${BACKUP_FILE}.gz"

# 删除旧备份（保留 30 天）
find "$BACKUP_DIR" -name "wangzhe-full-*.sql.gz" -mtime +30 -delete

echo "备份完成: ${BACKUP_FILE}.gz"
echo "备份大小: $(du -h ${BACKUP_FILE}.gz | cut -f1)"
```

#### 增量备份脚本

创建 `scripts/backup-incremental.sh`:

```bash
#!/bin/bash
# 增量备份（使用二进制日志）

BACKUP_DIR="/backup/mysql/binlog"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 刷新日志
docker compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -e "FLUSH LOGS"

# 复制二进制日志
docker compose exec mysql bash -c "cp /var/lib/mysql/mysql-bin.* /backup/"

# 压缩
tar czf "${BACKUP_DIR}/binlog-${DATE}.tar.gz" -C /backup mysql-bin.*

echo "增量备份完成: binlog-${DATE}.tar.gz"
```

#### Redis 备份脚本

创建 `scripts/backup-redis.sh`:

```bash
#!/bin/bash
# Redis 备份脚本

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 触发 RDB 快照
docker compose exec redis redis-cli BGSAVE

# 等待快照完成
sleep 5

# 复制快照文件
docker cp wangzhe-redis:/data/dump.rdb "${BACKUP_DIR}/redis-${DATE}.rdb"

# 压缩
gzip "${BACKUP_DIR}/redis-${DATE}.rdb"

echo "Redis 备份完成: redis-${DATE}.rdb.gz"
```

### 恢复操作

#### 完整恢复

```bash
#!/bin/bash
# 数据库完整恢复脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <backup-file.sql.gz>"
    exit 1
fi

echo "警告: 此操作将覆盖当前数据库！"
read -p "确认继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "取消操作"
    exit 0
fi

# 停止应用服务
docker compose stop game-server

# 解压备份文件
gunzip -c "$BACKUP_FILE" > /tmp/restore.sql

# 恢复数据库
docker compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" wangzhe < /tmp/restore.sql

# 清理临时文件
rm /tmp/restore.sql

# 启动应用服务
docker compose start game-server

echo "恢复完成"
```

#### 时间点恢复

```bash
#!/bin/bash
# 时间点恢复（PITR）

FULL_BACKUP=$1
TARGET_TIME=$2
BINLOG_DIR="/backup/mysql/binlog"

# 1. 恢复完整备份
gunzip -c "$FULL_BACKUP" | docker compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" wangzhe

# 2. 应用二进制日志到指定时间点
for binlog in "$BINLOG_DIR"/mysql-bin.*; do
    docker compose exec -T mysql mysqlbinlog \
        --stop-datetime="$TARGET_TIME" \
        "$binlog" | docker compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}"
done

echo "时间点恢复完成: $TARGET_TIME"
```

#### Redis 恢复

```bash
#!/bin/bash
# Redis 恢复脚本

BACKUP_FILE=$1

# 停止 Redis
docker compose stop redis

# 复制备份文件
gunzip -c "$BACKUP_FILE" > /tmp/dump.rdb
docker cp /tmp/dump.rdb wangzhe-redis:/data/dump.rdb

# 启动 Redis
docker compose start redis

echo "Redis 恢复完成"
```

### 定时备份

设置 crontab:

```bash
crontab -e

# 每日凌晨 2 点完整备份
0 2 * * * /path/to/wangzhe-chess/scripts/backup.sh >> /var/log/wangzhe/backup.log 2>&1

# 每小时增量备份
0 * * * * /path/to/wangzhe-chess/scripts/backup-incremental.sh >> /var/log/wangzhe/backup.log 2>&1

# 每日 Redis 备份
0 3 * * * /path/to/wangzhe-chess/scripts/backup-redis.sh >> /var/log/wangzhe/backup.log 2>&1
```

---

## 性能调优

### 应用性能调优

#### 1. 调整 Worker 数量

```bash
# .env
SERVER_WORKERS=4  # 建议: 2 * CPU 核心数
```

#### 2. 优化连接池

```bash
# .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

REDIS_MAX_CONNECTIONS=100
```

#### 3. 启用缓存

- 使用 Redis 缓存热点数据
- 设置合理的过期时间
- 实现缓存预热

#### 4. 异步处理

- 使用消息队列处理耗时任务
- 避免阻塞主线程

### 数据库性能调优

#### 1. 调整缓冲池

```ini
# my.cnf
[mysqld]
innodb_buffer_pool_size = 2G  # 可用内存的 70-80%
innodb_buffer_pool_instances = 4
innodb_log_file_size = 256M
```

#### 2. 优化查询

```sql
-- 启用查询缓存（MySQL 8.0 前版本）
query_cache_type = 1
query_cache_size = 64M

-- 调整连接数
max_connections = 500

-- 优化排序缓冲
sort_buffer_size = 2M
join_buffer_size = 2M
```

#### 3. 分区表

```sql
-- 按时间分区
CREATE TABLE games (
    id BIGINT,
    created_at DATETIME,
    ...
) PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### Redis 性能调优

#### 1. 内存优化

```bash
# 调整最大内存
maxmemory 1gb

# 设置淘汰策略
maxmemory-policy allkeys-lru
```

#### 2. 持久化优化

```bash
# 使用 AOF + RDB 混合持久化
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes
```

#### 3. 连接池

```bash
# 调整最大连接数
maxclients 10000
```

### 系统性能调优

#### 1. 内核参数优化

```bash
# /etc/sysctl.conf
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

# 文件描述符
fs.file-max = 65535

# 应用配置
sysctl -p
```

#### 2. 资源限制

```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
```

---

## 安全运维

### 安全检查清单

#### 1. 访问控制

- [ ] 修改默认密码
- [ ] 使用强密码
- [ ] 限制数据库远程访问
- [ ] 配置防火墙规则
- [ ] 启用双因素认证

#### 2. 网络安全

- [ ] 启用 HTTPS
- [ ] 配置 CORS 策略
- [ ] 隐藏内部服务端口
- [ ] 启用速率限制
- [ ] 配置 DDoS 防护

#### 3. 数据安全

- [ ] 加密敏感数据
- [ ] 定期备份数据
- [ ] 加密备份文件
- [ ] 异地存储备份
- [ ] 定期测试恢复

#### 4. 应用安全

- [ ] 更新依赖版本
- [ ] 修复安全漏洞
- [ ] 启用日志审计
- [ ] 配置错误页面
- [ ] 隐藏版本信息

### 安全审计

#### 定期安全检查脚本

创建 `scripts/security-audit.sh`:

```bash
#!/bin/bash
# 安全审计脚本

echo "=== 王者之奕安全审计 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# 1. 检查默认密码
echo "【检查默认密码】"
if docker compose exec -T mysql mysql -uroot -proot -e "SELECT 1" 2>/dev/null; then
    echo "❌ 警告: MySQL 使用默认密码"
else
    echo "✅ MySQL 密码已修改"
fi

# 2. 检查端口暴露
echo "【检查端口暴露】"
exposed=$(docker compose config | grep -E "^\s*-\s*\d+:\d+" | wc -l)
if [ "$exposed" -gt 1 ]; then
    echo "⚠️  警告: 有 $exposed 个端口暴露到宿主机"
else
    echo "✅ 端口配置合理"
fi

# 3. 检查安全更新
echo "【检查安全更新】"
docker compose run --rm game-server pip-audit 2>/dev/null || echo "⚠️  pip-audit 未安装"

# 4. 检查文件权限
echo "【检查文件权限】"
if [ -f ".env" ]; then
    perms=$(stat -c %a .env)
    if [ "$perms" = "600" ]; then
        echo "✅ .env 文件权限正确"
    else
        echo "⚠️  警告: .env 文件权限应为 600，当前为 $perms"
    fi
fi

# 5. 检查 SSL 配置
echo "【检查 SSL 配置】"
if curl -k https://localhost:8000/health 2>/dev/null | grep -q "healthy"; then
    echo "✅ HTTPS 已启用"
else
    echo "⚠️  警告: HTTPS 未启用"
fi

echo
echo "=== 审计完成 ==="
```

---

## 应急响应

### 应急响应流程

#### 1. 故障发现

- 监控告警
- 用户反馈
- 日志分析

#### 2. 故障确认

- 检查服务状态
- 查看错误日志
- 确认影响范围

#### 3. 故障处理

- 临时修复
- 根因分析
- 永久修复

#### 4. 故障恢复

- 服务恢复
- 数据恢复
- 验证测试

#### 5. 故障总结

- 编写故障报告
- 改进措施
- 知识沉淀

### 常见应急场景

#### 场景 1: 服务宕机

```bash
# 1. 确认故障
docker compose ps

# 2. 查看日志
docker compose logs --tail 100 game-server

# 3. 重启服务
docker compose restart game-server

# 4. 验证恢复
curl http://localhost:8000/health

# 5. 通知用户
# 发送公告、更新状态页面
```

#### 场景 2: 数据库故障

```bash
# 1. 确认故障
docker compose ps mysql
docker compose logs mysql

# 2. 尝试重启
docker compose restart mysql

# 3. 如果无法启动，恢复数据
# 参见"备份恢复"章节

# 4. 验证数据完整性
docker compose exec mysql mysqlcheck --check wangzhe
```

#### 场景 3: 数据丢失

```bash
# 1. 停止写入
docker compose stop game-server

# 2. 确认丢失范围
# 检查备份时间点

# 3. 恢复数据
# 参见"备份恢复"章节

# 4. 验证数据
# 对比关键数据

# 5. 恢复服务
docker compose start game-server
```

#### 场景 4: 安全事件

```bash
# 1. 隔离系统
# 停止服务、断开网络

# 2. 保护证据
# 保留日志、快照系统

# 3. 分析入侵
# 检查日志、分析攻击路径

# 4. 修复漏洞
# 更新密码、打补丁

# 5. 恢复服务
# 从干净备份恢复
```

### 应急联系人

| 角色 | 姓名 | 联系方式 | 职责 |
|------|------|---------|------|
| 运维负责人 | - | - | 总体协调 |
| DBA | - | - | 数据库问题 |
| 开发负责人 | - | - | 应用问题 |
| 安全负责人 | - | - | 安全事件 |

---

## 附录

### 常用运维命令速查

```bash
# 服务管理
docker compose up -d              # 启动服务
docker compose down               # 停止服务
docker compose restart [service]  # 重启服务
docker compose ps                 # 查看状态
docker compose logs -f [service]  # 查看日志

# 数据库操作
docker compose exec mysql mysql -uroot -p              # 登录 MySQL
docker compose exec mysql mysqldump -uroot -p wangzhe  # 备份数据库
docker compose exec mysql mysqlcheck -uroot -p --check wangzhe  # 检查表

# Redis 操作
docker compose exec redis redis-cli              # 登录 Redis
docker compose exec redis redis-cli info         # 查看信息
docker compose exec redis redis-cli monitor      # 监控命令

# 系统监控
docker stats                                     # 容器资源
docker compose exec game-server top              # 进程信息
docker compose exec mysql mysql -uroot -p -e "SHOW PROCESSLIST"  # 数据库连接

# 故障排查
docker compose logs --tail 100 game-server      # 查看最近日志
docker compose exec game-server curl http://localhost:8000/health  # 健康检查
docker compose exec game-server ping mysql      # 测试网络

# 备份恢复
./scripts/backup.sh                             # 执行备份
./scripts/restore.sh backup-file.sql.gz        # 恢复数据
```

### 监控告警配置模板

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-ops'

receivers:
  - name: 'team-ops'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
```

---

**最后更新**: 2024-01-01  
**版本**: v0.1.0  
**维护团队**: 运维团队
