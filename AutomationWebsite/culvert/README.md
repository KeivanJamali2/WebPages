# Culvert Module - Organized Structure

## 📁 Directory Structure

```
culvert/                                    # Main culvert module
├── __init__.py                            # Module initialization
├── calculators/                           # Calculation engines
│   ├── __init__.py
│   ├── base.py                           # BaseCulvertCalculator, CulvertInput
│   ├── factory.py                        # CulvertCalculatorFactory
│   ├── single_culvert.py                 # Single opening (n=1, alpha=0)
│   ├── angular_culvert.py                # Angular (n=1, alpha≠0)
│   └── multi_culvert.py                  # Multi-opening (n>1, alpha=0)
├── repositories/                          # Data access layer
│   ├── __init__.py
│   └── table_repository.py               # CSV table queries
├── services/                              # External services
│   ├── __init__.py
│   └── dxf_service.py                    # DXF file generation
├── processors/                            # Web request handlers
│   ├── __init__.py
│   └── culvert_processor.py              # CulvertProcessor for Flask
├── data/                                  # CSV data tables
│   ├── Culvert_one.csv                   # Table 1: Base parameters (38 rows)
│   ├── Culvert_full.csv                  # Table 2: Rebar specs (39 rows)
│   ├── Culvert_dastak.csv                # Table 3: Handle details (7 rows)
│   ├── Culvert_multi.csv                 # Table 4: Multi data (14 rows)
│   └── Culvert_multi_extra.csv           # Table 5: Extra positions (8 rows)
├── templates_dxf/                         # DXF template files
│   ├── 1_Culvert_with_one_opening.dxf
│   ├── 2_Culvert_with_one_opening_angular.dxf
│   └── 3_Culvert_with_multi_opening.dxf
├── results/                               # Generated DXF output files
│   └── (generated DXF files saved here)
└── tests/                                 # Module-specific tests
    ├── test_table_repository.py
    ├── test_single_culvert_calculator.py
    └── test_integration.py
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- All culvert-specific code isolated in `culvert/` module
- Clear separation from website infrastructure (`models/`, `templates/`, etc.)
- Each subdirectory has a single responsibility

### 2. **Self-Contained Module**
- All culvert data (CSV tables, DXF templates) in one place
- Independent tests that don't rely on website structure
- Can be extracted as standalone package if needed

### 3. **Clean Imports**
```python
# From Flask app
from culvert.processors import CulvertProcessor

# From tests
from culvert.calculators import CulvertInput, CulvertCalculatorFactory
from culvert.repositories import TableRepository
from culvert.services import DXFService
```

## 📝 What Stayed Outside culvert/

### templates/ (Flask HTML templates)
- `templates/culvert_process.html` - Web form UI
- Reason: Part of Flask's template system, not module-specific

### static/ (CSS, JS, translations)
- `static/translations/i18n.json` - Bilingual translations
- Reason: Shared across entire website, not culvert-specific

### Files/ (Website-wide file storage)
- Kept for other tools (generic, PPK, CSDP, etc.)
- culvert/ now has its own `templates_dxf/` and `results/`

## 🔄 Path Updates

### Before Reorganization:
```python
# Old paths
data/culvert_tables/              → culvert/data/
Files/culvert_templates/          → culvert/templates_dxf/
Files/culvert_results/            → culvert/results/
models/calculators/               → culvert/calculators/
models/repositories/table_repository.py → culvert/repositories/
models/services/dxf_service.py    → culvert/services/
models/core/culvert_processor.py  → culvert/processors/
tests/test_*.py                   → culvert/tests/
```

### After Reorganization:
```python
# New imports in app.py
from culvert.processors.culvert_processor import CulvertProcessor

# New download path in app.py
culvert_results_dir = os.path.join(BASE_DIR, 'culvert', 'results')

# New processor initialization
culvert_dir = os.path.join(base_dir, 'culvert')
template_dir = os.path.join(culvert_dir, 'templates_dxf')
output_dir = os.path.join(culvert_dir, 'results')
table_dir = os.path.join(culvert_dir, 'data')
```

## ✅ Verification

### Run Tests
```bash
# End-to-end web workflow test
python test_web_workflow.py

# Module-specific tests
cd culvert/tests
python test_table_repository.py
python test_single_culvert_calculator.py
python test_integration.py
```

### Expected Output
```
TEST SUMMARY
============================================================
✅ PASS: Translations
✅ PASS: Single Culvert
✅ PASS: Angular Culvert
✅ PASS: Multi-Opening Culvert

Total: 4/4 tests passed

🎉 All tests passed! Web interface is ready!
```

## 🚀 Benefits

1. **Organization**: All culvert code in one module
2. **Maintainability**: Easy to find and update culvert-specific code
3. **Testability**: Self-contained tests with clear dependencies
4. **Scalability**: Can add more tools without cluttering main directories
5. **Portability**: Module can be extracted or shared independently

## 📦 Module Size

```
culvert/
├── calculators/     ~3,000 lines
├── repositories/    ~350 lines
├── services/        ~200 lines
├── processors/      ~150 lines
├── data/            106 CSV rows (5 files)
├── templates_dxf/   3 DXF files (~2.5 MB total)
└── tests/           ~600 lines

Total: ~4,300 lines of Python code
       3 DXF templates
       5 data tables
```

## 🔮 Future Enhancements

The modular structure makes it easy to add:
- New calculator types (underground n=5,6,7,8)
- Additional data tables
- More DXF templates
- API endpoints (REST API for calculations)
- Command-line interface (CLI tool)
- Standalone desktop application

## 📚 Related Documentation

- `CULVERT_USAGE_GUIDE.md` - How to use the web interface
- `CULVERT_PROJECT_COMPLETE.md` - Project completion summary
- `culvert/calculators/base.py` - Calculator architecture
- `culvert/services/dxf_service.py` - DXF generation details

---

**Last Updated**: 2025-10-24
**Module Version**: 1.0.0
**Status**: ✅ Production Ready
