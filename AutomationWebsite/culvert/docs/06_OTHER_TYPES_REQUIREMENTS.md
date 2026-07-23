# Requirements for Other Culvert Types

## 📋 Implementation Status

| Calculator | File | Status | Template Available |
|------------|------|--------|-------------------|
| SinglePerpendicularAtGradeCalculator | `single_perpendicular_atgrade.py` | ✅ COMPLETE | ✅ `single_perpendicular_atGrade.dxf` |
| SingleAngularLessCalculator | `single_angular_less_atgrade.py` | ⏳ TO DO | ✅ `single_angularL_atGrade.dxf` |
| SingleAngularMoreCalculator | `single_angular_more_atgrade.py` | ⏳ TO DO | ✅ `single_angularM_atGrade.dxf` |
| MultiPerpendicularAtGradeCalculator | `multi_perpendicular_atgrade.py` | ⏳ STUB | ✅ `3_Culvert_with_multi_opening.dxf` |
| MultiAngularAtGradeCalculator | `multi_angular_atgrade.py` | ⏳ STUB | ❓ Not confirmed |

---

## 🔷 Type 2: Single Angular (n=1, α≠0)

### ⚠️ TWO Sub-Types Based on Angle

Single Angular has **two separate templates**:

| Sub-Type | Template File | Condition |
|----------|---------------|-----------|
| **Angular Less (L)** | `single_angularL_atGrade.dxf` | 0° < α < 45° |
| **Angular More (M)** | `single_angularM_atGrade.dxf` | α ≥ 45° |

```
ANGULAR LESS (L):                    ANGULAR MORE (M):
    α < 45°                              α ≥ 45°
                                     
    Road Direction →                     Road Direction →
    ════════════════                     ════════════════
         ╲                                    ╲
          ╲ Small angle                        ╲ Large angle
           ╲ (< 45°)                            ╲ (≥ 45°)
    ════════════════                     ════════════════
```

### ✅ CONFIRMED SPECIFICATIONS:
1. **Threshold angle: 45°** - α < 45° uses L, α ≥ 45° uses M
2. **Same calculations** - Both use identical formulas as Single Perpendicular
3. **Same parameters** - No additional inputs required
4. **Only template differs** - The DXF template layout is the only difference

---

### Conditions:
- Number of openings: `n = 1`
- Skew angle: `alpha ≠ 0` (e.g., 15°, 30°, 45°)

### Differences from Single Perpendicular:

#### 1. **Length Calculations**
```python
# PERPENDICULAR (α=0):
c08 = abs(A)  # cos(0) = 1

# ANGULAR (α≠0):
c08 = abs(A) / cos(radians(alpha))  # Adjusted for angle
c09 = abs(B) / cos(radians(alpha))
c10 = abs(L) / cos(radians(alpha))
```

#### 2. **Diameter Adjustment**
```python
# PERPENDICULAR (α=0):
d02 = D

# ANGULAR (α≠0):
d02 = D / cos(radians(alpha))  # Effective span increases
```

#### 3. **Rebar Shape Adjustments**
For positions with shapes that span the width (p1, p2), the shape dimensions need angular adjustment:
```python
# Example for position 1:
f020 = sh_i2 / cos(radians(alpha))  # Shape dimension 2
f022 = sh_i4 / cos(radians(alpha))  # Shape dimension 4
```

#### 4. **Wing Wall Geometry**
The wing walls at an angular culvert have different lengths:
- Two walls are shorter (acute angle side)
- Two walls are longer (obtuse angle side)

### Required Changes:

| Component | Change Required |
|-----------|-----------------|
| `_apply_table1()` | Add `/ cos(alpha)` to length/dimension calculations |
| `_apply_table2()` | Adjust shape dimensions for affected positions |
| `_apply_table3()` | Calculate different distances for each wall pair |
| Template | Use `2_Culvert_with_one_opening_angular.dxf` |

### Data Tables Used:
- ✅ `Culvert_one.csv` - Same as perpendicular
- ✅ `Culvert_full.csv` - Same, but values need adjustment
- ✅ `Culvert_dastak.csv` - Same, but 4 different H values needed

---

## 🔷 Type 3: Multi Perpendicular (n>1, α=0)

### Conditions:
- Number of openings: `n > 1` (typically 2 or 3)
- Skew angle: `alpha = 0`

### Additional Structural Elements:

