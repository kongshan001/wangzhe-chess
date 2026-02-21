#!/bin/bash
# =============================================================================
# 王者之奕 - 备份脚本
# =============================================================================
# 用途：自动化数据库和日志备份
# 使用：./scripts/backup.sh [选项]
#
# 选项：
#   -t, --type TYPE      备份类型: all|db|logs (默认: all)
#   -o, --output DIR     备份输出目录 (默认: ./backups)
#   -r, --retention DAYS 保留天数 (默认: 30)
#   -c, --compress       压缩备份文件
#   -h, --help           显示帮助信息
#
# 示例：
#   ./scripts/backup.sh                   # 完整备份
#   ./scripts/backup.sh -t db             # 仅数据库
#   ./scripts/backup.sh -t logs -c        # 日志并压缩
#   ./scripts/backup.sh -r 7              # 保留7天
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 配置变量
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
BACKUP_TYPE="all"
RETENTION_DAYS=30
COMPRESS=false

# 从环境变量或默认值获取数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-wangzhe}"
DB_USER="${DB_USER:-wangzhe}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Redis 配置
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# 时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# -----------------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
王者之奕 - 备份脚本

用法: $(basename "$0") [选项]

选项:
    -t, --type TYPE      备份类型: all|db|logs (默认: all)
    -o, --output DIR     备份输出目录 (默认: ./backups)
    -r, --retention DAYS 保留天数 (默认: 30)
    -c, --compress       压缩备份文件
    -h, --help           显示此帮助信息

示例:
    $(basename "$0")                   # 完整备份
    $(basename "$0") -t db             # 仅数据库
    $(basename "$0") -t logs -c        # 日志并压缩
    $(basename "$0") -r 7              # 保留7天

EOF
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            -o|--output)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -c|--compress)
                COMPRESS=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                ;;
        esac
    done
}

# 创建备份目录
create_backup_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        log_info "创建备份目录: $dir"
    fi
}

# 获取 Docker 容器名称
get_container_name() {
    local service="$1"
    docker compose -f "$PROJECT_DIR/docker-compose.yml" ps -q "$service" 2>/dev/null | xargs -r docker inspect --format '{{.Name}}' | tr -d '/'
}

# -----------------------------------------------------------------------------
# 数据库备份
# -----------------------------------------------------------------------------
backup_database() {
    log_info "开始数据库备份..."
    
    local backup_subdir="${BACKUP_DIR}/database/${DATE_ONLY}"
    create_backup_dir "$backup_subdir"
    
    local backup_file="${backup_subdir}/${DB_NAME}_${TIMESTAMP}.sql"
    
    # 检查是否使用 Docker
    local mysql_container
    mysql_container=$(get_container_name mysql)
    
    if [[ -n "$mysql_container" ]]; then
        log_info "检测到 Docker 环境，使用容器备份..."
        
        # 使用 Docker 容器执行备份
        docker exec "$mysql_container" mysqldump \
            --user="$DB_USER" \
            --password="$DB_PASSWORD" \
            --host="localhost" \
            --port=3306 \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            --hex-blob \
            --default-character-set=utf8mb4 \
            "$DB_NAME" > "$backup_file"
    else
        log_info "使用本地 mysqldump 备份..."
        
        # 使用本地 mysqldump
        mysqldump \
            --user="$DB_USER" \
            --password="$DB_PASSWORD" \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            --hex-blob \
            --default-character-set=utf8mb4 \
            "$DB_NAME" > "$backup_file"
    fi
    
    # 检查备份是否成功
    if [[ -f "$backup_file" && -s "$backup_file" ]]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        
        # 压缩备份
        if [[ "$COMPRESS" == "true" ]]; then
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
            size=$(du -h "$backup_file" | cut -f1)
        fi
        
        # 计算校验和
        local checksum
        checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)
        echo "$checksum  $(basename "$backup_file")" > "${backup_file}.sha256"
        
        log_success "数据库备份完成: $backup_file (大小: $size)"
        log_info "校验和文件: ${backup_file}.sha256"
    else
        log_error "数据库备份失败"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Redis 备份
# -----------------------------------------------------------------------------
backup_redis() {
    log_info "开始 Redis 备份..."
    
    local backup_subdir="${BACKUP_DIR}/redis/${DATE_ONLY}"
    create_backup_dir "$backup_subdir"
    
    local backup_file="${backup_subdir}/redis_${TIMESTAMP}.rdb"
    
    # 检查是否使用 Docker
    local redis_container
    redis_container=$(get_container_name redis)
    
    if [[ -n "$redis_container" ]]; then
        log_info "检测到 Docker 环境，使用容器备份..."
        
        # 触发 Redis RDB 快照
        docker exec "$redis_container" redis-cli BGSAVE
        
        # 等待快照完成
        sleep 2
        
        # 复制 RDB 文件
        docker cp "${redis_container}:/data/dump.rdb" "$backup_file"
    else
        log_info "使用本地 Redis 备份..."
        
        # 触发 RDB 快照
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
        sleep 2
        
        # 复制 RDB 文件（需要知道 Redis 数据目录）
        local redis_dir
        redis_dir=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET dir | tail -1)
        cp "${redis_dir}/dump.rdb" "$backup_file"
    fi
    
    if [[ -f "$backup_file" && -s "$backup_file" ]]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        
        if [[ "$COMPRESS" == "true" ]]; then
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
            size=$(du -h "$backup_file" | cut -f1)
        fi
        
        log_success "Redis 备份完成: $backup_file (大小: $size)"
    else
        log_warning "Redis 备份为空或失败（可能是空的 Redis 实例）"
    fi
}

