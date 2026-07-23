"""
Unified Single At-Grade Culvert Calculator (n=1, any alpha).

This calculator handles ALL single-opening at-grade cases:
    - Perpendicular (alpha = 0)
    - Angular More (alpha > 0)
    - Angular Less (alpha < 0)

The formulas use cos(alpha) and tan(alpha) corrections which naturally
reduce to the perpendicular case when alpha=0, since cos(0)=1 and tan(0)=0.

Template selection:
    alpha = 0  → single_perpendicular_atGrade.dxf
    alpha > 0  → single_angularM_atGrade.dxf
    alpha < 0  → single_angularL_atGrade.dxf

================================================================================
CULVERT GEOMETRY OVERVIEW
================================================================================

A box culvert is a reinforced concrete structure used to convey water under a
roadway. Key components:

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

    Side view showing left/right wing walls:

         Wing Wall 3    ┌───┐    Wing Wall 1
              ↖        │   │        ↗
               ↖       │   │       ↗
                ↖      │   │      ↗
    ─────────────◄─────│ B │─────►─────────────  ← Water flow direction
                 ↗     │ O │     ↖
                ↗      │ X │      ↖
               ↗       │   │       ↖
         Wing Wall 4   └───┘   Wing Wall 2

================================================================================
INPUT PARAMETERS
================================================================================

Geometric Parameters:
- n: Number of openings (1 for this calculator)
- D: Span/Diameter of opening (m)
- L: Total length of culvert (L = A + B) (m)
- A: Length on left side from centerline (m)
- B: Length on right side from centerline (m)
- Hs: Static head / fill height above top slab (m)
- H_min: Minimum wall height for wing walls (m)

Elevation Parameters:
- CL: Project line elevation at centerline (m)
- ax_natural: Natural ground axis elevation at centerline (m)
- ret: Retention depth below natural ground (m)

Slope Parameters:
- dever_left: Cross slope on left side (PERCENT, e.g., 2 = 2%)
- dever_right: Cross slope on right side (PERCENT, e.g., -2 = -2%)
- z_natural: Natural ground longitudinal slope (RATIO, e.g., 0.02 = 2%)
- z_toli: Culvert floor longitudinal slope (RATIO, e.g., 0.01 = 1%)
- z_shirvani: Wing wall transverse slope factor (1:z ratio)

Angle Parameters:
- ball_degree: Wing wall angle from horizontal (degrees)
- alpha: Skew angle (0=perpendicular, >0=angular more, <0=angular less)
- direction_flag: True = left is UPSTREAM, False = left is DOWNSTREAM

================================================================================
KEY FORMULAS (Unified — valid for all alpha including alpha=0)
================================================================================

Distance corrections:
    c08 = A / cos(alpha)
    c09 = B / cos(alpha)
    c10 = L / cos(alpha)

Elevation at left culvert end (bottom of box):
    c04 = CL + (dever_left/100) × A - A × tan(alpha) × z_toli - Hs - t - 0.3

Elevation at right culvert end (bottom of box):
    c14 = CL + (dever_right/100) × B + B × tan(alpha) × z_toli - Hs - t - 0.3

Natural ground at left end:
    If LEFT = UP:   c06 = ax_natural + z_natural × c08 - ret
    If LEFT = DOWN:  c06 = ax_natural - z_natural × c08 - ret

Wall height (average):
    H = ((c04 - c06 + 0.3) + (c14 - c12 + 0.3)) / 2

Pipe diameter correction:
    d02 = D × cos(alpha)

Shape dimension adjustment (f020, f022, f025, f027):
    adjustment = d10 / cos(alpha) - d10    (= 0 when alpha=0)

Wing wall distance (iterative):
    d = (H_max - H_min) / cos(ball_degree) × z_shirvani

Rebar weight per meter:
    W = (π × D² / 4) × 7850 kg/m³  (where D is in meters)
"""

from typing import Dict, Any, Optional, Callable
from math import ceil, pi, cos, radians, tan
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


