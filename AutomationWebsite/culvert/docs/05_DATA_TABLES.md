# Culvert Design - Data Tables Reference

## 📊 Overview of CSV Tables

The system uses **5 CSV tables** for lookup values:

| Table | File | Purpose | Used For |
|-------|------|---------|----------|
| Table 1 | `Culvert_one.csv` | Main structural parameters | n=1 (single opening) |
| Table 1b | `Culvert_multi.csv` | Main structural parameters | n>1 (multi opening) |
| Table 2 | `Culvert_full.csv` | Rebar specifications | All types |
| Table 3 | `Culvert_dastak.csv` | Wing wall parameters | All types |
| Table 4 | `Culvert_multi_extra.csv` | Extra rebar for multi-opening | n>1 only |

---

## 📋 Table 1: Culvert_one.csv (Single Opening)

### Purpose:
Main structural parameters for **single opening culverts (n=1)**.

### Columns:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `n` | int | - | Number of openings (always 1) |
| `D` | float | m | Span/Diameter (1.0 - 10.0) |
| `H` | float | m | Maximum wall height this row applies to |
| `Hs` | string | m | Static head range, e.g., "(0.00, 0.60)" |
| `a1` | float | m | Horizontal haunch size 1 |
| `a2` | float | m | Horizontal haunch size 2 |
| `b1` | float | m | Wall thickness |
| `b2` | float | m | Vertical dimension |
| `c1` | float | m | Concrete cover 1 |
| `c2` | float | m | Concrete cover 2 |
| `f` | float | m | Foundation width |
| `m` | float | m | Foundation depth |
| `t` | float | m | Slab thickness |
| `phi_b` | int | mm | Rebar diameter for bending |
| `j*` | float | - | Joint spacing factor |

### Sample Data:
```csv
n,D,H,Hs,a1,a2,b1,b2,c1,c2,f,m,t,phi_b,j*
1,1.00,1.20,"(0.00, 0.60)",0.00,0.20,0.80,0.45,0.20,0.25,1.00,0.60,0.25,32,0.01
1,1.00,1.20,"(0.60, 6.00)",0.00,0.20,0.80,0.45,0.20,0.25,1.00,0.60,0.25,37,0.01
1,2.00,1.30,"(0.00, 0.60)",0.00,0.30,0.70,0.55,0.30,0.25,1.00,0.80,0.25,30,0.01
1,2.00,2.20,"(0.00, 0.60)",0.00,0.70,1.10,0.55,0.30,0.25,1.80,0.80,0.25,30,0.01
```

### Available D Values:
- 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0 meters

### Hs Ranges Available:
- (0.00, 0.25), (0.25, 0.60), (0.60, 1.00), (1.00, 2.00), (2.00, 3.00), (3.00, 4.00), (4.00, 5.00), (5.00, 6.00)

---

## 📋 Table 1b: Culvert_multi.csv (Multi Opening)

### Purpose:
Main structural parameters for **multi-opening culverts (n>1)**.

### Columns:
Same as `Culvert_one.csv` PLUS:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `p1` | float | m | Pillar width 1 |
| `p2` | float | m | Pillar width 2 |
| `e` | float | m | Edge distance |
| `k` | float | m | Additional parameter |

### Sample Data:
```csv
n,D,H,Hs,a1,a2,b1,b2,c1,c2,f,m,p1,p2,e,n,k,t,phi_b,j*
3,1,1.2,"(0.00, 0.60)",0,0.5,0.8,0.45,0.2,0.25,1.3,0.8,0.4,0.4,0.2,0.8,0.8,0.25,32,0.02
3,2,2.2,"(0.00, 0.60)",0,0.8,1.2,0.55,0.3,0.25,2,0.8,1.2,0.6,0.3,0.8,1.8,0.25,35,0.02
2,3,2.25,"(0.60, 2.00)",0,0.2,0.8,0.55,0.3,0.25,1,0.8,0.6,0.6,0.4,0.8,1.4,0.3,35,0.02
```

### Available n Values:
- 2, 3 (based on current data)

### Note:
⚠️ The `n` column appears twice in the CSV. The second `n` column may need to be renamed.

---

## 📋 Table 2: Culvert_full.csv (Rebar Specifications)

### Purpose:
Detailed rebar specifications for all **10 rebar positions**.

### Lookup Keys:
- `n`: Number of openings
- `D`: Diameter
- `Hs`: Static head range
- `c1`: Concrete cover (from Table 1)
- `t`: Slab thickness (from Table 1)

### Columns for Each Position (p1-p9, p0):

| Pattern | Description |
|---------|-------------|
| `pX_diameter(mm)` | Rebar diameter in mm |
| `pX_n` | Count per meter OR fixed (e.g., "3.1" or "5*2") |
| `pX_distance(cm)` | Spacing between rebars in cm |
| `pX_L(m)` | Base length per rebar in m |
| `pX_sh_i1` to `pX_sh_i5` | Shape dimensions for bending schedule |

### Rebar Position Meanings:

