# Culvert Design - Input Parameters

## 📥 Form Input Parameters

The web form collects the following parameters from the user:

---

## 1️⃣ Basic Parameters

| Parameter | Symbol | Type | Unit | Description |
|-----------|--------|------|------|-------------|
| Number of Openings | `n` | int | - | 1 for single, 2-10 for multi |
| Span/Diameter | `D` | float | m | Internal opening width |
| Length Left | `L_left` (A) | float | m | Distance from centerline to left end |
| Length Right | `L_right` (B) | float | m | Distance from centerline to right end |
| Static Head | `Hs` | float | m | Fill height above top slab |
| Minimum Height | `H_min` | float | m | Minimum wing wall height |
| Project Line Elevation | `CL` | float | m | Centerline elevation of road |

### Visual Explanation:

```
                    ← A (L_left) →│← B (L_right) →
                                  │
    ══════════════════════════════╪══════════════════════════════  ← CL (elevation)
                                  │
                             ┌────┴────┐
                             │         │  ← D (Span)
                             │  CULVERT│
                             │         │
                             └─────────┘
```

---

## 2️⃣ Location Parameters

| Parameter | Symbol | Type | Unit | Description |
|-----------|--------|------|------|-------------|
| Natural Axis Elevation | `ax_natural` | float | m | Ground elevation at centerline |
| Right Slope | `dever_right` | float | % | Road cross-slope on right side |
| Left Slope | `dever_left` | float | % | Road cross-slope on left side |

### Visual Explanation:

```
                   dever_left %          dever_right %
                         ↘                    ↙
    ─────────────────────────╲──────╱─────────────────────────
                              ╲ CL ╱
                               ╲──╱
                                ▼
                          ax_natural
```

---

## 3️⃣ Slope Parameters

| Parameter | Symbol | Type | Unit | Description |
|-----------|--------|------|------|-------------|
| Natural Slope | `z_natural` | float | ratio | Longitudinal ground slope (e.g., 0.02 = 2%) |
| Longitudinal Slope | `z_toli` | float | ratio | Culvert floor slope |
| Transverse Slope | `z_shirvani` | float | factor | Wing wall slope factor (1:z ratio) |
| Retention | `ret` | float | m | Retention depth below natural ground |

### z_shirvani Explanation:

```
Wing wall slope ratio 1:z_shirvani

         │← z_shirvani →│
    ─────┼──────────────┤
         │              │  1
         │              ↓
         └──────────────┘
```

---

## 4️⃣ Angle Parameters

| Parameter | Symbol | Type | Unit | Description |
|-----------|--------|------|------|-------------|
| Wing Wall Angle | `ball_degree` | float | degrees | Wing wall angle from horizontal |
| Skew Angle | `alpha` | float | degrees | Culvert skew angle (0 = perpendicular) |

### Alpha (Skew Angle) Explanation:

```
PERPENDICULAR (α = 0°):              ANGULAR (α ≠ 0°):

    Road Direction →                     Road Direction →
    ════════════════                     ════════════════
         │                                    ╲
         │ Culvert                             ╲ Culvert
         │ α = 0°                               ╲ α = 30°
    ════════════════                     ════════════════
         ↓                                      ╲
    Water Flow                              Water Flow
```

---

## 5️⃣ Direction Flag

| Parameter | Symbol | Type | Description |
|-----------|--------|------|-------------|
| Direction | `direction_flag` | bool | **True**: Left = UPSTREAM, Right = DOWNSTREAM |
|           |                  |      | **False**: Left = DOWNSTREAM, Right = UPSTREAM |

### Direction Explanation:

```
direction_flag = True:               direction_flag = False:

    UPSTREAM                              DOWNSTREAM
        ↓                                     ↓
   ┌────┬────┐                          ┌────┬────┐
   │LEFT│RIGHT│                         │LEFT│RIGHT│
   └────┴────┘                          └────┴────┘
        ↓                                     ↓
   DOWNSTREAM                              UPSTREAM
```

---

## 📊 Parameter Relationships

### Derived Values:

| Derived Value | Formula | Description |
|---------------|---------|-------------|
| `L` | `A + B` | Total culvert length |
| `H` | `((c04-c06+0.3) + (c14-c12+0.3)) / 2` | Average wall height |

### Elevation Calculations:

```
c04 (Left bottom elevation):
c04 = CL + (dever_left/100) × A - Hs - t - 0.3

c14 (Right bottom elevation):
c14 = CL + (dever_right/100) × B - Hs - t - 0.3

c06 (Left natural ground):
If LEFT = UP:   c06 = ax_natural + z_natural × A - ret
If LEFT = DOWN: c06 = ax_natural - z_natural × A - ret

c12 (Right natural ground):
If LEFT = UP:   c12 = ax_natural - z_natural × B - ret
If LEFT = DOWN: c12 = ax_natural + z_natural × B - ret
```

---

## 🎯 Parameter Constraints

| Parameter | Min | Max | Typical |
|-----------|-----|-----|---------|
| `n` | 1 | 10 | 1-3 |
| `D` | 0.1 | 10 | 1-6 |
| `Hs` | 0 | 20 | 0-6 |
| `H_min` | 0 | 10 | 1-2 |
| `dever_left/right` | -50 | 50 | -5 to 5 |
| `z_natural` | 0 | 1 | 0.01-0.05 |
| `z_toli` | -1 | 1 | 0.005-0.02 |
| `z_shirvani` | 0 | 5 | 1-2 |
| `ball_degree` | 0 | 90 | 30-60 |
| `alpha` | -90 | 90 | 0-45 |

---

## 🔄 Form to CulvertInput Mapping

```python
# In CulvertProcessor._create_input_from_form():

culvert_input = CulvertInput(
    n = int(form_data['n']),
    D = float(form_data['D']),
    L = float(form_data['L_left']) + float(form_data['L_right']),
    Hs = float(form_data['Hs']),
    H_min = float(form_data['H_min']),
    CL = float(form_data['CL']),
    ax_natural = float(form_data['ax_natural']),
    dever_right = float(form_data['dever_right']),
    dever_left = float(form_data['dever_left']),
    z_natural = float(form_data['z_natural']),
    z_toli = float(form_data['z_toli']),
    z_shirvani = float(form_data['z_shirvani']),
    ret = float(form_data['ret']),
    ball_degree = float(form_data['ball_degree']),
    alpha = float(form_data['alpha']),
    A = float(form_data['L_left']),
    B = float(form_data['L_right']),
    direction_flag = form_data.get('direction_flag', 'true') == 'true'
)
```

---

*Last Updated: February 2, 2026*
