"""
Distance2 Processor
Extract and reorganize cross-section data from Excel files.

Processes Excel files with Project coordinates, extracting Distance, Offset, and Elevation data.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Tuple


class Distance2Processor:
    """
    Process Excel files containing cross-section data and extract Distance, Offset, Elevation.
    Supports column range specifications like 'L5:R3' or comma-separated columns 'L1, L2, R1'.
    """
    
    CODE_NAME = "distance2_processor"
    
    def __init__(self, file_path: str):
        """
        Initialize the distance2 processor.
        
        Args:
            file_path: Path to input Excel file with 'Project coordinates' sheet
        """
        self.file_path = file_path
        self.raw_data = None
        self.processed_data = None
        
        # Load the Excel data
        try:
            data = pd.read_excel(file_path, sheet_name="Project coordinates")
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}. Make sure the file has a 'Project coordinates' sheet.")
        
        # Find the header row (look for 'Distance' column)
        header_row = None
        for i in range(min(10, len(data))):  # Check first 10 rows
            row_values = data.iloc[i, :].astype(str).values
            if any('distance' in str(val).lower() for val in row_values):
                header_row = i
                break
        
        if header_row is None:
            raise ValueError("Could not find header row with 'Distance' column in first 10 rows")
        
        # Set headers and remove header rows
        headers = data.iloc[header_row, :].values
        data.columns = headers
        data = data.iloc[header_row + 1:].reset_index(drop=True)
        
        self.data = data
        print(f"Loaded data with columns: {list(data.columns)[:10]}...")  # Debug info
        
    def extract_columns(self, cols: str) -> list:
        """
        Extract column names from column specification string.
        
        Args:
            cols: Column specification in format:
                  - Range: 'L5:L1', 'L5:R3', 'R1:R5'
                  - List: 'L1, L2, R1, R2'
        
        Returns:
            List of column names to process
        
        Examples:
            'L5:L1' -> ['L5', 'L4', 'L3', 'L2', 'L1']
            'L3:R2' -> ['L3', 'L2', 'L1', 'R1', 'R2']
            'L1, L2, R1' -> ['L1', 'L2', 'R1']
        """
        if ":" in cols:
            start, stop = cols.split(":")
            start, stop = start.strip(), stop.strip()
            
            if start[0] == "L" and stop[0] == "L":
                # Left to left range (descending)
                col_names = [f"L{i}" for i in range(int(start[1:]), int(stop[1:]) - 1, -1)] + ["PL"]
            elif start[0] == "L" and stop[0] == "R":
                # Left to right range (crossing centerline)
                col_names = [f"L{i}" for i in range(int(start[1:]), 0, -1)] + \
                           ["PL"] + [f"R{i}" for i in range(1, int(stop[1:]) + 1)]
            elif start[0] == "R" and stop[0] == "R":
                # Right to right range (ascending)
                col_names = ["PL"] + [f"R{i}" for i in range(int(start[1:]), int(stop[1:]) + 1)]
            else:
                raise ValueError(f"Invalid column range: {cols}")
        else:
            # Comma-separated list
            col_names = [col.strip() for col in cols.split(",")]
        
        return col_names
    
    def fit(self, cols: str) -> pd.DataFrame:
        """
        Process the data by extracting specified columns and reorganizing.
        
        Args:
            cols: Column specification string (range or list)
        
        Returns:
            Processed DataFrame with Distance, Offset, Elevation columns
        """
        print(f"Processing columns: {cols}")
        
        col_names = self.extract_columns(cols)
        
        # Check if Distance column exists
        distance_col = None
        pl_col = None
        for col in self.data.columns:
            if 'distance' in str(col).lower():
                distance_col = col
                break
        
        if distance_col is None:
            raise ValueError(f"'Distance' column not found. Available columns: {list(self.data.columns)}")
        
        # Verify all requested columns exist
        missing_cols = []
        for col in col_names:
            if col not in self.data.columns:
                missing_cols.append(col)
        
        if missing_cols:
            raise ValueError(f"Columns {missing_cols} not found. Available columns: {list(self.data.columns)}")
        
        data = self.data[[distance_col] + col_names].copy()
        print(f"[DEBUG######] {data.head()}")
        new_data = pd.DataFrame(columns=["Distance", "Offset", "Elevation"])
        
        # Process rows (alternating offset and elevation)
        for i, row in data.iterrows():
            if i % 2 == 1:
                continue  # Skip elevation rows, they're processed with offset rows
            
            try:
                distance = float(row[distance_col])
            except (ValueError, TypeError):
                continue  # Skip invalid distance values
            
            print(col_names)
            for col in col_names:
                try:
                    # Handle left/right offset direction
                    if col[0] == "L":
                        offset = row[col]
                        offset = -abs(float(offset))
                        elevation = float(data.iloc[i + 1, :][col])
                    elif col[0] == "R":
                        offset = row[col]
                        offset = abs(float(offset))
                        elevation = float(data.iloc[i + 1, :][col])
                    elif col[0] == "P":
                        offset = 0.0
                        elevation = float(row[col])

                    # Add to results
                    new_data.loc[len(new_data)] = {
                        "Distance": distance,
                        "Offset": offset,
                        "Elevation": elevation
                    }
                except (ValueError, TypeError, IndexError) as e:
                    # Skip invalid values
                    continue
        
        if len(new_data) == 0:
            raise ValueError("No valid data points were extracted. Check your Excel file format.")
        
        # Sort by distance and offset - Attention
        
        
        # new_data.sort_values(by=["Distance", "Offset"], inplace=True)
        # new_data.reset_index(drop=True, inplace=True)
        
        # Ensure all columns are numeric
        new_data["Distance"] = pd.to_numeric(new_data["Distance"], errors='coerce')
        new_data["Offset"] = pd.to_numeric(new_data["Offset"], errors='coerce')
        new_data["Elevation"] = pd.to_numeric(new_data["Elevation"], errors='coerce')
        
        # Remove any rows with NaN values
        new_data.dropna(inplace=True)
        
        self.processed_data = new_data
        print(f"Processing complete: {len(new_data)} points extracted")
        
        return new_data
    
    def save_files(self, output_dir: str) -> str:
        """
        Save processed data to CSV file.
        
        Args:
            output_dir: Directory to save output file
            
        Returns:
            Path to saved CSV file
        """
        if self.processed_data is None:
            raise ValueError("Data not processed yet. Call fit() first.")
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(self.file_path)
        base_name_without_ext = os.path.splitext(base_name)[0]
        
        # Save CSV file
        csv_file = os.path.join(output_dir, f"{self.CODE_NAME}_{base_name_without_ext}.csv")
        self.processed_data.to_csv(csv_file, index=False)
        
        print(f"File saved to {csv_file}")
        return csv_file
    
    def get_results(self) -> dict:
        """
        Get processing results summary.
        
        Returns:
            Dictionary with processing statistics
        """
        if self.processed_data is None:
            return {'error': 'No data processed'}
        
        return {
            'total_points': int(len(self.processed_data)),
            'unique_distances': int(self.processed_data['Distance'].nunique()),
            'min_offset': float(self.processed_data['Offset'].min()),
            'max_offset': float(self.processed_data['Offset'].max()),
            'min_elevation': float(self.processed_data['Elevation'].min()),
            'max_elevation': float(self.processed_data['Elevation'].max())
        }


# Backward compatibility alias
Dataloader_Distance = Distance2Processor



