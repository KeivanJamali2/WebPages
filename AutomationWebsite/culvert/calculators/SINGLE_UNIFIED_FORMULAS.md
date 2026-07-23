# Unified Single Culvert Calculator — Formula Reference

## Overview

The three separate single-opening calculators (perpendicular, angular-more,
angular-less) have been merged into **one unified file**:

```
culvert/calculators/single_atgrade.py  →  SingleAtGradeCalculator
```

The key insight is that `cos(0) = 1` and `tan(0) = 0`, which means the
angular correction terms naturally vanish when `alpha = 0` (perpendicular).
A single set of formulas covers all cases.

---

## Template Selection

| Condition   | DXF Template                       |
|-------------|-------------------------------------|
| `alpha = 0` | `single_perpendicular_atGrade.dxf` |
| `alpha > 0` | `single_angularM_atGrade.dxf`      |
| `alpha < 0` | `single_angularL_atGrade.dxf`      |

---

## Unified Formulas

### Distance corrections (`c08`, `c09`, `c10`)

```
c08 = |A| / cos(α)
c09 = |B| / cos(α)
c10 = (|A| + |B|) / cos(α)
```

When `α = 0`: `cos(0) = 1` → `c08 = |A|`, `c09 = |B|`, `c10 = |L|`.

### Culvert base elevations (`c04`, `c14`)

```
c04 = CL + (dever_left / 100) × A  −  A × tan(α) × z_toli  − Hs − t − 0.3
c14 = CL + (dever_right / 100) × B  +  B × tan(α) × z_toli  − Hs − t − 0.3
```

- **c04 (left end)**: the angular correction is **subtracted** (`−`)
- **c14 (right end)**: the angular correction is **added** (`+`)
- When `α = 0`: `tan(0) = 0` → both reduce to the original perpendicular formulas.

### Natural ground elevations (`c06`, `c12`)

```
If LEFT = UP:
    c06 = ax_natural + z_natural × c08 − ret
    c12 = ax_natural − z_natural × c09 − ret

If LEFT = DOWN:
    c06 = ax_natural − z_natural × c08 − ret
    c12 = ax_natural + z_natural × c09 − ret
```

These use `c08` and `c09` (which already include the `/cos(α)` factor).

### Pipe diameter correction (`d02`)

```
d02 = D × cos(α)
```

When `α = 0`: `d02 = D`.

### Shape dimension adjustment (`f020`, `f022`, `f025`, `f027`)

```
adjustment = d10 / cos(α) − d10
f020 = p1_sh_i2 + adjustment
f022 = p1_sh_i4 + adjustment
f025 = p2_sh_i2 + adjustment
f027 = p2_sh_i4 + adjustment
```

Where `d10 = c1` (concrete cover from Table 1).
When `α = 0`: `adjustment = d10/1 − d10 = 0` → original values preserved.

### Longitudinal slope (`d01`)

```
d01 = round(z_toli × 100, 2)
```

`z_toli` is stored internally as a **ratio** (e.g., 0.02).
`d01` is the **percentage** display value (e.g., 2.00).

### Height calculation (`H`)

```
H_1 = c04 − c06 + 0.3
H_2 = c14 − c12 + 0.3
H   = (H_1 + H_2) / 2
```

If `H >= H_table`, the calculator re-queries Table 1 with the updated H.

### f029, f033, f034, f039 (m → cm)

These rebar shape dimensions are multiplied by 100 to convert from m to cm:

```
f029 = _length_in_pos(p=3, ...) × 100
f033 = _length_in_pos(p=5, ...) × 100
f034 = _length_in_pos(p=6, ...) × 100
f039 = _length_in_pos(p=8, ...) × 100
```

---

## Wing Wall Distance (iterative)

```
d = (H_max − H_min) / cos(ball_degree) × z_shirvani
```

Iterated because the ground slope (`z_natural`) changes the ending height as
the wall extends. Convergence criterion: `|d2 − d1| < 0.2 m`.

---

## Files Changed

| File | Change |
|------|--------|
| `culvert/calculators/single_atgrade.py` | **NEW** — unified calculator |
| `culvert/calculators/factory.py` | Routes all `n=1` to `SingleAtGradeCalculator` |
| `templates/culvert_process.html` | JS preview: c04 sign fixed to `−` |
| `culvert/calculators/single_perpendicular_atgrade.py` | No longer used (kept for reference) |
| `culvert/calculators/single_angular_more_atgrade.py` | No longer used (kept for reference) |
| `culvert/calculators/single_angular_less_atgrade.py` | No longer used (kept for reference) |

---

## Why This Works

The angular formulas are **generalizations** of the perpendicular ones.
Every angular correction term contains either `cos(α)` (as a divisor)
or `tan(α)` (as a factor):

- `cos(0°) = 1` → division by cos leaves the value unchanged
- `tan(0°) = 0` → multiplication by tan zeroes the term out

Therefore a single code path handles perpendicular and angular cases
identically, with only the DXF template varying.
