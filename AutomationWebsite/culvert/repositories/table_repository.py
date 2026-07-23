"""
Table Repository for loading and querying culvert design CSV tables.
Handles 5 different tables used in calculations.
"""

import pandas as pd
import os
from typing import Optional, Union


class TableRepository:
    """
    Repository for accessing culvert design tables.
    Loads 5 CSV files:
    - Culvert_one.csv: Main parameters for n=1 (table1)
    - Culvert_full.csv: Rebar details (table2)
    - Culvert_dastak.csv: Handle details (table3)
    - Culvert_multi.csv: Main parameters for n>1
    - Culvert_multi_extra.csv: Extra positions for multi-opening (table4)
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize repository and load all tables.
        
        Args:
            data_dir: Path to directory containing CSV files.
                     If None, uses 'data/culvert_tables' relative to project root.
        """
        if data_dir is None:
            # Use default path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, 'data', 'culvert_tables')
        
        self.data_dir = data_dir
        
        # Load all tables
        self.t1 = pd.read_csv(os.path.join(data_dir, 'Culvert_one.csv'))  # table1
        self.t2 = pd.read_csv(os.path.join(data_dir, 'Culvert_full.csv'))  # table2
        self.t3 = pd.read_csv(os.path.join(data_dir, 'Culvert_dastak.csv'))  # table3
        self.t_multi = pd.read_csv(os.path.join(data_dir, 'Culvert_multi.csv'))
        self.t4 = pd.read_csv(os.path.join(data_dir, 'Culvert_multi_extra.csv'))  # table4
        
        print(f"[INFO] Loaded {len(self.t1)} rows from Culvert_one.csv")
        print(f"[INFO] Loaded {len(self.t2)} rows from Culvert_full.csv")
        print(f"[INFO] Loaded {len(self.t3)} rows from Culvert_dastak.csv")
        print(f"[INFO] Loaded {len(self.t_multi)} rows from Culvert_multi.csv")
        print(f"[INFO] Loaded {len(self.t4)} rows from Culvert_multi_extra.csv")
    
    def find_in_table1_one(self, n: int, D: float, Hs: float, H: float = 0) -> Union[pd.Series, str]:
        """
        Find parameters in Culvert_one.csv for single-opening culverts (n=1).
        
        Filters by n, D, and Hs range.  The 'n' column in Culvert_one.csv
        corresponds to the number of openings (always 1).
        
        Args:
            n: Number of openings (should be 1)
            D: Diameter in meters
            Hs: Static head in meters
            H: Height (optional, for iteration)
        
        Returns:
            pd.Series with found parameters, or error string
        """
        table = self.t1
        
        # Filter by n and D
        mask = (table["n"] == n) & (table["D"] == D)
        choices = table[mask]
        
        if choices.empty:
            return f"[ERROR] No data found in Culvert_one for n={n}, D={D}"
        
        # Filter by Hs range (column "Hs" contains ranges like "(0.00, 0.60)")
        for idx, row in choices.iterrows():
            hs_range = row["Hs"]
            if isinstance(hs_range, str):
                try:
                    hs_range = hs_range.strip("()").split(",")
                    hs_min = float(hs_range[0])
                    hs_max = float(hs_range[1])
                    
                    if hs_min <= Hs < hs_max:
                        if H > 0 and H < row["H"]:
                            print(f"[INFO] Found parameters in Culvert_one for n={n}, D={D}, Hs={Hs}")
                            return row
                        elif H == 0:
                            print(f"[INFO] Found parameters in Culvert_one for n={n}, D={D}, Hs={Hs}")
                            return row
                except (ValueError, IndexError) as e:
                    print(f"[WARNING] Could not parse Hs range: {hs_range}, error: {e}")
                    continue
        
        return f"[ERROR] No suitable data found in Culvert_one for n={n}, D={D}, Hs={Hs}"
    
    def find_in_table1_multi(self, D: float, Hs: float, H: float = 0) -> Union[pd.Series, str]:
        """
        Find parameters in Culvert_multi.csv for multi-opening culverts (n>=2).
        
        The 'n' column in Culvert_multi.csv is a *structural* parameter
        (values like 0.8, 1.0, 1.5) — NOT the number of openings.
        Therefore this function does NOT filter by n; it only uses D and Hs
        to locate the correct row.  The same row is valid for any number
        of openings (2, 3, 4, …).
        
        Args:
            D: Diameter in meters
            Hs: Static head in meters
            H: Height (optional, for iteration)
        
        Returns:
            pd.Series with found parameters, or error string
        """
        table = self.t_multi
        
        # Filter by D only (no n filter)
        mask = (table["D"] == D)
        choices = table[mask]
        
        if choices.empty:
            return f"[ERROR] No data found in Culvert_multi for D={D}"
        
        # Filter by Hs range
        for idx, row in choices.iterrows():
            hs_range = row["Hs"]
            if isinstance(hs_range, str):
                try:
                    hs_range = hs_range.strip("()").split(",")
                    hs_min = float(hs_range[0])
                    hs_max = float(hs_range[1])
                    
                    if hs_min < Hs <= hs_max:
                        if H > 0 and H < row["H"]:
                            print(f"[INFO] Found parameters in Culvert_multi for D={D}, Hs={Hs}")
                            return row
                        elif H == 0:
                            print(f"[INFO] Found parameters in Culvert_multi for D={D}, Hs={Hs}")
                            return row
                except (ValueError, IndexError) as e:
                    print(f"[WARNING] Could not parse Hs range: {hs_range}, error: {e}")
                    continue
        
        return f"[ERROR] No suitable data found in Culvert_multi for D={D}, Hs={Hs}"
    
    def find_in_table2(self, n: int, D: float, Hs: float, c1: float, t: float) -> Union[pd.Series, str]:
        """
        Find rebar details in table2 (Culvert_full).
        
        This table contains detailed rebar specifications:
        - p1-p9, p0: Different rebar positions
        - Each position has: diameter(mm), n, distance(cm), L(m), sh_i1-i5
        - weight(kg/m), weight(kg)(start-end)
        
        Args:
            n: Number of openings
            D: Diameter in meters
            Hs: Static head in meters
            c1: Concrete cover from table1
            t: Thickness from table1
        
        Returns:
            pd.Series with rebar specifications, or error string
        """
        # Filter by n, D, c1, t
        mask = (
            (self.t2["n"] == n) &
            (self.t2["D"] == D) &
            (self.t2["c1"] == c1) &
            (self.t2["t"] == t)
        )
        choices = self.t2[mask]
        
        if choices.empty:
            return f"[ERROR] No data found in table2 for n={n}, D={D}, c1={c1}, t={t}"
        
        # Filter by Hs range
        for idx, row in choices.iterrows():
            hs_range = row["Hs"]
            if isinstance(hs_range, str):
                try:
                    hs_range = hs_range.strip("()").split(",")
                    hs_min = float(hs_range[0])
                    hs_max = float(hs_range[1])
                    
                    if hs_min < Hs <= hs_max:
                        print(f"[INFO] Found rebar specs in table2 for n={n}, D={D}, Hs={Hs}")
                        return row
                except (ValueError, IndexError) as e:
                    print(f"[WARNING] Could not parse Hs range in table2: {hs_range}, error: {e}")
                    continue
        
        return f"[ERROR] No suitable rebar data found in table2 for n={n}, D={D}, Hs={Hs}"
    
    def find_in_table3(self, H: float) -> Union[pd.Series, str]:
        """
        Find handle details in table3 (Culvert_dastak).
        
        This table contains handle specifications (b, f, m, x) based on H.
        Uses interpolation if exact H is not found.
        
        Args:
            H: Height in meters (1-7 range)
        
        Returns:
            pd.Series with handle specifications (possibly interpolated), or error string
        """
        # Check if H is in valid range
        if H > 7 or H < 1:
            return f"[ERROR] H={H} is out of range. Should be between 1 and 7."
        
        # Check for exact match
        exact_match = self.t3[self.t3["H"] == H]
        if not exact_match.empty:
            print(f"[INFO] Found exact match in table3 for H={H}")
            return exact_match.iloc[0]
        
        # Interpolate between closest values
        lower = self.t3[self.t3["H"] < H]
        upper = self.t3[self.t3["H"] > H]
        
        if lower.empty or upper.empty:
            return f"[ERROR] Cannot interpolate for H={H} in table3"
        
        lower_row = lower.iloc[-1]
        upper_row = upper.iloc[0]
        
        lower_H = lower_row['H']
        upper_H = upper_row['H']
        weight = (H - lower_H) / (upper_H - lower_H)
        
        # Linear interpolation
        interpolated_row = lower_row + weight * (upper_row - lower_row)
        
        print(f"[INFO] Interpolated in table3 for H={H} (between {lower_H} and {upper_H})")
        
        return interpolated_row
    
    def find_in_table4(self, D: float) -> Union[pd.Series, str]:
        """
        Find extra position parameters for multi-opening culverts in table4.
        
        This table contains additional position 11 and 12 data for n>1 culverts.
        
        Args:
            D: Diameter in meters
        
        Returns:
            pd.Series with extra position data, or error string
        """
        mask = abs(self.t4["D"] - D) < 0.001
        choice = self.t4[mask]
        
        if choice.empty:
            return f"[ERROR] No extra position data found in table4 for D={D}"
        
        print(f"[INFO] Found extra position data in table4 for D={D}")
        return choice.iloc[0]
