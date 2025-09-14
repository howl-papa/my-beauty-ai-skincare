"""
My Beauty AI Database Models

SQLAlchemy ORM models for the cosmetic ingredient analysis system.
These models correspond to the database schema defined in schema.sql.
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Date, Integer, String, Text, DECIMAL,
    ForeignKey, UniqueConstraint, CheckConstraint, text, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func


Base = declarative_base()

# Define PostgreSQL enum types
skin_type_enum = ENUM('dry', 'oily', 'combination', 'sensitive', 'normal', name='skin_type_enum')
routine_time_enum = ENUM('morning', 'evening', 'both', name='routine_time_enum')
conflict_severity_enum = ENUM('low', 'medium', 'high', 'critical', name='conflict_severity_enum')
approval_status_enum = ENUM('approved', 'pending', 'restricted', 'banned', name='approval_status_enum')


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime, 
        default=func.current_timestamp(), 
        onupdate=func.current_timestamp(),
        nullable=False
    )


class Brand(Base, TimestampMixin):
    """Cosmetic brand model."""

    __tablename__ = 'brands'

    brand_id = Column(Integer, primary_key=True)
    brand_name = Column(String(255), nullable=False, unique=True)
    brand_country = Column(String(100))
    brand_website = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(id={self.brand_id}, name='{self.brand_name}')>"

    @validates('brand_name')
    def validate_brand_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Brand name cannot be empty")
        return value.strip()


class Product(Base, TimestampMixin):
    """Cosmetic product model."""

    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True)
    product_name = Column(String(500), nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.brand_id', ondelete='CASCADE'), nullable=False)
    image_url = Column(String(1000))
    barcode = Column(String(100), unique=True)
    ingredients_raw = Column(Text)  # Original ingredient list as text
    product_type = Column(String(100))  # serum, moisturizer, cleanser, etc.
    price_usd = Column(DECIMAL(10, 2))
    volume_ml = Column(Integer)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    brand = relationship("Brand", back_populates="products")
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")
    routine_steps = relationship("RoutineStep", back_populates="product")
    conflict_predictions1 = relationship("ConflictPrediction", foreign_keys="ConflictPrediction.product1_id", back_populates="product1")
    conflict_predictions2 = relationship("ConflictPrediction", foreign_keys="ConflictPrediction.product2_id", back_populates="product2")

    # Constraints
    __table_args__ = (
        UniqueConstraint('brand_id', 'product_name', name='unique_brand_product'),
    )

    def __repr__(self):
        return f"<Product(id={self.product_id}, name='{self.product_name}')>"

    @validates('product_name')
    def validate_product_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Product name cannot be empty")
        return value.strip()

    @property
    def ingredients(self) -> List['Ingredient']:
        """Get list of ingredients for this product."""
        return [pi.ingredient for pi in self.product_ingredients if pi.is_active]


class Ingredient(Base, TimestampMixin):
    """Cosmetic ingredient model."""

    __tablename__ = 'ingredients'

    ingredient_id = Column(Integer, primary_key=True)
    ingredient_name = Column(String(255), nullable=False, unique=True)
    inci_name = Column(String(255))  # International Nomenclature of Cosmetic Ingredients
    korean_name = Column(String(255))
    chinese_name = Column(String(255))
    cas_number = Column(String(50))  # Chemical Abstracts Service number
    einecs_number = Column(String(50))  # European chemical identifier

    # Chemical properties
    molecular_formula = Column(String(200))
    molecular_weight = Column(DECIMAL(10, 4))
    ph_min = Column(DECIMAL(3, 1))
    ph_max = Column(DECIMAL(3, 1))

    # Regulatory information
    regulatory_status = Column(approval_status_enum, default='pending')
    max_concentration_face = Column(DECIMAL(5, 2))
    max_concentration_eye = Column(DECIMAL(5, 2))

    # Classification
    function_primary = Column(String(100))
    function_secondary = Column(String(100))
    ingredient_category = Column(String(100))

    # Safety information
    is_comedogenic = Column(Boolean, default=False)
    comedogenic_rating = Column(Integer, CheckConstraint('comedogenic_rating >= 0 AND comedogenic_rating <= 5'))
    is_photosensitive = Column(Boolean, default=False)
    pregnancy_safe = Column(Boolean)  # NULL means unknown/consult doctor

    # Data source tracking
    data_source = Column(String(100))
    origin_definition = Column(Text)

    # Relationships
    product_ingredients = relationship("ProductIngredient", back_populates="ingredient")
    conflicts1 = relationship("IngredientConflict", foreign_keys="IngredientConflict.ingredient1_id", back_populates="ingredient1")
    conflicts2 = relationship("IngredientConflict", foreign_keys="IngredientConflict.ingredient2_id", back_populates="ingredient2")
    skin_sensitivities = relationship("SkinSensitivity", back_populates="ingredient")
    document_ingredients = relationship("DocumentIngredient", back_populates="ingredient")

    def __repr__(self):
        return f"<Ingredient(id={self.ingredient_id}, name='{self.ingredient_name}')>"

    @validates('ingredient_name')
    def validate_ingredient_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Ingredient name cannot be empty")
        return value.strip()


class ProductIngredient(Base):
    """Junction table for product-ingredient relationships with concentration tracking."""

    __tablename__ = 'product_ingredients'

    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.ingredient_id', ondelete='CASCADE'), primary_key=True)
    concentration_percentage = Column(DECIMAL(5, 2))
    concentration_range = Column(String(50))  # e.g., "1-3%", "<0.5%"
    ingredient_order = Column(Integer)  # Order in ingredient list
    is_active = Column(Boolean, default=True, nullable=False)
    added_date = Column(DateTime, default=func.current_timestamp(), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")

    def __repr__(self):
        return f"<ProductIngredient(product_id={self.product_id}, ingredient_id={self.ingredient_id})>"


class User(Base, TimestampMixin):
    """User model for personalized recommendations."""

    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    skin_type = Column(skin_type_enum)
    skin_concerns = Column(ARRAY(String))
    allergies = Column(ARRAY(String))

    # Preferences
    preferred_routine_complexity = Column(String(20), default='moderate')
    preferred_price_range = Column(String(20), default='medium')
    timezone = Column(String(50), default='UTC')

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)

    # Relationships
    routines = relationship("UserRoutine", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("RoutineAnalytics", back_populates="user", cascade="all, delete-orphan")
    conflict_predictions = relationship("ConflictPrediction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}')>"

    @validates('email')
    def validate_email(self, key, value):
        import re
        if not value or not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise ValueError("Invalid email format")
        return value.lower().strip()


class UserRoutine(Base, TimestampMixin):
    """User's personalized skincare routines."""

    __tablename__ = 'user_routines'

    routine_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    routine_name = Column(String(255), nullable=False)
    routine_time = Column(routine_time_enum, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="routines")
    steps = relationship("RoutineStep", back_populates="routine", cascade="all, delete-orphan", order_by="RoutineStep.step_order")
    analytics = relationship("RoutineAnalytics", back_populates="routine", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'routine_name', 'routine_time', name='unique_user_routine'),
    )

    def __repr__(self):
        return f"<UserRoutine(id={self.routine_id}, name='{self.routine_name}')>"