```
MULTI-OPENING CULVERT (n=3):
═══════════════════════════════════════════════════════════════
                                                               
┌─────────────────┬─────────────────┬─────────────────┐        
│                 │                 │                 │        
│   Opening 1     │   Opening 2     │   Opening 3     │        
│      D × D      │      D × D      │      D × D      │        
│                 │                 │                 │        
└─────────────────┴─────────────────┴─────────────────┘        
        ↑               ↑               ↑                      
     Pillar 1        Pillar 2                                  
       (p1)            (p2)                                    
═══════════════════════════════════════════════════════════════
```

### New Parameters from Culvert_multi.csv:

| Parameter | Description |
|-----------|-------------|
| `p1` | Pillar width 1 |
| `p2` | Pillar width 2 |
| `e` | Edge distance |
| `k` | Additional spacing parameter |

### Additional Rebar from Culvert_multi_extra.csv:

| Parameter | Description |
|-----------|-------------|
| `n on each kole` | Rebars per opening |
| `n on each paye` | Rebars per pillar (format: "2*2") |

### Required Changes:

| Component | Change Required |
|-----------|-----------------|
| `_apply_table1()` | Use `Culvert_multi.csv`, add pillar parameters |
| `_apply_table2()` | Multiply rebar counts by n openings |
| `_apply_table4()` | NEW: Apply extra rebar for pillars |
| `_apply_table3()` | Same logic, but total width changes |
| Template | Use `3_Culvert_with_multi_opening.dxf` |

### New Output Keys Needed:

| Key | Description |
|-----|-------------|
| `p01` | Pillar 1 width |
| `p02` | Pillar 2 width |
| `p03` | Edge distance |
| `n_openings` | Number of openings |
| `total_width` | n×D + (n-1)×pillar_width + 2×wall_thickness |

### Calculation Differences:

```python
# Total culvert width
total_width = n * D + (n-1) * pillar_width + 2 * b1

# Foundation width
f_multi = f_single * factor  # Based on n

# Rebar counts (some positions)
rebar_count = base_count * n  # For positions spanning all openings
```

### Data Tables Used:
- ✅ `Culvert_multi.csv` - Instead of Culvert_one.csv
- ✅ `Culvert_full.csv` - With count multipliers
- ✅ `Culvert_dastak.csv` - Same
- ✅ `Culvert_multi_extra.csv` - NEW table for pillar rebars

---

## 🔷 Type 4: Multi Angular (n>1, α≠0)

### Conditions:
- Number of openings: `n > 1`
- Skew angle: `alpha ≠ 0`

### Combines Both:
This type combines all the adjustments from:
1. **Single Angular** - Angle adjustments
2. **Multi Perpendicular** - Multiple openings + pillars

### Required Changes:
All changes from Type 2 AND Type 3, plus:

| Component | Change Required |
|-----------|-----------------|
| `_apply_table1()` | Use multi table + angle adjustments |
| `_apply_table2()` | Multiply counts + adjust shapes |
| `_apply_table3()` | 4 different distances with angle consideration |
| `_apply_table4()` | Apply with angle adjustments |
| Template | Needs `multi_angular.dxf` (may need creation) |

---

## 📝 Implementation Checklist

### Single Angular (n=1, α≠0)
- [ ] Single Angular Less (L) - 0° < α < 45°
- [ ] Single Angular More (M) - α ≥ 45°

### Double/Multi Opening (n=2)
- [ ] Double Perpendicular (n=2, α=0)
- [ ] Double Angular Less (n=2, 0° < α < 45°)
- [ ] Double Angular More (n=2, α ≥ 45°)

---

## ⚠️ Questions to Verify Before Implementation

1. **Template Placeholders**: 
   - Are the placeholder IDs in angular/multi templates the same as single perpendicular? YES.
   - Are there additional placeholders for pillar dimensions? YES.

2. **Data Coverage**:
   - Does `Culvert_multi.csv` have data for all n values (2-10)? YES.
   - Are there angular-specific tables needed? Check yourself.

3. **Formulas**:
   - Confirm the exact formula for angular adjustments
   - Confirm pillar rebar calculation formulas

4. **Wing Walls**:
   - For angular: Do all 4 wing walls have different lengths?
   - For multi: Are wing walls the same as single, just wider?

---

## 🚀 Recommended Implementation Order

1. **First**: Single Angular (Type 2)
   - Closest to working code
   - Template already available
   - Only angle adjustments needed

2. **Second**: Multi Perpendicular (Type 3)
   - More structural changes
   - New table (table4) needed
   - Template available

3. **Third**: Multi Angular (Type 4)
   - Combines both
   - May need new template
   - Most complex

---

*Last Updated: February 2, 2026*
