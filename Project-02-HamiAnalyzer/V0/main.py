from pathlib import Path
import time

class HamiWorks:
    LOGIN_URL = "https://mail.iau.ac.ir"
    USERNAME = "Manager105001@iau.ir"
    PASSWORD = "@Hamiyazd110"

    def __init__(self):
        self.name = "HamiWorks"
        self.version = "2.0"

    def greet(self):
        """
        This function will greet the user.
        """
        return f"Welcome to {self.name} version {self.version}!"
    
    def get_version(self):
        """
        This function will return the version of the package.
        """
        return self.version

    def reverse_names(self, OUTPUT_DIR:str):
        """This function will rename all the files in the output directory. All the second numbers in the file names will be reveresed
        to make the output as the oldest file having the lowest second number.
        params:
            OUTPUT_DIR: str, e.g. "/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data/"
        """
        import rename_file_V1
        rename_file_V1.main(OUTPUT_DIR, dry_run=False)

    def request_data_from_website(self, 
                                  START_DATE:str, 
                                  END_DATE:str, 
                                  OUTPUT_DIR:str, 
                                  i_value:int, 
                                  name_value:str, 
                                  CHROMEPATH:str):
        """This function will open the webbrowser and do all the stuf to save the files in the output directory.
        params:
            START_DATE: str, e.g. "1402/01/01"
            END_DATE: str, e.g. "1404/12/29"
            OUTPUT_DIR: str, e.g. "/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data/"
            i_value: int, e.g. 105001
            name_value: str, e.g. "حامی 001 واحد یزد"
            CHROMEPATH: str, e.g. "/home/keivan/drivers/chromedriver/chromedriver"
        """
        from get_data_V2 import main
        main(LOGIN_URL= self.LOGIN_URL,
             USERNAME= self.USERNAME,
             PASSWORD= self.PASSWORD,
             START_DATE= START_DATE,
             END_DATE= END_DATE,
             OUTPUT_DIR= OUTPUT_DIR,
             i_value= i_value,
             name_value= name_value,
             CHROMEPATH= CHROMEPATH,
        )


    def dataloader(self, 
                   hami_data_path:str, 
                   hami_output_path:str, 
                   i_values:list[int]):
        hami_data_path = Path(hami_data_path)
        hami_output_path = Path(hami_output_path)
        from DataLoader import Raw_Data, Loader, Express_Data
        raw_data = Raw_Data(folder_path=hami_data_path)
        loader = Loader(raw_data=raw_data)
        express = Express_Data()
        combined_dir = hami_output_path / "combined_output"
        hami_dir = hami_output_path / "hami_output"

        combined_dir.mkdir(parents=True, exist_ok=True)
        hami_dir.mkdir(parents=True, exist_ok=True)

        for file in combined_dir.iterdir():
            if file.is_file():
                file.unlink()

        for file in hami_dir.iterdir():
            if file.is_file():
                file.unlink()

        time.sleep(3)
        for i in i_values:
            j = 1
            while j < 1000:
                # print(f"Processing file_{i}_{j}.txt and workflow_{i}_{j}.txt")
                exist = loader.fit(file_name_number=f"{i}_{j}")
                if not exist:
                    j += 1
                    break
                express.fit(loader=loader)
                express.save_combined_data(file_name=hami_output_path / "combined_output" / f"combined_{i}_{j}.csv")
                express.save_hami_data(file_name=hami_output_path / "hami_output" / f"hami_{i}.csv")
                # print(f"Finished processing file_{i}_{j}.txt and workflow_{i}_{j}.txt")
                j += 1

    def analyzer(self, hami_output_path:str, extra_data_file_path:str, plot_folder:str, csv_folder:str, analysis_type:str="all"):
        """Run specific analysis or all analyses based on user request.
        
        params:
            hami_output_path: str, path to hami output folder
            extra_data_file_path: str, path to extra data file
            plot_folder: str, path to save plots
            csv_folder: str, path to save CSV files
            analysis_type: str, one of ["all", "total_messages", "top_student", "top_place", "top_employee", 
                            "common_titles", "response_time", "month_request", "month", "day", 
                            "messages_per_request", "place_by_field", "place_by_year", "place_by_edu_level"]
        """
        from DataAnalyzer import DataAnalyzer, DataLoader
        dataloader = DataLoader(hami_output_folder=hami_output_path, extra_data_file_path=extra_data_file_path)
        dataloader.load_data()
        analyzer = DataAnalyzer(dataloader, plot_folder=Path(plot_folder), csv_folder=Path(csv_folder))
        
        if analysis_type == "all":
            analyzer.total_messages_per_student(plot=True)
            analyzer.top_communicators(for_who="student")
            analyzer.top_communicators(for_who="place")
            analyzer.top_communicators(for_who="employee")
            analyzer.common_titles(plot_=True)
            analyzer.response_time_per_person(plot=True)
            analyzer.message_date_distribution(plot=True, per="month_request")
            analyzer.message_date_distribution(plot=True, per="month")
            analyzer.message_date_distribution(plot=True, per="day")
            analyzer.total_messages_per_request(plot=True)
            analyzer.place_filtered_by(by="field")
            analyzer.place_filtered_by(by="year")
            analyzer.place_filtered_by(by="educational_level")
        elif analysis_type == "total_messages":
            analyzer.total_messages_per_student(plot=True)
        elif analysis_type == "top_student":
            analyzer.top_communicators(for_who="student")
        elif analysis_type == "top_place":
            analyzer.top_communicators(for_who="place")
        elif analysis_type == "top_employee":
            analyzer.top_communicators(for_who="employee")
        elif analysis_type == "common_titles":
            analyzer.common_titles(plot_=True)
        elif analysis_type == "response_time":
            analyzer.response_time_per_person(plot=True)
        elif analysis_type == "month_request":
            analyzer.message_date_distribution(plot=True, per="month_request")
        elif analysis_type == "month":
            analyzer.message_date_distribution(plot=True, per="month")
        elif analysis_type == "day":
            analyzer.message_date_distribution(plot=True, per="day")
        elif analysis_type == "messages_per_request":
            analyzer.total_messages_per_request(plot=True)
        elif analysis_type == "place_by_field":
            analyzer.place_filtered_by(by="field")
        elif analysis_type == "place_by_year":
            analyzer.place_filtered_by(by="year")
        elif analysis_type == "place_by_edu_level":
            analyzer.place_filtered_by(by="educational_level")
        else:
            raise ValueError(f"Invalid analysis_type: {analysis_type}")