"""
Generic Data Processor
Processes CSV files with Point, Station, Offset and Elevation data into generic format.

Refactored from Generic_DataLoader_V4.py for better modularity and maintainability.
"""

import pandas as pd
import numpy as np
import os
from sklearn.svm import SVC
from typing import Tuple, List


class GenericProcessor:
    """
    Process CSV files containing Point, Station, Offset and Elevation data.
    
    Output format:
        chainage    station_no
        Offset      Elevation
        Offset      Elevation
        ...
    """
    
    CODE_NAME = "Generic"
    
    def __init__(self, file_path: str):
        """
        Initialize the processor with a CSV file.
        
        Args:
            file_path: Path to the input CSV file
        """
        self.file_path = file_path
        self.raw_data = pd.read_csv(file_path)
        self.data = None
        self.generic = None
        self.center_points = None
        self.map_data = None
        self.zeros = []
        self.outrange_id = []
        
        self._clean_data()
    
    def _clean_data(self) -> None:
        """Clean and prepare the raw data for processing."""
        self.data = self.raw_data.copy()
        self.data.columns = self.data.loc[12]
        self.data = self.data.iloc[13:, :-1]
        self.data.index = range(len(self.data))
        
        self._remove_nan()
        self._correct_station_values()
        self._correct_elevation_values()
        self._correct_offset_values()
    
    def _remove_nan(self) -> None:
        """Remove rows with NaN values and 'Out of range' stations."""
        self.data.dropna(inplace=True)
        outranges = self.data[self.data["Station"] == "Out of range"].index
        self.outrange_id = list(self.data.loc[outranges]["Point"])
        self.data.drop(outranges, inplace=True)
    
    def _correct_station_values(self) -> None:
        """Convert station values to float format."""
        def station_apply(x):
            if "+" in str(x):
                return float("".join(str(x).split("+")))
            else:
                return float("-" + str(x))
        
        self.data["Station"] = self.data["Station"].apply(station_apply)
    
    def _correct_offset_values(self) -> None:
        """Convert offset values to float format."""
        self.data["Offset"] = self.data["Offset"].apply(lambda x: float(str(x)[:-1]))
    
    def _correct_elevation_values(self) -> None:
        """Convert elevation values to float format."""
        self.data["Elevation"] = self.data["Elevation"].apply(
            lambda x: float("".join(str(x)[:-1].split(",")))
        )
    
    def _find_center_of_clusters(self, epsilon: float, round_limit: float) -> None:
        """
        Find cluster centers based on station and offset values.
        
        Args:
            epsilon: Threshold for considering offsets as centered
            round_limit: Rounding limit for station values
        """
        # Find center points (points with offset close to 0)
        center_points = self.data[np.abs(self.data["Offset"]) < epsilon].copy()
        
        # Round station values based on limit
        center_points["Station"] = center_points["Station"].apply(
            lambda x: x if round_limit <= x % 10 <= (10 - round_limit) 
            else int(round(x / 10) * 10)
        )
        
        self.center_points = center_points
        
        # Prepare training data for SVM clustering
        x_train = center_points[["Station"]].values
        y_train = center_points.index
        x_total = self.data[["Station"]].values
        
        print(f"Training SVM with {len(y_train)} center points...")
        
        # Train SVM model for clustering
        svm_model = SVC(kernel="rbf", C=1)
        svm_model.fit(x_train, y_train)
        
        # Predict clusters for all data points
        predicted_clusters = svm_model.predict(x_total)
        self.data["Cluster"] = predicted_clusters
        
        print("Clustering completed successfully")
    
    def _generic_format(self, epsilon: float) -> pd.DataFrame:
        """
        Convert data into generic format.
        
        Args:
            epsilon: Threshold for considering offsets as centered
            
        Returns:
            DataFrame in generic format
        """
        result = []
        map_data = []
        
        unique_clusters = self.center_points.sort_values(by="Station").index
        
        for cluster_id in unique_clusters:
            cluster_data = self.data[self.data["Cluster"] == cluster_id]
            center_station = self.center_points.loc[cluster_id, 'Station']
            cluster_data = cluster_data.sort_values(by='Offset')
            
            if len(cluster_data) == 0:
                self.zeros.append(center_station)
                continue
            
            result.append(["chainage", center_station])
            
            # Count and find points near centerline
            number_of_zeros = 0
            lowest_offset = float("inf")
            
            for _, row in cluster_data.iterrows():
                if abs(row["Offset"]) < epsilon:
                    number_of_zeros += 1
                    if lowest_offset > abs(row["Offset"]):
                        lowest_offset = abs(row["Offset"])
            
            # Add points to result
            if number_of_zeros < 2:
                for _, row in cluster_data.iterrows():
                    offset = 0 if abs(row["Offset"]) < epsilon else row["Offset"]
                    result.append([offset, row["Elevation"]])
                    map_data.append([center_station, offset, row["Elevation"]])
            else:
                for _, row in cluster_data.iterrows():
                    offset = 0 if abs(row["Offset"]) - lowest_offset <= 0 else row["Offset"]
                    result.append([offset, row["Elevation"]])
                    map_data.append([center_station, offset, row["Elevation"]])
        
        self.map_data = pd.DataFrame(map_data, columns=["Station", "Offset", "Elevation"])
        return pd.DataFrame(result)
    
    def fit(self, epsilon: float, round_limit: float) -> None:
        """
        Process the data to find clusters and convert to generic format.
        
        Args:
            epsilon: Threshold for considering offsets as centered (meters)
            round_limit: Rounding limit for station values (meters)
        """
        print(f"Processing with epsilon={epsilon}, round_limit={round_limit}")
        self._find_center_of_clusters(epsilon=epsilon, round_limit=round_limit)
        self.generic = self._generic_format(epsilon=epsilon)
        print(f"Processing complete. Generated {len(self.generic)} rows")
    
    def save_files(self, output_dir: str) -> Tuple[str, str, str, str]:
        """
        Save processed data to files.
        
        Args:
            output_dir: Directory to save output files
            
        Returns:
            Tuple of (csv_file, txt_file, outranges_file, zeros_file) paths
        """
        if self.generic is None:
            raise ValueError("Data not processed yet. Call fit() first.")
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(self.file_path)
        base_name_without_ext = os.path.splitext(base_name)[0]
        
        # Save CSV file
        csv_file = os.path.join(output_dir, f"{self.CODE_NAME}_{base_name}")
        self.generic.to_csv(csv_file, index=False, header=False)
        
        # Save text file
        txt_file = os.path.join(output_dir, f"{self.CODE_NAME}_{base_name_without_ext}.txt")
        with open(txt_file, "w") as file:
            for _, row in self.generic.iterrows():
                file.write(f"{row[0]}\t{row[1]}\n")
        
        # Save out-of-range points file
        outranges_file = os.path.join(
            output_dir, 
            f"{self.CODE_NAME}_{base_name_without_ext}_outranges.txt"
        )
        with open(outranges_file, "w") as file:
            file.write("Out of range points which have no data in the input file.\n")
            file.write("Point\n")
            for point in self.outrange_id:
                file.write(f"{point}\n")
        
        # Save zeros/omitted stations file
        zeros_file = os.path.join(output_dir, f"{self.CODE_NAME}_{base_name_without_ext}_zeros.txt")
        with open(zeros_file, "w") as file:
            file.write("Stations with no members that were omitted.\n")
            file.write("This can occur when two stations are too close or epsilon threshold is not accurate.\n")
            file.write("Station\n")
            for station in self.zeros:
                file.write(f"{station}\n")
        
        print(f"Files saved to {output_dir}")
        return csv_file, txt_file, outranges_file, zeros_file
    
    def get_results(self) -> dict:
        """
        Get processing results summary.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_points': len(self.data),
            'clusters_found': len(self.center_points) if self.center_points is not None else 0,
            'outrange_points': len(self.outrange_id),
            'omitted_stations': len(self.zeros),
            'output_rows': len(self.generic) if self.generic is not None else 0
        }


# Backward compatibility alias
Generic_DataLoader = GenericProcessor
