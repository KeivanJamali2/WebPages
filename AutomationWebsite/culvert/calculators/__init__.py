"""Culvert calculators package

Calculator Types (Independent Implementations):
----------------------------------------------
1. SingleAtGradeCalculator: n=1, any alpha (UNIFIED)
2. MultiAtGradeCalculator: n>=2, any alpha (UNIFIED)
"""

from .base import BaseCulvertCalculator, CulvertInput, CulvertType
from .factory import CulvertCalculatorFactory

# Unified calculators
from .single_atgrade import SingleAtGradeCalculator
from .multi_atgrade import MultiAtGradeCalculator

__all__ = [
    # Base classes
    "BaseCulvertCalculator",
    "CulvertInput",
    "CulvertType",
    # Factory
    "CulvertCalculatorFactory",
    # Unified calculators
    "SingleAtGradeCalculator",
    "MultiAtGradeCalculator",
]
