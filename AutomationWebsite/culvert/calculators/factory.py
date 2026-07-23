"""
Calculator Factory for creating the appropriate culvert calculator.

Selects calculator based on:
- n: Number of openings (1 = single, >1 = multi)
- alpha: Angle (0 = perpendicular, alpha < 0 = angular less, alpha > 0 = angular more)

Each calculator type is INDEPENDENT - no inheritance between types.
"""

from typing import Callable, Optional

from culvert.calculators.base import CulvertInput, BaseCulvertCalculator
from culvert.calculators.single_atgrade import SingleAtGradeCalculator
from culvert.calculators.multi_atgrade import MultiAtGradeCalculator


class CulvertCalculatorFactory:
    """
    Factory class to create appropriate calculator based on input parameters.
    
    Calculator Types:
    -----------------
    1. SingleAtGrade: n=1, any alpha (UNIFIED — perpendicular + angular)
    2. MultiAtGrade: n>=2, any alpha (UNIFIED — all multi-opening types)
    
    Both calculators use cos(alpha)/tan(alpha) corrections which naturally
    reduce to the perpendicular case when alpha=0.
    """
    
    @staticmethod
    def create_calculator(
        input_params: CulvertInput,
        table_repository,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> BaseCulvertCalculator:
        """
        Create the appropriate calculator based on n and alpha.
        
        Args:
            input_params: CulvertInput with all parameters
            table_repository: TableRepository instance
            progress_callback: Optional progress callback
            
        Returns:
            Appropriate calculator instance
            
        Raises:
            ValueError: If n or alpha combination is not supported
        """
        n = input_params.n
        alpha = input_params.alpha
        
        # Single opening (n=1) — unified calculator handles all alpha values
        if n == 1:
            return SingleAtGradeCalculator(
                input_params=input_params,
                table_repository=table_repository,
                progress_callback=progress_callback
            )
        
        # Multi-opening (n>1) — unified calculator handles all alpha values
        elif n > 1:
            return MultiAtGradeCalculator(
                input_params=input_params,
                table_repository=table_repository,
                progress_callback=progress_callback
            )
        
        else:
            raise ValueError(
                f"Invalid number of openings: n={n}. "
                "Must be 1 (single), >1 (multi), or 5-8 (underground, not yet supported)."
            )
    
    @staticmethod
    def get_available_types() -> dict:
        """
        Get dictionary of available calculator types and their status.
        
        Returns:
            Dict with type names as keys and implementation status as values
        """
        return {
            "single_atgrade": {
                "n": 1,
                "alpha": "any",
                "implemented": True,
                "template": "single_perpendicular_atGrade.dxf / single_angularM_atGrade.dxf / single_angularL_atGrade.dxf",
                "description": "Single opening, unified (perpendicular + angular)"
            },
            "multi_atgrade": {
                "n": ">=2",
                "alpha": "any",
                "implemented": True,
                "template": "double_*/triple_* perpendicular/angularM/angularL _atGrade.dxf",
                "description": "Multi opening (n>=2), unified (perpendicular + angular)"
            }
        }
