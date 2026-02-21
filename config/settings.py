"""
王者之奕 - 配置管理模块
=======================

提供统一的配置管理，支持：
- 环境变量读取
- 默认配置
- 配置验证
- 类型安全

使用方式：
    from config.settings import settings
    
    db_host = settings.DB_HOST
    debug = settings.DEBUG
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# 环境类型定义
# =============================================================================
class Environment:
    """运行环境枚举"""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    
    @classmethod
    def is_production(cls, env: str) -> bool:
        """检查是否为生产环境"""
        return env.lower() == cls.PRODUCTION
    
    @classmethod
    def is_development(cls, env: str) -> bool:
        """检查是否为开发环境"""
        return env.lower() == cls.DEVELOPMENT


# =============================================================================
# 数据库配置
# =============================================================================
class DatabaseSettings(BaseSettings):
    """
    数据库配置
    
    环境变量：
        DB_HOST: 数据库主机地址
        DB_PORT: 数据库端口
        DB_NAME: 数据库名称
        DB_USER: 数据库用户名
        DB_PASSWORD: 数据库密码
        DB_POOL_SIZE: 连接池大小
        DB_MAX_OVERFLOW: 最大溢出连接数
        DB_POOL_TIMEOUT: 连接池超时（秒）
        DB_ECHO: 是否打印 SQL（调试用）
    """
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # 连接配置
    HOST: str = Field(default="localhost", description="数据库主机地址")
    PORT: int = Field(default=3306, ge=1, le=65535, description="数据库端口")
    NAME: str = Field(default="wangzhe", description="数据库名称")
    USER: str = Field(default="wangzhe", description="数据库用户名")
    PASSWORD: str = Field(default="", description="数据库密码")
    
    # 连接池配置
    POOL_SIZE: int = Field(default=10, ge=1, le=100, description="连接池大小")
    MAX_OVERFLOW: int = Field(default=20, ge=0, le=50, description="最大溢出连接数")
    POOL_TIMEOUT: int = Field(default=30, ge=1, le=300, description="连接池超时（秒）")
    POOL_RECYCLE: int = Field(default=3600, ge=60, description="连接回收时间（秒）")
    
    # 调试配置
    ECHO: bool = Field(default=False, description="是否打印 SQL")
    
    @property
    def url(self) -> str:
        """
        生成数据库连接 URL
        
        格式：mysql+aiomysql://user:password@host:port/name
        """
        return f"mysql+aiomysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
    
    @property
    def sync_url(self) -> str:
        """
        生成同步数据库连接 URL
        
        格式：mysql+pymysql://user:password@host:port/name
        """
        return f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
    
    @property
    def async_url(self) -> str:
        """异步连接 URL（与 url 相同）"""
        return self.url


# =============================================================================
# Redis 配置
# =============================================================================
class RedisSettings(BaseSettings):
    """
    Redis 配置
    
    环境变量：
        REDIS_HOST: Redis 主机地址
        REDIS_PORT: Redis 端口
        REDIS_PASSWORD: Redis 密码
        REDIS_DB: Redis 数据库编号
        REDIS_MAX_CONNECTIONS: 最大连接数
    """
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    HOST: str = Field(default="localhost", description="Redis 主机地址")
    PORT: int = Field(default=6379, ge=1, le=65535, description="Redis 端口")
    PASSWORD: str = Field(default="", description="Redis 密码")
    DB: int = Field(default=0, ge=0, le=15, description="Redis 数据库编号")
    MAX_CONNECTIONS: int = Field(default=50, ge=1, le=1000, description="最大连接数")
    SOCKET_TIMEOUT: int = Field(default=5, ge=1, description="Socket 超时（秒）")
    
    @property
    def url(self) -> str:
        """生成 Redis 连接 URL"""
        if self.PASSWORD:
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


# =============================================================================
# 服务器配置
# =============================================================================
class ServerSettings(BaseSettings):
    """
    服务器配置
    
    环境变量：
        SERVER_HOST: 服务器绑定地址
        SERVER_PORT: 服务器端口
        SERVER_WORKERS: 工作进程数
        SERVER_TIMEOUT: 请求超时（秒）
    """
    
    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    HOST: str = Field(default="0.0.0.0", description="服务器绑定地址")
    PORT: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    WORKERS: int = Field(default=1, ge=1, le=32, description="工作进程数")
    TIMEOUT: int = Field(default=120, ge=1, le=600, description="请求超时（秒）")
    GRACEFUL_TIMEOUT: int = Field(default=30, ge=5, description="优雅关闭超时（秒）")


# =============================================================================
# 安全配置
# =============================================================================
class SecuritySettings(BaseSettings):
    """
    安全配置
    
    环境变量：
        SECRET_KEY: 应用密钥（必需）
        ACCESS_TOKEN_EXPIRE_MINUTES: 访问令牌过期时间（分钟）
        REFRESH_TOKEN_EXPIRE_DAYS: 刷新令牌过期时间（天）
        CORS_ORIGINS: 允许的 CORS 来源
        RATE_LIMIT_PER_MINUTE: 每分钟请求限制
    """
    
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # 密钥配置
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="应用密钥（生产环境必须设置）"
    )
    
    # 令牌配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, ge=1, le=1440,
        description="访问令牌过期时间（分钟）"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, ge=1, le=30,
        description="刷新令牌过期时间（天）"
    )
    
    # CORS 配置
    CORS_ORIGINS: str = Field(
        default="*",
        description="允许的 CORS 来源（逗号分隔）"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="允许凭证")
    CORS_ALLOW_METHODS: str = Field(default="*", description="允许的方法")
    CORS_ALLOW_HEADERS: str = Field(default="*", description="允许的头部")
    
    # 速率限制
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60, ge=0,
        description="每分钟请求限制（0 表示不限制）"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """将 CORS 来源字符串转换为列表"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """验证密钥强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY 必须至少 32 个字符")
        return v


