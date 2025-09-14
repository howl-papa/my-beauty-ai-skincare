"""
My Beauty AI Routine Optimizer

Intelligent skincare routine optimization system that generates personalized
schedules, application orders, and usage frequencies based on ingredients,
skin type, and user preferences.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, time
import math

from sqlalchemy.orm import Session
from loguru import logger

from models import (
    Product, Ingredient, ProductIngredient, User, UserRoutine, 
    RoutineStep, RoutineAnalytics
)
from rag_system import BeautyRAGSystem
from conflict_analyzer import ConflictAnalyzer, ConflictSeverity
from config import get_config


class RoutineTime(Enum):
    """Time of day for routine application."""
    MORNING = "morning"
    EVENING = "evening"
    BOTH = "both"


class ApplicationFrequency(Enum):
    """Frequency of product application."""
    DAILY = "daily"
    ALTERNATE_DAYS = "alternate_days"
    TWICE_WEEKLY = "twice_weekly"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"


class ProductCategory(Enum):
    """Product categories for ordering logic."""
    CLEANSER = "cleanser"
    TONER = "toner"
    ESSENCE = "essence"
    SERUM = "serum"
    TREATMENT = "treatment"
    MOISTURIZER = "moisturizer"
    SUNSCREEN = "sunscreen"
    OIL = "oil"
    MASK = "mask"


@dataclass
class RoutineStep:
    """Individual step in an optimized routine."""
    step_number: int
    product_name: str
    product_id: Optional[int] = None
    category: Optional[ProductCategory] = None
    application_time: Optional[RoutineTime] = None
    frequency: ApplicationFrequency = ApplicationFrequency.DAILY
    wait_minutes: int = 0
    instructions: str = ""
    reasons: List[str] = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


@dataclass
class OptimizedRoutine:
    """Complete optimized routine with morning and evening steps."""
    user_id: Optional[str] = None
    routine_name: str = "Optimized Routine"
    morning_steps: List[RoutineStep] = None
    evening_steps: List[RoutineStep] = None
    general_recommendations: List[str] = None
    conflict_warnings: List[str] = None
    expected_timeline: str = ""
    confidence_score: float = 0.0
    created_at: datetime = None

    def __post_init__(self):
        if self.morning_steps is None:
            self.morning_steps = []
        if self.evening_steps is None:
            self.evening_steps = []
        if self.general_recommendations is None:
            self.general_recommendations = []
        if self.conflict_warnings is None:
            self.conflict_warnings = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_id': self.user_id,
            'routine_name': self.routine_name,
            'morning_steps': [asdict(step) for step in self.morning_steps],
            'evening_steps': [asdict(step) for step in self.evening_steps],
            'general_recommendations': self.general_recommendations,
            'conflict_warnings': self.conflict_warnings,
            'expected_timeline': self.expected_timeline,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'total_morning_steps': len(self.morning_steps),
            'total_evening_steps': len(self.evening_steps)
        }


class RoutineOptimizer:
    """
    Intelligent routine optimization system.

    Uses multi-factor analysis to create personalized skincare routines:
    1. Ingredient compatibility and timing
    2. Product categories and application order
    3. User skin type and concerns
    4. Seasonal and environmental factors
    5. RAG-powered expert knowledge
    """

    def __init__(self, db_session: Session, conflict_analyzer: ConflictAnalyzer = None,
                 rag_system: BeautyRAGSystem = None):
        self.db_session = db_session
        self.config = get_config()
        self.conflict_analyzer = conflict_analyzer
        self.rag_system = rag_system

        # Initialize optimization rules
        self._setup_ingredient_timing_rules()
        self._setup_product_category_rules()
        self._setup_application_order_rules()

        logger.info("Routine Optimizer initialized")

    def _setup_ingredient_timing_rules(self):
        """Set up timing preferences for different ingredients."""

        # Morning-preferred ingredients
        self.morning_ingredients = {
            'vitamin c', 'l-ascorbic acid', 'magnesium ascorbyl phosphate',
            'niacinamide', 'hyaluronic acid', 'peptides', 'antioxidants'
        }

        # Evening-preferred ingredients
        self.evening_ingredients = {
            'retinol', 'tretinoin', 'retinyl palmitate', 'bakuchiol',
            'glycolic acid', 'lactic acid', 'salicylic acid',
            'hydroquinone', 'kojic acid'
        }

        # Photosensitizing ingredients (evening only)
        self.photosensitive_ingredients = {
            'retinol', 'tretinoin', 'glycolic acid', 'lactic acid',
            'hydroquinone', 'benzoyl peroxide'
        }

        # Frequency adjustment based on potency
        self.frequency_modifiers = {
            'retinol': ApplicationFrequency.ALTERNATE_DAYS,
            'tretinoin': ApplicationFrequency.ALTERNATE_DAYS,
            'glycolic acid': ApplicationFrequency.TWICE_WEEKLY,
            'salicylic acid': ApplicationFrequency.ALTERNATE_DAYS,
            'hydroquinone': ApplicationFrequency.DAILY,
        }

        logger.debug("Ingredient timing rules initialized")

    def _setup_product_category_rules(self):
        """Set up product category classification rules."""

        self.category_keywords = {
            ProductCategory.CLEANSER: ['cleanser', 'cleansing', 'foam', 'gel cleanser', 'face wash'],
            ProductCategory.TONER: ['toner', 'tonic', 'astringent', 'essence toner'],
            ProductCategory.ESSENCE: ['essence', 'first essence', 'treatment essence'],
            ProductCategory.SERUM: ['serum', 'concentrate', 'ampoule', 'booster'],
            ProductCategory.TREATMENT: ['treatment', 'spot treatment', 'targeted'],
            ProductCategory.MOISTURIZER: ['moisturizer', 'cream', 'lotion', 'hydrator'],
            ProductCategory.SUNSCREEN: ['sunscreen', 'spf', 'sun protection', 'uv protection'],
            ProductCategory.OIL: ['oil', 'facial oil', 'face oil'],
            ProductCategory.MASK: ['mask', 'sheet mask', 'sleeping mask']
        }

        # Wait times between categories (in minutes)
        self.category_wait_times = {
            ProductCategory.TONER: 1,
            ProductCategory.ESSENCE: 2,
            ProductCategory.SERUM: 5,
            ProductCategory.TREATMENT: 10,
            ProductCategory.MOISTURIZER: 2,
            ProductCategory.OIL: 5,
            ProductCategory.SUNSCREEN: 0
        }

    def _setup_application_order_rules(self):
        """Set up application order based on texture and function."""

        # Standard application order (thinnest to thickest + function)
        self.application_order = [
            ProductCategory.CLEANSER,      # Only in cleansing step
            ProductCategory.TONER,         # Prep skin
            ProductCategory.ESSENCE,       # Light hydration
            ProductCategory.SERUM,         # Active ingredients
            ProductCategory.TREATMENT,     # Targeted treatments
            ProductCategory.MOISTURIZER,   # Lock in moisture
            ProductCategory.OIL,          # Seal everything
            ProductCategory.SUNSCREEN     # Final protection (AM only)
        ]

    def optimize_routine(self, products: List[Dict[str, Any]], 
                        user_profile: Dict[str, Any] = None,
                        preferences: Dict[str, Any] = None) -> OptimizedRoutine:
        """
        Generate an optimized skincare routine.

        Args:
            products: List of product dictionaries with names and ingredients
            user_profile: User information (skin type, concerns, age, etc.)
            preferences: User preferences (routine complexity, time available, etc.)

        Returns:
            Complete optimized routine with morning and evening steps
        """
        logger.info(f"Optimizing routine for {len(products)} products")

        # Get detailed product information from database
        detailed_products = self._get_detailed_products(products)

        # Analyze conflicts first
        conflicts = []
        if self.conflict_analyzer:
            product_names = [p['name'] for p in products]
            skin_type = user_profile.get('skin_type') if user_profile else None
            conflict_report = self.conflict_analyzer.analyze_products(product_names, skin_type=skin_type)
            conflicts = conflict_report.conflicts

        # Categorize and analyze products
        categorized_products = self._categorize_products(detailed_products)

        # Determine optimal timing for each product
        timing_analysis = self._analyze_product_timing(detailed_products, user_profile)

        # Create morning and evening routines
        morning_routine = self._create_time_specific_routine(
            categorized_products, timing_analysis, RoutineTime.MORNING, conflicts, user_profile
        )
        evening_routine = self._create_time_specific_routine(
            categorized_products, timing_analysis, RoutineTime.EVENING, conflicts, user_profile
        )

        # Generate recommendations and warnings
        recommendations = self._generate_routine_recommendations(
            detailed_products, user_profile, preferences, conflicts
        )

        warnings = self._generate_conflict_warnings(conflicts)

        # Calculate expected timeline
        timeline = self._estimate_results_timeline(detailed_products, user_profile)

        # Calculate confidence score
        confidence = self._calculate_routine_confidence(
            detailed_products, user_profile, conflicts, len(morning_routine) + len(evening_routine)
        )

        # Get RAG-powered insights if available
        if self.rag_system:
            rag_insights = self._get_rag_insights(products, user_profile)
            recommendations.extend(rag_insights)

        # Create optimized routine
        routine = OptimizedRoutine(
            user_id=user_profile.get('user_id') if user_profile else None,
            routine_name=f"Optimized Routine - {datetime.now().strftime('%Y%m%d')}",
            morning_steps=morning_routine,
            evening_steps=evening_routine,
            general_recommendations=recommendations,
            conflict_warnings=warnings,
            expected_timeline=timeline,
            confidence_score=confidence
        )

        # Store routine if user provided
        if user_profile and user_profile.get('user_id'):
            self._store_user_routine(user_profile['user_id'], routine)

        logger.info(f"Routine optimization complete: {len(morning_routine)} AM + {len(evening_routine)} PM steps")
        return routine

    def _get_detailed_products(self, products: List[Dict[str, Any]]) -> List[Product]:
        """Get detailed product information from database."""
        detailed_products = []

        for product_info in products:
            product_name = product_info.get('name', '')

            # Try to find in database first
            db_product = self.db_session.query(Product).filter(
                Product.product_name.ilike(f'%{product_name}%')
            ).first()

            if db_product:
                detailed_products.append(db_product)
            else:
                # Create temporary product object for products not in DB
                # In production, you might want to add them to the database
                logger.warning(f"Product not found in database: {product_name}")

        return detailed_products

    def _categorize_products(self, products: List[Product]) -> Dict[ProductCategory, List[Product]]:
        """Categorize products based on name and ingredients."""
        categorized = {category: [] for category in ProductCategory}

        for product in products:
            category = self._determine_product_category(product)
            categorized[category].append(product)

        return categorized

    def _determine_product_category(self, product: Product) -> ProductCategory:
        """Determine product category based on name and type."""
        product_name = product.product_name.lower()
        product_type = (product.product_type or '').lower()

        # Check product type first
        if product_type:
            for category, keywords in self.category_keywords.items():
                if any(keyword in product_type for keyword in keywords):
                    return category

        # Check product name
        for category, keywords in self.category_keywords.items():
            if any(keyword in product_name for keyword in keywords):
                return category

        # Default categorization based on ingredients
        ingredient_names = [pi.ingredient.ingredient_name.lower() 
                          for pi in product.product_ingredients if pi.is_active]

        # If contains active ingredients, likely a serum/treatment
        active_ingredients = {'retinol', 'vitamin c', 'niacinamide', 'salicylic acid', 'glycolic acid'}
        if any(ing in ' '.join(ingredient_names) for ing in active_ingredients):
            return ProductCategory.SERUM

        # If contains moisturizing ingredients, likely a moisturizer
        moisturizing_ingredients = {'hyaluronic acid', 'ceramide', 'squalane', 'glycerin'}
        if any(ing in ' '.join(ingredient_names) for ing in moisturizing_ingredients):
            return ProductCategory.MOISTURIZER

        # Default to serum for unknown products
        return ProductCategory.SERUM

    def _analyze_product_timing(self, products: List[Product], 
                              user_profile: Dict[str, Any] = None) -> Dict[int, RoutineTime]:
        """Analyze optimal timing for each product based on ingredients."""
        timing_analysis = {}

        for product in products:
            ingredient_names = [pi.ingredient.ingredient_name.lower() 
                              for pi in product.product_ingredients if pi.is_active]

            morning_score = 0
            evening_score = 0

            # Score based on ingredient preferences
            for ingredient_name in ingredient_names:
                # Check specific ingredient timing preferences
                if any(ing in ingredient_name for ing in self.morning_ingredients):
                    morning_score += 1

                if any(ing in ingredient_name for ing in self.evening_ingredients):
                    evening_score += 1

                # Photosensitive ingredients strongly prefer evening
                if any(ing in ingredient_name for ing in self.photosensitive_ingredients):
                    evening_score += 3

            # Category-based timing preferences
            category = self._determine_product_category(product)

            if category == ProductCategory.SUNSCREEN:
                timing_analysis[product.product_id] = RoutineTime.MORNING
            elif category in [ProductCategory.CLEANSER]:
                timing_analysis[product.product_id] = RoutineTime.BOTH
            elif evening_score > morning_score:
                timing_analysis[product.product_id] = RoutineTime.EVENING
            elif morning_score > evening_score:
                timing_analysis[product.product_id] = RoutineTime.MORNING
            else:
                # Default based on category
                if category in [ProductCategory.SERUM, ProductCategory.TREATMENT]:
                    timing_analysis[product.product_id] = RoutineTime.EVENING
                else:
                    timing_analysis[product.product_id] = RoutineTime.BOTH

        return timing_analysis

    def _create_time_specific_routine(self, categorized_products: Dict[ProductCategory, List[Product]],
                                    timing_analysis: Dict[int, RoutineTime],
                                    routine_time: RoutineTime,
                                    conflicts: List[Any],
                                    user_profile: Dict[str, Any] = None) -> List[RoutineStep]:
        """Create routine steps for a specific time (morning or evening)."""

        steps = []
        step_number = 1

        # Filter products appropriate for this time
        time_appropriate_products = []
        for category in self.application_order:
            for product in categorized_products.get(category, []):
                product_timing = timing_analysis.get(product.product_id, RoutineTime.BOTH)

                if (product_timing == routine_time or 
                    product_timing == RoutineTime.BOTH or
                    (routine_time == RoutineTime.MORNING and category == ProductCategory.SUNSCREEN)):
                    time_appropriate_products.append((category, product))

        # Create steps in optimal order
        for category, product in time_appropriate_products:
            # Skip cleansers except for evening routine or if specifically mentioned
            if category == ProductCategory.CLEANSER and routine_time == RoutineTime.MORNING:
                continue

            # Check for conflicts and adjust
            frequency = self._determine_frequency(product, conflicts, user_profile)
            wait_time = self.category_wait_times.get(category, 0)
            instructions = self._generate_step_instructions(product, category, routine_time)
            reasons = self._generate_step_reasons(product, category, routine_time)

            step = RoutineStep(
                step_number=step_number,
                product_name=product.product_name,
                product_id=product.product_id,
                category=category,
                application_time=routine_time,
                frequency=frequency,
                wait_minutes=wait_time,
                instructions=instructions,
                reasons=reasons
            )

            steps.append(step)
            step_number += 1

        return steps

    def _determine_frequency(self, product: Product, conflicts: List[Any], 
                           user_profile: Dict[str, Any] = None) -> ApplicationFrequency:
        """Determine optimal frequency for a product."""

        # Check ingredient-based frequency modifiers
        ingredient_names = [pi.ingredient.ingredient_name.lower() 
                          for pi in product.product_ingredients if pi.is_active]

        for ingredient_name in ingredient_names:
            for modifier_ingredient, frequency in self.frequency_modifiers.items():
                if modifier_ingredient in ingredient_name:
                    return frequency

        # Adjust for sensitive skin
        if user_profile and user_profile.get('skin_type') == 'sensitive':
            # Check if product contains potentially irritating ingredients
            irritating_ingredients = {'retinol', 'glycolic acid', 'salicylic acid', 'benzoyl peroxide'}
            if any(ing in ' '.join(ingredient_names) for ing in irritating_ingredients):
                return ApplicationFrequency.ALTERNATE_DAYS

        # Adjust if conflicts detected
        product_conflicts = [c for c in conflicts 
                           if product.product_name in [c.ingredient1, c.ingredient2]]

        if any(c.severity == ConflictSeverity.HIGH for c in product_conflicts):
            return ApplicationFrequency.ALTERNATE_DAYS

        return ApplicationFrequency.DAILY

    def _generate_step_instructions(self, product: Product, category: ProductCategory, 
                                  routine_time: RoutineTime) -> str:
        """Generate specific instructions for applying a product."""

        base_instructions = {
            ProductCategory.CLEANSER: "Massage onto damp skin, rinse thoroughly with lukewarm water",
            ProductCategory.TONER: "Apply to clean skin using cotton pad or gentle patting motions",
            ProductCategory.ESSENCE: "Pat gently into skin until fully absorbed",
            ProductCategory.SERUM: "Apply 2-3 drops to face and neck, pat until absorbed",
            ProductCategory.TREATMENT: "Apply thin layer to affected areas only",
            ProductCategory.MOISTURIZER: "Apply evenly to face and neck with gentle upward motions",
            ProductCategory.OIL: "Warm 2-3 drops between palms, press into skin",
            ProductCategory.SUNSCREEN: "Apply liberally 15 minutes before sun exposure, reapply every 2 hours"
        }

        instruction = base_instructions.get(category, "Apply as directed on product packaging")

        # Add time-specific notes
        if routine_time == RoutineTime.EVENING and category == ProductCategory.TREATMENT:
            instruction += ". Start with 2-3 times per week and increase gradually"

        return instruction

    def _generate_step_reasons(self, product: Product, category: ProductCategory, 
                             routine_time: RoutineTime) -> List[str]:
        """Generate reasons for the timing and placement of this step."""

        reasons = []

        # Category-based reasons
        category_reasons = {
            ProductCategory.TONER: ["Prepares skin for better absorption of subsequent products"],
            ProductCategory.SERUM: ["Active ingredients work best on clean, prepared skin"],
            ProductCategory.MOISTURIZER: ["Seals in previous products and provides hydration"],
            ProductCategory.SUNSCREEN: ["Essential protection from UV damage and photoaging"]
        }

        reasons.extend(category_reasons.get(category, []))

        # Timing-specific reasons
        if routine_time == RoutineTime.MORNING:
            timing_reasons = {
                ProductCategory.SUNSCREEN: ["UV protection needed during daytime"],
                ProductCategory.SERUM: ["Antioxidants protect skin throughout the day"]
            }
        else:  # Evening
            timing_reasons = {
                ProductCategory.TREATMENT: ["Skin repairs and regenerates during sleep"],
                ProductCategory.OIL: ["Overnight nourishment without interfering with sunscreen"]
            }

        reasons.extend(timing_reasons.get(category, []))

        return reasons

    def _generate_routine_recommendations(self, products: List[Product],
                                        user_profile: Dict[str, Any] = None,
                                        preferences: Dict[str, Any] = None,
                                        conflicts: List[Any] = None) -> List[str]:
        """Generate general routine recommendations."""

        recommendations = []

        # Basic routine guidelines
        recommendations.append("🌅 Morning Focus: Protection and preparation for the day")
        recommendations.append("🌙 Evening Focus: Repair and renewal while you sleep")
        recommendations.append("⏰ Allow products to absorb between steps for maximum effectiveness")

        # Skin type specific recommendations
        if user_profile and user_profile.get('skin_type'):
            skin_type = user_profile['skin_type']
            skin_recommendations = {
                'dry': [
                    "💧 Layer hydrating products for maximum moisture retention",
                    "🛡️ Use gentle, cream-based cleansers to avoid stripping skin"
                ],
                'oily': [
                    "🧽 Use gel-based cleansers to control excess oil",
                    "⚖️ Balance active ingredients to avoid over-drying"
                ],
                'sensitive': [
                    "🧪 Always patch test new products before full application",
                    "👶 Start new actives slowly - 2-3 times per week initially"
                ],
                'combination': [
                    "🎯 Consider different products for T-zone and cheek areas",
                    "⚖️ Balance moisture and oil control across different face zones"
                ]
            }
            recommendations.extend(skin_recommendations.get(skin_type, []))

        # Product-specific recommendations
        active_ingredients = []
        for product in products:
            ingredient_names = [pi.ingredient.ingredient_name.lower() 
                              for pi in product.product_ingredients if pi.is_active]
            active_ingredients.extend(ingredient_names)

        if any('retinol' in ing for ing in active_ingredients):
            recommendations.append("🌙 Retinol products: Start slowly and always use sunscreen during the day")

        if any('vitamin c' in ing or 'ascorbic acid' in ing for ing in active_ingredients):
            recommendations.append("☀️ Vitamin C: Best used in morning for antioxidant protection")

        if any('acid' in ing for ing in active_ingredients):
            recommendations.append("🧪 Chemical exfoliants: Monitor skin response and adjust frequency as needed")

        # Conflict-based recommendations
        if conflicts:
            recommendations.append("⚠️ Some ingredients may interact - follow separation guidelines carefully")

        return recommendations

    def _generate_conflict_warnings(self, conflicts: List[Any]) -> List[str]:
        """Generate specific warnings about ingredient conflicts."""

        warnings = []

        for conflict in conflicts:
            if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                warnings.append(
                    f"⚠️ {conflict.severity.value.upper()}: "
                    f"{conflict.ingredient1} and {conflict.ingredient2} - {conflict.description}"
                )

                if conflict.separation_hours:
                    warnings.append(f"   → Separate by at least {conflict.separation_hours} hours")

        return warnings

    def _estimate_results_timeline(self, products: List[Product], 
                                 user_profile: Dict[str, Any] = None) -> str:
        """Estimate timeline for seeing results."""

        # Analyze ingredients for timeline estimation
        quick_results = []  # 1-2 weeks
        medium_results = []  # 4-6 weeks  
        long_results = []   # 3-6 months

        for product in products:
            ingredient_names = [pi.ingredient.ingredient_name.lower() 
                              for pi in product.product_ingredients if pi.is_active]

            for ingredient_name in ingredient_names:
                if any(ing in ingredient_name for ing in ['hyaluronic acid', 'glycerin', 'niacinamide']):
                    quick_results.append(ingredient_name)
                elif any(ing in ingredient_name for ing in ['vitamin c', 'salicylic acid', 'glycolic acid']):
                    medium_results.append(ingredient_name)
                elif any(ing in ingredient_name for ing in ['retinol', 'tretinoin']):
                    long_results.append(ingredient_name)

        timeline_parts = []

        if quick_results:
            timeline_parts.append("1-2 weeks: Improved hydration and skin texture")

        if medium_results:
            timeline_parts.append("4-6 weeks: Reduced blemishes and improved skin tone")

        if long_results:
            timeline_parts.append("3-6 months: Significant anti-aging and skin renewal benefits")

        if not timeline_parts:
            return "Results typically visible within 4-8 weeks of consistent use"

        return " | ".join(timeline_parts)

    def _calculate_routine_confidence(self, products: List[Product], 
                                    user_profile: Dict[str, Any] = None,
                                    conflicts: List[Any] = None,
                                    total_steps: int = 0) -> float:
        """Calculate confidence score for the routine optimization."""

        base_confidence = 0.7  # Base confidence

        # Boost confidence based on available information
        if user_profile:
            if user_profile.get('skin_type'):
                base_confidence += 0.1
            if user_profile.get('skin_concerns'):
                base_confidence += 0.05
            if user_profile.get('age'):
                base_confidence += 0.05

        # Product information quality
        db_products = sum(1 for p in products if p.product_id)
        if db_products == len(products):
            base_confidence += 0.1  # All products in database

        # Conflict analysis available
        if self.conflict_analyzer and conflicts is not None:
            base_confidence += 0.1
            # Reduce confidence if many conflicts
            if len(conflicts) > 2:
                base_confidence -= 0.05

        # Routine complexity (optimal range is 3-7 steps per routine)
        if 6 <= total_steps <= 14:  # 3-7 per routine
            base_confidence += 0.05
        elif total_steps > 20:  # Too complex
            base_confidence -= 0.1

        return round(min(base_confidence, 1.0), 2)

    def _get_rag_insights(self, products: List[Dict[str, Any]], 
                         user_profile: Dict[str, Any] = None) -> List[str]:
        """Get additional insights from RAG system."""

        if not self.rag_system:
            return []

        try:
            rag_result = self.rag_system.query_routine_optimization(products, user_profile or {})

            # Extract key insights from RAG response
            insights = []
            response_text = rag_result.get('routine_recommendation', '')

            # Simple extraction of actionable insights
            # In production, you'd want more sophisticated parsing
            if 'morning' in response_text.lower() and 'evening' in response_text.lower():
                insights.append("💡 RAG Insight: Consider timing separation based on ingredient interactions")

            if 'gradual' in response_text.lower() or 'slowly' in response_text.lower():
                insights.append("💡 RAG Insight: Introduce new products gradually to minimize irritation")

            return insights[:2]  # Limit to 2 insights

        except Exception as e:
            logger.warning(f"Could not get RAG insights: {e}")
            return []

    def _store_user_routine(self, user_id: str, routine: OptimizedRoutine):
        """Store optimized routine in database for user."""

        try:
            # Create morning routine
            if routine.morning_steps:
                morning_routine = UserRoutine(
                    user_id=user_id,
                    routine_name=f"{routine.routine_name} - Morning",
                    routine_time='morning'
                )
                self.db_session.add(morning_routine)
                self.db_session.flush()  # Get ID

                # Add steps
                for step in routine.morning_steps:
                    if step.product_id:
                        routine_step = RoutineStep(
                            routine_id=morning_routine.routine_id,
                            product_id=step.product_id,
                            step_order=step.step_number,
                            wait_minutes=step.wait_minutes,
                            notes=step.instructions
                        )
                        self.db_session.add(routine_step)

            # Create evening routine
            if routine.evening_steps:
                evening_routine = UserRoutine(
                    user_id=user_id,
                    routine_name=f"{routine.routine_name} - Evening",
                    routine_time='evening'
                )
                self.db_session.add(evening_routine)
                self.db_session.flush()  # Get ID

                # Add steps
                for step in routine.evening_steps:
                    if step.product_id:
                        routine_step = RoutineStep(
                            routine_id=evening_routine.routine_id,
                            product_id=step.product_id,
                            step_order=step.step_number,
                            wait_minutes=step.wait_minutes,
                            notes=step.instructions
                        )
                        self.db_session.add(routine_step)

            self.db_session.commit()
            logger.info(f"Stored optimized routine for user {user_id}")

        except Exception as e:
            logger.error(f"Error storing user routine: {e}")
            self.db_session.rollback()


# Factory function
def create_routine_optimizer(db_session: Session,
                           conflict_analyzer: ConflictAnalyzer = None,
                           rag_system: BeautyRAGSystem = None) -> RoutineOptimizer:
    """Create and initialize a RoutineOptimizer instance."""
    return RoutineOptimizer(db_session, conflict_analyzer, rag_system)