class SingleAtGradeCalculator(BaseCulvertCalculator):
    """
    Unified calculator for single-opening at-grade culverts (any alpha).

    Handles perpendicular (alpha=0), angular more (alpha>0), and
    angular less (alpha<0) cases with one set of formulas.
    cos(0)=1 and tan(0)=0 make all angular terms vanish when alpha=0.
    """

    def __init__(self,
                 input_params: CulvertInput,
                 table_repository,
                 progress_callback: Optional[Callable[[int], None]] = None):
        super().__init__(input_params, table_repository, progress_callback)

        if self.params.n != 1:
            raise ValueError(
                f"SingleAtGradeCalculator requires n=1, got n={self.params.n}"
            )

    # --------------------------------------------------------------------- #
    #  MAIN CALCULATION
    # --------------------------------------------------------------------- #

    def calculate(self) -> Dict[str, Any]:
        """
        Perform single at-grade culvert calculations.

        Process:
        1. Query Table1 (Culvert_one.csv) for structural parameters
        2. Query Table2 (Culvert_full.csv) for rebar specifications
        3. Query Table3 (Culvert_dastak.csv) for wing wall parameters
        4. Convert all values to strings for DXF output

        Returns:
            Dictionary of calculated values ready for DXF template
        """
        self._update_progress(50)
        self._apply_directions()

        has_errors = False

        # --- Table 1 --------------------------------------------------------
        try:
            table1_result = self.tables.find_in_table1_one(
                n=self.params.n,
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
            self.messages.append(f"Table1 error: {str(e)}")
            has_errors = True
            table1_result = None

        # --- Table 2 --------------------------------------------------------
        if table1_result is not None:
            try:
                table2_result = self.tables.find_in_table2(
                    n=self.params.n,
                    D=self.params.D,
                    Hs=self.params.Hs,
                    c1=table1_result["c1"],
                    t=table1_result["t"],
                )
                if isinstance(table2_result, str):
                    self.messages.append(table2_result)
                    has_errors = True
                else:
                    msg2 = self._apply_table2(table2_result)
                    if msg2:
                        self.messages.append(msg2)
            except Exception as e:
                self.messages.append(f"Table2 error: {str(e)}")
                has_errors = True

        # --- Table 3 --------------------------------------------------------
        if table1_result is not None and "c04" in self.data and "d11" in self.data:
            try:
                H_min = self.params.H_min
                print(self.data["d11"], self.data["c12"], self.data["c14"])
                H_max_l = self.data["c04"] + 0.3 + self.data["d11"] - self.data["c06"]
                H_max_r = self.data["c14"] + 0.3 + self.data["d11"] - self.data["c12"]

                print(f"[DEBUG] Table3 H values: H_min={H_min}, H_max_l={H_max_l}, H_max_r={H_max_r}")
                print(f"[DEBUG] Components: c04={self.data['c04']}, c06={self.data['c06']}, "
                      f"c14={self.data['c14']}, c12={self.data['c12']}, d11={self.data['d11']}")

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
        Return the DXF template based on the skew angle.

        alpha = 0  → perpendicular template
        alpha > 0  → angular more template
        alpha < 0  → angular less template
        """
        if self.params.alpha == 0:
            return "single_perpendicular_atGrade.dxf"
        elif self.params.alpha > 0:
            return "single_angularM_atGrade.dxf"
        else:
            return "single_angularL_atGrade.dxf"

    # ===================================================================== #
    #  TABLE 1 APPLICATION
    # ===================================================================== #

    def _apply_table1(self, d: pd.Series) -> Optional[str]:
        """
        Apply parameters from Table1 (Culvert_one.csv).

        TABLE1 PARAMETERS FROM CSV:
        ===========================
        - a1, a2: Horizontal dimensions (haunch sizes)
        - b1, b2: Vertical dimensions (b1=wall thickness)
        - c1, c2: Concrete cover values (mm)
        - f: Foundation width (total base width)
        - m: Foundation depth below box bottom
        - t: Slab thickness (top and bottom)
        - phi_b: Rebar diameter for bending
        - j*: Joint spacing factor
        - H: Maximum wall height this row applies to

        CALCULATED VALUES (unified formulas):
        ======================================
        c01: CL (centerline elevation)
        c02: dever_left (left cross slope in %)
        c03: dever_right (right cross slope in %)
        c08: A / cos(alpha)   — left distance along skew
        c09: B / cos(alpha)   — right distance along skew
        c10: L / cos(alpha)   — total length along skew
        c04: CL + (dever_left/100)*A - A*tan(α)*z_toli - Hs - t - 0.3
        c14: CL + (dever_right/100)*B + B*tan(α)*z_toli - Hs - t - 0.3
        c06, c12: Natural ground elevations (using c08 / c09)
        d02: D * cos(alpha)   — pipe diameter correction

        Args:
            d: pandas Series from table1 containing structural parameters

        Returns:
            Error message if failed, None if successful
        """
        alpha_rad = radians(self.params.alpha)
        cos_alpha = cos(alpha_rad)
        tan_alpha = tan(alpha_rad)

        # Basic parameters
        self.data["c01"] = round(self.params.CL, 2)
        self.data["c02"] = round(self.params.dever_left, 2)
        self.data["c03"] = round(self.params.dever_right, 2)

        # Distance corrections — cos(0)=1 so perpendicular values unchanged
        self.data["c08"] = round(abs(self.params.A) / cos_alpha, 1)
        self.data["c09"] = round(abs(self.params.B) / cos_alpha, 1)
        self.data["c10"] = round(
            (self.data["c08"] + self.data["c09"]), 1
        )

        # Base elevation
        element1 = float(self.params.CL)

        # Culvert base elevations — tan(0)=0 so angular term vanishes for perpendicular
        self.data["c04"] = round(
            element1
            + (self.data["c02"] / 100) * self.params.A
            - self.params.A * tan_alpha * self.params.z_toli
            - self.params.Hs
            - d["t"]
            - 0.3,
            2,
        )
        self.data["c14"] = round(
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
            self.data["c06"] = round(
                self.params.ax_natural
                + self.params.z_natural * self.data["c08"]
                - self.params.ret,
                2,
            )
            self.data["c12"] = round(
                self.params.ax_natural
                - self.params.z_natural * self.data["c09"]
                - self.params.ret,
                2,
            )
        elif self.left == "DOWN":
            self.data["c06"] = round(
                self.params.ax_natural
                - self.params.z_natural * self.data["c08"]
                - self.params.ret,
                2,
            )
            self.data["c12"] = round(
                self.params.ax_natural
                + self.params.z_natural * self.data["c09"]
                - self.params.ret,
                2,
            )
        else:
            print(f"[WARNING] Direction not set correctly: left={self.left}")

        self.data["c07"] = round(self.data["c06"] - d["m"], 2)
        self.data["c11"] = round(self.data["c12"] - d["m"], 2)

        # Wall height (average of left and right)
        H_1 = self.data["c04"] - self.data["c06"] + 0.3
        H_2 = self.data["c14"] - self.data["c12"] + 0.3
        self.H = round((H_1 + H_2) / 2, 2)

        print(f"[INFO] Calculated H={self.H}, comparing with table H={d['H']}")

        if self.H >= d["H"]:
            print(f"[WARNING] H={self.H} >= table H={d['H']}, need to re-query table")
            self.H = d["H"]
            new_result = self.tables.find_in_table1_one(
                n=self.params.n,
                D=self.params.D,
                Hs=self.params.Hs,
                H=self.H,
            )
            if isinstance(new_result, str):
                return new_result
            return self._apply_table1(new_result)

        print(f"[INFO] H={self.H} is valid")

        # Remaining structural parameters
        self.data["d13"] = self.params.Hs
        self.data["d01"] = round(self.params.z_toli * 100, 2)   # slope as percentage
        self.data["d09"] = d["c2"]
        self.data["d10"] = d["c1"]
        self.data["d12"] = d["j*"]
        self.data["d11"] = d["t"]
        self.data["d05"] = d["b1"]
        self.data["d07"] = d["a1"]
        self.data["d08"] = d["b2"]
        self.data["d06"] = d["a2"]
        self.data["d04"] = d["m"]
        self.data["d03"] = d["f"]
        self.data["d02"] = round(self.params.D * cos_alpha, 2)   # D × cos(α)

        print("[INFO] Successfully applied parameters from table1")
        return None

    # ===================================================================== #
    #  TABLE 2 APPLICATION (REBAR)
    # ===================================================================== #

    def _apply_table2(self, d: pd.Series) -> Optional[str]:
        """
        Apply rebar parameters from Table2 (Culvert_full.csv).

        Shape-dimension adjustment for skew (f020, f022, f025, f027):
            adjustment = d10 / cos(alpha) - d10      (= 0 when alpha = 0)

        f029, f033, f034, f039 are converted from m to cm (* 100).

        Args:
            d: pandas Series from table2 containing rebar specifications

        Returns:
            Error message if failed, None if successful
        """
        alpha_rad = radians(self.params.alpha)
        cos_alpha = cos(alpha_rad)

        # Shape-dimension adjustment for angular culverts
        # d10 = concrete cover c1 from table1 (already stored)
        d10_adj = 100*(self.data["d10"] / cos_alpha - self.data["d10"])  # 0 when α=0

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
        self.data["f029"] = round(self._length_in_pos(p=3, L=d["p3_L(m)"], D=d["p3_diameter(mm)"]) * 100)
        self.data["f047"] = self._length_in_pos(p=3, L=d["p3_L(m)"], D=d["p3_diameter(mm)"])
        self.data["f056"] = self._length_in_pos(
            p=3, L=d["p3_L(m)"],
            N=self._count_in_pos(3, d["p3_n"], cal=True),
            D=d["p3_diameter(mm)"], dec=2,
        )
        self.data["f065"] = self._weight_in_pos(d["p3_diameter(mm)"], dec=3)
        self.data["f074"] = self._weight_in_pos(d["p3_diameter(mm)"], self.data["f056"], 1)

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
        self.data["f033"] = round(self._length_in_pos(p=5, L=d["p5_L(m)"], D=d["p5_diameter(mm)"]) * 100)
        self.data["f049"] = self._length_in_pos(p=5, L=d["p5_L(m)"], D=d["p5_diameter(mm)"])
        self.data["f058"] = self._length_in_pos(
            p=5, L=d["p5_L(m)"],
            N=self._count_in_pos(5, d["p5_n"], cal=True),
            D=d["p5_diameter(mm)"], dec=2,
        )
        self.data["f067"] = self._weight_in_pos(d["p5_diameter(mm)"], dec=3)
        self.data["f076"] = self._weight_in_pos(d["p5_diameter(mm)"], self.data["f058"], 1)

        # Position 6
        self.data["f006"] = d["p6_diameter(mm)"]
        self.data["f015"] = self._count_in_pos(6, d["p6_n"])
        self.data["f034"] = round(self._length_in_pos(p=6, L=d["p6_L(m)"], D=d["p6_diameter(mm)"]) * 100)
        self.data["f050"] = self._length_in_pos(p=6, L=d["p6_L(m)"], D=d["p6_diameter(mm)"])
        self.data["f059"] = self._length_in_pos(
            p=6, L=d["p6_L(m)"],
            N=self._count_in_pos(6, d["p6_n"], cal=True),
            D=d["p6_diameter(mm)"], dec=2,
        )
        self.data["f068"] = self._weight_in_pos(d["p6_diameter(mm)"], dec=3)
        self.data["f077"] = self._weight_in_pos(d["p6_diameter(mm)"], self.data["f059"], 1)

        # Position 7
        self.data["f007"] = d["p7_diameter(mm)"]
        self.data["f016"] = self._count_in_pos(7, d["p7_n"])
        self.data["f035"] = d["p7_sh_i1"]
        self.data["f036"] = d["p7_sh_i2"]
        self.data["f037"] = d["p7_sh_i3"]
        self.data["f038"] = d["p7_sh_i4"]
        self.data["f051"] = self._length_in_pos(p=7, L=d["p7_L(m)"], D=d["p7_diameter(mm)"])
        self.data["f060"] = self._length_in_pos(
            p=7, L=d["p7_L(m)"],
            N=self._count_in_pos(7, d["p7_n"], cal=True),
            D=d["p7_diameter(mm)"], dec=2,
        )
        self.data["f069"] = self._weight_in_pos(d["p7_diameter(mm)"], dec=3)
        self.data["f078"] = self._weight_in_pos(d["p7_diameter(mm)"], self.data["f060"], 1)

        # Position 8
        self.data["f008"] = d["p8_diameter(mm)"]
        self.data["f017"] = self._count_in_pos(8, d["p8_n"])
        self.data["f039"] = round(self._length_in_pos(p=8, L=d["p8_L(m)"], D=d["p8_diameter(mm)"]) * 100)
        self.data["f052"] = self._length_in_pos(p=8, L=d["p8_L(m)"], D=d["p8_diameter(mm)"])
        self.data["f061"] = self._length_in_pos(
            p=8, L=d["p8_L(m)"],
            N=self._count_in_pos(8, d["p8_n"], cal=True),
            D=d["p8_diameter(mm)"], dec=2,
        )
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
        self.data["f062"] = self._length_in_pos(
            p=9, L=d["p9_L(m)"],
            N=self._count_in_pos(9, d["p9_n"], cal=True),
            D=d["p9_diameter(mm)"], dec=2,
        )
        self.data["f071"] = self._weight_in_pos(d["p9_diameter(mm)"], dec=3)
        self.data["f080"] = self._weight_in_pos(d["p9_diameter(mm)"], self.data["f062"], 2)

        # Position 10 (p0)
        self.data["f081"] = d["p0_diameter(mm)"]
        self.data["f082"] = self._count_in_pos(10, d["p0_n"])

        if self.data["f082"] != "-":
            self.data["f083"] = int(float(d["p0_sh_i1"]) + float(d["p0_sh_i2"]))
            self.data["f084"] = d["p0_sh_i3"]
            self.data["f085"] = self._length_in_pos(p=10, L=d["p0_L(m)"], D=d["p0_diameter(mm)"])
            self.data["f086"] = self._length_in_pos(
                p=10, L=d["p0_L(m)"],
                N=self._count_in_pos(10, d["p0_n"], cal=True),
                D=d["p0_diameter(mm)"], dec=2,
            )
            self.data["f087"] = self._weight_in_pos(d["p0_diameter(mm)"], dec=3)
            weight_088 = self._weight_in_pos(d["p0_diameter(mm)"], self.data["f086"], 1)
            self.data["f088"] = weight_088 if weight_088 != "-" else "-"
        else:
            self.data["f083"] = "-"
            self.data["f084"] = "-"
            self.data["f085"] = "-"
            self.data["f086"] = "-"
            self.data["f087"] = "-"
            self.data["f088"] = "-"

        # Totals (f089, f090, f091)
        c1 = [
            self.data["f072"], self.data["f073"], self.data["f074"],
            self.data["f075"], self.data["f076"], self.data["f077"],
            self.data["f078"], self.data["f088"],
        ]
        c2 = [self.data["f079"], self.data["f080"]]
        c3 = c1 + c2

        c1_filtered = [float(i) for i in c1 if i != "-"]
        c2_filtered = [float(i) for i in c2 if i != "-"]
        c3_filtered = [float(i) for i in c3 if i != "-"]

        self.data["f089"] = round(sum(c1_filtered) / self.data["c10"], 1) if c1_filtered else 0
        self.data["f090"] = round(sum(c2_filtered), 1) if c2_filtered else 0
        self.data["f091"] = round(sum(c3_filtered), 1) if c3_filtered else 0

        print("[INFO] Successfully applied rebar parameters from table2")
        return None

    # ===================================================================== #
    #  TABLE 3 APPLICATION (WING WALLS)
    # ===================================================================== #

    def _apply_table3(self, data_list: list) -> Optional[str]:
        """
        Apply wing wall parameters from Table3 (Culvert_dastak.csv).

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


        # Wall distances
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

        # Code first pei (starting elevation at wall base)
        try:
            w1_code_first_pei = round(self.data["c12"] - safe_get(d_right, "m", 0), 2)
            w2_code_first_pei = round(self.data["c12"] - safe_get(d_right, "m", 0), 2)
            w3_code_first_pei = round(self.data["c06"] - safe_get(d_left, "m", 0), 2)
            w4_code_first_pei = round(self.data["c06"] - safe_get(d_left, "m", 0), 2)
        except Exception:
            w1_code_first_pei = w2_code_first_pei = 0
            w3_code_first_pei = w4_code_first_pei = 0

        # Code end pei (ending elevation at wall top) — depends on direction
        try:
            if self.left == "UP":
                w1_code_end_pei = round(
                    self.data["c12"] + self.params.z_natural * w1_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w2_code_end_pei = round(
                    self.data["c12"] + self.params.z_natural * w2_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w3_code_end_pei = round(
                    self.data["c06"] - self.params.z_natural * w3_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w4_code_end_pei = round(
                    self.data["c06"] - self.params.z_natural * w4_distance
                    - safe_get(d_min, "m", 0), 2
                )
            elif self.left == "DOWN":
                w1_code_end_pei = round(
                    self.data["c12"] - self.params.z_natural * w1_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w2_code_end_pei = round(
                    self.data["c12"] - self.params.z_natural * w2_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w3_code_end_pei = round(
                    self.data["c06"] + self.params.z_natural * w3_distance
                    - safe_get(d_min, "m", 0), 2
                )
                w4_code_end_pei = round(
                    self.data["c06"] + self.params.z_natural * w4_distance
                    - safe_get(d_min, "m", 0), 2
                )
            else:
                w1_code_end_pei = w2_code_end_pei = 0
                w3_code_end_pei = w4_code_end_pei = 0
        except Exception:
            w1_code_end_pei = w2_code_end_pei = 0
            w3_code_end_pei = w4_code_end_pei = 0

        # Store wall data
        self.data["e01"] = w1_distance
        self.data["e05"] = w1_height_max
        self.data["e07"] = w1_width_pei_max
        self.data["e11"] = w1_s1_max
        self.data["e15"] = s1_min
        self.data["e19"] = w1_s2_max

        self.data["e02"] = w2_distance
        self.data["e08"] = w2_width_pei_max
        self.data["e12"] = w2_s1_max
        self.data["e16"] = s1_min
        self.data["e20"] = w2_s2_max

        self.data["e03"] = w3_distance
        self.data["e06"] = w3_height_max
        self.data["e09"] = w3_width_pei_max
        self.data["e13"] = w3_s1_max
        self.data["e17"] = s1_min
        self.data["e21"] = w3_s2_max

        self.data["e04"] = w4_distance
        self.data["e10"] = w4_width_pei_max
        self.data["e14"] = w4_s1_max
        self.data["e18"] = s1_min
        self.data["e22"] = w4_s2_max

        print("[INFO] Successfully applied handle parameters from table3")
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

        Iterated because the ground slope (z_natural) changes the ending
        height as the wall extends further from the culvert.

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
            while abs(d2 - d1) > 0.1 and iteration < max_iterations:
                d1 = formula(hmax=h_max, hmin=h_min_temp)
                h_min_temp = h_min + d1 * self.params.z_natural
                d2 = formula(hmax=h_max, hmin=h_min_temp)
                iteration += 1
        else:
            while abs(d2 - d1) > 0.1 and iteration < max_iterations:
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

        Positions 1,2,4,7,10: count = ceil(c10 × rate)
        Positions 3,5,6,8,9 : count = ceil(fixed)

        Args:
            p: Position number (1-10)
            count: Count string from table (e.g. "3.1" or "5*2")
            cal: If True, return numeric total; if False, keep display format

        Returns:
            Formatted count string or calculated value
        """
        if count == "-":
            return "-"

        n = 1

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