class RoutineStep(Base):
    """Individual steps in a skincare routine."""

    __tablename__ = 'routine_steps'

    step_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    routine_id = Column(UUID(as_uuid=True), ForeignKey('user_routines.routine_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    step_order = Column(Integer, nullable=False)
    wait_minutes = Column(Integer, default=0)
    notes = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    routine = relationship("UserRoutine", back_populates="steps")
    product = relationship("Product", back_populates="routine_steps")

    # Constraints
    __table_args__ = (
        UniqueConstraint('routine_id', 'step_order', name='unique_routine_step_order'),
    )

    def __repr__(self):
        return f"<RoutineStep(routine_id={self.routine_id}, order={self.step_order})>"


class IngredientConflict(Base, TimestampMixin):
    """Known conflicts between ingredients."""

    __tablename__ = 'ingredient_conflicts'

    conflict_id = Column(Integer, primary_key=True)
    ingredient1_id = Column(Integer, ForeignKey('ingredients.ingredient_id', ondelete='CASCADE'), nullable=False)
    ingredient2_id = Column(Integer, ForeignKey('ingredients.ingredient_id', ondelete='CASCADE'), nullable=False)

    # Conflict details
    conflict_type = Column(String(50), nullable=False)  # chemical, physical, effectiveness
    severity = Column(conflict_severity_enum, nullable=False)
    description = Column(Text, nullable=False)
    scientific_explanation = Column(Text)

    # Conditions
    ph_dependent = Column(Boolean, default=False)
    concentration_dependent = Column(Boolean, default=False)
    time_dependent = Column(Boolean, default=False)

    # Recommendations
    recommended_separation_hours = Column(Integer)
    alternative_suggestions = Column(Text)

    # Evidence
    evidence_level = Column(String(20), default='moderate')
    research_references = Column(ARRAY(String))

    # Metadata
    verified_by_expert = Column(Boolean, default=False)
    expert_id = Column(UUID(as_uuid=True))

    # Relationships
    ingredient1 = relationship("Ingredient", foreign_keys=[ingredient1_id], back_populates="conflicts1")
    ingredient2 = relationship("Ingredient", foreign_keys=[ingredient2_id], back_populates="conflicts2")

    # Constraints - ensure we don't duplicate conflicts
    __table_args__ = (
        UniqueConstraint(
            text('LEAST(ingredient1_id, ingredient2_id)'),
            text('GREATEST(ingredient1_id, ingredient2_id)'),
            name='unique_ingredient_pair'
        ),
    )

    def __repr__(self):
        return f"<IngredientConflict(id={self.conflict_id}, severity='{self.severity}')>"


class SkinSensitivity(Base):
    """Skin type specific sensitivities to ingredients."""

    __tablename__ = 'skin_sensitivities'

    sensitivity_id = Column(Integer, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.ingredient_id', ondelete='CASCADE'), nullable=False)
    skin_type = Column(skin_type_enum, nullable=False)
    sensitivity_level = Column(String(20), nullable=False)  # low, medium, high, avoid
    description = Column(Text)
    recommended_max_concentration = Column(DECIMAL(5, 2))
    patch_test_required = Column(Boolean, default=True)

    # Relationships
    ingredient = relationship("Ingredient", back_populates="skin_sensitivities")

    # Constraints
    __table_args__ = (
        UniqueConstraint('ingredient_id', 'skin_type', name='unique_ingredient_skin_type'),
    )

    def __repr__(self):
        return f"<SkinSensitivity(ingredient_id={self.ingredient_id}, skin_type='{self.skin_type}')>"


class KnowledgeDocument(Base, TimestampMixin):
    """Scientific documents for RAG system."""

    __tablename__ = 'knowledge_documents'

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(50))  # research_paper, clinical_study, regulatory_guideline
    source_url = Column(String(1000))
    publication_date = Column(Date)
    authors = Column(ARRAY(String))
    journal = Column(String(200))
    doi = Column(String(100))
    credibility_score = Column(Integer, CheckConstraint('credibility_score >= 1 AND credibility_score <= 10'))

    # For vector search (note: actual vector column would be defined with pgvector extension)
    # embedding_vector = Column(Vector(1536))

    # Relationships
    document_ingredients = relationship("DocumentIngredient", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.document_id}, title='{self.title[:50]}...')>"


class DocumentIngredient(Base):
    """Relationship between documents and ingredients."""

    __tablename__ = 'document_ingredients'

    document_id = Column(UUID(as_uuid=True), ForeignKey('knowledge_documents.document_id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.ingredient_id', ondelete='CASCADE'), primary_key=True)
    relevance_score = Column(DECIMAL(3, 2), CheckConstraint('relevance_score >= 0 AND relevance_score <= 1'))

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="document_ingredients")
    ingredient = relationship("Ingredient", back_populates="document_ingredients")

    def __repr__(self):
        return f"<DocumentIngredient(doc_id={self.document_id}, ingredient_id={self.ingredient_id})>"


