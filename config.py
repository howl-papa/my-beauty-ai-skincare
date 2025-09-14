"""
My Beauty AI Configuration Module

This module handles all configuration settings for the application,
including database connections, API keys, and environment-specific settings.
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'mybeauty_ai')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')

    # Connection pool settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_connection_string(self) -> str:
        """Generate async PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""

    api_key: str = os.getenv('OPENAI_API_KEY', '')
    model: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    embedding_model: str = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
    max_tokens: int = int(os.getenv('OPENAI_MAX_TOKENS', '1500'))
    temperature: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))

    # Rate limiting
    requests_per_minute: int = int(os.getenv('OPENAI_RPM', '3000'))
    tokens_per_minute: int = int(os.getenv('OPENAI_TPM', '40000'))


@dataclass
class VectorStoreConfig:
    """Vector database configuration."""

    provider: str = os.getenv('VECTOR_STORE_PROVIDER', 'chroma')  # chroma, pinecone, weaviate

    # ChromaDB settings
    chroma_persist_directory: str = os.getenv('CHROMA_PERSIST_DIR', './data/chroma_db')
    chroma_collection_name: str = os.getenv('CHROMA_COLLECTION', 'beauty_knowledge')

    # Pinecone settings (if used)
    pinecone_api_key: str = os.getenv('PINECONE_API_KEY', '')
    pinecone_environment: str = os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')
    pinecone_index_name: str = os.getenv('PINECONE_INDEX_NAME', 'beauty-ai')

    # Vector dimensions and similarity metrics
    embedding_dimension: int = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
    similarity_metric: str = os.getenv('SIMILARITY_METRIC', 'cosine')

    # RAG settings
    chunk_size: int = int(os.getenv('RAG_CHUNK_SIZE', '1000'))
    chunk_overlap: int = int(os.getenv('RAG_CHUNK_OVERLAP', '200'))
    top_k_retrieval: int = int(os.getenv('RAG_TOP_K', '5'))
    similarity_threshold: float = float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.7'))


@dataclass
class SecurityConfig:
    """Security and authentication configuration."""

    secret_key: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    jwt_access_token_expires: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    jwt_refresh_token_expires: int = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days

    # Password hashing
    bcrypt_rounds: int = int(os.getenv('BCRYPT_ROUNDS', '12'))

    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '100'))
    rate_limit_per_hour: int = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))

    # CORS settings
    cors_origins: List[str] = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')


@dataclass
class CacheConfig:
    """Caching configuration."""

    provider: str = os.getenv('CACHE_PROVIDER', 'redis')  # redis, memory

    # Redis settings
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    redis_password: str = os.getenv('REDIS_PASSWORD', '')

    # Cache TTL settings (in seconds)
    ingredient_cache_ttl: int = int(os.getenv('INGREDIENT_CACHE_TTL', '86400'))  # 24 hours
    product_cache_ttl: int = int(os.getenv('PRODUCT_CACHE_TTL', '3600'))  # 1 hour
    conflict_cache_ttl: int = int(os.getenv('CONFLICT_CACHE_TTL', '7200'))  # 2 hours
    routine_cache_ttl: int = int(os.getenv('ROUTINE_CACHE_TTL', '1800'))  # 30 minutes


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', '{time} | {level} | {name}:{function}:{line} | {message}')

    # File logging
    log_to_file: bool = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    log_file_path: str = os.getenv('LOG_FILE_PATH', './logs/beauty_ai.log')
    log_rotation: str = os.getenv('LOG_ROTATION', '10 MB')
    log_retention: str = os.getenv('LOG_RETENTION', '30 days')

    # External logging (optional)
    sentry_dsn: str = os.getenv('SENTRY_DSN', '')