| Position | Location | Type |
|----------|----------|------|
| p1 | Top slab - bottom | Longitudinal main |
| p2 | Top slab - top | Longitudinal main |
| p3 | Top slab | Transverse distribution |
| p4 | Walls - outer | Vertical main |
| p5 | Walls - inner | Vertical main |
| p6 | Walls | Horizontal distribution |
| p7 | Bottom slab - top | Longitudinal main |
| p8 | Bottom slab - bottom | Longitudinal main |
| p9 | Bottom slab | Transverse distribution |
| p0 | Haunches | Extra reinforcement |

### Additional Columns:
| Column | Description |
|--------|-------------|
| `weight(kg/m)` | Weight per meter of culvert |
| `weight(kg)(start-end)` | Total weight for start/end pieces |

### Sample Row (truncated):
```csv
n,D,Hs,c1,t,p1_diameter(mm),p1_n,p1_distance(cm),p1_L(m),p1_sh_i1,...
1,1,"(0.00, 0.25)",0.2,0.25,14,3.1,32,1.7,17,...
```

---

## 📋 Table 3: Culvert_dastak.csv (Wing Walls)

### Purpose:
Wing wall (بال/داستک) parameters based on wall height.

### Columns:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `H` | int | m | Wall height (1-7) |
| `x` | float | m | Heel extension behind wall |
| `b` | float | m | Wall thickness at base |
| `f` | float | m | Foundation width |
| `m` | float | m | Foundation depth |

### Complete Data:
```csv
H,x,b,f,m
1,0,0.17,0.85,0.8
2,0.15,0.43,1.6,0.8
3,0.3,0.75,2.4,0.8
4,0.45,1.02,3.15,0.8
5,0.6,1.28,3.9,1
6,0.75,1.6,4.7,1.3
7,0.95,1.82,5.45,1.7
```

### Usage:
- Lookup 3 times: for `H_min`, `H_max_left`, `H_max_right`
- Values interpolated/rounded to nearest integer H

---

## 📋 Table 4: Culvert_multi_extra.csv (Multi-Opening Extra Rebar)

### Purpose:
Extra rebar specifications for **pillars/columns** in multi-opening culverts.

### Columns:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `D` | int | m | Diameter (1-8) |
| `diameter(mm)` | int | mm | Rebar diameter |
| `n on each kole` | int/str | - | Count on each opening |
| `n on each paye` | str | - | Count on each pillar (e.g., "2*2") |
| `distance(cm)` | int | cm | Spacing |
| `L(m)` | float | m | Length |
| `shape_1` | int | mm | Bending dimension 1 |
| `shape_2` | int | mm | Bending dimension 2 |
| `shape_3` | int | mm | Bending dimension 3 |

### Complete Data:
```csv
D,diameter(mm),n on each kole,n on each paye,distance(cm),L(m),shape_1,shape_2,shape_3
1,14,2,2*2,50,1.35,65,50,20
2,14,2,2*2,50,1.35,65,50,20
3,14,2,2*2,50,1.4,65,55,20
4,14,2,2*2,50,1.45,65,65,20
5,14,2,2*2,50,1.5,65,65,20
6,14,3.3,2*3.3,30,1.55,65,70,20
7,25,2,2*2,50,2.5,145,75,30
8,25,2,2*2,50,2.55,145,80,30
```

---

## 🔍 Query Logic

### TableRepository.find_in_table1():
```python
def find_in_table1(self, n, D, Hs, H=0):
    # Select table based on n
    table = self.t1 if n == 1 else self.t_multi
    
    # Filter by n and D
    mask = (table["n"] == n) & (table["D"] == D)
    choices = table[mask]
    
    # Find row where Hs is in range
    for row in choices:
        hs_range = parse_range(row["Hs"])  # "(0.00, 0.60)" → (0.0, 0.6)
        if hs_range[0] <= Hs < hs_range[1]:
            if H == 0 or H < row["H"]:
                return row
    
    return "ERROR: No suitable data found"
```

### TableRepository.find_in_table2():
```python
def find_in_table2(self, n, D, Hs, c1, t):
    mask = (
        (self.t2["n"] == n) &
        (self.t2["D"] == D) &
        (self.t2["c1"] == c1) &
        (self.t2["t"] == t)
    )
    choices = self.t2[mask]
    
    for row in choices:
        hs_range = parse_range(row["Hs"])
        if hs_range[0] < Hs <= hs_range[1]:
            return row
    
    return "ERROR: No suitable data found"
```

### TableRepository.find_in_table3():
```python
def find_in_table3(self, H):
    # Round H to nearest integer (1-7 range)
    H_rounded = max(1, min(7, round(H)))
    
    mask = self.t3["H"] == H_rounded
    if mask.any():
        return self.t3[mask].iloc[0]
    
    return "ERROR: H out of range (1-7)"
```

---

## ⚠️ Data Limitations

1. **Single Opening (n=1)**: Full data for D = 1-10m
2. **Multi Opening (n=2,3)**: Limited data, primarily D = 1-8m
3. **Wing Walls**: Only supports H = 1-7m
4. **Hs Ranges**: Maximum Hs = 6.0m in current tables

---

*Last Updated: February 2, 2026*
