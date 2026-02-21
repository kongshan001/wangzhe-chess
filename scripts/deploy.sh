#!/bin/bash
# =============================================================================
# 王者之奕 - 部署脚本
# =============================================================================
# 用途：自动化生产环境部署流程
# 使用：./scripts/deploy.sh [选项]
# 
# 选项：
#   -e, --env FILE       指定环境变量文件（默认：.env）
#   -v, --version VER    指定版本标签（默认：latest）
#   -b, --build          强制重新构建镜像
#   -s, --skip-check     跳过环境检查
#   -h, --help           显示帮助信息
#
# 示例：
#   ./scripts/deploy.sh                    # 标准部署
#   ./scripts/deploy.sh -v v1.2.0          # 指定版本
#   ./scripts/deploy.sh -b                 # 强制重新构建
#   ./scripts/deploy.sh -e .env.prod       # 使用生产环境文件
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 配置变量
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
ENV_FILE="${PROJECT_DIR}/.env"
VERSION="${VERSION:-latest}"
FORCE_BUILD=false
SKIP_CHECK=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------------

# 打印信息
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

# 显示帮助
show_help() {
    cat << EOF
王者之奕 - 部署脚本

用法: $(basename "$0") [选项]

选项:
    -e, --env FILE       指定环境变量文件（默认：.env）
    -v, --version VER    指定版本标签（默认：latest）
    -b, --build          强制重新构建镜像
    -s, --skip-check     跳过环境检查
    -h, --help           显示此帮助信息

示例:
    $(basename "$0")                    # 标准部署
    $(basename "$0") -v v1.2.0          # 指定版本
    $(basename "$0") -b                 # 强制重新构建
    $(basename "$0") -e .env.prod       # 使用生产环境文件

EOF
    exit 0
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -b|--build)
                FORCE_BUILD=true
                shift
                ;;
            -s|--skip-check)
                SKIP_CHECK=true
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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 '$1' 未安装，请先安装"
        return 1
    fi
    return 0
}

