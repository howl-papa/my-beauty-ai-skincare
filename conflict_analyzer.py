"""
My Beauty AI Conflict Analyzer

Advanced ingredient conflict detection system that combines database rules
with RAG-powered analysis to identify potential interactions between cosmetic ingredients.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from models import (
    Ingredient, Product, ProductIngredient, IngredientConflict, 
    SkinSensitivity, ConflictPrediction, User
)
from rag_system import BeautyRAGSystem
from config import get_config


class ConflictSeverity(Enum):
    """Severity levels for ingredient conflicts."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ConflictType(Enum):
    """Types of ingredient conflicts."""
    CHEMICAL = "chemical"
    PHYSICAL = "physical"
    EFFECTIVENESS = "effectiveness"
    pH_INCOMPATIBILITY = "ph_incompatibility"
    PHOTOSENSITIVITY = "photosensitivity"


@dataclass
class ConflictResult:
    """Result of a conflict analysis."""
    ingredient1: str
    ingredient2: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    scientific_explanation: Optional[str] = None
    recommendations: List[str] = None
    confidence_score: float = 0.0
    source: str = "database"  # 'database', 'rag', 'heuristic'
    separation_hours: Optional[int] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ConflictAnalysisReport:
    """Comprehensive conflict analysis report."""
    products: List[str]
    ingredients: List[str]
    conflicts: List[ConflictResult]
    skin_type_warnings: List[Dict[str, Any]]
    overall_severity: ConflictSeverity
    safe_combinations: List[Tuple[str, str]]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime

    @property
    def has_conflicts(self) -> bool:
        """Check if any conflicts were found."""
        return len(self.conflicts) > 0

    @property
    def critical_conflicts(self) -> List[ConflictResult]:
        """Get only critical severity conflicts."""
        return [c for c in self.conflicts if c.severity == ConflictSeverity.CRITICAL]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'products': self.products,
            'ingredients': self.ingredients,
            'conflicts': [asdict(c) for c in self.conflicts],
            'skin_type_warnings': self.skin_type_warnings,
            'overall_severity': self.overall_severity.value,
            'safe_combinations': self.safe_combinations,
            'recommendations': self.recommendations,
            'confidence_score': self.confidence_score,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'has_conflicts': self.has_conflicts,
            'critical_count': len(self.critical_conflicts)
        }