class RoutineAnalytics(Base, TimestampMixin):
    """User routine performance tracking."""

    __tablename__ = 'routine_analytics'

    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    routine_id = Column(UUID(as_uuid=True), ForeignKey('user_routines.routine_id', ondelete='CASCADE'), nullable=False)

    # User feedback
    effectiveness_rating = Column(Integer, CheckConstraint('effectiveness_rating >= 1 AND effectiveness_rating <= 5'))
    skin_condition_improvement = Column(Boolean)
    experienced_irritation = Column(Boolean, default=False)
    ease_of_use_rating = Column(Integer, CheckConstraint('ease_of_use_rating >= 1 AND ease_of_use_rating <= 5'))

    # Usage tracking
    adherence_percentage = Column(DECIMAL(5, 2))
    average_completion_time_minutes = Column(Integer)

    feedback_date = Column(Date, nullable=False)
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="analytics")
    routine = relationship("UserRoutine", back_populates="analytics")

    def __repr__(self):
        return f"<RoutineAnalytics(id={self.analytics_id}, rating={self.effectiveness_rating})>"


class ConflictPrediction(Base, TimestampMixin):
    """Conflict prediction results tracking."""

    __tablename__ = 'conflict_predictions'

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product1_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    product2_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)

    predicted_conflict_severity = Column(conflict_severity_enum)
    confidence_score = Column(DECIMAL(3, 2), CheckConstraint('confidence_score >= 0 AND confidence_score <= 1'))
    prediction_explanation = Column(Text)

    # User outcome
    user_proceeded = Column(Boolean)
    actual_outcome = Column(String(50))  # no_issue, mild_irritation, severe_reaction, etc.
    user_feedback = Column(Text)

    prediction_date = Column(DateTime, default=func.current_timestamp(), nullable=False)
    outcome_date = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="conflict_predictions")
    product1 = relationship("Product", foreign_keys=[product1_id], back_populates="conflict_predictions1")
    product2 = relationship("Product", foreign_keys=[product2_id], back_populates="conflict_predictions2")

    def __repr__(self):
        return f"<ConflictPrediction(id={self.prediction_id}, severity='{self.predicted_conflict_severity}')>"


# Database views as models (read-only)
class ProductSummary(Base):
    """View for product summary with ingredient count."""

    __tablename__ = 'product_summary'

    product_id = Column(Integer, primary_key=True)
    product_name = Column(String(500))
    brand_name = Column(String(255))
    product_type = Column(String(100))
    ingredient_count = Column(Integer)
    price_usd = Column(DECIMAL(10, 2))
    created_at = Column(DateTime)

    # This is a view, so we don't want SQLAlchemy to try to create/modify it
    __table_args__ = {'info': {'is_view': True}}


class IngredientUsageStats(Base):
    """View for ingredient usage statistics."""

    __tablename__ = 'ingredient_usage_stats'

    ingredient_id = Column(Integer, primary_key=True)
    ingredient_name = Column(String(255))
    inci_name = Column(String(255))
    function_primary = Column(String(100))
    used_in_products = Column(Integer)
    avg_concentration = Column(DECIMAL(5, 2))

    # This is a view, so we don't want SQLAlchemy to try to create/modify it
    __table_args__ = {'info': {'is_view': True}}