# -----------------------------------------------------------------------------
# 日志备份
# -----------------------------------------------------------------------------
backup_logs() {
    log_info "开始日志备份..."
    
    local backup_subdir="${BACKUP_DIR}/logs/${DATE_ONLY}"
    create_backup_dir "$backup_subdir"
    
    local backup_file="${backup_subdir}/logs_${TIMESTAMP}.tar"
    
    # 收集日志源
    local log_sources=()
    
    # 本地日志目录
    if [[ -d "${PROJECT_DIR}/logs" ]]; then
        log_sources+=("${PROJECT_DIR}/logs")
    fi
    
    # Docker 日志
    local containers=("wangzhe-server" "wangzhe-mysql" "wangzhe-redis")
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "$container"; then
            local container_log="${backup_subdir}/${container}_${TIMESTAMP}.log"
            docker logs "$container" > "$container_log" 2>&1 || true
            log_sources+=("$container_log")
        fi
    done
    
    # 创建日志归档
    if [[ ${#log_sources[@]} -gt 0 ]]; then
        tar -cf "$backup_file" "${log_sources[@]}" 2>/dev/null || true
        
        if [[ "$COMPRESS" == "true" ]]; then
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        local size
        size=$(du -h "$backup_file" | cut -f1)
        log_success "日志备份完成: $backup_file (大小: $size)"
        
        # 清理临时日志文件
        for src in "${log_sources[@]}"; do
            if [[ "$src" == "${backup_subdir}/"* ]]; then
                rm -f "$src"
            fi
        done
    else
        log_warning "没有找到日志文件"
    fi
}

# -----------------------------------------------------------------------------
# 清理旧备份
# -----------------------------------------------------------------------------
cleanup_old_backups() {
    log_info "清理 ${RETENTION_DAYS} 天前的旧备份..."
    
    local deleted_count=0
    
    # 查找并删除旧备份
    while IFS= read -r -d '' dir; do
        rm -rf "$dir"
        ((deleted_count++))
        log_info "删除旧备份: $dir"
    done < <(find "$BACKUP_DIR" -type d -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    # 也删除旧的压缩文件
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
        log_info "删除旧文件: $file"
    done < <(find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $deleted_count -gt 0 ]]; then
        log_success "清理完成，删除 $deleted_count 个旧备份"
    else
        log_info "没有需要清理的旧备份"
    fi
}

# -----------------------------------------------------------------------------
# 生成备份报告
# -----------------------------------------------------------------------------
generate_report() {
    local report_file="${BACKUP_DIR}/backup_report_${TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
==============================================================================
                        王者之奕 - 备份报告
==============================================================================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份类型: $BACKUP_TYPE
备份目录: $BACKUP_DIR
保留天数: $RETENTION_DAYS 天

------------------------------------------------------------------------------
                            备份详情
------------------------------------------------------------------------------

$(find "$BACKUP_DIR" -type f -name "*${TIMESTAMP}*" -exec ls -lh {} \; 2>/dev/null)

------------------------------------------------------------------------------
                            存储统计
------------------------------------------------------------------------------

总备份大小: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
数据库备份: $(find "$BACKUP_DIR"/database -type f 2>/dev/null | wc -l) 个文件
日志备份:   $(find "$BACKUP_DIR"/logs -type f 2>/dev/null | wc -l) 个文件
Redis备份:  $(find "$BACKUP_DIR"/redis -type f 2>/dev/null | wc -l) 个文件

==============================================================================
EOF
    
    log_info "备份报告: $report_file"
}

# -----------------------------------------------------------------------------
# 主函数
# -----------------------------------------------------------------------------
main() {
    echo "========================================"
    echo "   王者之奕 - 自动备份脚本"
    echo "========================================"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 加载环境变量
    if [[ -f "${PROJECT_DIR}/.env" ]]; then
        # shellcheck source=/dev/null
        source "${PROJECT_DIR}/.env"
        # 重新设置可能的覆盖
        DB_HOST="${DB_HOST:-mysql}"
        DB_PORT="${DB_PORT:-3306}"
        DB_NAME="${DB_NAME:-wangzhe}"
        DB_USER="${DB_USER:-wangzhe}"
        DB_PASSWORD="${DB_PASSWORD:-}"
    fi
    
    # 创建备份根目录
    create_backup_dir "$BACKUP_DIR"
    
    # 执行备份
    case "$BACKUP_TYPE" in
        all)
            backup_database || true
            backup_redis || true
            backup_logs || true
            ;;
        db)
            backup_database
            ;;
        logs)
            backup_logs
            ;;
        redis)
            backup_redis
            ;;
        *)
            log_error "未知的备份类型: $BACKUP_TYPE"
            exit 1
            ;;
    esac
    
    # 清理旧备份
    cleanup_old_backups
    
    # 生成报告
    generate_report
    
    echo ""
    log_success "=========================================="
    log_success "  备份完成！"
    log_success "=========================================="
}

# 执行主函数
main "$@"