# -----------------------------------------------------------------------------
# 环境检查
# -----------------------------------------------------------------------------
check_environment() {
    log_info "检查运行环境..."
    
    local errors=0
    
    # 检查必要命令
    local required_commands=("docker" "docker compose")
    for cmd in "${required_commands[@]}"; do
        if ! check_command "$cmd"; then
            ((errors++))
        fi
    done
    
    # 检查 Docker 服务
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        ((errors++))
    fi
    
    # 检查环境变量文件
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "环境变量文件 '$ENV_FILE' 不存在"
        if [[ -f "${PROJECT_DIR}/.env.example" ]]; then
            log_info "正在从 .env.example 创建 .env 文件..."
            cp "${PROJECT_DIR}/.env.example" "$ENV_FILE"
            log_warning "请编辑 $ENV_FILE 文件并设置必要的环境变量"
        else
            log_error "请创建 $ENV_FILE 文件"
            ((errors++))
        fi
    fi
    
    # 检查必要的环境变量
    if [[ -f "$ENV_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$ENV_FILE"
        
        local required_vars=("SECRET_KEY" "DB_PASSWORD" "MYSQL_ROOT_PASSWORD")
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                log_error "环境变量 '$var' 未设置"
                ((errors++))
            fi
        done
    fi
    
    # 检查磁盘空间
    local available_space
    available_space=$(df -BG "$PROJECT_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ $available_space -lt 5 ]]; then
        log_warning "磁盘空间不足 5GB，当前可用: ${available_space}GB"
    fi
    
    if [[ $errors -gt 0 ]]; then
        log_error "环境检查失败，共 $errors 个错误"
        return 1
    fi
    
    log_success "环境检查通过"
    return 0
}

# -----------------------------------------------------------------------------
# 构建镜像
# -----------------------------------------------------------------------------
build_image() {
    log_info "构建 Docker 镜像 (版本: $VERSION)..."
    
    cd "$PROJECT_DIR"
    
    # 构建参数
    local build_args=(
        "--build-arg" "PYTHON_VERSION=3.11"
        "--build-arg" "VERSION=$VERSION"
        "-t" "wangzhe-chess:$VERSION"
        "-t" "wangzhe-chess:latest"
        "-f" "Dockerfile"
    )
    
    # 如果强制构建，添加 --no-cache
    if [[ "$FORCE_BUILD" == "true" ]]; then
        build_args+=("--no-cache")
    fi
    
    # 执行构建
    if docker build "${build_args[@]}" .; then
        log_success "镜像构建成功: wangzhe-chess:$VERSION"
    else
        log_error "镜像构建失败"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# 拉取基础镜像
# -----------------------------------------------------------------------------
pull_base_images() {
    log_info "拉取基础镜像..."
    
    local images=(
        "python:3.11-slim-bookworm"
        "mysql:8.0"
        "redis:7.2-alpine"
    )
    
    for image in "${images[@]}"; do
        if docker pull "$image"; then
            log_success "拉取成功: $image"
        else
            log_warning "拉取失败: $image (可能已存在)"
        fi
    done
}

# -----------------------------------------------------------------------------
# 启动服务
# -----------------------------------------------------------------------------
start_services() {
    log_info "启动服务..."
    
    cd "$PROJECT_DIR"
    
    # 导出版本变量
    export VERSION
    
    # 停止旧容器
    log_info "停止旧容器..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # 启动新容器
    log_info "启动新容器..."
    if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# 健康检查
# -----------------------------------------------------------------------------
health_check() {
    log_info "执行健康检查..."
    
    local max_retries=30
    local retry_interval=5
    local retry=0
    
    while [[ $retry -lt $max_retries ]]; do
        # 检查服务状态
        if docker compose -f "$COMPOSE_FILE" ps | grep -q "healthy\|running"; then
            log_success "所有服务健康运行"
            
            # 显示服务状态
            echo ""
            docker compose -f "$COMPOSE_FILE" ps
            echo ""
            
            # 显示访问信息
            log_info "服务已就绪:"
            echo "  - API: http://localhost:${SERVER_PORT:-8000}"
            echo "  - 健康检查: http://localhost:${SERVER_PORT:-8000}/health"
            echo "  - API 文档: http://localhost:${SERVER_PORT:-8000}/docs"
            
            return 0
        fi
        
        ((retry++))
        log_info "等待服务就绪... ($retry/$max_retries)"
        sleep "$retry_interval"
    done
    
    log_error "健康检查超时"
    
    # 显示日志以帮助调试
    log_info "最近的日志:"
    docker compose -f "$COMPOSE_FILE" logs --tail=50
    
    return 1
}

# -----------------------------------------------------------------------------
# 清理旧镜像
# -----------------------------------------------------------------------------
cleanup_old_images() {
    log_info "清理未使用的镜像..."
    
    # 删除悬空镜像
    docker image prune -f
    
    # 保留最近的镜像，删除旧版本
    local images
    images=$(docker images wangzhe-chess --format "{{.Tag}}" | grep -v latest | sort -Vr | tail -n +6)
    
    if [[ -n "$images" ]]; then
        for tag in $images; do
            log_info "删除旧镜像: wangzhe-chess:$tag"
            docker rmi "wangzhe-chess:$tag" 2>/dev/null || true
        done
    fi
    
    log_success "清理完成"
}

# -----------------------------------------------------------------------------
# 主函数
# -----------------------------------------------------------------------------
main() {
    echo "========================================"
    echo "   王者之奕 - 自动部署脚本"
    echo "========================================"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 环境检查
    if [[ "$SKIP_CHECK" == "false" ]]; then
        if ! check_environment; then
            exit 1
        fi
    fi
    
    # 拉取基础镜像
    pull_base_images
    
    # 构建镜像
    if ! build_image; then
        exit 1
    fi
    
    # 启动服务
    if ! start_services; then
        exit 1
    fi
    
    # 健康检查
    if ! health_check; then
        exit 1
    fi
    
    # 清理
    cleanup_old_images
    
    echo ""
    log_success "=========================================="
    log_success "  部署完成！"
    log_success "=========================================="
}

# 执行主函数
main "$@"
