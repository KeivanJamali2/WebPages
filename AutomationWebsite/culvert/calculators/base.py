"""
Base calculator class for culvert design calculations.
Defines the interface and common functionality for all calculator types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import pandas as pd


class CulvertType(Enum):
    """Enum for different culvert types based on n and alpha parameters."""
    SINGLE = (1, 0)  # n=1, alpha=0 (single opening, no angle)
    SINGLE_ANGULAR = (1, 'any')  # n=1, alpha!=0 (single opening, angular)
    MULTI = ('multi', 0)  # n>1, alpha=0 (multiple openings, no angle)
    MULTI_ANGULAR = ('multi', 'any')  # n>1, alpha!=0 (multiple openings, angular)
    UNDERGROUND_SINGLE = (5, 0)  # n=5 (underground single)
    UNDERGROUND_SINGLE_ANGULAR = (6, 0)  # n=6 (underground single angular)
    UNDERGROUND_MULTI = (7, 0)  # n=7 (underground multi)
    UNDERGROUND_MULTI_ANGULAR = (8, 0)  # n=8 (underground multi angular)


@dataclass
class CulvertInput:
    """Input parameters for culvert design."""
    # Basic parameters
    n: int  # Number of openings (or type code 5-8 for underground)
    D: float  # Diameter (m)
    L: float  # Length (m)
    Hs: float  # Static head (m)
    H_min: float  # Minimum height (m)
    
    # Location parameters
    CL: float  # Center line elevation
    ax_natural: float  # Natural axis elevation
    dever_right: float  # Right slope
    dever_left: float  # Left slope
    
    # Slope parameters
    z_natural: float  # Natural slope
    z_toli: float  # Longitudinal slope
    z_shirvani: float  # Transverse slope (was int, but form allows float values)
    u_shirvani: float
    ret: float  # Retention
    
    # Angle parameters
    ball_degree: float  # Ball degree
    alpha: float  # Angle (degrees)
    
    # Distance parameters
    A: float  # Distance A
    B: float  # Distance B
    
    # Direction flag
    direction_flag: bool  # True = left UP/right DOWN, False = left DOWN/right UP

    # Project information
    employer: str = ""          # Employer / Client name
    project_title: str = ""     # Project title
    project_type: str = ""      # Project type / category
    date: str = ""              # Date
    map_code: str = ""          # Map / drawing code
    page_number: str = ""       # Page / sheet number
    location: str = ""          # Project location
    city_top: str = ""          # Upper city name (b01)
    city_bottom: str = ""       # Lower city name (b02)


class BaseCulvertCalculator(ABC):
    """
    Abstract base class for culvert design calculations.
    All specific calculator types inherit from this class.
    """
    
    def __init__(self, 
                 input_params: CulvertInput,
                 table_repository,
                 progress_callback: Optional[Callable[[int], None]] = None):
        """
        Initialize calculator with input parameters.
        
        Args:
            input_params: CulvertInput dataclass with all parameters
            table_repository: Repository for accessing CSV tables
            progress_callback: Optional callback for progress updates (0-100)
        """
        self.params = input_params
        self.tables = table_repository
        self.progress_callback = progress_callback
        
        # Store calculated data as dict for DXF placeholders
        self.data: Dict[str, Any] = {}
        
        # Error messages
        self.messages: list[str] = []
        
        # Calculate derived values
        self.H = 0.0  # Final height (calculated)
        
        # Direction labels
        if self.params.direction_flag:
            self.left = "UP"
            self.right = "DOWN"
        else:
            self.left = "DOWN"
            self.right = "UP"
    
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        Perform the calculation and return data dictionary.
        This is the main entry point for calculation.
        
        Returns:
            Dictionary with placeholder keys (i-001, i-002, etc.) and calculated values
            
        Raises:
            CalculationError: If calculation fails
        """
        pass
    
    @abstractmethod
    def get_template_filename(self) -> str:
        """
        Get the DXF template filename for this culvert type.
        
        Returns:
            DXF template filename (e.g., '1_Culvert_with_one_opening.dxf')
        """
        pass
    
    def _update_progress(self, progress: int):
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def _apply_directions(self):
        """Apply direction labels to data dictionary."""
        self.data["b03"] = self.left
        self.data["b01"] = self.params.city_top
        self.data["b02"] = self.params.city_bottom
        self.data["b04"] = self.right
        print(f"[INFO] Successfully applied parameters for directions. Left: {self.data['b03']}, Up: {self.data['b01']}, Down: {self.data['b02']}, Right: {self.data['b04']}")
    
    def _apply_information(self):
        """Apply project information from input parameters to data dictionary."""
        self.data["a01"] = self.params.employer
        self.data["a02"] = self.params.project_title
        self.data["a03"] = self.params.project_type
        self.data["a04"] = self.params.date
        self.data["a05"] = self.params.map_code
        self.data["a06"] = self.params.page_number
        self.data["a07"] = f"{self.params.n} * {self.params.D}m"
        self.data["a08"] = self.params.location
        print("[INFO] Successfully applied project information")
        self.data["a09"] = f"{self.params.alpha}"
        self.data["a10"] = self.params.Hs # Need attention
        print(f"[INFO] Successfully applied general information. Employer: {self.data['a01']}, Project Title: {self.data['a02']}, Project Type: {self.data['a03']}, Date: {self.data['a04']}, Map Code: {self.data['a05']}, Page Number: {self.data['a06']}, Culvert Type: {self.data['a07']}, Location: {self.data['a08']}, Angle: {self.data['a09']}, Static Head: {self.data['a10']}")
        
    def _round_data_to_strings(self):
        """Convert all data values to strings for DXF output."""
        for k, v in self.data.items():
            self.data[k] = str(v)
    
    def get_messages(self) -> str:
        """
        Get all error/warning messages as single string.
        
        Returns:
            Combined message string separated by ' / '
        """
        return " / ".join(self.messages) if self.messages else ""
    
    def validate_input(self) -> Optional[str]:
        """
        Validate input parameters.
        
        Returns:
            Error message if validation fails, None otherwise
        """
        if self.params.D <= 0:
            return f"[CHECK] Diameter (D) must be positive - currently {self.params.D}"
        if self.params.L <= 0:
            return f"[CHECK] Length (L) must be positive - currently {self.params.L}"
        if self.params.Hs < 0:
            return f"[CHECK] Static head (Hs) cannot be negative - currently {self.params.Hs}"
        if self.params.n <= 0:
            return f"[CHECK] Number of openings (n) must be positive - currently {self.params.n}"
        
        return None