# =============================================================================
# 游戏配置
# =============================================================================
class GameSettings(BaseSettings):
    """
    游戏逻辑配置
    
    环境变量：
        MAX_PLAYERS_PER_ROOM: 每个房间最大玩家数
        GAME_TICK_RATE: 游戏帧率
        ROUND_DURATION_SECONDS: 回合持续时间
        BUY_PHASE_DURATION: 购买阶段持续时间
        BATTLE_PHASE_DURATION: 战斗阶段持续时间
    """
    
    model_config = SettingsConfigDict(
        env_prefix="GAME_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    MAX_PLAYERS_PER_ROOM: int = Field(
        default=8, ge=2, le=16,
        description="每个房间最大玩家数"
    )
    TICK_RATE: int = Field(
        default=30, ge=10, le=60,
        description="游戏帧率（FPS）"
    )
    ROUND_DURATION_SECONDS: int = Field(
        default=30, ge=10, le=120,
        description="回合持续时间（秒）"
    )
    BUY_PHASE_DURATION: int = Field(
        default=30, ge=15, le=60,
        description="购买阶段持续时间（秒）"
    )
    BATTLE_PHASE_DURATION: int = Field(
        default=60, ge=30, le=120,
        description="战斗阶段持续时间（秒）"
    )
    STARTING_GOLD: int = Field(default=10, ge=0, description="初始金币")
    STARTING_HEALTH: int = Field(default=100, ge=1, description="初始生命值")


