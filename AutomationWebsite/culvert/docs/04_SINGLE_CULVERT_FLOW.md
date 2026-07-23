# Single Perpendicular Culvert - Implementation Flow

## ✅ Currently Working Implementation

This document describes the **complete working flow** for the `SinglePerpendicularAtGradeCalculator` (n=1, α=0).

---

## 📊 Calculation Steps Overview

```
┌─────────────────────────────────────────────────────────────┐
│              SinglePerpendicularAtGradeCalculator           │
│                     calculate() method                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Step 1        │    │ Step 2        │    │ Step 3        │
│ Apply         │    │ Apply Table1  │    │ Apply Table2  │
│ Directions    │    │ (Geometry)    │    │ (Rebar)       │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Step 4        │    │ Step 5        │    │ Step 6        │
│ Apply Table3  │    │ Round to      │    │ Return Data   │
│ (Wing Walls)  │    │ Strings       │    │ Dictionary    │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 🔄 Step 1: Apply Directions

```python
def _apply_directions(self):
    """Set direction labels based on direction_flag."""
    if self.params.direction_flag:
        self.left = "UP"
        self.right = "DOWN"
    else:
        self.left = "DOWN"
        self.right = "UP"
    
    self.data["b03"] = self.left   # Left direction
    self.data["b04"] = self.right  # Right direction
```

### Output Keys:
- `b03`: Left direction label ("UP" or "DOWN")
- `b04`: Right direction label ("DOWN" or "UP")

---

## 📐 Step 2: Apply Table1 (Geometry)

### Source: `Culvert_one.csv`

### Lookup Process:
1. Filter by `n` and `D`
2. Find row where `Hs` falls within the range
3. Check if calculated `H` < table `H`

### Table1 Columns:
| Column | Description |
|--------|-------------|
| `n` | Number of openings |
| `D` | Diameter (m) |
| `H` | Maximum wall height this row applies to |
| `Hs` | Static head range (e.g., "(0.00, 0.60)") |
| `a1, a2` | Horizontal haunch dimensions |
| `b1, b2` | Vertical dimensions |
| `c1, c2` | Concrete cover values (mm) |
| `f` | Foundation width |
| `m` | Foundation depth |
| `t` | Slab thickness |
| `phi_b` | Rebar diameter for bending |
| `j*` | Joint spacing factor |

### Calculations Performed:

```python
# Basic parameters stored directly
self.data["c01"] = CL                    # Centerline elevation
self.data["c02"] = dever_left            # Left slope %
self.data["c03"] = dever_right           # Right slope %
self.data["c08"] = abs(A)                # Left distance
self.data["c09"] = abs(B)                # Right distance
self.data["c10"] = abs(L)                # Total length

# Elevation at bottom of culvert (LEFT)
c04 = CL + (dever_left/100) × A - Hs - t - 0.3

# Elevation at bottom of culvert (RIGHT)
c14 = CL + (dever_right/100) × B - Hs - t - 0.3

# Natural ground elevation (LEFT) - depends on direction
if LEFT == "UP":
    c06 = ax_natural + z_natural × A - ret
else:
    c06 = ax_natural - z_natural × A - ret

# Natural ground elevation (RIGHT)
if LEFT == "UP":
    c12 = ax_natural - z_natural × B - ret
else:
    c12 = ax_natural + z_natural × B - ret

# Foundation bottom elevations
c07 = c06 - m   # Left
c11 = c12 - m   # Right

# Average wall height
H = ((c04 - c06 + 0.3) + (c14 - c12 + 0.3)) / 2
```

### Output Keys (c-series and d-series):
| Key | Value | Description |
|-----|-------|-------------|
| `c01` | CL | Project line elevation |
| `c02` | dever_left | Left cross slope |
| `c03` | dever_right | Right cross slope |
| `c04` | calculated | Left bottom elevation |
| `c06` | calculated | Left natural ground |
| `c07` | calculated | Left foundation bottom |
| `c08` | A | Left distance |
| `c09` | B | Right distance |
| `c10` | L | Total length |
| `c11` | calculated | Right foundation bottom |
| `c12` | calculated | Right natural ground |
| `c14` | calculated | Right bottom elevation |
| `d01` | z_toli | Longitudinal slope |
| `d02` | D | Diameter |
| `d03` | f | Foundation width |
| `d04` | m | Foundation depth |
| `d05` | b1 | Wall thickness |
| `d06` | a2 | Haunch dimension |
| `d07` | a1 | Haunch dimension |
| `d08` | b2 | Vertical dimension |
| `d09` | c2 | Concrete cover |
| `d10` | c1 | Concrete cover |
| `d11` | t | Slab thickness |
| `d12` | j* | Joint spacing |
| `d13` | Hs | Static head |

---

## 🔩 Step 3: Apply Table2 (Rebar)

### Source: `Culvert_full.csv`

### Lookup Process:
1. Filter by `n`, `D`, `c1`, `t`
2. Find row where `Hs` falls within range

### Rebar Positions (10 total):

```
CROSS SECTION OF BOX CULVERT:
═══════════════════════════════════════════
         P2 (top slab, top)
    ┌─────────────────────────────────┐
    │ P1 (top slab, bottom)           │
