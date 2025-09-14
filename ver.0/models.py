"""
SQLAlchemy models for My Beauty AI database.
Defines ORM models matching the PostgreSQL schema.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Numeric, Text, 
    ForeignKey, CheckConstraint, Index, JSON, ARRAY, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

Base = declarative_base()

# Enum definitions matching database schema
class SkinTypeEnum(enum.Enum):
    OILY = "oily"
    DRY = "dry"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"
    NORMAL = "normal"

class ProductCategoryEnum(enum.Enum):
    CLEANSER = "cleanser"
    TONER = "toner"
    ESSENCE = "essence"
    SERUM = "serum"
    MOISTURIZER = "moisturizer"
    SUNSCREEN = "sunscreen"
    TREATMENT = "treatment"
    MASK = "mask"
    EXFOLIANT = "exfoliant"
    OIL = "oil"
    MIST = "mist"
    EYE_CREAM = "eye_cream"

class SeverityEnum(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RoutineTimeEnum(enum.Enum):
    MORNING = "morning"
    EVENING = "evening"
    BOTH = "both"

class Brand(Base):
    """Cosmetic brand information and metadata"""
    __tablename__ = 'brands'

    brand_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    country = Column(String(100))
    website = Column(String(500))
    description = Column(Text)
    founded_year = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(name='{self.name}', country='{self.country}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'brand_id': str(self.brand_id),
            'name': self.name,
            'country': self.country,
            'website': self.website,
            'description': self.description,
            'founded_year': self.founded_year,
            'is_active': self.is_active
        }

class Ingredient(Base):
    """Comprehensive ingredient database with chemical and functional properties"""
    __tablename__ = 'ingredients'

    ingredient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    inci_name = Column(String(255), index=True)  # International Nomenclature
    cas_number = Column(String(50))  # Chemical Abstracts Service number
    category = Column(String(100), index=True)
    function_type = Column(String(100))
    molecular_weight = Column(Numeric(10, 4))
    ph_range_min = Column(Numeric(3, 1))
    ph_range_max = Column(Numeric(3, 1))
    solubility = Column(String(100))
    description = Column(Text)
    benefits = Column(Text)
    side_effects = Column(Text)
    concentration_range_min = Column(Numeric(5, 2))
    concentration_range_max = Column(Numeric(5, 2))
    # embedding = Column(Vector(1536))  # Vector column for RAG
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    product_ingredients = relationship("ProductIngredient", back_populates="ingredient")
    conflict_rules_as_ingredient1 = relationship(
        "ConflictRule", 
        foreign_keys="ConflictRule.ingredient1_id",
        back_populates="ingredient1"
    )
    conflict_rules_as_ingredient2 = relationship(
        "ConflictRule", 
        foreign_keys="ConflictRule.ingredient2_id",
        back_populates="ingredient2"
    )

    @validates('concentration_range_min', 'concentration_range_max')
    def validate_concentration_range(self, key, value):
        if value is not None and (value < 0 or value > 100):
            raise ValueError(f"Concentration must be between 0 and 100, got {value}")
        return value

    def __repr__(self):
        return f"<Ingredient(name='{self.name}', category='{self.category}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ingredient_id': str(self.ingredient_id),
            'name': self.name,
            'inci_name': self.inci_name,
            'category': self.category,
            'function_type': self.function_type,
            'description': self.description,
            'benefits': self.benefits,
            'concentration_range_min': float(self.concentration_range_min) if self.concentration_range_min else None,
            'concentration_range_max': float(self.concentration_range_max) if self.concentration_range_max else None
        }

class Product(Base):
    """Product catalog with categorization and skin type targeting"""
    __tablename__ = 'products'

    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.brand_id'), nullable=False)
    name = Column(String(500), nullable=False)
    category = Column(SQLEnum(ProductCategoryEnum), nullable=False, index=True)
    subcategory = Column(String(100))
    price = Column(Numeric(10, 2))
    currency = Column(String(3), default='USD')
    volume_ml = Column(Integer)
    description = Column(Text)
    instructions = Column(Text)
    ph_level = Column(Numeric(3, 1))
    suitable_skin_types = Column(ARRAY(SQLEnum(SkinTypeEnum)))
    target_concerns = Column(ARRAY(Text))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('price >= 0', name='positive_price'),
        CheckConstraint('volume_ml > 0', name='positive_volume'),
    )

    # Relationships
    brand = relationship("Brand", back_populates="products")
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")

    @validates('price')
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative")
        return value

    def __repr__(self):
        return f"<Product(name='{self.name}', category='{self.category.value}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_id': str(self.product_id),
            'brand_id': str(self.brand_id),
            'name': self.name,
            'category': self.category.value,
            'subcategory': self.subcategory,
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'volume_ml': self.volume_ml,
            'description': self.description,
            'suitable_skin_types': [st.value for st in self.suitable_skin_types] if self.suitable_skin_types else [],
            'target_concerns': self.target_concerns or []
        }

class ProductIngredient(Base):
    """Junction table linking products to ingredients with concentration data"""
    __tablename__ = 'product_ingredients'

    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), primary_key=True)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), primary_key=True)
    concentration = Column(Numeric(5, 2))
    ingredient_order = Column(Integer)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime(timezone=True), default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('concentration >= 0 AND concentration <= 100', name='valid_concentration'),
        CheckConstraint('ingredient_order > 0', name='positive_order'),
    )

    # Relationships
    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")

    def __repr__(self):
        return f"<ProductIngredient(product_id='{self.product_id}', ingredient_id='{self.ingredient_id}')>"

class ConflictRule(Base):
    """Predefined rules for ingredient interactions and conflicts"""
    __tablename__ = 'conflict_rules'

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient1_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), nullable=False)
    ingredient2_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), nullable=False)
    severity = Column(SQLEnum(SeverityEnum), nullable=False, default=SeverityEnum.MEDIUM, index=True)
    description = Column(Text, nullable=False)
    scientific_basis = Column(Text)
    affected_skin_types = Column(ARRAY(SQLEnum(SkinTypeEnum)))
    time_separation_hours = Column(Integer)
    ph_conflict = Column(Boolean, default=False)
    concentration_limit = Column(Numeric(5, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('ingredient1_id != ingredient2_id', name='different_ingredients'),
        CheckConstraint('time_separation_hours >= 0', name='valid_separation'),
    )

    # Relationships
    ingredient1 = relationship("Ingredient", foreign_keys=[ingredient1_id], back_populates="conflict_rules_as_ingredient1")
    ingredient2 = relationship("Ingredient", foreign_keys=[ingredient2_id], back_populates="conflict_rules_as_ingredient2")

    def __repr__(self):
        return f"<ConflictRule(severity='{self.severity.value}', description='{self.description[:50]}...')>"

class UserProfile(Base):
    """User skin profiles and personalization preferences"""
    __tablename__ = 'user_profiles'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skin_type = Column(SQLEnum(SkinTypeEnum), nullable=False, index=True)
    skin_concerns = Column(ARRAY(Text))
    sensitivity_level = Column(String(20), default='moderate')
    allergies = Column(ARRAY(Text))
    age_range = Column(String(20))
    climate = Column(String(50))
    current_routine = Column(JSON)
    preferences = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    routine_logs = relationship("RoutineLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserProfile(skin_type='{self.skin_type.value}', concerns='{self.skin_concerns}')>"

class RoutineLog(Base):
    """Historical tracking of user routines and AI analysis results"""
    __tablename__ = 'routine_logs'

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.user_id'), nullable=True)
    session_id = Column(String(255), nullable=True)
    routine_data = Column(JSON, nullable=False)
    conflict_analysis = Column(JSON)
    optimization_suggestions = Column(JSON)
    rag_insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('user_id IS NOT NULL OR session_id IS NOT NULL', name='user_or_session'),
    )

    # Relationships
    user = relationship("UserProfile", back_populates="routine_logs")

    def __repr__(self):
        return f"<RoutineLog(user_id='{self.user_id}', session_id='{self.session_id}')>"

class RAGDocument(Base):
    """Document storage for RAG knowledge base system"""
    __tablename__ = 'rag_documents'

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500))
    document_type = Column(String(100), index=True)
    category = Column(String(100), index=True)
    author = Column(String(255))
    publication_date = Column(DateTime)
    # embedding = Column(Vector(1536))  # Document embedding
    metadata = Column(JSON)
    is_processed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RAGDocument(title='{self.title}', type='{self.document_type}')>"

class AnalysisCache(Base):
    """Performance optimization cache for expensive AI operations"""
    __tablename__ = 'analysis_cache'

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False, index=True)
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=False)
    confidence_score = Column(Numeric(3, 2))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='valid_confidence'),
    )

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self):
        return f"<AnalysisCache(type='{self.analysis_type}', key='{self.cache_key[:20]}...')>"

class SystemLog(Base):
    """System activity logging for debugging and monitoring"""
    __tablename__ = 'system_logs'

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False, index=True)
    component = Column(String(100), index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.user_id'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f"<SystemLog(level='{self.level}', component='{self.component}')>"

# Helper function to create all tables
def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

# Helper function for database session management
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

SessionLocal = sessionmaker()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Export all models
__all__ = [
    'Base',
    'SkinTypeEnum', 'ProductCategoryEnum', 'SeverityEnum', 'RoutineTimeEnum',
    'Brand', 'Ingredient', 'Product', 'ProductIngredient', 'ConflictRule',
    'UserProfile', 'RoutineLog', 'RAGDocument', 'AnalysisCache', 'SystemLog',
    'create_all_tables', 'get_db_session', 'SessionLocal'
]
