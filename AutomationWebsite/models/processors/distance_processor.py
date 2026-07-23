"""
Distance Processor
Filters cross-section data based on distance from centerline.

Refactored from Delete_distance_from_centerline.py for better modularity.
"""

import pandas as pd
import os
from typing import Tuple


class DistanceProcessor:
    """
    Filter cross-section data by removing points outside specified distance bounds.
    Keeps only points within left_bound and right_bound distance from centerline.
    """
    
    CODE_NAME = "delete_distance_from_centerline"
    
    def __init__(self, file_path: str, left_bound: float, right_bound: float):
        """
        Initialize the distance processor.
        
        Args:
            file_path: Path to input CSV file
            left_bound: Left side distance bound (negative value)
            right_bound: Right side distance bound (positive value)
        """
        self.file_path = file_path
        self.left_bound = left_bound
        self.right_bound = right_bound
        
        self.raw_data_main = pd.read_csv(file_path, header=0)
        self.data = None
        self.left_modes = None
        self.CSDP = None
        self.result_without_additionals = None
        self.columns_for_result = None
        
        self._setup_raw_data()
    
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
        column_for_result = ["No", "Distance"]
        
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
        column_for_result.append("end")
        
        self.raw_data_main.columns = column
        self.columns_for_result = column_for_result
    
    def _use_bounds(self) -> pd.DataFrame:
        """
        Apply distance bounds to filter data points.
        
        Returns:
            DataFrame with filtered results
        """
        result = pd.DataFrame(
            "empty",
            index=self.raw_data_main.index,
            columns=self.columns_for_result
        )
        
        # Process each pair of rows (offset and elevation)
        for i in range(0, len(self.raw_data_main), 2):
            for j in range(2, len(self.raw_data_main.loc[i]) - 1):
                node = self.raw_data_main.iloc[i, j]
                col_name = self.raw_data_main.columns[j]
                
                # Handle left side
                if col_name in self.left_modes:
                    if (self.left_bound - node) <= 0:
                        result.iloc[i, j] = node
                        result.iloc[i + 1, j] = self.raw_data_main.iloc[i + 1, j]
                    else:
                        result.iloc[i, j] = "empty"
                        result.iloc[i + 1, j] = "empty"
                
                # Handle right side
                elif "R" in col_name:
                    if (node - self.right_bound) >= 0:
                        result.iloc[i, j] = node
                        result.iloc[i + 1, j] = self.raw_data_main.iloc[i + 1, j]
                    else:
                        result.iloc[i, j] = "empty"
                        result.iloc[i + 1, j] = "empty"
        
        # Copy standard columns
        result["CL"] = self.raw_data_main["CL"]
        result["Distance"] = self.raw_data_main["Distance"]
        result["No"] = self.raw_data_main["No"]
        result["end"] = "empty"
        
        self.result_without_additionals = result
        self.CSDP = result.copy()
        return result
    
    @staticmethod
    def _shift_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Shift empty columns to maintain continuity in data.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with shifted empty columns
        """
        cols = df.columns
        l_cols = [col for col in cols if col.startswith('L')]
        r_cols = [col for col in cols if col.startswith('R')]
        
        def shift_row(row, cols, direction):
            """Shift values in a row to fill empty positions."""
            first_empty = None
            
            if direction == "right":
                for col in reversed(cols):
                    if first_empty is None and row[col] == 'empty':
                        first_empty = col
                    elif first_empty is not None:
                        row[first_empty] = row[col]
                        first_empty = col
                if first_empty is not None:
                    row[first_empty] = "empty"
            
            elif direction == "left":
                for col in cols:
                    if first_empty is None and row[col] == 'empty':
                        first_empty = col
                    elif first_empty is not None:
                        row[first_empty] = row[col]
                        first_empty = col
                if first_empty is not None:
                    row[first_empty] = "empty"
            
            return row
        
        def process_row(row):
            """Process a single row to shift empty columns."""
            # Process left side columns
            l_continuous_empty = [col for col in l_cols if row[col] == 'empty']
            if len(l_continuous_empty) > 0 and l_continuous_empty[-1] == l_cols[-1]:
                row = shift_row(row, l_cols, 'right')
            
            # Process right side columns
            r_continuous_empty = [col for col in r_cols if row[col] == 'empty']
            if len(r_continuous_empty) > 0 and r_continuous_empty[0] == r_cols[0]:
                row = shift_row(row, r_cols, 'left')
            
            return row
        
        # Apply processing multiple times to ensure complete shifting
        for _ in range(10):
            df = df.apply(process_row, axis=1)
        
        return df
    
    def fit(self) -> pd.DataFrame:
        """
        Process data by applying bounds and shifting empty columns.
        
        Returns:
            Processed DataFrame
        """
        print(f"Processing with bounds: left={self.left_bound}, right={self.right_bound}")
        
        result = self._use_bounds()
        result.fillna("", inplace=True)
        result = self._shift_empty_columns(result)
        result.replace("empty", "", inplace=True)
        
        self.CSDP = result
        print("Distance filtering complete")
        return self.CSDP
    
    def save_files(self, output_dir: str) -> str:
        """
        Save processed data to CSV file.
        
        Args:
            output_dir: Directory to save output file
            
        Returns:
            Path to saved CSV file
        """
        if self.CSDP is None:
            raise ValueError("Data not processed yet. Call fit() first.")
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(self.file_path)
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
        
        print(f"File saved to {csv_file}")
        return csv_file
    
    def get_results(self) -> dict:
        """
        Get processing results summary.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_sections': len(self.raw_data_main) // 2,
            'left_bound': self.left_bound,
            'right_bound': self.right_bound,
            'output_columns': len(self.CSDP.columns) if self.CSDP is not None else 0
        }


# Backward compatibility alias
Delete_Distance_From_Centerline = DistanceProcessor
