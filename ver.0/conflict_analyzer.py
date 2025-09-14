"""
Ingredient conflict analysis module for My Beauty AI.
Multi-source analysis combining database rules, RAG insights, and heuristics.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_

from config import config
from models import (
    ConflictRule, Ingredient, ProductIngredient, Product, 
    SeverityEnum, SkinTypeEnum, get_db_session
)
from rag_system import RAGSystem, QueryResponse

logger = logging.getLogger(__name__)

class ConflictSeverity(Enum):
    """Conflict severity levels with numeric values for scoring"""
    LOW = (1, "LOW")
    MEDIUM = (2, "MEDIUM") 
    HIGH = (3, "HIGH")
    CRITICAL = (4, "CRITICAL")

    def __init__(self, score, db_value):
        self.score = score
        self.db_value = db_value

@dataclass
class ConflictDetection:
    """Result of conflict analysis"""
    ingredient1: str
    ingredient2: str
    severity: ConflictSeverity
    description: str
    confidence: float
    sources: List[str]
    affected_skin_types: List[str]
    recommendations: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class RoutineAnalysis:
    """Complete routine conflict analysis"""
    conflicts: List[ConflictDetection]
    overall_risk_score: float
    safety_assessment: str
    general_recommendations: List[str]
    product_specific_advice: Dict[str, List[str]]

class ConflictAnalyzer:
    """
    Advanced ingredient conflict analyzer using multiple detection methods:
    1. Database rule matching
    2. RAG system insights
    3. Heuristic analysis
    """

    def __init__(self, rag_system: RAGSystem = None):
        self.rag_system = rag_system
        self.session_factory = sessionmaker()

        # Heuristic conflict patterns
        self.ph_conflict_patterns = {
            'acids': ['salicylic acid', 'glycolic acid', 'lactic acid', 'mandelic acid', 'azelaic acid'],
            'bases': ['sodium bicarbonate', 'calcium carbonate'],
            'vitamin_c': ['l-ascorbic acid', 'magnesium ascorbyl phosphate', 'ascorbyl glucoside'],
            'retinoids': ['retinol', 'retinyl palmitate', 'adapalene', 'tretinoin']
        }

        # Known problematic combinations
        self.known_conflicts = {
            ('retinol', 'vitamin c'): {
                'severity': ConflictSeverity.MEDIUM,
                'reason': 'pH incompatibility and potential irritation',
                'separation_hours': 12
            },
            ('retinol', 'aha'): {
                'severity': ConflictSeverity.HIGH,
                'reason': 'Excessive exfoliation and irritation risk',
                'separation_hours': 24
            },
            ('vitamin c', 'niacinamide'): {
                'severity': ConflictSeverity.LOW,
                'reason': 'Potential conversion to nicotinic acid (debated)',
                'separation_hours': 4
            }
        }

    def analyze_routine(self, products: List[Dict[str, Any]], 
                       skin_type: str = None, 
                       sensitivity_level: str = "moderate") -> RoutineAnalysis:
        """
        Perform comprehensive routine analysis for conflicts.

        Args:
            products: List of products with ingredients
            skin_type: User's skin type
            sensitivity_level: Sensitivity level (low/moderate/high)

        Returns:
            Complete routine analysis with conflicts and recommendations
        """
        try:
            logger.info(f"Starting routine analysis for {len(products)} products")

            # Extract all ingredients from products
            all_ingredients = self._extract_ingredients_from_products(products)

            # Find all pairwise conflicts
            conflicts = []
            for i, ingredient1 in enumerate(all_ingredients):
                for ingredient2 in all_ingredients[i+1:]:
                    conflict = self._analyze_ingredient_pair(
                        ingredient1, ingredient2, skin_type, sensitivity_level
                    )
                    if conflict:
                        conflicts.append(conflict)

            # Calculate overall risk score
            risk_score = self._calculate_overall_risk(conflicts)

            # Generate safety assessment
            safety_assessment = self._generate_safety_assessment(risk_score, conflicts)

            # Generate recommendations
            general_recommendations = self._generate_general_recommendations(conflicts, skin_type)
            product_advice = self._generate_product_specific_advice(products, conflicts)

            return RoutineAnalysis(
                conflicts=conflicts,
                overall_risk_score=risk_score,
                safety_assessment=safety_assessment,
                general_recommendations=general_recommendations,
                product_specific_advice=product_advice
            )

        except Exception as e:
            logger.error(f"Routine analysis failed: {e}")
            return RoutineAnalysis(
                conflicts=[],
                overall_risk_score=0.0,
                safety_assessment="Analysis failed - please consult a dermatologist",
                general_recommendations=["System error occurred - manual review recommended"],
                product_specific_advice={}
            )

    def _extract_ingredients_from_products(self, products: List[Dict[str, Any]]) -> List[str]:
        """Extract unique ingredients from product list"""
        ingredients = set()
        for product in products:
            if 'ingredients' in product:
                ingredients.update([ing.lower().strip() for ing in product['ingredients']])
        return list(ingredients)

    def _analyze_ingredient_pair(self, ingredient1: str, ingredient2: str, 
                               skin_type: str = None, sensitivity_level: str = "moderate") -> Optional[ConflictDetection]:
        """
        Analyze a specific pair of ingredients for conflicts using multiple methods.

        Args:
            ingredient1: First ingredient name
            ingredient2: Second ingredient name
            skin_type: User's skin type
            sensitivity_level: User's sensitivity level

        Returns:
            ConflictDetection if conflict found, None otherwise
        """
        try:
            # Method 1: Database rule lookup
            db_conflict = self._check_database_rules(ingredient1, ingredient2, skin_type)

            # Method 2: RAG system query
            rag_conflict = None
            if self.rag_system:
                rag_conflict = self._check_rag_insights(ingredient1, ingredient2, skin_type)

            # Method 3: Heuristic analysis
            heuristic_conflict = self._check_heuristic_patterns(ingredient1, ingredient2)

            # Combine results from all methods
            conflict = self._combine_conflict_results(
                ingredient1, ingredient2, db_conflict, rag_conflict, heuristic_conflict,
                skin_type, sensitivity_level
            )

            return conflict

        except Exception as e:
            logger.error(f"Error analyzing ingredient pair {ingredient1}-{ingredient2}: {e}")
            return None

    def _check_database_rules(self, ingredient1: str, ingredient2: str, 
                            skin_type: str = None) -> Optional[Dict[str, Any]]:
        """Check database for predefined conflict rules"""
        try:
            with get_db_session() as session:
                # Get ingredient IDs
                ing1 = session.query(Ingredient).filter(
                    Ingredient.name.ilike(f'%{ingredient1}%')
                ).first()
                ing2 = session.query(Ingredient).filter(
                    Ingredient.name.ilike(f'%{ingredient2}%')
                ).first()

                if not ing1 or not ing2:
                    return None

                # Look for conflict rules (bidirectional)
                conflict_rule = session.query(ConflictRule).filter(
                    or_(
                        and_(ConflictRule.ingredient1_id == ing1.ingredient_id,
                             ConflictRule.ingredient2_id == ing2.ingredient_id),
                        and_(ConflictRule.ingredient1_id == ing2.ingredient_id,
                             ConflictRule.ingredient2_id == ing1.ingredient_id)
                    ),
                    ConflictRule.is_active == True
                ).first()

                if conflict_rule:
                    # Check if rule applies to specific skin type
                    if (skin_type and conflict_rule.affected_skin_types and 
                        skin_type not in [st.value for st in conflict_rule.affected_skin_types]):
                        return None

                    return {
                        'severity': ConflictSeverity[conflict_rule.severity.value],
                        'description': conflict_rule.description,
                        'scientific_basis': conflict_rule.scientific_basis,
                        'time_separation_hours': conflict_rule.time_separation_hours,
                        'confidence': 0.9,  # High confidence for database rules
                        'source': 'database'
                    }

                return None

        except Exception as e:
            logger.error(f"Database rule check failed: {e}")
            return None

    def _check_rag_insights(self, ingredient1: str, ingredient2: str, 
                          skin_type: str = None) -> Optional[Dict[str, Any]]:
        """Query RAG system for ingredient interaction insights"""
        try:
            if not self.rag_system:
                return None

            context = {'skin_type': skin_type} if skin_type else {}
            response = self.rag_system.query_ingredient_interaction(
                ingredient1, ingredient2, context
            )

            if response.confidence < config.rag.confidence_threshold:
                return None

            # Parse response for conflict indicators
            response_text = response.response.lower()
            conflict_keywords = [
                'avoid', 'conflict', 'contraindicated', 'incompatible',
                'separate', 'not recommended', 'irritation', 'cancel out'
            ]

            has_conflict = any(keyword in response_text for keyword in conflict_keywords)
            if not has_conflict:
                return None

            # Determine severity from response
            severity = ConflictSeverity.MEDIUM
            if any(word in response_text for word in ['severe', 'critical', 'dangerous']):
                severity = ConflictSeverity.CRITICAL
            elif any(word in response_text for word in ['high', 'strong', 'significant']):
                severity = ConflictSeverity.HIGH
            elif any(word in response_text for word in ['mild', 'minor', 'slight']):
                severity = ConflictSeverity.LOW

            return {
                'severity': severity,
                'description': response.response[:200] + "..." if len(response.response) > 200 else response.response,
                'confidence': response.confidence,
                'sources': response.sources,
                'source': 'rag_system'
            }

        except Exception as e:
            logger.error(f"RAG system check failed: {e}")
            return None

    def _check_heuristic_patterns(self, ingredient1: str, ingredient2: str) -> Optional[Dict[str, Any]]:
        """Apply heuristic rules for common conflict patterns"""
        try:
            # Normalize ingredient names
            ing1_lower = ingredient1.lower()
            ing2_lower = ingredient2.lower()

            # Check known conflicts
            for (pattern1, pattern2), conflict_info in self.known_conflicts.items():
                if ((pattern1 in ing1_lower and pattern2 in ing2_lower) or
                    (pattern2 in ing1_lower and pattern1 in ing2_lower)):
                    return {
                        'severity': conflict_info['severity'],
                        'description': conflict_info['reason'],
                        'time_separation_hours': conflict_info['separation_hours'],
                        'confidence': 0.7,  # Moderate confidence for heuristics
                        'source': 'heuristic'
                    }

            # pH conflict detection
            acid_ingredients = self.ph_conflict_patterns['acids']
            base_ingredients = self.ph_conflict_patterns['bases']

            is_acid1 = any(acid in ing1_lower for acid in acid_ingredients)
            is_acid2 = any(acid in ing2_lower for acid in acid_ingredients)
            is_base1 = any(base in ing1_lower for base in base_ingredients)
            is_base2 = any(base in ing2_lower for base in base_ingredients)

            if (is_acid1 and is_base2) or (is_base1 and is_acid2):
                return {
                    'severity': ConflictSeverity.MEDIUM,
                    'description': 'pH incompatibility between acid and base ingredients',
                    'confidence': 0.6,
                    'source': 'heuristic_ph'
                }

            # Multiple actives detection
            actives = self.ph_conflict_patterns['acids'] + self.ph_conflict_patterns['retinoids']
            is_active1 = any(active in ing1_lower for active in actives)
            is_active2 = any(active in ing2_lower for active in actives)

            if is_active1 and is_active2:
                return {
                    'severity': ConflictSeverity.LOW,
                    'description': 'Multiple active ingredients may increase irritation risk',
                    'confidence': 0.5,
                    'source': 'heuristic_actives'
                }

            return None

        except Exception as e:
            logger.error(f"Heuristic pattern check failed: {e}")
            return None

    def _combine_conflict_results(self, ingredient1: str, ingredient2: str,
                                db_result: Optional[Dict[str, Any]],
                                rag_result: Optional[Dict[str, Any]],
                                heuristic_result: Optional[Dict[str, Any]],
                                skin_type: str = None,
                                sensitivity_level: str = "moderate") -> Optional[ConflictDetection]:
        """Combine results from different detection methods"""

        # Collect all non-None results
        results = [r for r in [db_result, rag_result, heuristic_result] if r is not None]

        if not results:
            return None

        # Determine final severity (take the highest)
        final_severity = max([r['severity'] for r in results], key=lambda s: s.score)

        # Adjust severity based on sensitivity level
        if sensitivity_level == "high":
            if final_severity.score < ConflictSeverity.CRITICAL.score:
                final_severity = ConflictSeverity(final_severity.score + 1, 
                                                list(ConflictSeverity)[final_severity.score].name)
        elif sensitivity_level == "low":
            if final_severity.score > ConflictSeverity.LOW.score:
                final_severity = ConflictSeverity(final_severity.score - 1,
                                                list(ConflictSeverity)[final_severity.score - 2].name)

        # Combine descriptions
        descriptions = [r['description'] for r in results if 'description' in r]
        final_description = "; ".join(descriptions)

        # Calculate weighted confidence
        confidences = [(r.get('confidence', 0.5), r.get('source', 'unknown')) for r in results]
        weights = {'database': 0.4, 'rag_system': 0.4, 'heuristic': 0.2}
        total_weight = sum(weights.get(source, 0.1) for _, source in confidences)
        weighted_confidence = sum(conf * weights.get(source, 0.1) for conf, source in confidences) / total_weight

        # Collect sources
        sources = []
        for r in results:
            if 'sources' in r:
                sources.extend(r['sources'])
            sources.append(r.get('source', 'unknown'))

        # Generate recommendations
        recommendations = self._generate_conflict_recommendations(
            ingredient1, ingredient2, final_severity, results
        )

        return ConflictDetection(
            ingredient1=ingredient1,
            ingredient2=ingredient2,
            severity=final_severity,
            description=final_description,
            confidence=weighted_confidence,
            sources=list(set(sources)),
            affected_skin_types=[skin_type] if skin_type else [],
            recommendations=recommendations,
            metadata={
                'detection_methods': [r.get('source', 'unknown') for r in results],
                'sensitivity_adjusted': sensitivity_level != "moderate"
            }
        )

    def _generate_conflict_recommendations(self, ingredient1: str, ingredient2: str,
                                         severity: ConflictSeverity,
                                         detection_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate specific recommendations for a conflict"""
        recommendations = {
            'action': 'monitor',
            'separation_time': None,
            'alternatives': [],
            'precautions': []
        }

        if severity == ConflictSeverity.CRITICAL:
            recommendations['action'] = 'avoid_combination'
            recommendations['precautions'].append('Do not use these ingredients together')

        elif severity == ConflictSeverity.HIGH:
            recommendations['action'] = 'separate_applications'
            recommendations['separation_time'] = 24  # hours
            recommendations['precautions'].append('Use on alternate days or different times')

        elif severity == ConflictSeverity.MEDIUM:
            recommendations['action'] = 'time_separation'
            recommendations['separation_time'] = 12  # hours
            recommendations['precautions'].append('Wait several hours between applications')

        elif severity == ConflictSeverity.LOW:
            recommendations['action'] = 'monitor'
            recommendations['precautions'].append('Monitor skin for irritation')

        # Add specific separation times from detection results
        separation_times = [r.get('time_separation_hours') for r in detection_results 
                          if r.get('time_separation_hours')]
        if separation_times:
            recommendations['separation_time'] = max(separation_times)

        return recommendations

    def _calculate_overall_risk(self, conflicts: List[ConflictDetection]) -> float:
        """Calculate overall routine risk score (0-1)"""
        if not conflicts:
            return 0.0

        # Weight conflicts by severity and confidence
        risk_score = 0.0
        for conflict in conflicts:
            severity_weight = conflict.severity.score / 4.0  # Normalize to 0-1
            confidence_weight = conflict.confidence
            risk_score += severity_weight * confidence_weight

        # Normalize by number of conflicts and cap at 1.0
        normalized_score = risk_score / len(conflicts)
        return min(normalized_score, 1.0)

    def _generate_safety_assessment(self, risk_score: float, 
                                   conflicts: List[ConflictDetection]) -> str:
        """Generate overall safety assessment"""
        if risk_score == 0.0:
            return "No significant conflicts detected. Routine appears safe for general use."
        elif risk_score < 0.3:
            return "Low risk routine with minor considerations. Monitor for any irritation."
        elif risk_score < 0.6:
            return "Moderate risk routine. Follow timing recommendations carefully."
        elif risk_score < 0.8:
            return "High risk routine. Consider modifications or professional consultation."
        else:
            return "Critical risk detected. Strongly recommend dermatologist consultation before use."

    def _generate_general_recommendations(self, conflicts: List[ConflictDetection],
                                        skin_type: str = None) -> List[str]:
        """Generate general recommendations for the routine"""
        recommendations = []

        if conflicts:
            recommendations.append("Patch test new products before full application")
            recommendations.append("Introduce one product at a time to monitor reactions")

            # Severity-specific recommendations
            critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
            if critical_conflicts:
                recommendations.append("Avoid using conflicting ingredients together completely")

            high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
            if high_conflicts:
                recommendations.append("Use conflicting products on alternate days")

            medium_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.MEDIUM]
            if medium_conflicts:
                recommendations.append("Allow adequate time between conflicting product applications")

        # Skin type specific recommendations
        if skin_type == "sensitive":
            recommendations.append("Start with lower concentrations and less frequent use")
            recommendations.append("Consider using products every other day initially")

        recommendations.append("Consult a dermatologist for personalized advice")

        return recommendations

    def _generate_product_specific_advice(self, products: List[Dict[str, Any]],
                                        conflicts: List[ConflictDetection]) -> Dict[str, List[str]]:
        """Generate advice specific to each product"""
        advice = {}

        for product in products:
            product_name = product.get('name', 'Unknown Product')
            product_ingredients = [ing.lower() for ing in product.get('ingredients', [])]
            product_advice = []

            # Find conflicts involving this product's ingredients
            product_conflicts = []
            for conflict in conflicts:
                if (conflict.ingredient1 in product_ingredients or 
                    conflict.ingredient2 in product_ingredients):
                    product_conflicts.append(conflict)

            if product_conflicts:
                severity_levels = [c.severity for c in product_conflicts]
                max_severity = max(severity_levels, key=lambda s: s.score)

                if max_severity == ConflictSeverity.CRITICAL:
                    product_advice.append("⚠️ CRITICAL: Review usage with dermatologist")
                elif max_severity == ConflictSeverity.HIGH:
                    product_advice.append("⚠️ HIGH RISK: Use with caution and timing separation")
                elif max_severity == ConflictSeverity.MEDIUM:
                    product_advice.append("⚠️ MODERATE: Allow time between applications")
                else:
                    product_advice.append("ℹ️ Monitor for any adverse reactions")

                # Add specific timing advice
                for conflict in product_conflicts:
                    if conflict.recommendations.get('separation_time'):
                        product_advice.append(
                            f"Wait {conflict.recommendations['separation_time']} hours before/after "
                            f"using products with {conflict.ingredient1} or {conflict.ingredient2}"
                        )
            else:
                product_advice.append("✅ No significant conflicts detected")

            advice[product_name] = product_advice

        return advice

# Export main class
__all__ = ['ConflictAnalyzer', 'ConflictDetection', 'RoutineAnalysis', 'ConflictSeverity']
