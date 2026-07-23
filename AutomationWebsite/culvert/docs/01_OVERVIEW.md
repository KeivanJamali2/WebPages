# Culvert Design Automation - Overview

## 📋 Project Summary

This project automates the design and drawing generation of **box culverts** - reinforced concrete structures used to convey water under roadways. The system takes engineering input parameters and generates professional DXF drawings with all calculated dimensions and rebar specifications.

---

## 🎯 What is a Culvert?

A box culvert is a reinforced concrete structure with the following key components:

```
    Road Surface (CL = Center Line Elevation)
    ═══════════════════════════════════════════
           ↑ Hs (Static Head / Fill Height)
    ┌─────────────────────────────────────────┐  ← Top Slab (thickness = t)
    │                                         │
    │         Box Opening (D x D)             │  ← Internal dimensions
    │                                         │
    └─────────────────────────────────────────┘  ← Bottom Slab
           ↓ m (Foundation depth)
    ═══════════════════════════════════════════  ← Natural ground level
```

---

## 🔢 Culvert Types

The system supports **4 main culvert types** based on two parameters:

| Type | n (Openings) | α (Angle) | Status |
|------|-------------|-----------|--------|
| **Single Perpendicular** | n = 1 | α = 0° | ✅ IMPLEMENTED |
| **Single Angular** | n = 1 | α ≠ 0° | ⏳ NOT IMPLEMENTED |
| **Multi Perpendicular** | n > 1 | α = 0° | ⏳ NOT IMPLEMENTED |
| **Multi Angular** | n > 1 | α ≠ 0° | ⏳ NOT IMPLEMENTED |

### Visual Representation:

```
PERPENDICULAR (α = 0°):          ANGULAR (α ≠ 0°):
                                 
    Road                              Road
    ════                              ════
      │                                  ╲
      │ Culvert                           ╲ Culvert
      │                                    ╲
    ════                              ════
    Water flow →                      Water flow →
```

---

## 📁 Project Structure

```
culvert/
├── calculators/           # Core calculation logic
│   ├── base.py           # Abstract base class & data structures
│   ├── factory.py        # Calculator selection factory
│   ├── single_perpendicular_atgrade.py  # ✅ Working
│   ├── single_angular_atgrade.py        # ⏳ Stub
│   ├── multi_perpendicular_atgrade.py   # ⏳ Stub
│   └── multi_angular_atgrade.py         # ⏳ Stub
│
├── data/                  # CSV lookup tables
│   ├── Culvert_one.csv        # Single opening parameters
│   ├── Culvert_multi.csv      # Multi opening parameters
│   ├── Culvert_full.csv       # Rebar specifications
│   ├── Culvert_dastak.csv     # Wing wall parameters
│   └── Culvert_multi_extra.csv # Extra rebar for multi-opening
│
├── processors/            # Web interface processors
│   └── culvert_processor.py
│
├── repositories/          # Data access layer
│   └── table_repository.py
│
├── services/              # DXF generation service
│   └── dxf_service.py
│
├── templates_dxf/         # AutoCAD DXF templates
│   ├── single_perpendicular_atGrade.dxf    # ✅ Available
│   ├── 2_Culvert_with_one_opening_angular.dxf
│   └── 3_Culvert_with_multi_opening.dxf
│
├── results/               # Generated DXF output files
│
└── docs/                  # Documentation (this folder)
```

---

## 🔄 High-Level Process Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Web Form   │ ──► │  Processor   │ ──► │  Calculator  │ ──► │ DXF Service  │
│   (HTML)     │     │  (Python)    │     │  (Python)    │     │  (ezdxf)     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
   User Input          Validation           Calculations         DXF Output
   Parameters          & Routing            + Table Lookup       File Generation
```

---

## 📄 Related Documentation

1. **[02_ARCHITECTURE.md](02_ARCHITECTURE.md)** - Detailed code architecture
2. **[03_INPUT_PARAMETERS.md](03_INPUT_PARAMETERS.md)** - All input parameters explained
3. **[04_SINGLE_CULVERT_FLOW.md](04_SINGLE_CULVERT_FLOW.md)** - Single perpendicular implementation
4. **[05_DATA_TABLES.md](05_DATA_TABLES.md)** - CSV table structure reference
5. **[06_OTHER_TYPES_REQUIREMENTS.md](06_OTHER_TYPES_REQUIREMENTS.md)** - What needs to be implemented

---

## 🚀 Quick Start

1. User accesses `/culvert_processing` route
2. Fills in the form with design parameters
3. Submits form to `/process_culvert`
4. System generates DXF file
5. User downloads the generated drawing

---

*Last Updated: February 2, 2026*