class ConflictAnalyzer:
    """
    Advanced conflict detection system for cosmetic ingredients.

    Combines multiple analysis methods:
    1. Database rule matching
    2. RAG-powered knowledge retrieval
    3. Heuristic pH and chemical class analysis
    4. User-specific skin type considerations
    """

    def __init__(self, db_session: Session, rag_system: BeautyRAGSystem = None):
        self.db_session = db_session
        self.config = get_config()
        self.rag_system = rag_system

        # Initialize heuristic rules
        self._setup_heuristic_rules()

        logger.info("Conflict Analyzer initialized")

    def _setup_heuristic_rules(self):
        """Set up heuristic conflict detection rules."""

        # pH incompatible ingredient classes
        self.ph_sensitive_acids = {
            'vitamin_c', 'l-ascorbic acid', 'magnesium ascorbyl phosphate',
            'glycolic acid', 'lactic acid', 'mandelic acid', 'salicylic acid',
            'kojic acid', 'azelaic acid'
        }

        self.ph_sensitive_bases = {
            'retinol', 'retinyl palmitate', 'tretinoin', 'adapalene',
            'niacinamide', 'peptides'
        }

        # Photosensitizing ingredients
        self.photosensitizers = {
            'retinol', 'tretinoin', 'glycolic acid', 'lactic acid', 
            'salicylic acid', 'hydroquinone', 'vitamin c'
        }

        # Ingredients that increase skin sensitivity
        self.sensitizers = {
            'retinol', 'tretinoin', 'glycolic acid', 'lactic acid',
            'salicylic acid', 'benzoyl peroxide'
        }

        logger.debug("Heuristic conflict rules initialized")

    def analyze_products(self, product_names: List[str], 
                        user_id: Optional[str] = None,
                        skin_type: Optional[str] = None) -> ConflictAnalysisReport:
        """
        Analyze potential conflicts between multiple products.

        Args:
            product_names: List of product names to analyze
            user_id: Optional user ID for personalized analysis
            skin_type: Optional skin type override

        Returns:
            Comprehensive conflict analysis report
        """
        logger.info(f"Analyzing conflicts for {len(product_names)} products")

        # Get products and their ingredients
        products = self._get_products_by_names(product_names)
        all_ingredients = self._extract_ingredients_from_products(products)

        # Get user context if available
        user_context = None
        if user_id:
            user_context = self._get_user_context(user_id)
        elif skin_type:
            user_context = {'skin_type': skin_type}

        # Run comprehensive analysis
        conflicts = []

        # 1. Database rule matching
        db_conflicts = self._check_database_conflicts(all_ingredients)
        conflicts.extend(db_conflicts)

        # 2. Heuristic analysis
        heuristic_conflicts = self._check_heuristic_conflicts(all_ingredients)
        conflicts.extend(heuristic_conflicts)

        # 3. RAG-powered analysis (if available)
        if self.rag_system:
            rag_conflicts = self._check_rag_conflicts(all_ingredients, user_context)
            conflicts.extend(rag_conflicts)

        # 4. Skin type specific warnings
        skin_warnings = []
        if user_context and user_context.get('skin_type'):
            skin_warnings = self._check_skin_sensitivities(
                all_ingredients, user_context['skin_type']
            )

        # Deduplicate and prioritize conflicts
        unique_conflicts = self._deduplicate_conflicts(conflicts)

        # Calculate safe combinations
        safe_combinations = self._find_safe_combinations(all_ingredients, unique_conflicts)

        # Generate overall assessment
        overall_severity = self._calculate_overall_severity(unique_conflicts)
        overall_recommendations = self._generate_recommendations(
            unique_conflicts, skin_warnings, user_context
        )

        # Calculate confidence score
        confidence = self._calculate_analysis_confidence(unique_conflicts, user_context)

        # Create report
        report = ConflictAnalysisReport(
            products=product_names,
            ingredients=[ing.ingredient_name for ing in all_ingredients],
            conflicts=unique_conflicts,
            skin_type_warnings=skin_warnings,
            overall_severity=overall_severity,
            safe_combinations=safe_combinations,
            recommendations=overall_recommendations,
            confidence_score=confidence,
            analysis_timestamp=datetime.now()
        )

        # Store prediction in database if user provided
        if user_id and len(products) >= 2:
            self._store_conflict_prediction(user_id, products[:2], report)

        logger.info(f"Analysis complete: {len(unique_conflicts)} conflicts found")
        return report

    def _get_products_by_names(self, product_names: List[str]) -> List[Product]:
        """Retrieve products from database by names."""
        products = []
        for name in product_names:
            # Try exact match first
            product = self.db_session.query(Product).filter(
                Product.product_name.ilike(f'%{name}%')
            ).first()

            if product:
                products.append(product)
            else:
                logger.warning(f"Product not found in database: {name}")

        return products

    def _extract_ingredients_from_products(self, products: List[Product]) -> List[Ingredient]:
        """Extract all unique ingredients from products."""
        ingredient_ids = set()

        for product in products:
            for pi in product.product_ingredients:
                if pi.is_active:
                    ingredient_ids.add(pi.ingredient_id)

        ingredients = self.db_session.query(Ingredient).filter(
            Ingredient.ingredient_id.in_(ingredient_ids)
        ).all()

        return ingredients

    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context for personalized analysis."""
        try:
            user = self.db_session.query(User).filter(User.user_id == user_id).first()
            if user:
                return {
                    'skin_type': user.skin_type,
                    'skin_concerns': user.skin_concerns or [],
                    'allergies': user.allergies or [],
                    'age': self._calculate_age(user.date_of_birth) if user.date_of_birth else None
                }
        except Exception as e:
            logger.warning(f"Could not get user context: {e}")

        return {}

    def _calculate_age(self, birth_date) -> int:
        """Calculate age from birth date."""
        today = datetime.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _check_database_conflicts(self, ingredients: List[Ingredient]) -> List[ConflictResult]:
        """Check for conflicts using database rules."""
        conflicts = []
        ingredient_ids = [ing.ingredient_id for ing in ingredients]

        # Query existing conflict rules
        db_conflicts = self.db_session.query(IngredientConflict).filter(
            and_(
                IngredientConflict.ingredient1_id.in_(ingredient_ids),
                IngredientConflict.ingredient2_id.in_(ingredient_ids)
            )
        ).all()

        for db_conflict in db_conflicts:
            # Get ingredient names
            ing1 = next(ing for ing in ingredients if ing.ingredient_id == db_conflict.ingredient1_id)
            ing2 = next(ing for ing in ingredients if ing.ingredient_id == db_conflict.ingredient2_id)

            conflict = ConflictResult(
                ingredient1=ing1.ingredient_name,
                ingredient2=ing2.ingredient_name,
                conflict_type=ConflictType(db_conflict.conflict_type),
                severity=ConflictSeverity(db_conflict.severity.value),
                description=db_conflict.description,
                scientific_explanation=db_conflict.scientific_explanation,
                confidence_score=0.9,  # High confidence for database rules
                source="database",
                separation_hours=db_conflict.recommended_separation_hours
            )

            # Add specific recommendations
            if db_conflict.alternative_suggestions:
                conflict.recommendations.append(db_conflict.alternative_suggestions)

            if db_conflict.recommended_separation_hours:
                conflict.recommendations.append(
                    f"Separate usage by at least {db_conflict.recommended_separation_hours} hours"
                )

            conflicts.append(conflict)

        logger.debug(f"Found {len(conflicts)} database conflicts")
        return conflicts

    def _check_heuristic_conflicts(self, ingredients: List[Ingredient]) -> List[ConflictResult]:
        """Check for conflicts using heuristic rules."""
        conflicts = []
        ingredient_names = {ing.ingredient_name.lower() for ing in ingredients}

        # Check pH incompatibilities
        has_acids = any(acid in ingredient_names for acid in self.ph_sensitive_acids)
        has_bases = any(base in ingredient_names for base in self.ph_sensitive_bases)

        if has_acids and has_bases:
            # Find specific acid-base pairs
            for ing1 in ingredients:
                for ing2 in ingredients:
                    if (ing1.ingredient_name.lower() in self.ph_sensitive_acids and 
                        ing2.ingredient_name.lower() in self.ph_sensitive_bases):

                        conflict = ConflictResult(
                            ingredient1=ing1.ingredient_name,
                            ingredient2=ing2.ingredient_name,
                            conflict_type=ConflictType.pH_INCOMPATIBILITY,
                            severity=ConflictSeverity.MEDIUM,
                            description=f"pH incompatibility between {ing1.ingredient_name} and {ing2.ingredient_name}",
                            scientific_explanation="Different pH requirements may reduce effectiveness or cause irritation",
                            confidence_score=0.7,
                            source="heuristic",
                            recommendations=[
                                "Use in different routines (AM/PM)",
                                "Allow 30+ minutes between applications",
                                "Consider pH-buffered formulations"
                            ]
                        )
                        conflicts.append(conflict)

        # Check multiple sensitizer combinations
        sensitizer_count = sum(1 for ing in ingredients 
                             if ing.ingredient_name.lower() in self.sensitizers)

        if sensitizer_count >= 3:
            # Create a general warning for multiple sensitizers
            sensitizer_names = [ing.ingredient_name for ing in ingredients 
                              if ing.ingredient_name.lower() in self.sensitizers]

            conflict = ConflictResult(
                ingredient1=sensitizer_names[0],
                ingredient2="Multiple Sensitizers",
                conflict_type=ConflictType.CHEMICAL,
                severity=ConflictSeverity.HIGH,
                description=f"High risk of irritation from multiple sensitizing ingredients: {', '.join(sensitizer_names)}",
                scientific_explanation="Combining multiple sensitizing ingredients increases risk of irritation and compromised skin barrier",
                confidence_score=0.8,
                source="heuristic",
                recommendations=[
                    "Introduce products gradually",
                    "Use lower concentrations",
                    "Monitor skin response carefully",
                    "Consider alternating usage days"
                ]
            )
            conflicts.append(conflict)

        logger.debug(f"Found {len(conflicts)} heuristic conflicts")
        return conflicts

    def _check_rag_conflicts(self, ingredients: List[Ingredient], 
                           user_context: Optional[Dict[str, Any]]) -> List[ConflictResult]:
        """Check for conflicts using RAG system."""
        if not self.rag_system:
            return []

        try:
            ingredient_names = [ing.ingredient_name for ing in ingredients]

            # Query RAG system for interactions
            rag_result = self.rag_system.query_ingredients_interaction(
                ingredient_names, user_context
            )

            # Parse RAG response into conflict results
            conflicts = self._parse_rag_response(rag_result)

            logger.debug(f"Found {len(conflicts)} RAG-based conflicts")
            return conflicts

        except Exception as e:
            logger.error(f"Error in RAG conflict analysis: {e}")
            return []

    def _parse_rag_response(self, rag_result: Dict[str, Any]) -> List[ConflictResult]:
        """Parse RAG system response into ConflictResult objects."""
        conflicts = []

        try:
            analysis_text = rag_result.get('analysis', '')
            confidence = rag_result.get('confidence', 0.5)

            # Simple heuristic parsing - in production, you might want more sophisticated NLP
            if 'should not be used together' in analysis_text.lower():
                # Extract ingredient pairs and create conflicts
                # This is a simplified implementation - you'd want better parsing
                ingredients = rag_result.get('ingredients', [])

                if len(ingredients) >= 2:
                    conflict = ConflictResult(
                        ingredient1=ingredients[0],
                        ingredient2=ingredients[1] if len(ingredients) > 1 else "Other ingredients",
                        conflict_type=ConflictType.CHEMICAL,
                        severity=ConflictSeverity.MEDIUM,
                        description="Potential interaction identified by knowledge base analysis",
                        scientific_explanation=analysis_text[:500],
                        confidence_score=confidence,
                        source="rag"
                    )
                    conflicts.append(conflict)

        except Exception as e:
            logger.warning(f"Error parsing RAG response: {e}")

        return conflicts

    def _check_skin_sensitivities(self, ingredients: List[Ingredient], 
                                skin_type: str) -> List[Dict[str, Any]]:
        """Check for skin type specific sensitivities."""
        warnings = []

        try:
            ingredient_ids = [ing.ingredient_id for ing in ingredients]

            sensitivities = self.db_session.query(SkinSensitivity).filter(
                and_(
                    SkinSensitivity.ingredient_id.in_(ingredient_ids),
                    SkinSensitivity.skin_type == skin_type
                )
            ).all()

            for sensitivity in sensitivities:
                ingredient = next(ing for ing in ingredients 
                                if ing.ingredient_id == sensitivity.ingredient_id)

                warning = {
                    'ingredient': ingredient.ingredient_name,
                    'skin_type': sensitivity.skin_type,
                    'sensitivity_level': sensitivity.sensitivity_level,
                    'description': sensitivity.description,
                    'patch_test_required': sensitivity.patch_test_required,
                    'max_concentration': sensitivity.recommended_max_concentration
                }
                warnings.append(warning)

        except Exception as e:
            logger.warning(f"Error checking skin sensitivities: {e}")

        return warnings

    def _deduplicate_conflicts(self, conflicts: List[ConflictResult]) -> List[ConflictResult]:
        """Remove duplicate conflicts and keep highest severity/confidence."""
        conflict_map = {}

        for conflict in conflicts:
            # Create key for ingredient pair (order independent)
            key = tuple(sorted([conflict.ingredient1, conflict.ingredient2]))

            if key not in conflict_map:
                conflict_map[key] = conflict
            else:
                existing = conflict_map[key]

                # Keep conflict with higher severity, then higher confidence
                if (conflict.severity.value > existing.severity.value or 
                    (conflict.severity == existing.severity and 
                     conflict.confidence_score > existing.confidence_score)):
                    conflict_map[key] = conflict

        return list(conflict_map.values())

    def _find_safe_combinations(self, ingredients: List[Ingredient], 
                              conflicts: List[ConflictResult]) -> List[Tuple[str, str]]:
        """Find ingredient pairs that are safe to use together."""
        safe_pairs = []
        conflicted_pairs = {
            tuple(sorted([c.ingredient1, c.ingredient2])) for c in conflicts
        }

        ingredient_names = [ing.ingredient_name for ing in ingredients]

        for i, ing1 in enumerate(ingredient_names):
            for j, ing2 in enumerate(ingredient_names[i+1:], i+1):
                pair_key = tuple(sorted([ing1, ing2]))

                if pair_key not in conflicted_pairs:
                    safe_pairs.append((ing1, ing2))

        return safe_pairs

    def _calculate_overall_severity(self, conflicts: List[ConflictResult]) -> ConflictSeverity:
        """Calculate overall severity based on individual conflicts."""
        if not conflicts:
            return ConflictSeverity.LOW

        # Get highest severity
        max_severity = max(conflict.severity for conflict in conflicts)
        return max_severity

    def _generate_recommendations(self, conflicts: List[ConflictResult], 
                                skin_warnings: List[Dict[str, Any]],
                                user_context: Optional[Dict[str, Any]]) -> List[str]:
        """Generate overall recommendations based on analysis."""
        recommendations = []

        if not conflicts and not skin_warnings:
            recommendations.append("✅ No major conflicts detected between these ingredients.")
            recommendations.append("Always perform patch tests when introducing new products.")
            return recommendations

        # Critical conflicts
        critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
        if critical_conflicts:
            recommendations.append("⚠️ CRITICAL: Do not use these products together:")
            for conflict in critical_conflicts:
                recommendations.append(f"   • {conflict.ingredient1} + {conflict.ingredient2}")

        # High severity conflicts
        high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
        if high_conflicts:
            recommendations.append("🔸 HIGH PRIORITY: Consider separating these combinations:")
            for conflict in high_conflicts:
                recommendations.append(f"   • {conflict.ingredient1} + {conflict.ingredient2}")
                if conflict.separation_hours:
                    recommendations.append(f"     → Separate by {conflict.separation_hours}+ hours")

        # General recommendations
        if conflicts:
            recommendations.append("💡 General Recommendations:")
            recommendations.append("   • Start with one new product at a time")
            recommendations.append("   • Use morning/evening separation for conflicting ingredients")
            recommendations.append("   • Monitor skin for any irritation or sensitivity")

        # Skin type specific
        if skin_warnings:
            recommendations.append(f"🎯 {user_context.get('skin_type', 'Your skin type')} Skin Considerations:")
            for warning in skin_warnings:
                if warning['sensitivity_level'] in ['high', 'avoid']:
                    recommendations.append(f"   • Use {warning['ingredient']} with extra caution")

        return recommendations

    def _calculate_analysis_confidence(self, conflicts: List[ConflictResult], 
                                     user_context: Optional[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the analysis."""
        if not conflicts:
            return 0.8  # High confidence in "no conflicts"

        # Average confidence of individual conflicts, weighted by severity
        severity_weights = {
            ConflictSeverity.LOW: 0.5,
            ConflictSeverity.MEDIUM: 0.7,
            ConflictSeverity.HIGH: 0.9,
            ConflictSeverity.CRITICAL: 1.0
        }

        total_weighted_confidence = 0
        total_weights = 0

        for conflict in conflicts:
            weight = severity_weights[conflict.severity]
            total_weighted_confidence += conflict.confidence_score * weight
            total_weights += weight

        base_confidence = total_weighted_confidence / total_weights if total_weights > 0 else 0.5

        # Boost confidence if we have user context
        if user_context:
            base_confidence = min(base_confidence + 0.1, 1.0)

        return round(base_confidence, 2)

    def _store_conflict_prediction(self, user_id: str, products: List[Product], 
                                 report: ConflictAnalysisReport):
        """Store conflict prediction result for learning."""
        try:
            if len(products) < 2:
                return

            overall_severity = None
            if report.conflicts:
                max_severity = max(c.severity for c in report.conflicts)
                overall_severity = max_severity.value

            prediction = ConflictPrediction(
                user_id=user_id,
                product1_id=products[0].product_id,
                product2_id=products[1].product_id,
                predicted_conflict_severity=overall_severity,
                confidence_score=report.confidence_score,
                prediction_explanation="; ".join(report.recommendations[:3])  # First 3 recommendations
            )

            self.db_session.add(prediction)
            self.db_session.commit()

        except Exception as e:
            logger.error(f"Error storing conflict prediction: {e}")
            self.db_session.rollback()


# Factory function
def create_conflict_analyzer(db_session: Session, 
                           rag_system: BeautyRAGSystem = None) -> ConflictAnalyzer:
    """Create and initialize a ConflictAnalyzer instance."""
    return ConflictAnalyzer(db_session, rag_system)
