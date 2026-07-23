# Culvert Design - Code Architecture

## 🏗️ Layered Architecture

The culvert design system follows a clean layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ culvert_process │  │  app.py routes  │                   │
│  │     .html       │  │ /process_culvert│                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            CulvertProcessor                          │    │
│  │  - Receives form data                                │    │
│  │  - Creates CulvertInput dataclass                    │    │
│  │  - Calls factory to get calculator                   │    │
│  │  - Triggers DXF generation                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              CulvertCalculatorFactory                  │  │
│  │  - Selects calculator based on n and alpha             │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│         ┌────────────────────┼────────────────────┐         │
│         ▼                    ▼                    ▼         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   Single    │     │   Single    │     │    Multi    │   │
│  │Perpendicular│     │   Angular   │     │ Calculators │   │
│  │ Calculator  │     │ Calculator  │     │   (Stubs)   │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                         │
│  ┌─────────────────┐        ┌─────────────────┐             │
│  │TableRepository  │        │   DXFService    │             │
│  │ - Load CSV      │        │ - Load template │             │
│  │ - Query tables  │        │ - Replace text  │             │
│  │ - Return params │        │ - Save output   │             │
│  └─────────────────┘        └─────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER                        │
│  ┌─────────────────┐        ┌─────────────────┐             │
│  │   CSV Tables    │        │  DXF Templates  │             │
│  │ culvert/data/   │        │culvert/templates│             │
│  └─────────────────┘        └─────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Key Classes

### 1. CulvertInput (base.py)
```python
@dataclass
class CulvertInput:
    """Input parameters for culvert design."""
    # Basic parameters
    n: int          # Number of openings
    D: float        # Diameter (m)
    L: float        # Length (m)
    Hs: float       # Static head (m)
    H_min: float    # Minimum height (m)
    
    # Location parameters
    CL: float           # Center line elevation
    ax_natural: float   # Natural axis elevation
    dever_right: float  # Right slope (%)
    dever_left: float   # Left slope (%)
    
    # Slope parameters
    z_natural: float    # Natural slope (ratio)
    z_toli: float       # Longitudinal slope (ratio)
    z_shirvani: float   # Transverse slope factor
    ret: float          # Retention depth
    
    # Angle parameters
    ball_degree: float  # Wing wall angle (degrees)
    alpha: float        # Skew angle (degrees)
    
    # Distance parameters
    A: float            # Left distance from centerline
    B: float            # Right distance from centerline
    
    # Direction flag
    direction_flag: bool  # True = left UP, False = left DOWN
```

### 2. BaseCulvertCalculator (base.py)
```python
class BaseCulvertCalculator(ABC):
    """Abstract base class for all calculators."""
    
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """Perform calculations and return data dictionary."""
        pass
    
    @abstractmethod
    def get_template_filename(self) -> str:
        """Get DXF template filename."""
        pass
```

### 3. CulvertCalculatorFactory (factory.py)
```python
class CulvertCalculatorFactory:
    @staticmethod
    def create_calculator(input_params, table_repository, progress_callback=None):
        n = input_params.n
        alpha = input_params.alpha
        
        if n == 1:
            if alpha == 0:
                return SinglePerpendicularAtGradeCalculator(...)  # ✅ IMPLEMENTED
            else:
                return SingleAngularAtGradeCalculator(...)        # ⏳ STUB
        elif n > 1:
            if alpha == 0:
                return MultiPerpendicularAtGradeCalculator(...)   # ⏳ STUB
            else:
                return MultiAngularAtGradeCalculator(...)         # ⏳ STUB
```

### 4. TableRepository (table_repository.py)
```python
class TableRepository:
    """Access to all CSV lookup tables."""
    
    def __init__(self, data_dir):
        self.t1 = pd.read_csv('Culvert_one.csv')      # Single params
        self.t2 = pd.read_csv('Culvert_full.csv')     # Rebar specs
        self.t3 = pd.read_csv('Culvert_dastak.csv')   # Wing walls
        self.t_multi = pd.read_csv('Culvert_multi.csv')
        self.t4 = pd.read_csv('Culvert_multi_extra.csv')
    
    def find_in_table1(self, n, D, Hs, H=0) -> pd.Series
    def find_in_table2(self, n, D, Hs, c1, t) -> pd.Series
    def find_in_table3(self, H) -> pd.Series
```

### 5. DXFService (dxf_service.py)
```python
class DXFService:
    """DXF file generation service."""
    
    def load_template(self, template_filename) -> Drawing
    def replace_placeholders(self, doc, data) -> int
    def generate_dxf(self, template_filename, data, output_filename) -> str
```

---

## 🔄 Data Flow Diagram

```
┌────────────┐
│  Web Form  │
└─────┬──────┘
      │ POST /process_culvert
      ▼
┌────────────────────────────────────────────────────┐
│                 CulvertProcessor                    │
│  1. Extract form data                              │
│  2. Create CulvertInput dataclass                  │
│  3. Call CulvertCalculatorFactory.create_calculator│
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────┐
│           CulvertCalculatorFactory                  │
│  Check: n=1 and alpha=0?                           │
│  → Return SinglePerpendicularAtGradeCalculator     │
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────┐
│      SinglePerpendicularAtGradeCalculator          │
│                                                     │
│  calculator.calculate():                           │
│    1. _apply_directions()                          │
│    2. tables.find_in_table1(n, D, Hs)             │
│       → _apply_table1(result)                      │
│    3. tables.find_in_table2(n, D, Hs, c1, t)      │
│       → _apply_table2(result)                      │
│    4. tables.find_in_table3(H_min, H_max_l, H_max_r)│
│       → _apply_table3(results)                     │
│    5. _round_data_to_strings()                     │
│    6. Return self.data dict                        │
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────┐
│                  DXFService                         │
│                                                     │
│  generate_dxf(template, data, output_filename):    │
│    1. Load DXF template file                       │
│    2. Find all TEXT entities with placeholders     │
│    3. Replace placeholders with calculated values  │
│    4. Save to output directory                     │
│    5. Return file path                             │
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────┐
│              JSON Response to Browser              │
│  {                                                 │
│    "status": "success",                            │
│    "filename": "culvert_single_n1_D2.0.dxf",      │
│    "download_url": "/download_culvert/..."         │
│  }                                                 │
└────────────────────────────────────────────────────┘
```

---

## 🔑 Key Design Patterns Used

1. **Factory Pattern** - `CulvertCalculatorFactory` creates appropriate calculator
2. **Repository Pattern** - `TableRepository` abstracts data access
3. **Service Pattern** - `DXFService` handles DXF operations
4. **Template Method Pattern** - Base calculator defines algorithm structure
5. **Strategy Pattern** - Different calculators implement different strategies

---

*Last Updated: February 2, 2026*
