"""
Configuration management for My Beauty AI system.
Handles database connections, API keys, and environment-specific settings.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'my_beauty_ai')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')

    # Connection pool settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))

    @property
    def url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def url_async(self) -> str:
        """Generate async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str = os.getenv('OPENAI_API_KEY', '')
    model: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    embedding_model: str = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
    max_tokens: int = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
    temperature: float = float(os.getenv('OPENAI_TEMPERATURE', '0.2'))

    def validate(self) -> bool:
        """Validate OpenAI configuration"""
        return bool(self.api_key and self.api_key.startswith('sk-'))

@dataclass
class ChromaDBConfig:
    """ChromaDB vector database configuration"""
    persist_directory: str = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
    collection_name: str = os.getenv('CHROMA_COLLECTION', 'cosmetic_knowledge')

    # Embedding settings
    embedding_dimension: int = 1536  # OpenAI embedding size
    similarity_top_k: int = int(os.getenv('CHROMA_SIMILARITY_TOP_K', '10'))

@dataclass
class RAGConfig:
    """RAG system configuration"""
    chunk_size: int = int(os.getenv('RAG_CHUNK_SIZE', '1000'))
    chunk_overlap: int = int(os.getenv('RAG_CHUNK_OVERLAP', '200'))
    similarity_threshold: float = float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.7'))

    # Query settings
    max_retrieved_docs: int = int(os.getenv('RAG_MAX_DOCS', '5'))
    confidence_threshold: float = float(os.getenv('RAG_CONFIDENCE_THRESHOLD', '0.6'))

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    secret_key: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    jwt_secret: str = os.getenv('JWT_SECRET', 'jwt-secret-key')
    jwt_expiry_hours: int = int(os.getenv('JWT_EXPIRY_HOURS', '24'))

    # API rate limiting
    rate_limit_per_minute: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))

    def validate(self) -> bool:
        """Validate security configuration"""
        return len(self.secret_key) >= 16 and len(self.jwt_secret) >= 16

@dataclass
class CacheConfig:
    """Caching configuration"""
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    default_timeout: int = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '3600'))

    # Analysis cache settings
    conflict_analysis_timeout: int = int(os.getenv('CACHE_CONFLICT_TIMEOUT', '7200'))
    routine_optimization_timeout: int = int(os.getenv('CACHE_ROUTINE_TIMEOUT', '3600'))

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_path: Optional[str] = os.getenv('LOG_FILE_PATH')

    # Component-specific logging
    log_database_queries: bool = os.getenv('LOG_DB_QUERIES', 'false').lower() == 'true'
    log_api_requests: bool = os.getenv('LOG_API_REQUESTS', 'true').lower() == 'true'
    log_rag_queries: bool = os.getenv('LOG_RAG_QUERIES', 'true').lower() == 'true'

@dataclass
class FeatureFlags:
    """Feature flags for enabling/disabling functionality"""
    enable_caching: bool = os.getenv('FEATURE_CACHING', 'true').lower() == 'true'
    enable_rag_system: bool = os.getenv('FEATURE_RAG', 'true').lower() == 'true'
    enable_conflict_analysis: bool = os.getenv('FEATURE_CONFLICTS', 'true').lower() == 'true'
    enable_routine_optimization: bool = os.getenv('FEATURE_OPTIMIZATION', 'true').lower() == 'true'
    enable_user_profiles: bool = os.getenv('FEATURE_USER_PROFILES', 'true').lower() == 'true'

    # Development features
    enable_debug_mode: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    enable_api_docs: bool = os.getenv('ENABLE_API_DOCS', 'true').lower() == 'true'

@dataclass
class AppConfig:
    """Main application configuration"""
    environment: str = os.getenv('ENVIRONMENT', 'development')
    host: str = os.getenv('HOST', '127.0.0.1')
    port: int = int(os.getenv('PORT', '5000'))

    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    chromadb: ChromaDBConfig = field(default_factory=ChromaDBConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'

    def validate(self) -> List[str]:
        """Validate all configuration settings and return list of errors"""
        errors = []

        # Validate OpenAI configuration
        if not self.openai.validate():
            errors.append("Invalid OpenAI API key")

        # Validate security configuration
        if not self.security.validate():
            errors.append("Security configuration validation failed")

        # Validate database connection
        if not self.database.password and self.is_production:
            errors.append("Database password required in production")

        # Validate required directories
        os.makedirs(self.chromadb.persist_directory, exist_ok=True)

        return errors

# Global configuration instance
config = AppConfig()

# Validation on import
validation_errors = config.validate()
if validation_errors and config.is_production:
    raise ValueError(f"Configuration validation failed: {', '.join(validation_errors)}")

def get_database_url() -> str:
    """Get database connection URL"""
    return config.database.url

def get_openai_client_config() -> dict:
    """Get OpenAI client configuration"""
    return {
        'api_key': config.openai.api_key,
        'model': config.openai.model,
        'max_tokens': config.openai.max_tokens,
        'temperature': config.openai.temperature,
    }

def get_chroma_config() -> dict:
    """Get ChromaDB configuration"""
    return {
        'persist_directory': config.chromadb.persist_directory,
        'collection_name': config.chromadb.collection_name,
    }

# Environment-specific configurations
FLASK_CONFIG = {
    'development': {
        'DEBUG': True,
        'TESTING': False,
        'SQLALCHEMY_ECHO': config.logging.log_database_queries,
    },
    'testing': {
        'DEBUG': False,
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    },
    'production': {
        'DEBUG': False,
        'TESTING': False,
        'SQLALCHEMY_ECHO': False,
    }
}

def get_flask_config() -> dict:
    """Get Flask-specific configuration"""
    base_config = FLASK_CONFIG.get(config.environment, FLASK_CONFIG['development'])

    return {
        **base_config,
        'SECRET_KEY': config.security.secret_key,
        'SQLALCHEMY_DATABASE_URI': config.database.url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_size': config.database.pool_size,
            'max_overflow': config.database.max_overflow,
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    }

# Export commonly used configurations
__all__ = [
    'config',
    'AppConfig',
    'DatabaseConfig', 
    'OpenAIConfig',
    'ChromaDBConfig',
    'RAGConfig',
    'SecurityConfig',
    'CacheConfig',
    'LoggingConfig',
    'FeatureFlags',
    'get_database_url',
    'get_openai_client_config', 
    'get_chroma_config',
    'get_flask_config',
]
