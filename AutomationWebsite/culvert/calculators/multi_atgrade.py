"""
Unified Multi At-Grade Culvert Calculator (n>=2, any alpha).

This calculator handles ALL multi-opening at-grade cases:
    - Double perpendicular (n=2, alpha = 0)
    - Double angular more (n=2, alpha > 0)
    - Double angular less (n=2, alpha < 0)
    - Triple+ perpendicular (n>2, alpha = 0)
    - Triple+ angular more (n>2, alpha > 0)
    - Triple+ angular less (n>2, alpha < 0)

The formulas use cos(alpha) and tan(alpha) corrections which naturally
reduce to the perpendicular case when alpha=0, since cos(0)=1 and tan(0)=0.

Template selection:
    n=2, alpha = 0  → double_perpendicular_atGrade.dxf
    n=2, alpha > 0  → double_angularM_atGrade.dxf
    n=2, alpha < 0  → double_angularL_atGrade.dxf
    n>2, alpha = 0  → triple_perpendicular_atGrade.dxf
    n>2, alpha > 0  → triple_angularM_atGrade.dxf
    n>2, alpha < 0  → triple_angularL_atGrade.dxf

================================================================================
CULVERT GEOMETRY OVERVIEW (Double/Multi)
================================================================================

A multi-opening box culvert has n openings separated by middle piers:

    Road Surface (CL = Center Line Elevation)
    ═══════════════════════════════════════════
           ↑ Hs (Static Head / Fill Height)
    ┌───────┬───────┬───────┐  ← Top Slab (thickness = t)
    │       │ pier  │       │
    │  D×D  │  p2   │  D×D  │  ← n openings (n=2 shown)
    │       │       │       │
    └───────┴───────┴───────┘  ← Bottom Slab
           ↓ m (Foundation depth)
    ═══════════════════════════════════════════  ← Natural ground level

    p2 = middle pier thickness (from Culvert_multi.csv)
    k  = pier extension parameter (from Culvert_multi.csv)

================================================================================
TABLES USED
================================================================================

- Culvert_multi.csv   : Main structural parameters (table1 for multi)
- Culvert_full.csv    : Rebar specifications (table2, queried with n=1)
- Culvert_dastak.csv  : Wing wall parameters (table3)
- Culvert_multi_extra.csv : Extra rebar positions for middle piers (table4)

================================================================================
C-PARAMETERS (unified — valid for all alpha including alpha=0)
================================================================================

    c01 = CL (centerline elevation)
    c02 = dever_left (left cross slope in %)
    c03 = dever_right (right cross slope in %)
    c04 = CL + (dever_left/100)*A - A*tan(α)*z_toli - Hs - t - 0.3
    c05 = ax_natural ± z_natural * (|A|/cos(α)) - ret     (natural ground left)
    c06 = c05 - m                                          (foundation left)
    c07 = |A|/cos(α) + p2/2 + (k*tan(α))/2 + 0.2         (left total width)
    c08 = |B|/cos(α) + p2/2 + (k*tan(α))/2 + 0.2         (right total width)
    c09 = c07 + c08                                         (full width)
    c10 = (|A| + |B|) / cos(α)                             (internal length)
    c11 = c12 - m                                          (foundation right)
    c12 = ax_natural ∓ z_natural * (|B|/cos(α)) - ret     (natural ground right)
    c13 = CL + (dever_right/100)*B + B*tan(α)*z_toli - Hs - t - 0.3

================================================================================
D-PARAMETERS
================================================================================

    d01 = z_toli * 100 (slope as percentage)
    d02 = D * cos(α)
    d03 = f (from Culvert_multi)
    d04 = m (from Culvert_multi)
    d05 = b1 (from Culvert_multi)
    d06 = a2 (from Culvert_multi)
    d07 = a1 (from Culvert_multi)
    d08 = b2 (from Culvert_multi)
    d09 = c2 (from Culvert_multi)
    d10 = c1 (from Culvert_multi)
    d11 = t (from Culvert_multi)
    d12 = j* (from Culvert_multi)
    d13 = Hs (from inputs)
    d14 = p2 (from Culvert_multi)
    d15 = d17 = e (from Culvert_multi)
    d16 = p1 (from Culvert_multi)
    d18 = n (structural param from Culvert_multi, NOT number of openings)
    d19 = k (from Culvert_multi)
"""

from typing import Dict, Any, Optional, Callable
from math import ceil, pi, cos, radians, tan, sqrt
import pandas as pd

from culvert.calculators.base import BaseCulvertCalculator, CulvertInput

def round(value: float, decimals: int = 0) -> float:
    """
    Round a value to a specified number of decimal places.

    Args:
        value: The value to round
        decimals: Number of decimal places (default=0)

    Returns:
        Rounded value
    """
    value = str(value)
    i, d = value.split(".")
    if decimals >= len(d):
        return float(value)
    if decimals == 0:
        if int(d[0]) >= 5:
            return int(int(i) + 1)
        else:
            return int(i)
    else:
        temp = d[decimals]
        new_d = d[:decimals]
        if int(temp) >= 5:
            d = int(new_d[-1]) + 1
        else:
            d = new_d
    
    return float(".".join([i, str(new_d)]))        