P4 ─┤                                 ├─ P5
    │ P3 (distribution)               │
    │                                 │
P6 ─┤       P0 (haunch)               ├─ P6
    │                                 │
    │ P7 (bottom slab, top)           │
    └─────────────────────────────────┘
         P8 (bottom slab, bottom)
         P9 (distribution)
═══════════════════════════════════════════
```

### For Each Position (p1-p9, p0):

| Data | Description |
|------|-------------|
| `diameter(mm)` | Rebar diameter |
| `n` | Count per meter OR fixed count (format: "3.1" or "5*2") |
| `distance(cm)` | Spacing between rebars |
| `L(m)` | Base length per rebar |
| `sh_i1-i5` | Shape dimensions for bending schedule |

### Output Keys (f-series):

| Range | Description |
|-------|-------------|
| `f001-f009` | Diameters for positions 1-9 |
| `f010-f018` | Counts for positions 1-9 |
| `f019-f044` | Shape dimensions |
| `f045-f053` | Base lengths per bar |
| `f054-f062` | Total lengths |
| `f063-f071` | Weight per meter (kg/m) |
| `f072-f080` | Total weights (kg) |
| `f081-f088` | Position 10 (p0) data |
| `f089` | Average rebar weight per meter (kg/m) |
| `f090` | Total weight for positions 8-9 |
| `f091` | Grand total rebar weight |

### Weight Calculation Formula:
```python
# Weight per meter for diameter D (mm):
W = (π × (D/1000)² / 4) × 7850  # kg/m
# Where 7850 kg/m³ is steel density
```

---

## 🏗️ Step 4: Apply Table3 (Wing Walls)

### Source: `Culvert_dastak.csv`

### Lookup Process:
- Query 3 times for: `H_min`, `H_max_left`, `H_max_right`

### Table3 Columns:
| Column | Description |
|--------|-------------|
| `H` | Wall height (1-7m range) |
| `x` | Heel extension behind wall |
| `b` | Wall thickness at base |
| `f` | Foundation width |
| `m` | Foundation depth |

### Wing Wall Layout:

```
                    UPSTREAM
                       ↑
             W3 ←─────────────→ W1
                    ┌───┐
                    │   │ CULVERT
                    │   │
             W4 ←───┴───┴───→ W2
                       ↓
                   DOWNSTREAM
```

### Distance Calculation (Iterative):

```python
def _find_distance_for_bal(h_min, h_max, ball_degree, direction):
    """
    Wing wall distance formula:
    d = (H_max - H_min) / cos(ball_degree) × z_shirvani
    
    Iterates because ground slope affects ending height.
    """
    d1, d2 = 0, 1
    while abs(d2 - d1) > 0.2:
        d1 = (h_max - h_min) / cos(radians(ball_degree)) * z_shirvani
        if direction == "UP":
            h_min_temp = h_min + d1 * z_natural
        else:
            h_min_temp = h_min - d1 * z_natural
        d2 = (h_max - h_min_temp) / cos(radians(ball_degree)) * z_shirvani
    return d2
```

### Output Keys (e-series):

| Key | Description |
|-----|-------------|
| `e01-e04` | Wall distances for W1-W4 |
| `e05-e06` | Maximum heights (e05=right, e06=left) |
| `e07-e10` | Foundation widths at max height |
| `e11-e14` | s1 dimensions at max height (f - b) |
| `e15-e18` | s1 dimensions at min height |
| `e19-e22` | s2 dimensions (x + 0.35 offset) |

---

## 📄 Step 5 & 6: Finalize Output

```python
def _round_data_to_strings(self):
    """Convert all values to strings for DXF."""
    for k, v in self.data.items():
        self.data[k] = str(v)

def get_template_filename(self) -> str:
    """Return DXF template for this calculator."""
    return 'single_perpendicular_atGrade.dxf'
```

---

## 🗺️ DXF Placeholder Mapping

The DXF template contains TEXT entities with placeholder IDs (e.g., `i-001`, `i-A`).

### Mapping Reference (from hint.txt):

```
# Direction Labels
i-092 → b03 (LEFT direction)
i-093 → b01 (City top - optional)
i-094 → b02 (City bottom - optional)
i-095 → b04 (RIGHT direction)

# Elevation & Distance
i-097 → c01 (CL)
i-098 → c02 (dever_left)
i-099 → c03 (dever_right)
i-100 → c04 (left bottom elevation)
i-101 → c06 (left natural ground)
i-102 → c07 (left foundation bottom)
i-103 → c14 (right bottom elevation)
i-104 → c12 (right natural ground)
i-105 → c11 (right foundation bottom)
i-A   → c08 (distance A)
i-B   → c09 (distance B)
i-L   → c10 (total length L)

# Structural Parameters
i-096 → d01 (z_toli)
i-D   → d02 (diameter)
i-f   → d03 (foundation width)
i-m   → d04 (foundation depth)
i-b1  → d05 (wall thickness)
... and many more
```

---

## 📁 Output Files

Generated DXF files are saved to:
```
culvert/results/culvert_single_n1_D{D}.dxf
```

If errors occurred:
```
culvert/results/culvert_single_n1_D{D}_DEBUG.dxf
```

---

*Last Updated: February 2, 2026*
