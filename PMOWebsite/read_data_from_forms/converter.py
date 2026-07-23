"""
Excel Converter for Daily Forms

This module reads an Excel file with multiple sheets (one for each day of the month,
possibly including both daily and nightly shifts). Each sheet may contain multiple
tables, which are extracted as separate DataFrames.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np


def find_tables_in_sheet(df: pd.DataFrame, min_rows: int = 2, min_cols: int = 2) -> List[Tuple[int, int, int, int]]:
    """
    Find distinct tables within a sheet by detecting blocks of non-empty cells.
    
    Args:
        df: The raw DataFrame from the sheet
        min_rows: Minimum number of rows for a valid table
        min_cols: Minimum number of columns for a valid table
    
    Returns:
        List of tuples (start_row, end_row, start_col, end_col) for each table
    """
    # Create a mask of non-empty cells
    mask = df.notna() & df.map(lambda x: str(x).strip() != '' if pd.notna(x) else False)
    
    tables = []
    visited = np.zeros(mask.shape, dtype=bool)
    
    for i in range(len(df)):
        for j in range(len(df.columns)):
            if mask.iloc[i, j] and not visited[i, j]:
                # Found a potential table start, expand to find boundaries
                start_row, start_col = i, j
                end_row, end_col = i, j
                
                # Expand right
                while end_col < len(df.columns) - 1:
                    # Check if there's data in the next column within a reasonable range
                    col_has_data = mask.iloc[start_row:min(start_row + 50, len(df)), end_col + 1].any()
                    if col_has_data:
                        end_col += 1
                    else:
                        break
                
                # Expand down
                while end_row < len(df) - 1:
                    # Check if there's data in the next row within the column range
                    row_has_data = mask.iloc[end_row + 1, start_col:end_col + 1].any()
                    if row_has_data:
                        end_row += 1
                    else:
                        break
                
                # Mark cells as visited
                visited[start_row:end_row + 1, start_col:end_col + 1] = True
                
                # Only add if it meets minimum size requirements
                if (end_row - start_row + 1) >= min_rows and (end_col - start_col + 1) >= min_cols:
                    tables.append((start_row, end_row, start_col, end_col))
    
    return tables


def extract_table(df: pd.DataFrame, start_row: int, end_row: int, 
                  start_col: int, end_col: int, use_first_row_as_header: bool = True,
                  is_first_table: bool = False) -> pd.DataFrame | List[pd.DataFrame]:
    """
    Extract a table from the sheet DataFrame.
    
    Args:
        df: The raw DataFrame from the sheet
        start_row: Starting row index
        end_row: Ending row index (inclusive)
        start_col: Starting column index
        end_col: Ending column index (inclusive)
        use_first_row_as_header: Whether to use the first row as column headers
        is_first_table: If True, applies special processing for the first table:
                        removes rows 0, 1, 2, 4 and uses row 3 as header (0-indexed),
                        then splits at column index 5 into two tables
    
    Returns:
        Extracted DataFrame, or list of two DataFrames if is_first_table=True
    """
    table = df.iloc[start_row:end_row + 1, start_col:end_col + 1].copy()
    table = table.reset_index(drop=True)
    
    if is_first_table and len(table) > 5:
        # Special handling for first table:
        # Remove first 3 rows (0, 1, 2) and row 5 (index 4), use row 4 (index 3) as header
        new_header = table.iloc[4].astype(str).str.strip()
        table = table.iloc[6:]
        table.columns = new_header
        table = table.reset_index(drop=True)
        
        # Split at column index 5 into two tables
        # First table: columns 0-4 (indices 0, 1, 2, 3, 4)
        # Second table: columns 5+ (index 5 onwards)
        split_col_idx = 5
        if len(table.columns) > split_col_idx:
            table_left = table.iloc[:, :split_col_idx].copy()
            table_right = table.iloc[:, split_col_idx:].copy()
            
            # Split table_left (first table) at row index 31
            # First table: rows 0-31 (inclusive)
            # Third table: rows 32+ 
            split_row_idx = 32  # rows 0-31 means up to but not including 32
            table_1 = table_left.iloc[:split_row_idx].copy()
            table_3 = table_left.iloc[split_row_idx:].copy().reset_index(drop=True)

            try:
                new_header = table_3.iloc[2].astype(str).str.strip()
                table_3 = table_3.iloc[3:].reset_index(drop=True)
                table_3.columns = list(new_header)
            except:
                print("Error processing header for table 3")
                table_3 = table_3.iloc[3:].reset_index(drop=True)
            
            # For table_right (second table), keep only rows up to index 23 (inclusive)
            # Remove rows after index 23
            table_right_trimmed = table_right.iloc[:24].copy()  # rows 0-23 (inclusive)
            
            # Split table_right_trimmed at column index 6
            # Table 2: columns 0-5 (indices 0, 1, 2, 3, 4, 5)
            # Table 4: columns 6+ (index 6 onwards)
            split_col_idx_2 = 6
            table_2 = table_right_trimmed.iloc[:, :split_col_idx_2].copy()
            table_4 = table_right_trimmed.iloc[:, split_col_idx_2:].copy()
            try:
                new_header = table_4.iloc[0].astype(str).str.strip()
                table_4 = table_4.iloc[1:].reset_index(drop=True)
                table_4.columns = list(new_header)
            except:
                print("Error processing header for table 4")
                table_4 = table_4.iloc[1:].reset_index(drop=True)
                
            table_1 = table_1.dropna(how='all')
            table_2 = table_2.dropna(how='all')
            table_3 = table_3.dropna(how='all')
            table_4 = table_4.dropna(how='all')
            
            return [table_1, table_2, table_3, table_4]
    
    return table


def read_excel_with_multiple_tables(
    file_path: str | Path,
    min_rows: int = 2,
    min_cols: int = 2,
    use_first_row_as_header: bool = True
) -> Dict[str, List[pd.DataFrame]]:
    """
    Read an Excel file with multiple sheets, extracting multiple tables from each sheet.
    
    Args:
        file_path: Path to the Excel file
        min_rows: Minimum number of rows for a valid table
        min_cols: Minimum number of columns for a valid table
        use_first_row_as_header: Whether to use the first row of each table as column headers
    
    Returns:
        Dictionary where keys are sheet names and values are lists of DataFrames (one per table)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    # Read all sheets without header processing
    xlsx = pd.ExcelFile(file_path)
    sheet_names = xlsx.sheet_names
    
    result: Dict[str, List[pd.DataFrame]] = {}
    
    for sheet_name in sheet_names:
        # Read sheet without header to get raw data
        raw_df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
        
        # Find all tables in the sheet
        table_bounds = find_tables_in_sheet(raw_df, min_rows, min_cols)
        
        tables = []
        for idx, (start_row, end_row, start_col, end_col) in enumerate(table_bounds):
            is_first_table = (idx == 0)
            extracted = extract_table(raw_df, start_row, end_row, start_col, end_col, 
                                  use_first_row_as_header, is_first_table)
            # Handle case where first table is split into two tables
            if isinstance(extracted, list):
                tables.extend(extracted)
            else:
                tables.append(extracted)
        
        result[sheet_name] = tables
    
    xlsx.close()
    
    
    return result


def get_sheet_summary(data: Dict[str, List[pd.DataFrame]]) -> pd.DataFrame:
    """
    Create a summary DataFrame showing the number of tables and their sizes for each sheet.
    
    Args:
        data: Dictionary from read_excel_with_multiple_tables
    
    Returns:
        Summary DataFrame
    """
    summary_rows = []
    for sheet_name, tables in data.items():
        for idx, table in enumerate(tables):
            summary_rows.append({
                'sheet_name': sheet_name,
                'table_index': idx + 1,
                'rows': len(table),
                'columns': len(table.columns),
                'column_names': ', '.join(table.columns.astype(str)[:5]) + ('...' if len(table.columns) > 5 else '')
            })
    
    return pd.DataFrame(summary_rows)

