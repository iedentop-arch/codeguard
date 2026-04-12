"""
应用配置模块

使用 pydantic-settings 管理环境变量配置
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def load_private_key(key_value: str) -> str:
    """加载私钥，支持直接值或文件路径"""
    if not key_value or key_value.startswith("placeholder"):
        # 尝试从文件读取
        key_file = Path(__file__).parent.parent.parent / "private-key.pem"
        if key_file.exists():
            return key_file.read_text()
        return ""
    # 如果是文件路径引用 (@private-key.pem)
    if key_value.startswith("@"):
        key_file = Path(__file__).parent.parent.parent / key_value[1:]
        if key_file.exists():
            return key_file.read_text()
    return key_value


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 允许忽略占位符等额外字段
    )

    # 应用配置
    APP_NAME: str = "CodeGuard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/codeguard"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # GitHub App配置
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY: str = ""  # 支持直接填值或保存到 private-key.pem 文件
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_APP_INSTALLATION_ID: int = 0

    # 文件存储
    UPLOAD_DIR: str = "./uploads"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()


def get_private_key() -> str:
    """获取 GitHub App 私钥（支持文件读取）"""
    return load_private_key(settings.GITHUB_APP_PRIVATE_KEY)