# =============================================================================
# 日志配置
# =============================================================================
class LogSettings(BaseSettings):
    """
    日志配置
    
    环境变量：
        LOG_LEVEL: 日志级别
        LOG_FORMAT: 日志格式（json/text）
        LOG_FILE: 日志文件路径
        LOG_MAX_SIZE: 日志文件最大大小（MB）
        LOG_BACKUP_COUNT: 日志备份数量
    """
    
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    LEVEL: str = Field(default="INFO", description="日志级别")
    FORMAT: str = Field(default="json", description="日志格式（json/text）")
    FILE: str = Field(default="logs/app.log", description="日志文件路径")
    MAX_SIZE: int = Field(default=10, ge=1, le=100, description="日志文件最大大小（MB）")
    BACKUP_COUNT: int = Field(default=5, ge=1, le=30, description="日志备份数量")
    
    @field_validator("LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"无效的日志级别: {v}，有效值: {valid_levels}")
        return v_upper


# =============================================================================
# 主配置类
# =============================================================================
class Settings(BaseSettings):
    """
    应用主配置
    
    整合所有配置模块，提供统一的配置访问接口。
    
    使用方式：
        from config.settings import settings
        
        # 访问数据库配置
        print(settings.database.url)
        
        # 访问 Redis 配置
        print(settings.redis.url)
        
        # 检查环境
        if settings.is_production:
            print("生产环境")
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    
    # 环境配置
    APP_ENV: str = Field(
        default="development",
        description="运行环境（development/staging/production）"
    )
    DEBUG: bool = Field(default=False, description="调试模式")
    APP_NAME: str = Field(default="王者之奕", description="应用名称")
    APP_VERSION: str = Field(default="0.1.0", description="应用版本")
    
    # 子配置模块
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    game: GameSettings = Field(default_factory=GameSettings)
    logging: LogSettings = Field(default_factory=LogSettings)
    
    @property
    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return Environment.is_production(self.APP_ENV)
    
    @property
    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return Environment.is_development(self.APP_ENV)
    
    @property
    def is_testing(self) -> bool:
        """检查是否为测试环境"""
        return self.APP_ENV.lower() == Environment.TESTING
    
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """验证生产环境配置"""
        if self.is_production:
            # 生产环境必须设置强密钥
            if len(self.security.SECRET_KEY) < 32:
                raise ValueError("生产环境 SECRET_KEY 必须至少 32 个字符")
            
            # 生产环境必须设置数据库密码
            if not self.database.PASSWORD:
                raise ValueError("生产环境必须设置数据库密码")
            
            # 生产环境禁用调试模式
            if self.DEBUG:
                raise ValueError("生产环境不能启用 DEBUG 模式")
        
        return self
    
    def get_cors_config(self) -> dict[str, Any]:
        """获取 CORS 配置字典"""
        return {
            "allow_origins": self.security.cors_origins_list,
            "allow_credentials": self.security.CORS_ALLOW_CREDENTIALS,
            "allow_methods": self.security.CORS_ALLOW_METHODS.split(","),
            "allow_headers": self.security.CORS_ALLOW_HEADERS.split(","),
        }


# =============================================================================
# 配置实例（单例模式）
# =============================================================================
@lru_cache
def get_settings() -> Settings:
    """
    获取配置实例（缓存）
    
    使用 lru_cache 确保配置只加载一次。
    如需重新加载配置，调用 get_settings.cache_clear()
    """
    return Settings()


# 全局配置实例
settings = get_settings()


# =============================================================================
# 配置导出
# =============================================================================
__all__ = [
    "Settings",
    "settings",
    "get_settings",
    "DatabaseSettings",
    "RedisSettings",
    "ServerSettings",
    "SecuritySettings",
    "GameSettings",
    "LogSettings",
    "Environment",
]


# =============================================================================
# 配置打印（调试用）
# =============================================================================
def print_settings() -> None:
    """打印当前配置（隐藏敏感信息）"""
    print("=" * 60)
    print("王者之奕 - 当前配置")
    print("=" * 60)
    print(f"环境: {settings.APP_ENV}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"版本: {settings.APP_VERSION}")
    print("-" * 60)
    print(f"服务器: {settings.server.HOST}:{settings.server.PORT}")
    print(f"数据库: {settings.database.HOST}:{settings.database.PORT}/{settings.database.NAME}")
    print(f"Redis: {settings.redis.HOST}:{settings.redis.PORT}/{settings.redis.DB}")
    print(f"日志级别: {settings.logging.LEVEL}")
    print("-" * 60)
    print(f"游戏: 最大 {settings.game.MAX_PLAYERS_PER_ROOM} 人/房间")
    print("=" * 60)


if __name__ == "__main__":
    print_settings()
