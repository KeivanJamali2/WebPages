"""
CSDP Data Processor
Processes Cross-Section Design Profile data from multiple input files.

Refactored from CSDP_DataLoader.py for better modularity and maintainability.
"""

import pandas as pd
import os
from typing import Tuple, List


class CSDPProcessor:
    """
    Process CSDP (Cross-Section Design Profile) data from three input files:
    - Main file: Primary cross-section data
    - Second ground file: Secondary ground boundary data
    - Pashneh file: Additional boundary points (shoulder/edge data)
    """
    
    CODE_NAME = "CSDP"
    
    def __init__(self, main_file: str, second_ground_file: str, pashneh_file: str):
        """
        Initialize the CSDP processor.
        
        Args:
            main_file: Path to main cross-section CSV file
            second_ground_file: Path to second ground CSV file
            pashneh_file: Path to pashneh (shoulder) CSV file
        """
        self.main_file_path = main_file
        self.second_ground_file_path = second_ground_file
        self.pashneh_file_path = pashneh_file
        
        # Load raw data
        self.raw_data_main = pd.read_csv(main_file, header=0)
        self.raw_data_pashneh = pd.read_csv(pashneh_file, header=3)
        self.raw_data_second = pd.read_csv(second_ground_file, header=3)
        
        # Processing results
        self.data = None
        self.left_modes = None
        self.result_without_additionals = None
        self.CSDP = None
        self.columns_for_result = None
        self.left_bound = None
        self.right_bound = None
        self.additionals = None
        
        # Initialize processing
        self._setup_raw_data()
        self.left_bound, self.right_bound, self.additionals = self._create_boundaries()
    
    def _setup_raw_data(self) -> None:
        """Setup column names and structure for main data."""
        # Count left and right columns
        counted_L = -1
        counted_R = 0
        
        for col in self.raw_data_main.columns:
            if "L" in col:
                counted_L += 1
            if "R" in col:
                counted_R += 1
        
        # Create column names
        column = ["No", "Distance"]
        column_for_result = ["No", "Distance", f"L{counted_L+3}", f"L{counted_L+2}", f"L{counted_L+1}"]
        
        self.left_modes = []
        for i in range(counted_L, 0, -1):
            column.append(f"L{i}")
            column_for_result.append(f"L{i}")
            self.left_modes.append(f"L{i}")
        
        column.append("CL")
        column_for_result.append("CL")
        
        for i in range(1, counted_R + 1):
            column.append(f"R{i}")
            column_for_result.append(f"R{i}")
        
        column.append("end")
        column_for_result.extend([f"R{counted_R+1}", f"R{counted_R+2}", f"R{counted_R+3}", "end"])
        
        self.raw_data_main.columns = column
        self.columns_for_result = column_for_result
    
    def _get_end_nodes(self) -> pd.DataFrame:
        """
        Create DataFrame for additional end nodes from pashneh data.
        
        Returns:
            DataFrame with empty placeholders for additional nodes
        """
        temp_additional = ["L3", "L4", "L5", "R3", "R4", "R5"]
        additional = [add for add in temp_additional if add in self.raw_data_pashneh.columns]
        
        return pd.DataFrame(
            "empty",
            index=range(len(self.raw_data_main)),
            columns=additional
        )
    
    def _create_boundaries(self) -> Tuple[List, List, pd.DataFrame]:
        """
        Create left and right boundaries and additional points.
        
        Returns:
            Tuple of (left_bound, right_bound, additionals)
        """
        additionals = self._get_end_nodes()
        bound_l = []
        bound_r = []
        
        # Process each pair of rows (offset and elevation)
        for row in range(0, len(self.raw_data_second), 2):
            done = False
            
            # Find matching distance in main data
            for row_temp in range(0, len(self.raw_data_main), 2):
                if self.raw_data_second["Distance"][row] == self.raw_data_main["Distance"][row_temp]:
                    # Add boundaries
                    bound_l.append(self.raw_data_second["L3"][row])
                    bound_l.append(self.raw_data_second["L3"][row + 1])
                    bound_r.append(self.raw_data_second["R3"][row])
                    bound_r.append(self.raw_data_second["R3"][row + 1])
                    
                    # Add pashneh data
                    additionals.loc[row] = self.raw_data_pashneh[additionals.columns].loc[row]
                    additionals.loc[row + 1] = self.raw_data_pashneh[additionals.columns].loc[row + 1]
                    done = True
                    break
            
            if not done:
                print(f"Warning: No match found for row {row}")
                bound_l.extend(["empty", "empty"])
                bound_r.extend(["empty", "empty"])
        
        additionals.fillna("empty", inplace=True)
        return bound_l, bound_r, additionals
    
    def _use_bounds(self) -> pd.DataFrame:
        """
        Apply boundaries to filter data points.
        
        Returns:
            DataFrame with filtered results
        """
        result = pd.DataFrame(
            "empty",
            index=self.raw_data_main.index,
            columns=self.columns_for_result
        )
        
        # Process each pair of rows
        for i in range(0, len(self.raw_data_main), 2):
            if self.left_bound[i]:
                # Check each node
                for j in range(2, len(self.raw_data_main.loc[i]) - 1):
                    node = self.raw_data_main.iloc[i, j]
                    col_name = self.raw_data_main.columns[j]
                    
                    # Handle left side
                    if col_name in self.left_modes:
                        if (self.left_bound[i] - node) >= 0.01:
                            result.iloc[i, j + 3] = node
                            result.iloc[i + 1, j + 3] = self.raw_data_main.iloc[i + 1, j]
                        else:
                            result.iloc[i, j + 3] = "empty"
                            result.iloc[i + 1, j + 3] = "empty"
                    
                    # Handle right side
                    elif "R" in col_name:
                        if (node - self.right_bound[i]) <= 0.01:
                            result.iloc[i, j + 3] = node
                            result.iloc[i + 1, j + 3] = self.raw_data_main.iloc[i + 1, j]
                        else:
                            result.iloc[i, j + 3] = "empty"
                            result.iloc[i + 1, j + 3] = "empty"
        
        # Copy standard columns
        result["CL"] = self.raw_data_main["CL"]
        result["Distance"] = self.raw_data_main["Distance"]
        result["No"] = self.raw_data_main["No"]
        result["end"] = 0
        
        self.result_without_additionals = result
        self.CSDP = result.copy()
        return result
    
    def _add_additional_bounds(self) -> pd.DataFrame:
        """
        Add additional boundary points from pashneh data.
        
        Returns:
            Updated CSDP DataFrame
        """
        for row in range(0, len(self.additionals), 2):
            for col in range(len(self.additionals.columns)):
                if self.additionals.iloc[row, col] != "empty":
                    col_name = self.additionals.columns[col]
                    side = col_name[0]  # 'R' or 'L'
                    
                    # Find first empty slot on the appropriate side
                    for i in range(1, 11):
                        target_col = f"{side}{i}"
                        if target_col in self.CSDP.columns:
                            if self.CSDP.loc[row][target_col] == "empty":
                                col_i = list(self.CSDP.columns).index(target_col)
                                self.CSDP.iloc[row, col_i] = self.additionals.iloc[row, col]
                                self.CSDP.iloc[row + 1, col_i] = self.additionals.iloc[row + 1, col]
                                break
        
        return self.CSDP
    
    def _add_left_right_bounds(self) -> None:
        """Add left and right boundary points to CSDP data."""
        for row in range(0, len(self.left_bound), 2):
            # Add right boundary
            if self.right_bound[row] != "empty":
                for i in range(1, 11):
                    target_col = f"R{i}"
                    if target_col in self.CSDP.columns:
                        if self.CSDP.loc[row][target_col] == "empty":
                            col_i = list(self.CSDP.columns).index(target_col)
                            self.CSDP.iloc[row, col_i] = self.right_bound[row]
                            self.CSDP.iloc[row + 1, col_i] = self.right_bound[row + 1]
                            break
            
            # Add left boundary
            if self.left_bound[row] != "empty":
                for i in range(1, 11):
                    target_col = f"L{i}"
                    if target_col in self.CSDP.columns:
                        if self.CSDP.loc[row][target_col] == "empty":
                            col_i = list(self.CSDP.columns).index(target_col)
                            self.CSDP.iloc[row, col_i] = self.left_bound[row]
                            self.CSDP.iloc[row + 1, col_i] = self.left_bound[row + 1]
                            break
    
    def fit(self) -> pd.DataFrame:
        """
        Process all CSDP data and create final result.
        
        Returns:
            Processed CSDP DataFrame
        """
        print("Processing CSDP data...")
        
        # Apply boundaries
        self.result_without_additionals = self._use_bounds()
        
        # Add additional points
        self._add_left_right_bounds()
        result = self._add_additional_bounds()
        
        # Clean up result
        result.fillna("", inplace=True)
        result.replace("empty", "", inplace=True)
        
        # Remove empty columns
        for col in result.columns:
            if not result[col].astype(str).sum():
                result.drop(columns=col, inplace=True)
        
        print("CSDP processing complete")
        return result
    
    def save_files(self, output_dir: str) -> str:
        """
        Save processed CSDP data to CSV file.
        
        Args:
            output_dir: Directory to save output file
            
        Returns:
            Path to saved CSV file
        """
        if self.CSDP is None:
            raise ValueError("Data not processed yet. Call fit() first.")
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(self.main_file_path)
        base_name_without_ext = os.path.splitext(base_name)[0]
        
        # Save CSV file
        csv_file = os.path.join(output_dir, f"{self.CODE_NAME}_{base_name}")
        
        # Simplify column names
        columns = list(self.CSDP.columns[0:2]) + [
            i[0] if i != "CL" else "CL" 
            for i in self.CSDP.columns[2:]
        ]
        self.CSDP.columns = columns
        
        self.CSDP.to_csv(csv_file, index=False, header=True)
        
        print(f"CSDP file saved to {csv_file}")
        return csv_file
    
    def get_results(self) -> dict:
        """
        Get processing results summary.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_sections': len(self.raw_data_main) // 2,
            'left_columns': len(self.left_modes),
            'output_columns': len(self.CSDP.columns) if self.CSDP is not None else 0
        }


# Backward compatibility alias
CSDP_DataLoader = CSDPProcessor