@dataclass
class EmailConfig:
    """Email configuration for notifications."""

    smtp_server: str = os.getenv('SMTP_SERVER', 'localhost')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_username: str = os.getenv('SMTP_USERNAME', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    smtp_use_tls: bool = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    from_email: str = os.getenv('FROM_EMAIL', 'noreply@mybeauty-ai.com')
    admin_email: str = os.getenv('ADMIN_EMAIL', 'admin@mybeauty-ai.com')


@dataclass
class AppConfig:
    """Main application configuration."""

    # Environment
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    testing: bool = os.getenv('TESTING', 'false').lower() == 'true'

    # Server settings
    host: str = os.getenv('APP_HOST', '0.0.0.0')
    port: int = int(os.getenv('APP_PORT', '5000'))

    # Application metadata
    app_name: str = os.getenv('APP_NAME', 'My Beauty AI')
    version: str = os.getenv('APP_VERSION', '1.0.0')

    # Feature flags
    enable_conflict_detection: bool = os.getenv('ENABLE_CONFLICT_DETECTION', 'true').lower() == 'true'
    enable_routine_optimization: bool = os.getenv('ENABLE_ROUTINE_OPTIMIZATION', 'true').lower() == 'true'
    enable_analytics: bool = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'

    # Data sources
    enable_kfda_integration: bool = os.getenv('ENABLE_KFDA_INTEGRATION', 'false').lower() == 'true'
    kfda_api_key: str = os.getenv('KFDA_API_KEY', '')

    # Medical disclaimer settings
    require_medical_disclaimer: bool = os.getenv('REQUIRE_MEDICAL_DISCLAIMER', 'true').lower() == 'true'
    max_conflict_severity_without_warning: str = os.getenv('MAX_SEVERITY_NO_WARNING', 'low')


class Config:
    """Unified configuration class."""

    def __init__(self):
        self.app = AppConfig()
        self.database = DatabaseConfig()
        self.openai = OpenAIConfig()
        self.vector_store = VectorStoreConfig()
        self.security = SecurityConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.email = EmailConfig()

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Check required OpenAI API key
        if not self.openai.api_key:
            errors.append("OPENAI_API_KEY is required")

        # Check database configuration
        if not self.database.password and self.app.environment == 'production':
            errors.append("DB_PASSWORD is required in production")

        # Check secret keys in production
        if self.app.environment == 'production':
            if self.security.secret_key == 'dev-secret-key-change-in-production':
                errors.append("SECRET_KEY must be changed in production")
            if self.security.jwt_secret_key == 'jwt-secret-key-change-in-production':
                errors.append("JWT_SECRET_KEY must be changed in production")

        # Validate vector store configuration
        if self.vector_store.provider == 'pinecone' and not self.vector_store.pinecone_api_key:
            errors.append("PINECONE_API_KEY is required when using Pinecone")

        return errors

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment.lower() == 'production'

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment.lower() == 'development'

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app.testing or self.app.environment.lower() == 'testing'


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def validate_config() -> None:
    """Validate configuration and raise exception if invalid."""
    errors = config.validate()
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_message)


# Convenience functions for common configurations
def get_database_url() -> str:
    """Get database connection URL."""
    return config.database.connection_string


def get_async_database_url() -> str:
    """Get async database connection URL."""
    return config.database.async_connection_string


def get_redis_url() -> str:
    """Get Redis connection URL."""
    if config.cache.redis_password:
        return f"redis://:{config.cache.redis_password}@{config.cache.redis_host}:{config.cache.redis_port}/{config.cache.redis_db}"
    return f"redis://{config.cache.redis_host}:{config.cache.redis_port}/{config.cache.redis_db}"


if __name__ == "__main__":
    # Print current configuration (for debugging)
    print(f"Environment: {config.app.environment}")
    print(f"Debug: {config.app.debug}")
    print(f"Database: {config.database.host}:{config.database.port}/{config.database.name}")
    print(f"Vector Store: {config.vector_store.provider}")

    # Validate configuration
    try:
        validate_config()
        print("✅ Configuration is valid")
    except ValueError as e:
        print(f"❌ Configuration errors:\n{e}")
