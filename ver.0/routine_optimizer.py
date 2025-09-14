"""
Routine optimization module for My Beauty AI.
Intelligent skincare routine creation and optimization with AI-powered recommendations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, time
import math

from sqlalchemy.orm import sessionmaker

from config import config
from models import (
    Product, Ingredient, ProductIngredient, UserProfile,
    ProductCategoryEnum, SkinTypeEnum, get_db_session
)
from rag_system import RAGSystem, QueryResponse
from conflict_analyzer import ConflictAnalyzer, ConflictSeverity

logger = logging.getLogger(__name__)

class RoutineTimeSlot(Enum):
    """Time slots for routine application"""
    MORNING = "morning"
    EVENING = "evening"
    BOTH = "both"

class ProductPriority(Enum):
    """Priority levels for product application order"""
    ESSENTIAL = 1
    IMPORTANT = 2
    BENEFICIAL = 3
    OPTIONAL = 4

@dataclass
class ProductApplication:
    """Optimized product application details"""
    product: Dict[str, Any]
    time_slot: RoutineTimeSlot
    application_order: int
    frequency: str  # 'daily', 'alternate', '2-3x/week', etc.
    wait_time_minutes: int
    priority: ProductPriority
    notes: List[str]

@dataclass
class OptimizedRoutine:
    """Complete optimized routine with timing and instructions"""
    morning_routine: List[ProductApplication]
    evening_routine: List[ProductApplication]
    weekly_schedule: Dict[str, List[str]]  # Day -> Special instructions
    estimated_time_morning: int  # minutes
    estimated_time_evening: int  # minutes
    introduction_timeline: Dict[str, List[str]]  # Week -> Products to introduce
    general_guidelines: List[str]
    personalization_notes: List[str]

class RoutineOptimizer:
    """
    Advanced routine optimizer that creates personalized skincare routines.
    Uses AI insights, ingredient compatibility, and dermatological best practices.
    """

    def __init__(self, rag_system: RAGSystem = None, conflict_analyzer: ConflictAnalyzer = None):
        self.rag_system = rag_system
        self.conflict_analyzer = conflict_analyzer or ConflictAnalyzer(rag_system)

        # Product category priorities and timing
        self.category_order = {
            RoutineTimeSlot.MORNING: [
                ProductCategoryEnum.CLEANSER,
                ProductCategoryEnum.TONER,
                ProductCategoryEnum.ESSENCE,
                ProductCategoryEnum.SERUM,
                ProductCategoryEnum.TREATMENT,
                ProductCategoryEnum.EYE_CREAM,
                ProductCategoryEnum.MOISTURIZER,
                ProductCategoryEnum.SUNSCREEN
            ],
            RoutineTimeSlot.EVENING: [
                ProductCategoryEnum.CLEANSER,
                ProductCategoryEnum.EXFOLIANT,
                ProductCategoryEnum.TONER,
                ProductCategoryEnum.ESSENCE,
                ProductCategoryEnum.SERUM,
                ProductCategoryEnum.TREATMENT,
                ProductCategoryEnum.EYE_CREAM,
                ProductCategoryEnum.MOISTURIZER,
                ProductCategoryEnum.OIL
            ]
        }

        # Wait times between different product types (minutes)
        self.wait_times = {
            ProductCategoryEnum.SERUM: 5,
            ProductCategoryEnum.TREATMENT: 10,
            ProductCategoryEnum.EXFOLIANT: 15,
            ProductCategoryEnum.SUNSCREEN: 5,
            'default': 2
        }

        # Products that should typically be used at specific times
        self.time_preferences = {
            'sunscreen': RoutineTimeSlot.MORNING,
            'retinol': RoutineTimeSlot.EVENING,
            'tretinoin': RoutineTimeSlot.EVENING,
            'aha': RoutineTimeSlot.EVENING,
            'bha': RoutineTimeSlot.BOTH,  # Can be flexible
            'vitamin c': RoutineTimeSlot.MORNING
        }

    def optimize_routine(self, products: List[Dict[str, Any]], 
                        user_profile: Dict[str, Any]) -> OptimizedRoutine:
        """
        Create an optimized routine based on products and user profile.

        Args:
            products: List of products to include in routine
            user_profile: User skin profile and preferences

        Returns:
            Optimized routine with timing and application instructions
        """
        try:
            logger.info(f"Optimizing routine for {len(products)} products")
            
            # Analyze conflicts first
            conflict_analysis = self.conflict_analyzer.analyze_routine(
                products,
                user_profile.get('skin_type'),
                user_profile.get('sensitivity_level', 'moderate')
            )
            
            # Categorize and prioritize products
            categorized_products = self._categorize_products(products, user_profile)
            
            # Assign time slots based on ingredients and conflicts
            time_assigned_products = self._assign_time_slots(
                categorized_products, conflict_analysis, user_profile
            )
            
            # Create morning and evening routines
            morning_routine = self._create_time_routine(
                time_assigned_products[RoutineTimeSlot.MORNING],
                RoutineTimeSlot.MORNING,
                user_profile
            )
            
            evening_routine = self._create_time_routine(
                time_assigned_products[RoutineTimeSlot.EVENING],
                RoutineTimeSlot.EVENING,
                user_profile
            )
            
            # Generate weekly schedule for products with special timing
            weekly_schedule = self._generate_weekly_schedule(
                morning_routine + evening_routine, user_profile
            )
            
            # Calculate estimated times
            morning_time = self._estimate_routine_time(morning_routine)
            evening_time = self._estimate_routine_time(evening_routine)
            
            # Create introduction timeline for new users
            introduction_timeline = self._create_introduction_timeline(
                morning_routine + evening_routine, user_profile
            )
            
            # Generate guidelines and personalization notes
            general_guidelines = self._generate_general_guidelines(user_profile, conflict_analysis)
            personalization_notes = self._generate_personalization_notes(
                user_profile, conflict_analysis, products
            )
            
            return OptimizedRoutine(
                morning_routine=morning_routine,
                evening_routine=evening_routine,
                weekly_schedule=weekly_schedule,
                estimated_time_morning=morning_time,
                estimated_time_evening=evening_time,
                introduction_timeline=introduction_timeline,
                general_guidelines=general_guidelines,
                personalization_notes=personalization_notes
            )
            
        except Exception as e:
            logger.error(f"Routine optimization failed: {e}")
            return self._create_fallback_routine(products, user_profile)
    
    def _categorize_products(self, products: List[Dict[str, Any]], 
                           user_profile: Dict[str, Any]) -> Dict[ProductCategoryEnum, List[Dict[str, Any]]]:
        """Categorize products and determine their priority based on user profile"""  
        categorized = {category: [] for category in ProductCategoryEnum}
        
        for product in products:
            # Determine category from product data
            category = self._determine_product_category(product)
            if category:
                # Add priority and user-specific notes
                enhanced_product = product.copy()
                enhanced_product['priority'] = self._determine_product_priority(
                    product, user_profile
                )
                enhanced_product['user_notes'] = self._generate_product_notes(
                    product, user_profile
                )
                categorized[category].append(enhanced_product)
        
        return categorized
    
    def _determine_product_category(self, product: Dict[str, Any]) -> Optional[ProductCategoryEnum]:
        """Determine product category from product information"""  
        # Direct category if provided
        if 'category' in product:
            try:
                return ProductCategoryEnum(product['category'].lower())
            except ValueError:
                pass
        
        # Infer from product name
        name = product.get('name', '').lower()
        
        if any(word in name for word in ['cleanser', 'cleansing', 'wash', 'foam']):
            return ProductCategoryEnum.CLEANSER
        elif any(word in name for word in ['sunscreen', 'spf', 'sun protection']):
            return ProductCategoryEnum.SUNSCREEN
        elif any(word in name for word in ['serum']):
            return ProductCategoryEnum.SERUM
        elif any(word in name for word in ['moisturizer', 'moisturiser', 'cream', 'lotion']):
            return ProductCategoryEnum.MOISTURIZER
        elif any(word in name for word in ['toner', 'tonic']):
            return ProductCategoryEnum.TONER
        elif any(word in name for word in ['essence']):
            return ProductCategoryEnum.ESSENCE
        elif any(word in name for word in ['eye cream', 'eye serum']):
            return ProductCategoryEnum.EYE_CREAM
        elif any(word in name for word in ['exfoliant', 'exfoliating', 'peel']):
            return ProductCategoryEnum.EXFOLIANT
        elif any(word in name for word in ['oil', 'facial oil']):
            return ProductCategoryEnum.OIL
        elif any(word in name for word in ['mask']):
            return ProductCategoryEnum.MASK
        elif any(word in name for word in ['treatment', 'spot treatment']):
            return ProductCategoryEnum.TREATMENT
        elif any(word in name for word in ['mist', 'spray']):
            return ProductCategoryEnum.MIST
        
        # Default to treatment if can't determine
        return ProductCategoryEnum.TREATMENT
    
    def _determine_product_priority(self, product: Dict[str, Any], 
                                  user_profile: Dict[str, Any]]) -> ProductPriority:
        """Determine product priority based on user needs"""  
        ingredients = [ing.lower() for ing in product.get('ingredients', [])]
        skin_type = user_profile.get('skin_type', 'normal')
        concerns = [c.lower() for c in user_profile.get('concerns', [])]
        
        # Essential products
        category = self._determine_product_category(product)
        if category in [ProductCategoryEnum.CLEANSER, ProductCategoryEnum.MOISTURIZER, 
                       ProductCategoryEnum.SUNSCREEN]:
            return ProductPriority.ESSENTIAL
        
        # Important for specific concerns
        concern_ingredients = {
            'acne': ['salicylic acid', 'benzoyl peroxide', 'niacinamide'],
            'aging': ['retinol', 'vitamin c', 'peptides'],
            'dark spots': ['vitamin c', 'arbutin', 'kojic acid'],
            'dryness': ['hyaluronic acid', 'ceramides', 'squalane'],
            'sensitivity': ['niacinamide', 'centella asiatica', 'allantoin']
        }
        
        for concern in concerns:
            if concern in concern_ingredients:
                target_ingredients = concern_ingredients[concern]
                if any(ing in ingredients for ing in target_ingredients):
                    return ProductPriority.IMPORTANT
        
        # Beneficial for skin type
        if skin_type == 'oily' and any(ing in ingredients for ing in ['niacinamide', 'salicylic acid']):
            return ProductPriority.BENEFICIAL
        elif skin_type == 'dry' and any(ing in ingredients for ing in ['hyaluronic acid', 'ceramides']):
            return ProductPriority.BENEFICIAL
        
        return ProductPriority.OPTIONAL
    
    def _assign_time_slots(self, categorized_products: Dict[ProductCategoryEnum, List[Dict[str, Any]]],
                          conflict_analysis, user_profile: Dict[str, Any]) -> Dict[RoutineTimeSlot, List[Dict[str, Any]]]:
        """Assign products to morning or evening based on ingredients and conflicts"""  
        assigned = {
            RoutineTimeSlot.MORNING: [],
            RoutineTimeSlot.EVENING: []
        }
        
        for category, products in categorized_products.items():
            for product in products:
                time_slot = self._determine_optimal_time_slot(product, conflict_analysis)
                
                # Add time slot and category info to product
                enhanced_product = product.copy()
                enhanced_product['category'] = category
                enhanced_product['time_slot'] = time_slot
                
                assigned[time_slot].append(enhanced_product)
        
        return assigned
    
    def _determine_optimal_time_slot(self, product: Dict[str, Any], conflict_analysis) -> RoutineTimeSlot:
        """Determine optimal time slot for a product"""  
        ingredients = [ing.lower() for ing in product.get('ingredients', [])]
        
        # Check for time-specific ingredients
        for ingredient_pattern, preferred_time in self.time_preferences.items():
            if any(ingredient_pattern in ing for ing in ingredients):
                return preferred_time
        
        # Category-based defaults
        category = product.get('category') or self._determine_product_category(product)
        
        if category == ProductCategoryEnum.SUNSCREEN:
            return RoutineTimeSlot.MORNING
        elif category in [ProductCategoryEnum.EXFOLIANT, ProductCategoryEnum.TREATMENT]:
            # Check if it contains actives that are better at night
            night_actives = ['retinol', 'aha', 'glycolic', 'lactic']
            if any(active in ' '.join(ingredients) for active in night_actives):
                return RoutineTimeSlot.EVENING
        
        # Default to morning for most products
        return RoutineTimeSlot.MORNING
    
    def _create_time_routine(self, products: List[Dict[str, Any]], 
                           time_slot: RoutineTimeSlot,
                           user_profile: Dict[str, Any]) -> List[ProductApplication]:
        """Create ordered routine for specific time slot"""  
        if not products:
            return []
        
        # Sort products by category order
        category_order = self.category_order[time_slot]
        sorted_products = []
        
        for category in category_order:
            category_products = [p for p in products if p.get('category') == category]
            # Sort by priority within category
            category_products.sort(key=lambda p: p.get('priority', ProductPriority.OPTIONAL).value)
            sorted_products.extend(category_products)
        
        # Create ProductApplication objects
        applications = []
        for i, product in enumerate(sorted_products):
            category = product.get('category')
            wait_time = self.wait_times.get(category, self.wait_times['default'])
            
            frequency = self._determine_frequency(product, user_profile)
            notes = self._generate_application_notes(product, user_profile, time_slot)
            
            application = ProductApplication(
                product=product,
                time_slot=time_slot,
                application_order=i + 1,
                frequency=frequency,
                wait_time_minutes=wait_time,
                priority=product.get('priority', ProductPriority.OPTIONAL),
                notes=notes
            )
            applications.append(application)
        
        return applications
    
    def _determine_frequency(self, product: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Determine how often a product should be used"""  
        ingredients = [ing.lower() for ing in product.get('ingredients', [])]
        sensitivity = user_profile.get('sensitivity_level', 'moderate')
        
        # Strong actives - start slow
        strong_actives = ['retinol', 'tretinoin', 'glycolic acid', 'salicylic acid']
        if any(active in ' '.join(ingredients) for active in strong_actives):
            if sensitivity == 'high':
                return '2x per week'
            elif sensitivity == 'moderate':
                return 'every other day'
            else:
                return 'daily'
        
        # Exfoliants
        if any(exfoliant in ' '.join(ingredients) for exfoliant in ['aha', 'bha']):
            return '2-3x per week'
        
        # Masks
        category = product.get('category') or self._determine_product_category(product)
        if category == ProductCategoryEnum.MASK:
            return '1-2x per week'
        
        # Default to daily for most products
        return 'daily'
    
    def _generate_application_notes(self, product: Dict[str, Any], 
                                  user_profile: Dict[str, Any],
                                  time_slot: RoutineTimeSlot) -> List[str]:
        """Generate specific application notes for a product"""  
        notes = []
        ingredients = [ing.lower() for ing in product.get('ingredients', [])]
        
        # Sunscreen specific notes
        if 'sunscreen' in product.get('name', '').lower():
            notes.append('Apply 15-20 minutes before sun exposure')
            notes.append('Reapply every 2 hours when outdoors')
        
        # Active ingredient notes
        if any(active in ' '.join(ingredients) for active in ['retinol', 'tretinoin']):
            notes.append('Start slowly to build tolerance')
            notes.append('Always use sunscreen during the day')
        
        if 'vitamin c' in ' '.join(ingredients):
            notes.append('Store in cool, dark place')
            notes.append('Use within 6 months of opening')
        
        # Sensitivity notes
        if user_profile.get('sensitivity_level') == 'high':
            notes.append('Patch test before first use')
            notes.append('Reduce frequency if irritation occurs')
        
        return notes
    
    def _generate_weekly_schedule(self, all_applications: List[ProductApplication],
                                user_profile: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate weekly schedule for products with special timing"""  
        schedule = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [],
            'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        days = list(schedule.keys())
        
        # Products that need spacing
        for app in all_applications:
            if app.frequency == 'every other day':
                # Alternate days
                for i in range(0, 7, 2):
                    if i < len(days):
                        schedule[days[i]].append(f"Use {app.product.get('name', 'product')}")
            
            elif app.frequency == '2x per week':
                # Monday and Thursday
                schedule['Monday'].append(f"Use {app.product.get('name', 'product')}")
                schedule['Thursday'].append(f"Use {app.product.get('name', 'product')}")
            
            elif app.frequency == '2-3x per week':
                # Monday, Wednesday, Friday
                for day in ['Monday', 'Wednesday', 'Friday']:
                    schedule[day].append(f"Use {app.product.get('name', 'product')}")
        
        return schedule
    
    def _estimate_routine_time(self, applications: List[ProductApplication]) -> int:
        """Estimate total time for routine in minutes"""  
        if not applications:
            return 0
        
        base_time = len(applications) * 1  # 1 minute per product application
        wait_time = sum(app.wait_time_minutes for app in applications[:-1])  # No wait after last product
        
        return base_time + wait_time
    
    def _create_introduction_timeline(self, all_applications: List[ProductApplication],
                                    user_profile: Dict[str, Any]) -> Dict[str, List[str]]:
        """Create timeline for introducing products gradually"""  
        timeline = {}
        
        # Sort by priority
        sorted_apps = sorted(all_applications, key=lambda x: x.priority.value)
        
        week = 1
        for i in range(0, len(sorted_apps), 2):  # Introduce 2 products per week
            week_products = sorted_apps[i:i+2]
            week_key = f"Week {week}"
            timeline[week_key] = []
            
            for app in week_products:
                timeline[week_key].append(f"Introduce {app.product.get('name', 'product')}")
            
            week += 1
        
        return timeline
    
    def _generate_general_guidelines(self, user_profile: Dict[str, Any], conflict_analysis) -> List[str]:
        """Generate general routine guidelines"""  
        guidelines = [
            "Always patch test new products before full application",
            "Introduce one new product at a time",
            "Use sunscreen daily, especially when using actives",
            "Listen to your skin - reduce frequency if irritation occurs"
        ]
        
        if user_profile.get('sensitivity_level') == 'high':
            guidelines.extend([
                "Start with every other day for new actives",
                "Consider using products on alternate nights"
            ])
        
        if conflict_analysis.overall_risk_score > 0.5:
            guidelines.extend([
                "Follow timing recommendations carefully",
                "Consider consulting a dermatologist for personalized advice"
            ])
        
        return guidelines
    
    def _generate_personalization_notes(self, user_profile: Dict[str, Any],
                                       conflict_analysis, products: List[Dict[str, Any]]) -> List[str]:
        """Generate personalized notes based on user profile"""  
        notes = []
        skin_type = user_profile.get('skin_type', 'normal')
        concerns = user_profile.get('concerns', [])
        
        # Skin type specific notes
        if skin_type == 'oily':
            notes.append("Focus on oil control and pore-minimizing ingredients")
        elif skin_type == 'dry':
            notes.append("Prioritize hydrating and barrier-repairing ingredients")
        elif skin_type == 'sensitive':
            notes.append("Choose gentle, fragrance-free formulations")
        elif skin_type == 'combination':
            notes.append("You may need different products for T-zone vs. cheeks")
        
        # Concern-specific notes
        if 'acne' in concerns:
            notes.append("Look for non-comedogenic products")
        if 'aging' in concerns:
            notes.append("Consistency is key for anti-aging ingredients")
        if 'dark spots' in concerns:
            notes.append("Be patient - brightening ingredients take 8-12 weeks to show results")
        
        return notes
    
    def _create_fallback_routine(self, products: List[Dict[str, Any]], 
                                user_profile: Dict[str, Any]) -> OptimizedRoutine:
        """Create simple fallback routine if optimization fails"""  
        return OptimizedRoutine(
            morning_routine=[],
            evening_routine=[],
            weekly_schedule={},
            estimated_time_morning=0,
            estimated_time_evening=0,
            introduction_timeline={"Week 1": ["Consult skincare professional"]},
            general_guidelines=["System error - please seek professional advice"],
            personalization_notes=["Routine optimization failed - manual review needed"]
        )
    
    def _generate_product_notes(self, product: Dict[str, Any], 
                              user_profile: Dict[str, Any]) -> List[str]:
        """Generate user-specific notes for a product"""  
        notes = []
        # This would be expanded with more specific logic
        return notes

# Export main classes
__all__ = [
    'RoutineOptimizer', 'OptimizedRoutine', 'ProductApplication', 
    'RoutineTimeSlot', 'ProductPriority'
]
