import pandas as pd

class Human_Resources:
    def __init__(self):
        self.columns = ["post", "present", "vacation", "total"] # سمت حاضر مرخصی مجموع
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, item: str, d: list) -> None:
        "d -> 3 elements"
        self.data.loc[len(self.data)] = [item] + d
    
    def sum_up(self):
        self.data.loc[len(self.data)] = ["total"] + [self.data['present'].sum(), self.data['vacation'].sum(), self.data['total'].sum()]
        

class Tools_And_Equipments:
    def __init__(self):
        self.columns = ["tools_and_equipment", "count", "active", "repair", "diactive"] # ماشین الات، تعداد، فعال، تعمیر، غیرفعال
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, item: str, d: list) -> None:
        "d -> 4 elements"
        self.data.loc[len(self.data)] = [item] + d
        
    def sum_up(self):
        self.data.loc[len(self.data)] = ["total"] + [self.data['present'].sum(), self.data['vacation'].sum(), self.data['total'].sum()]
        
class Incoming_Materials_And_Goods:
    def __init__(self):
        self.columns = ["materials_and_goods", "daily", "unit"]
        self.data = pd.DataFrame(columns=self.columns)

    def add_item(self, item: str, d: list) -> None:
        "d -> 2 elements"
        self.data.loc[len(self.data)] = [item] + d
        
    # def sum_up(self):
    #     self.data.loc[len(self.data)] = ["total"] + [self.data['present'].sum(), self.data['vacation'].sum(), self.data['total'].sum()]
        
class Climate_Condition:
    def __init__(self):
        self.columns = ["temperature", "humidity", "sunny", "rainy", "windy", "stormy"]
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 6 elements"
        self.data.loc[len(self.data)] = d
        
class Daily_Activity_Report:
    def __init__(self):
        self.columns = ["description", "location", "unit", "daily_quantity", "total_quantity"]
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 5 elements"
        self.data.loc[len(self.data)] = d
        
class Project_Issues:
    def __init__(self):
        self.columns = ["issue"]
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 1 elements"
        self.data.loc[len(self.data)] = d


class Daily_Form:
    def __init__(self):
        self.human_resources = Human_Resources()
        self.tools_and_equipments = Tools_And_Equipments()
        self.incoming_materials_and_goods = Incoming_Materials_And_Goods()
        self.climate_condition = Climate_Condition()
        self.daily_activity_report = Daily_Activity_Report()
        self.project_issues = Project_Issues()
        
    def add_to_table(self, table_name: str, d: list, item: str = None) -> None:
        if table_name == "human_resources":
            self.human_resources.add_item(item, d)
        elif table_name == "tools_and_equipments":
            self.tools_and_equipments.add_item(item, d)
        elif table_name == "incoming_materials_and_goods":
            self.incoming_materials_and_goods.add_item(item, d)
        elif table_name == "climate_condition":
            self.climate_condition.add_item(d)
        elif table_name == "daily_activity_report":
            self.daily_activity_report.add_item(d)
        elif table_name == "project_issues":
            self.project_issues.add_item(d)

