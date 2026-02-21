# =============================================================================
# 王者之奕 - Docker 镜像构建文件
# =============================================================================
# 多阶段构建：优化镜像大小、提升构建缓存效率、增强安全性
# 构建命令: docker build -t wangzhe-chess:latest .
# =============================================================================

# -----------------------------------------------------------------------------
# 阶段 1: 构建阶段 - 用于编译依赖和生成 requirements
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# 设置构建环境变量
# PYTHONDONTWRITEBYTECODE: 防止 Python 生成 .pyc 文件
# PYTHONUNBUFFERED: 确保 Python 输出直接打印到终端
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip 配置：不缓存下载，只安装需要的包
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖
# - build-essential: C 编译器（部分 Python 包需要）
# - libpq-dev: PostgreSQL 客户端库（如需 psycopg2）
# - default-libmysqlclient-dev: MySQL 客户端库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境（隔离依赖）
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件（利用 Docker 缓存）
COPY pyproject.toml ./

# 安装生产依赖到虚拟环境
# --no-deps 避免意外安装额外依赖
RUN pip install --no-deps --upgrade pip setuptools wheel && \
    pip install .

# -----------------------------------------------------------------------------
# 阶段 2: 生产镜像 - 最小化运行环境
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

# 镜像元数据
LABEL maintainer="OpenClaw <dev@openclaw.ai>" \
      version="0.1.0" \
      description="王者之奕 - 自走棋游戏服务器" \
      org.opencontainers.image.source="https://github.com/openclaw/wangzhe-chess"

# 安全配置：禁止 pip 在运行时安装包
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Python 路径配置
    PYTHONPATH=/app \
    # 安全：禁止 Python 写入 .pyc
    PYTHONDONTWRITEBYTECODE=1 \
    # 禁止 pip（可选，更严格的安全控制）
    # PIP_NO_WARN_SCRIPT_LOCATION=0

# 安装运行时依赖（仅必要的系统库）
# - libmariadb3: MySQL/MariaDB 客户端库
# - curl: 健康检查
# - dumb-init: 正确处理信号（PID 1 问题）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建非 root 用户（安全最佳实践）
# - 系统用户（不可登录）
# - 固定 UID/GID 便于权限管理
RUN groupadd --gid 1000 wangzhe && \
    useradd --uid 1000 --gid wangzhe --shell /bin/false --no-create-home wangzhe

# 创建应用目录和数据目录
# /app: 应用代码
# /app/logs: 日志目录
# /app/data: 持久化数据（如 SQLite）
RUN mkdir -p /app/logs /app/data && \
    chown -R wangzhe:wangzhe /app

WORKDIR /app

# 复制应用代码
# --chown: 确保文件归属于非 root 用户
COPY --chown=wangzhe:wangzhe . .

# 安全：移除不必要的文件
RUN rm -rf tests/ docs/ .git/ .gitignore *.md .env* .dockerignore

# 健康检查配置
# 每 30 秒检查一次，超时 10 秒，重试 3 次
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
# 8000: HTTP/WebSocket 服务端口
EXPOSE 8000

# 切换到非 root 用户
USER wangzhe

# 使用 dumb-init 作为 PID 1（正确处理信号）
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# 启动命令（生产模式）
# --workers: 工作进程数（建议 2 * CPU 核心数）
# --bind: 绑定地址
# --timeout: worker 超时时间（秒）
# --graceful-timeout: 优雅关闭超时
# --access-logfile: 访问日志（- 表示 stdout）
# --error-logfile: 错误日志（- 表示 stderr）
CMD ["gunicorn", "src.server.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# -----------------------------------------------------------------------------
# 开发镜像目标（可选）
# docker build --target development -t wangzhe-chess:dev .
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# 安装开发依赖
RUN pip install --no-cache-dir \
    pytest pytest-asyncio pytest-cov \
    mypy ruff black isort \
    debugpy

# 开发模式：允许 root（便于调试）
USER wangzhe

# 开发启动命令（热重载）
CMD ["uvicorn", "src.server.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "debug"]