class MultiAtGradeCalculator(BaseCulvertCalculator):
    """
    Unified calculator for multi-opening at-grade culverts (n>=2, any alpha).

    Handles perpendicular (alpha=0), angular more (alpha>0), and
    angular less (alpha<0) cases with one set of formulas.
    cos(0)=1 and tan(0)=0 make all angular terms vanish when alpha=0.
    """

    def __init__(self,
                 input_params: CulvertInput,
                 table_repository,
                 progress_callback: Optional[Callable[[int], None]] = None):
        super().__init__(input_params, table_repository, progress_callback)

        if self.params.n < 2:
            raise ValueError(
                f"MultiAtGradeCalculator requires n>=2, got n={self.params.n}"
            )

    # --------------------------------------------------------------------- #
    #  MAIN CALCULATION
    # --------------------------------------------------------------------- #

    def calculate(self) -> Dict[str, Any]:
        """
        Perform multi at-grade culvert calculations.

        Process:
        1. Query Culvert_multi.csv for structural parameters
        2. Query Culvert_full.csv (with n=1) for rebar specifications
        3. Query Culvert_dastak.csv for wing wall parameters
        4. Query Culvert_multi_extra.csv for extra rebar positions
        5. Convert all values to strings for DXF output

        Returns:
            Dictionary of calculated values ready for DXF template
        """
        self._update_progress(50)
        self._apply_directions()

        has_errors = False

        # --- Table 1 (Culvert_multi.csv) ------------------------------------
        try:
            table1_result = self.tables.find_in_table1_multi(
                D=self.params.D,
                Hs=self.params.Hs,
            )
            if isinstance(table1_result, str):
                self.messages.append(table1_result)
                has_errors = True
                table1_result = None
            else:
                msg1 = self._apply_table1(table1_result)
                if msg1:
                    self.messages.append(msg1)
                    has_errors = True
        except Exception as e:
            self.messages.append(f"Table1 (multi) error: {str(e)}")
            has_errors = True
            table1_result = None

        # --- Table 2 (Culvert_full.csv, queried with n=1) -------------------
        if table1_result is not None:
            try:
                table2_result = self.tables.find_in_table2(
                    n=1,  # Culvert_full.csv only has n=1 entries
                    D=self.params.D,
                    Hs=self.params.Hs,
                    c1=table1_result["c1"],
                    t=table1_result["t"],
                )
                if isinstance(table2_result, str):
                    self.messages.append(table2_result)
                    has_errors = True
                else:
                    msg2 = self._apply_table2(table2_result, table1_result)
                    if msg2:
                        self.messages.append(msg2)
            except Exception as e:
                self.messages.append(f"Table2 error: {str(e)}")
                has_errors = True

        # --- Table 3 (Culvert_dastak.csv) -----------------------------------
        if table1_result is not None and "c04" in self.data and "d11" in self.data:
            try:
                H_min = self.params.H_min
                # In multi: c05 = natural ground left, c12 = natural ground right
                # c04 = left elevation, c13 = right elevation
                H_max_l = self.data["c04"] + 0.3 + self.data["d11"] - self.data["c05"]
                H_max_r = self.data["c13"] + 0.3 + self.data["d11"] - self.data["c12"]

                print(f"[DEBUG] Table3 H values: H_min={H_min}, H_max_l={H_max_l}, H_max_r={H_max_r}")
                print(f"[DEBUG] Components: c04={self.data['c04']}, c05={self.data['c05']}, "
                      f"c13={self.data['c13']}, c12={self.data['c12']}, d11={self.data['d11']}")

                table3_results = []
                table3_errors = []
                for H_val in [H_min, H_max_l, H_max_r]:
                    result = self.tables.find_in_table3(H=H_val)
                    if isinstance(result, str):
                        print(f"[ERROR] Table3 lookup failed for H={H_val}: {result}")
                        self.messages.append(result)
                        table3_errors.append(H_val)
                        table3_results.append(None)
                        has_errors = True
                    else:
                        table3_results.append(result)

                if any(r is not None for r in table3_results):
                    msg3 = self._apply_table3(table3_results)
                    if msg3:
                        self.messages.append(msg3)
            except Exception as e:
                self.messages.append(f"Table3 error: {str(e)}")
                has_errors = True

        # --- Table 4 (Culvert_multi_extra.csv) ------------------------------
        if table1_result is not None and "c10" in self.data:
            try:
                table4_result = self.tables.find_in_table4(D=self.params.D)
                if isinstance(table4_result, str):
                    self.messages.append(table4_result)
                    has_errors = True
                else:
                    msg4 = self._apply_extra_positions(table4_result, table1_result)
                    if msg4:
                        self.messages.append(msg4)
            except Exception as e:
                self.messages.append(f"Table4 error: {str(e)}")
                has_errors = True

        self._apply_information()

        self._update_progress(65)

        # Convert all values to strings for DXF output
        self._round_data_to_strings()

        if has_errors:
            self.data["_has_errors"] = "true"
            self.data["_error_messages"] = " | ".join(self.messages)

        return self.data

    # --------------------------------------------------------------------- #
    #  TEMPLATE SELECTION
    # --------------------------------------------------------------------- #

    def get_template_filename(self) -> str:
        """
        Return the DXF template based on n and skew angle.

        n=2: double templates
        n>2: triple templates
        """
        if self.is_undergrade:
            end = "underGrade"
            print("\n\n\nTHIS IS UNDERGRADE\n\n\n")
        else:
            end = "atGrade"
        if self.params.n == 2:
            if self.params.alpha == 0:
                return f"double_perpendicular_{end}.dxf"
            elif self.params.alpha > 0:
                return f"double_angularM_{end}.dxf"
            else:
                return f"double_angularL_{end}.dxf"
        elif self.params.n == 3:
            if self.params.alpha == 0:
                return f"triple_perpendicular_{end}.dxf"
            elif self.params.alpha > 0:
                return f"triple_angularM_{end}.dxf"
            else:
                return f"triple_angularL_{end}.dxf"
        elif self.params.n == 4:
            if self.params.alpha == 0:
                return f"four_perpendicular_{end}.dxf"
            elif self.params.alpha > 0:
                return f"four_angularM_{end}.dxf"
            else:
                return f"four_angularL_{end}.dxf"
        elif self.params.n == 5:
            if self.params.alpha == 0:
                return f"five_perpendicular_{end}.dxf"
            elif self.params.alpha > 0:
                return f"five_angularM_{end}.dxf"
            else:
                return f"five_angularL_{end}.dxf"
        elif self.params.n == 6:
            if self.params.alpha == 0:
                return f"six_perpendicular_{end}.dxf"
            elif self.params.alpha > 0:
                return f"six_angularM_{end}.dxf"
            else:
                return f"six_angularL_{end}.dxf"
        else:
            raise NotImplemented

    # ===================================================================== #
    #  TABLE 1 APPLICATION (C-PARAMETERS + D-PARAMETERS)
    # ===================================================================== #

    def _apply_table1(self, d: pd.Series) -> Optional[str]:
        """
        Apply parameters from Culvert_multi.csv.

        Computes c01-c13 (geometry) and d01-d19 (structural dimensions).

        Args:
            d: pandas Series from Culvert_multi.csv

        Returns:
            Error message if failed, None if successful
        
        # 06 -> 05
        # 07 -> 06
        # 14 -> 13
        # 08 -> 07
        # 09 -> 08
        """
        self.is_undergrade = False
        alpha_rad = radians(self.params.alpha)
        cos_alpha = cos(alpha_rad)
        tan_alpha = tan(alpha_rad)
        

        # Table parameters needed for c07/c08
        p2 = float(d["p2"])  # middle pier thickness
        k = float(d["k"])    # pier extension parameter

        # ----------------------------------------------------------------- #
        # C-PARAMETERS
        # ----------------------------------------------------------------- #

        # c01-c03: Basic elevation and slope parameters
        self.data["c01"] = round(self.params.CL, 2)
        self.data["c02"] = round(self.params.dever_left, 2)
        self.data["c03"] = round(self.params.dever_right, 2)
        # Internal distances (not stored as c-keys, used for computations)
        L_left_cos = abs(self.params.A) / cos_alpha    # |A| / cos(α)
        L_right_cos = abs(self.params.B) / cos_alpha   # |B| / cos(α)
        
        self.data["c07"] = round(L_left_cos + p2 / 2 + (k * tan_alpha) / 2 + 0.2, 1)
        self.data["c08"] = round(L_right_cos + p2 / 2 + (k * tan_alpha) / 2 + 0.2, 1)
        
        element1 = float(self.params.CL)

        # c09: Full width (c07 + c08)
        self.data["c09"] = round(self.data["c07"] + self.data["c08"], 1)

        # c10: Internal length = L / cos(α) (same as single c10)
        self.data["c10"] = round(L_left_cos + L_right_cos, 1)

        self.data["c04"] = round(
            element1
            + (self.data["c02"] / 100) * self.params.A
            - self.params.A * tan_alpha * self.params.z_toli
            - self.params.Hs
            - d["t"]
            - 0.3,
            2,
        )
        # c13: Right culvert base elevation (= c14 in single)
        self.data["c13"] = round(
            element1
            + (self.data["c03"] / 100) * self.params.B
            + self.params.B * tan_alpha * self.params.z_toli
            - self.params.Hs
            - d["t"]
            - 0.3,
            2,
        )

        # Natural ground elevations (c06/c12) — use c08/c09 (already divided by cos)
        if self.left == "UP":
            self.data["c05"] = round(
                self.params.ax_natural
                + self.params.z_natural * self.data["c07"]
                - self.params.ret,
                2,
            )
            self.data["c12"] = round(
                self.params.ax_natural
                - self.params.z_natural * self.data["c08"]
                - self.params.ret,
                2,
            )
        elif self.left == "DOWN":
            self.data["c05"] = round(
                self.params.ax_natural
                - self.params.z_natural * self.data["c07"]
                - self.params.ret,
                2,
            )
            self.data["c12"] = round(
                self.params.ax_natural
                + self.params.z_natural * self.data["c08"]
                - self.params.ret,
                2,
            )
        else:
            print(f"[WARNING] Direction not set correctly: left={self.left}")


        self.data["c06"] = round(self.data["c05"] - d["m"], 2)
        self.data["c11"] = round(self.data["c12"] - d["m"], 2)

        # ----------------------------------------------------------------- #
        # WALL HEIGHT CALCULATION
        # ----------------------------------------------------------------- #
        H1 = self.data["c04"] - self.data["c05"] + 0.3
        H2 = self.data["c13"] - self.data["c12"] + 0.3
        # self.H = round((H_1 + H_2) / 2, 2)

        print(f"[INFO] Calculated H-left={H1} H-right={H2}, comparing with table H={d['H']}")
        if H1 > d["H"]:
            print(f"[INFO] H={H1} > table H={d['H']}")
            print(f"[INFO] Started to design undergrade culvert for Left side...")
            temp = element1 + (self.data["c02"] / 100) * self.params.A - self.params.A * tan_alpha * self.params.z_toli
            
            hs = temp - (self.data["c05"] + d["H"] + d["t"])
            sign = 1 if self.left == "up" else -1
            extra_width = hs * cos_alpha / ((1/self.params.u_shirvani + (sign) * self.params.z_natural / 100) * sqrt(1 + (self.params.z_natural/100)**2))
            self.data["c07"] = round(self.data["c07"] + extra_width, 2)
            
            if self.left == "UP":
                self.data["c05"] = round(
                    self.params.ax_natural
                    + self.params.z_natural * self.data["c07"]
                    - self.params.ret,
                    2,
                )
            elif self.left == "DOWN":
                self.data["c05"] = round(
                    self.params.ax_natural
                    - self.params.z_natural * self.data["c07"]
                    - self.params.ret,
                    2,
                )
            else:
                print(f"[WARNING] Direction not set correctly: left={self.left}")
                
            self.data["c06"] = round(self.data["c05"] - d["m"], 2)
            self.data["c04"] = round(self.data["c05"] + d["H"] - 0.3, 2)
            print(f"temp: {temp}\nhs:{hs}\nsign:{sign}\nextra_width:{extra_width}\n")
            print(f"[INFO] Left UnderGrade Done!")
            self.is_undergrade = True
            
        if H2 > d["H"]:
            print(f"[INFO] H={H2} > table H={d['H']}")
            print(f"[INFO] Started to design undergrade culvert for Right side...")
            temp = element1 + (self.data["c03"] / 100) * self.params.B + self.params.B * tan_alpha * self.params.z_toli
            
            hs = temp - (self.data["c12"] + d["H"] + d["t"])
            sign = 1 if self.left == "up" else -1
            extra_width = hs * cos_alpha / ((1/self.params.u_shirvani + (sign) * self.params.z_natural / 100) * sqrt(1 + (self.params.z_natural/100)**2))
            self.data["c08"] = round(self.data["c08"] + extra_width, 2)
            
            if self.left == "UP":
                self.data["c12"] = round(
                    self.params.ax_natural
                    - self.params.z_natural * self.data["c08"]
                    - self.params.ret,
                    2,
                )
            elif self.left == "DOWN":
                self.data["c12"] = round(
                    self.params.ax_natural
                    + self.params.z_natural * self.data["c08"]
                    - self.params.ret,
                    2,
                )
            else:
                print(f"[WARNING] Direction not set correctly: left={self.left}")

            self.data["c11"] = round(self.data["c12"] - d["m"], 2)
            self.data["c13"] = round(self.data["c12"] + d["H"] - 0.3, 2)
            
            print(f"temp: {temp}\nhs:{hs}\nsign:{sign}\nextra_width:{extra_width}\n")
            print(f"[INFO] Right UnderGrade Done!")
            self.is_undergrade = True
            
        print(f"[INFO] H={self.H} is valid")

        # c05: Natural ground at left end (= c06 in single)
        if self.left == "UP":
            self.data["c05"] = round(
                self.params.ax_natural
                + self.params.z_natural * L_left_cos
                - self.params.ret,
                2,
            )
        elif self.left == "DOWN":
            self.data["c05"] = round(
                self.params.ax_natural
                - self.params.z_natural * L_left_cos
                - self.params.ret,
                2,
            )
        else:
            print(f"[WARNING] Direction not set correctly: left={self.left}")
            
        # ----------------------------------------------------------------- #
        # D-PARAMETERS
        # ----------------------------------------------------------------- #
        self.data["d01"] = round(self.params.z_toli * 100, 2)   # slope as percentage
        self.data["d02"] = round(self.params.D * cos_alpha, 2)   # D × cos(α)
        self.data["d03"] = d["f"]
        self.data["d04"] = d["m"]
        self.data["d05"] = d["b1"]
        self.data["d06"] = d["a2"]
        self.data["d07"] = d["a1"]
        self.data["d08"] = d["b2"]
        self.data["d09"] = d["c2"]
        self.data["d10"] = d["c1"]
        self.data["d11"] = d["t"]
        self.data["d12"] = d["j*"]
        self.data["d13"] = self.params.Hs
        self.data["d14"] = p2                  # middle pier thickness
        self.data["d15"] = d["e"]              # e parameter
        self.data["d16"] = d["p1"]             # p1 parameter
        self.data["d17"] = d["e"]              # same as d15
        self.data["d18"] = d["n"]              # structural n (NOT openings count)
        self.data["d19"] = k                   # pier extension parameter
        self.data["c15"] = self.params.u_shirvani

        print("[INFO] Successfully applied c-parameters and d-parameters from Culvert_multi")
        return None

    # ===================================================================== #
    #  TABLE 2 APPLICATION (REBAR) — positions 1-9
    # ===================================================================== #

    def _apply_table2(self, d: pd.Series, d_multi: pd.Series) -> Optional[str]:
        """
        Apply rebar parameters from Table2 (Culvert_full.csv).

        Same formulas as single calculator, but counts (f010-f018)
        are multiplied by the number of openings (n) via _count_in_pos.

        Args:
            d: pandas Series from table2 containing rebar specifications

        Returns:
            Error message if failed, None if successful
        """
        alpha_rad = radians(self.params.alpha)
        cos_alpha = cos(alpha_rad)

        # Shape-dimension adjustment for angular culverts
        d10_adj = 100 * (self.data["d10"] / cos_alpha - self.data["d10"])  # 0 when α=0

        # Position 1
        self.data["f001"] = d["p1_diameter(mm)"]
        self.data["f010"] = self._count_in_pos(1, d["p1_n"])
        self.data["f019"] = d["p1_sh_i1"]
        self.data["f020"] = round(d["p1_sh_i2"] + d10_adj)
        self.data["f021"] = d["p1_sh_i3"]
        self.data["f022"] = round(d["p1_sh_i4"] + d10_adj)
        self.data["f023"] = d["p1_sh_i1"]
        self.data["f045"] = round((self.data["f019"] + self.data["f020"] + self.data["f021"] + self.data["f022"] + self.data["f023"]) / 100, 2)
        self.data["f054"] = round(float(self.data["f010"]) * float(self.data["f045"]), 1)
        self.data["f063"] = self._weight_in_pos(d["p1_diameter(mm)"], dec=3)
        self.data["f072"] = self._weight_in_pos(d["p1_diameter(mm)"], self.data["f054"], 1)

        # Position 2
        self.data["f002"] = d["p2_diameter(mm)"]
        self.data["f011"] = self._count_in_pos(2, d["p2_n"])
        self.data["f024"] = d["p2_sh_i1"]
        self.data["f025"] = round(d["p2_sh_i2"] + d10_adj)
        self.data["f026"] = d["p2_sh_i3"]
        self.data["f027"] = round(d["p2_sh_i4"] + d10_adj)
        self.data["f028"] = d["p2_sh_i1"]
        self.data["f046"] = round((self.data["f024"] + self.data["f025"] + self.data["f026"] + self.data["f027"] + self.data["f028"]) / 100, 2)
        self.data["f055"] = round(float(self.data["f011"]) * float(self.data["f046"]), 1)
        self.data["f064"] = self._weight_in_pos(d["p2_diameter(mm)"], dec=3)
        self.data["f073"] = self._weight_in_pos(d["p2_diameter(mm)"], self.data["f055"], 1)
        
        # Position 3
        self.data["f003"] = d["p3_diameter(mm)"]
        self.data["f012"] = self._count_in_pos(3, d["p3_n"])
        self.data["f029"] = round(56 * self.data["f003"] / 10 + self.data["c10"] * 100) if self.data["c10"] > 12 else round(self.data["c10"] * 100)
        self.data["f047"] = self.data["f029"] / 100
        self.data["f056"] = round(float(self.data["f012"]) * float(self.data["f047"]), 1)
        self.data["f065"] = self._weight_in_pos(d["p3_diameter(mm)"], dec=3)
        self.data["f074"] = round(float(self.data["f056"]) * float(self.data["f065"]), 1)

        # Position 4
        self.data["f004"] = d["p4_diameter(mm)"]
        self.data["f013"] = self._count_in_pos(4, d["p4_n"])
        self.data["f030"] = d["p4_sh_i1"]
        self.data["f031"] = d["p4_sh_i2"]
        self.data["f032"] = d["p4_sh_i1"]
        self.data["f048"] = self._length_in_pos(p=4, L=d["p4_L(m)"], D=d["p4_diameter(mm)"])
        self.data["f057"] = self._length_in_pos(
            p=4, L=d["p4_L(m)"],
            N=self._count_in_pos(4, d["p4_n"], cal=True),
            D=d["p4_diameter(mm)"], dec=2,
        )
        self.data["f066"] = self._weight_in_pos(d["p4_diameter(mm)"], dec=3)
        self.data["f075"] = self._weight_in_pos(d["p4_diameter(mm)"], self.data["f057"], 1)

        # Position 5
        self.data["f005"] = d["p5_diameter(mm)"]
        self.data["f014"] = self._count_in_pos(5, d["p5_n"])
        self.data["f033"] = round(56 * float(self.data["f005"]) / 10 + float(self.data["c10"]) * 100) if float(self.data["c10"]) > 12 else round(float(self.data["c10"]) * 100)
        self.data["f049"] = self.data["f033"] / 100
        self.data["f058"] = round(float(self.data["f049"]) * float(self.data["f014"]), 1)
        self.data["f067"] = self._weight_in_pos(d["p5_diameter(mm)"], dec=3)
        self.data["f076"] = self._weight_in_pos(d["p5_diameter(mm)"], self.data["f058"], 1)

        # Position 6
        self.data["f006"] = d["p6_diameter(mm)"]
        self.data["f015"] = "2*8"
        self.data["f034"] = int(round(56 * float(self.data["f006"]) / 10 + float(self.data["c10"]) * 100)) if float(self.data["c10"]) > 12 else int(round(float(self.data["c10"]) * 100))
        self.data["f050"] = self.data["f034"] / 100
        self.data["f059"] = round(self.data["f050"] * 16, 1)
        self.data["f068"] = self._weight_in_pos(d["p6_diameter(mm)"], dec=3)
        self.data["f077"] = self._weight_in_pos(d["p6_diameter(mm)"], self.data["f059"], 1)

        # Position 7
        self.data["f007"] = d["p7_diameter(mm)"]
        self.data["f016"] = "2*" + str(round(float(self.data["c10"]) * 3.3)) 
        self.data["f035"] = d["p7_sh_i1"]
        self.data["f036"] = d["p7_sh_i2"]
        self.data["f037"] = d["p7_sh_i3"]
        self.data["f038"] = d["p7_sh_i4"]
        self.data["f051"] = self._length_in_pos(p=7, L=d["p7_L(m)"], D=d["p7_diameter(mm)"])
        self.data["f060"] = round(2 * float(self.data["f016"][2:]) * float(self.data["f051"]), 1)
        self.data["f069"] = self._weight_in_pos(d["p7_diameter(mm)"], dec=3)
        self.data["f078"] = self._weight_in_pos(d["p7_diameter(mm)"], self.data["f060"], 1)

        # Position 8
        self.data["f008"] = d["p8_diameter(mm)"]
        self.data["f017"] = "2*4"
        temp = 100 * ((self.params.n * (self.params.D*cos_alpha) + (self.params.n - 1) * d_multi["p2"] + 2 * (d_multi["c1"]) - 0.1))
        self.data["f039"] = round(temp + 56 * self.data["f008"] / 10) if temp > 1200 else round(temp)
        self.data["f052"] = self.data["f039"] / 100
        self.data["f061"] = 8 * self.data["f052"]
        self.data["f070"] = self._weight_in_pos(d["p8_diameter(mm)"], dec=3)
        self.data["f079"] = self._weight_in_pos(d["p8_diameter(mm)"], self.data["f061"], 2)

        # Position 9
        self.data["f009"] = d["p9_diameter(mm)"]
        self.data["f018"] = self._count_in_pos(9, d["p9_n"])
        self.data["f040"] = d["p9_sh_i1"]
        self.data["f041"] = d["p9_sh_i2"]
        self.data["f042"] = d["p9_sh_i3"]
        self.data["f043"] = d["p9_sh_i4"]
        self.data["f044"] = d["p9_sh_i5"]
        self.data["f053"] = self._length_in_pos(p=9, L=d["p9_L(m)"], D=d["p9_diameter(mm)"])
        self.data["f062"] = round(self.data["f053"] * float(self.data["f018"][:-2]) * float(self.data["f018"][-1:]), 1)
        self.data["f071"] = self._weight_in_pos(d["p9_diameter(mm)"], dec=3)
        self.data["f080"] = self._weight_in_pos(d["p9_diameter(mm)"], self.data["f062"], 2)

        print("[INFO] Successfully applied rebar parameters from table2")
        return None

    # ===================================================================== #
    #  TABLE 3 APPLICATION (WING WALLS / E-PARAMETERS)
    # ===================================================================== #

    def _apply_table3(self, data_list: list) -> Optional[str]:
        """
        Apply wing wall parameters from Table3 (Culvert_dastak.csv).

        Same logic as single calculator but uses:
        - c05 (natural ground left) instead of single's c06
        - c13 (right elevation) instead of single's c14

        Args:
            data_list: [d_min, d_left, d_right] — Table3 results for each H

        Returns:
            Error message if failed, None if successful
        """
        d_min = data_list[0]
        d_left = data_list[1]
        d_right = data_list[2]

        if d_min is None and d_left is None and d_right is None:
            wall_params = [
                "e01", "e02", "e03", "e04", "e05", "e06", "e07", "e08",
                "e09", "e10", "e11", "e12", "e13", "e14", "e15", "e16",
                "e17", "e18", "e19", "e20", "e21", "e22",
            ]
            for param in wall_params:
                self.data[param] = "ERR"
            return "All Table3 lookups failed - wall parameters set to ERR"

        def safe_get(series, key, default=""):
            if series is None:
                return default
            try:
                return series[key]
            except Exception:
                return default

        fallback = d_min if d_min is not None else (d_left if d_left is not None else d_right)
        if d_min is None:
            d_min = fallback
            print("[WARNING] Using fallback for H_min data")
        if d_left is None:
            d_left = fallback
            print("[WARNING] Using fallback for H_max_left data")
        if d_right is None:
            d_right = fallback
            print("[WARNING] Using fallback for H_max_right data")

        # Wall distances (same logic as single, using alpha-based branching)
        if self.params.alpha > 0:
            try:
                w1_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=self.params.ball_degree, direction=self.right,
                ), 1)
                w2_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=0, direction=self.right,
                ), 1)
                w3_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=self.params.ball_degree, direction=self.left,
                ), 1)
                w4_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=0, direction=self.left,
                ), 1)
            except Exception as e:
                print(f"[ERROR] Wall distance calculation failed: {e}")
                w1_distance = w2_distance = w3_distance = w4_distance = 0
        elif self.params.alpha < 0:
            try:
                w1_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=0, direction=self.right,
                ), 1)
                w2_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=self.params.ball_degree, direction=self.right,
                ), 1)
                w3_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=0, direction=self.left,
                ), 1)
                w4_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=self.params.ball_degree, direction=self.left,
                ), 1)
            except Exception as e:
                print(f"[ERROR] Wall distance calculation failed: {e}")
                w1_distance = w2_distance = w3_distance = w4_distance = 0
        elif self.params.alpha == 0:
            try:
                w1_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=self.params.ball_degree, direction=self.right,
                ), 1)
                w2_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_right["H"],
                    ball_degree=self.params.ball_degree, direction=self.right,
                ), 1)
                w3_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=self.params.ball_degree, direction=self.left,
                ), 1)
                w4_distance = round(self._find_distance_for_bal(
                    h_min=d_min["H"], h_max=d_left["H"],
                    ball_degree=self.params.ball_degree, direction=self.left,
                ), 1)
            except Exception as e:
                print(f"[ERROR] Wall distance calculation failed: {e}")
                w1_distance = w2_distance = w3_distance = w4_distance = 0

        # Basic parameters from minimum H
        s1_min = round(safe_get(d_min, "f", 0) - safe_get(d_min, "b", 0), 2)

        # Maximum heights
        w1_height_max = round(safe_get(d_right, "H", 0), 2)
        w3_height_max = round(safe_get(d_left, "H", 0), 2)

        # Foundation widths at max height
        w1_width_pei_max = round(safe_get(d_right, "f", 0), 2)
        w2_width_pei_max = round(safe_get(d_right, "f", 0), 2)
        w3_width_pei_max = round(safe_get(d_left, "f", 0), 2)
        w4_width_pei_max = round(safe_get(d_left, "f", 0), 2)

        # s1 maximum values
        w1_s1_max = round(float(safe_get(d_right, "f", 0)) - float(safe_get(d_right, "b", 0)), 2)
        w2_s1_max = round(float(safe_get(d_right, "f", 0)) - float(safe_get(d_right, "b", 0)), 2)
        w3_s1_max = round(float(safe_get(d_left, "f", 0)) - float(safe_get(d_left, "b", 0)), 2)
        w4_s1_max = round(float(safe_get(d_left, "f", 0)) - float(safe_get(d_left, "b", 0)), 2)

        # s2 maximum values
        w1_s2_max = round(safe_get(d_right, "x", 0) + 0.35, 2)
        w2_s2_max = round(safe_get(d_right, "x", 0) + 0.35, 2)
        w3_s2_max = round(safe_get(d_left, "x", 0) + 0.35, 2)
        w4_s2_max = round(safe_get(d_left, "x", 0) + 0.35, 2)

        # Store wall data
        self.data["e01"] = w1_distance
        self.data["e05"] = w1_height_max
        self.data["e07"] = w1_width_pei_max
        self.data["e11"] = w1_s1_max
        self.data["e15"] = s1_min
        self.data["e19"] = w1_s2_max
        self.data["e23"] = round(safe_get(d_right, "m", 0), 2)
        self.data["e02"] = w2_distance
        self.data["e08"] = w2_width_pei_max
        self.data["e12"] = w2_s1_max
        self.data["e16"] = s1_min
        self.data["e20"] = w2_s2_max
        self.data["e24"] = round(safe_get(d_right, "m", 0), 2)
        self.data["e03"] = w3_distance
        self.data["e06"] = w3_height_max
        self.data["e09"] = w3_width_pei_max
        self.data["e13"] = w3_s1_max
        self.data["e17"] = s1_min
        self.data["e21"] = w3_s2_max
        self.data["e25"] = round(safe_get(d_left, "m", 0), 2)
        self.data["e04"] = w4_distance
        self.data["e10"] = w4_width_pei_max
        self.data["e14"] = w4_s1_max
        self.data["e18"] = s1_min
        self.data["e22"] = w4_s2_max
        self.data["e26"] = round(safe_get(d_left, "m", 0), 2)
        self.data["e27"] = self.params.h_min_dastak_r
        self.data["e28"] = self.params.h_min_dastak_l

        print("[INFO] Successfully applied wing wall parameters from table3")
        return None

    # ===================================================================== #
    #  TABLE 4 APPLICATION (EXTRA REBAR POSITIONS FOR MULTI)
    # ===================================================================== #

    def _apply_extra_positions(self, d_extra: pd.Series, d_multi: pd.Series) -> Optional[str]:
        """
        Apply extra rebar positions for multi-opening culverts.

        Uses Culvert_multi_extra.csv and Culvert_multi.csv data.

        Positions:
            f081-f088: Position 11 (outer pier bars)
            f092-f099: Position 12 (middle pier bars, scaled by n-1)
            f100-f106: Position 13 (transverse bars)
            f107-f114: Position 14 (pier tie bars)

        Args:
            d_extra: pandas Series from Culvert_multi_extra.csv
            d_multi: pandas Series from Culvert_multi.csv

        Returns:
            Error message if failed, None if successful
        """
        n = self.params.n
        D = self.params.D
        c10 = self.data["c10"]
        p2 = float(d_multi["p2"])

        # Spacing from extra table
        spacing = float(d_extra["distance(cm)"]) / 100  # convert cm to m
        # ----------------------------------------------------------------- #
        # Position 11 (f081-f088): Outer pier bars
        # ----------------------------------------------------------------- #
        # f081: diameter — 25mm for D in [7, 8], else 14mm
        self.data["f081"] = 25 if D in [7, 8] else 14

        # f082: count — "2 * ceil(c10 / spacing)"
        count_per_side = ceil(c10 / spacing)
        self.data["f082"] = f"2*{count_per_side}"

        # f083: shape_1 + shape_2 from extra table
        self.data["f083"] = int(float(d_extra["shape_1"]) + float(d_extra["shape_2"]))

        # f084: shape_3 from extra table
        self.data["f084"] = int(float(d_extra["shape_3"]))

        # f085: total shape = f083 + f084
        self.data["f085"] = int(self.data["f083"] + self.data["f084"]) / 100

        self.data["f086"] = self.data["f085"] * float(self.data["f082"][2:]) * 2

        # f087: weight per meter for this diameter
        self.data["f087"] = self._weight_in_pos(self.data["f081"], dec=3)

        # f088: total weight = weight_per_m × per_bar_length × numeric_count
        numeric_count_11 = 2 * count_per_side
        total_length_11 = round(self.data["f086"] * numeric_count_11, 2)
        self.data["f088"] = round(self.data["f087"] * self.data["f086"], 1)

        # ----------------------------------------------------------------- #
        # Position 12 (f092-f099): Middle pier bars (n-1 piers)
        # ----------------------------------------------------------------- #
        # f092: diameter (same as position 11)
        self.data["f092"] = self.data["f081"]

        # f093: count — "2 * (n-1) * ceil(c10 / spacing)"
        self.data["f093"] = f"2*{(n - 1) * count_per_side}"

        # f094: shape_1 + shape_2 from extra table
        self.data["f094"] = int(float(d_extra["shape_1"]) + float(d_extra["shape_2"]))

        # f095: shape_3 from extra table
        self.data["f095"] = int(float(d_extra["shape_3"]))

        # f096: total shape = f094 + f095
        self.data["f096"] = (self.data["f094"] + self.data["f095"]) / 100

        self.data["f097"] = self.data["f096"] * float(self.data["f093"][2:]) * 2

        # f098: weight per meter
        self.data["f098"] = self._weight_in_pos(self.data["f092"], dec=3)

        # f099: total weight
        numeric_count_12 = 2 * (n - 1) * count_per_side
        total_length_12 = round(float(self.data["f097"]) * numeric_count_12, 2)
        self.data["f099"] = round(self.data["f098"] * self.data["f097"], 1)

        # ----------------------------------------------------------------- #
        # Position 13 (f100-f106): Transverse bars
        # ----------------------------------------------------------------- #
        # f100: diameter
        self.data["f100"] = "10"

        # f101: count — "2*(2n+2)" → e.g. "2*6" for n=2, "2*8" for n=3
        count_13 = 2 * n + 2
        self.data["f101"] = f"{n-1}*6" if abs(float(self.params.D)-2)<0.0001 else f"{n-1}*8"

        # f102: shape dimension (cm) — splice addition if c10 > 12m
        f100_diameter = 10  # mm
        if c10 > 12:
            n_splices = ceil(c10 / 12)
            nd = 56 if f100_diameter < 20 else 70
            self.data["f102"] = int(round((nd * f100_diameter / 10) + c10 * 100))
        else:
            self.data["f102"] = int(round(c10 * 100))

        # f103: same as f102
        self.data["f103"] = self.data["f102"] / 100

        self.data["f104"] = round(self.data["f103"] * float(self.data["f101"][2:]) * (n - 1), 1)

        # f105: weight per meter for 10mm diameter
        self.data["f105"] = self._weight_in_pos(f100_diameter, dec=3)

        # f106: total weight
        numeric_count_13 = 2 * count_13
        total_length_13 = round(self.data["f104"] * numeric_count_13, 2)
        self.data["f106"] = round(self.data["f105"] * self.data["f104"], 1)

        # ----------------------------------------------------------------- #
        # Position 14 (f107-f114): Pier tie bars
        # ----------------------------------------------------------------- #
        # f107: diameter
        self.data["f107"] = "10"

        # f108: count — "(n-1) * ceil(c10 / 0.3)"
        count_14_per_pier = ceil(c10 / 0.3)
        count_14_total = (n - 1) * count_14_per_pier
        self.data["f108"] = f"{n - 1}*{count_14_per_pier}"

        # f109: shape dimension = (p2 * 100 - 10) * 2
        self.data["f109"] = int(round((p2 * 100 - 10) * 2)/2)

        # f110: constant shape dimension
        self.data["f110"] = 22

        # f111: total shape = 2 * f110 + 2 * f109 + 10
        f110_val = 22
        f109_val = float(self.data["f109"])
        self.data["f111"] = round(2 * f110_val + 2 * f109_val + 10) / 100

        self.data["f112"] = round(self.data["f111"] * float(self.data["f108"][2:]) * (n - 1), 1)

        # f113: weight per meter for 10mm diameter
        f107_diameter = 10
        self.data["f113"] = self._weight_in_pos(f107_diameter, dec=3)

        # f114: total weight
        total_length_14 = round(self.data["f112"] * count_14_total, 2)
        self.data["f114"] = round(self.data["f113"] * self.data["f112"], 1)
        
        # Totals (f089, f090, f091)
        c1 = [
            self.data["f072"], self.data["f073"], self.data["f074"],
            self.data["f075"], self.data["f076"], self.data["f077"],
            self.data["f078"],
        ]
        c2 = [self.data["f079"], self.data["f080"]]
        c3 = [self.data["f088"], self.data["f099"], self.data["f106"], self.data["f114"]]
        c4 = c1 + c2 + c3

        c1_filtered = [float(i) for i in c1 if i != "-"]
        c2_filtered = [float(i) for i in c2 if i != "-"]
        c3_filtered = [float(i) for i in c3 if i != "-"]
        c4_filtered = [float(i) for i in c4 if i != "-"]

        self.data["f089"] = round(sum(c1_filtered+c3_filtered) / self.data["c10"], 1) if c1_filtered else 0
        self.data["f090"] = round(sum(c2_filtered), 1) if c2_filtered else 0
        self.data["f091"] = round(sum(c4_filtered), 1) if c4_filtered else 0

        print("[INFO] Successfully applied extra rebar positions from table4")
        return None

    # ===================================================================== #
    #  HELPER METHODS
    # ===================================================================== #

    def _find_distance_for_bal(self, h_min: float, h_max: float,
                               ball_degree: float, direction: str) -> float:
        """
        Calculate wing wall distance using iterative convergence.

        Formula:
            d = (H_max - H_min) / cos(ball_degree) × z_shirvani

        Args:
            h_min: Minimum wall height at wall end (m)
            h_max: Maximum wall height at culvert end (m)
            ball_degree: Wing wall angle from horizontal (degrees)
            direction: "UP" (upstream) or "DOWN" (downstream)

        Returns:
            Calculated wall distance in meters
        """
        def formula(hmax, hmin):
            return (hmax - hmin) / cos(radians(ball_degree)) * self.params.z_shirvani

        h_min_temp = h_min
        d1, d2 = 0, 1
        max_iterations = 100
        iteration = 0

        if direction.upper() == "UP":
            while abs(d2 - d1) > 0.2 and iteration < max_iterations:
                d1 = formula(hmax=h_max, hmin=h_min_temp)
                h_min_temp = h_min + d1 * self.params.z_natural
                d2 = formula(hmax=h_max, hmin=h_min_temp)
                iteration += 1
        else:
            while abs(d2 - d1) > 0.2 and iteration < max_iterations:
                d1 = formula(hmax=h_max, hmin=h_min_temp)
                h_min_temp = h_min - d1 * self.params.z_natural
                d2 = formula(hmax=h_max, hmin=h_min_temp)
                iteration += 1

        if iteration >= max_iterations:
            print("[WARNING] Wall distance calculation did not converge")

        print(f"[INFO] Wall distance in {direction}: {d2:.2f}m "
              f"(h_min={h_min}, h_max={h_max})")
        return d2

    def _count_in_pos(self, p: int, count: str, cal: bool = False) -> str:
        """
        Calculate rebar count for a given position.

        For multi-culverts, counts are multiplied by n (number of openings).

        Positions 1,2,4,7,10: count = ceil(c10 × rate × n)
        Positions 3,5,6,8,9 : count = ceil(fixed × n)

        Args:
            p: Position number (1-10)
            count: Count string from table (e.g. "3.1" or "5*2")
            cal: If True, return numeric total; if False, keep display format

        Returns:
            Formatted count string or calculated value
        """
        if count == "-":
            return "-"

        # Multi-culvert: multiply by number of openings
        n = self.params.n

        try:
            count_p1, count_p2 = str(count).split("*")
        except ValueError:
            count_p1, count_p2 = str(count), None

        if p in [1, 2, 4, 7, 10]:
            res = self.data["c10"] * float(count_p1)
            if count_p2:
                if cal:
                    return str(ceil(res * n) * int(count_p2))
                else:
                    return str(ceil(res * n)) + "*" + count_p2
            else:
                return str(ceil(res * n))
        elif p in [3, 5, 6, 8, 9]:
            if count_p2:
                if cal:
                    return str(ceil(float(count_p1) * n) * int(count_p2))
                else:
                    return str(ceil(float(count_p1) * n)) + "*" + count_p2
            else:
                return str(ceil(float(count_p1) * n))
        else:
            print(f"[ERROR] Invalid position p={p}")
            return "ERROR"

    def _length_in_pos(self, p: int, L: float = None, D: float = None,
                       N: float = None, dec: int = 2) -> float:
        """
        Calculate total rebar length for a position.

        Transverse positions (3,5,6) use c10 (= L/cos(alpha)) and
        include splice additions when c10 > 12m.

        Args:
            p: Position number (1-10)
            L: Base rebar length from table (m)
            D: Rebar diameter (mm) — for splice calculation
            N: Number of rebars — multiplies total length
            dec: Decimal places for rounding

        Returns:
            Calculated length (m) or "-"
        """
        if L == "-":
            return "-"

        L = float(L) if L else None
        N = float(N) if N else None
        D = float(D) if D else None
        if not L:
            L = float()

        if p in [1, 2, 4, 7, 8, 9, 10]:
            if N:
                return round(L * N, dec)
            else:
                return round(L, dec)

        elif p in [3, 5, 6]:
            if N:
                if self.data["c10"] <= 12:
                    return round(self.data["c10"] * N, dec)
                else:
                    n = ceil(self.data["c10"] / 12)
                    nd = 56 if D < 20 else 70
                    return round((self.data["c10"] + n * D * nd / 1000) * N, dec)
            else:
                if self.data["c10"] <= 12:
                    return round(self.data["c10"], dec)
                else:
                    n = ceil(self.data["c10"] / 12)
                    nd = 56 if D < 20 else 70
                    return round(self.data["c10"] + n * D * nd / 1000, dec)

        return round(L, dec)

    def _weight_in_pos(self, diameter: float, length: float = None,
                       dec: int = 1) -> float:
        """
        Calculate rebar weight.

        Weight per meter = (π × D² / 4) × 7850 kg/m³

        Args:
            diameter: Rebar diameter in mm
            length: Total length (m) — None returns weight per meter
            dec: Decimal places for rounding

        Returns:
            Weight in kg or "-"
        """
        if diameter == "-" or diameter == "":
            return "-"

        weight_per_meter = ((pi * (float(diameter) / 1000) ** 2) / 4) * 7850

        if length:
            return round(weight_per_meter * float(length), dec)
        else:
            return round(weight_per_meter, dec)
