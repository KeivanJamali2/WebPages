import pandas as pd

class Date_And_Time:
    def __init__(self, document_code: str, date: str, day_of_week: str, work_shift: str):
        self.document_code = document_code
        self.date = date
        self.day_of_week = day_of_week
        self.work_shift = work_shift

class Human_Resources:
    def __init__(self):
        self.columns = ["post", "present", "vacation", "total", "notes"] # سمت حاضر مرخصی مجموع یادداشت
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, item: str, d: list) -> None:
        "d -> 4 elements (present, vacation, total, notes)"
        self.data.loc[len(self.data)] = [item] + d
    
    def sum_up(self):
        self.data.loc[len(self.data)] = ["total"] + [self.data['present'].sum(), self.data['vacation'].sum(), self.data['total'].sum(), ""]
        

class Tools_And_Equipments:
    def __init__(self):
        self.columns = ["tools_and_equipment", "count_active", "working_hours", "situation", "inactivity_reason"] # ماشین الات، تعداد، ساعت کار، وضعیت، دلیل غیرفعال
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, item: str, d: list) -> None:
        "d -> 4 elements (count_active, working_hours, situation, inactivity_reason)"
        self.data.loc[len(self.data)] = [item] + d

class Construction_Operations:
    def __init__(self):
        self.columns = ["operation_type", "start_km", "end_km", "unit", "progress", "map_number", "explanation"] # نوع عملیات، کیلومتر شروع، کیلومتر پایان، واحد، مقدار پیشرفت، شماره نقشه، توضیحات
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 7 elements (operation_type, start_km, end_km, unit, progress, map_number, explanation)"
        self.data.loc[len(self.data)] = d
        
class Incoming_Materials_And_Goods:
    def __init__(self):
        self.columns = ["material_type", "incoming_amount", "used_amount", "storage_place", "waybill_number"] # نوع مصالح، مقدار ورودی، مقدار مصرفی، محل نگهداری، شماره بارنامه
        self.data = pd.DataFrame(columns=self.columns)

    def add_item(self, d: list) -> None:
        "d -> 5 elements (material_type, incoming_amount, used_amount, storage_place, waybill_number)"
        self.data.loc[len(self.data)] = d
        
class Climate_Condition:
    def __init__(self):
        self.columns = ["min_temperature", "max_temperature", "humidity", "clear", "cloudy", "rainy", "foggy", "snowy"]
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 8 elements (min_temp, max_temp, humidity, clear, cloudy, rainy, foggy, snowy)"
        self.data.loc[len(self.data)] = d
        
class Project_Issues:
    def __init__(self):
        self.columns = ["issue_type", "effect", "location_station", "start_time", "end_time", "notes"] # نوع مشکل، تاثیر، محل (ایستگاه)، زمان شروع، زمان خاتمه، توضیحات
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 6 elements (issue_type, effect, location_station, start_time, end_time, notes)"
        self.data.loc[len(self.data)] = d

class Safety:
    def __init__(self):
        self.columns = ["safety_situation", "safety_inspection", "incident_occurred", "incident_explanation"] # وضعیت ایمنی، بازرسی ایمنی، حادثه رخ داده، توضیحات حادثه
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 4 elements (safety_situation, safety_inspection, incident_occurred, incident_explanation)"
        self.data.loc[len(self.data)] = d

class Event:
    def __init__(self):
        self.columns = ["event_name", "explanation"] # نام رویداد، توضیحات
        self.data = pd.DataFrame(columns=self.columns)
        
    def add_item(self, d: list) -> None:
        "d -> 2 elements (event_name, explanation)"
        self.data.loc[len(self.data)] = d


class Daily_Form:
    def __init__(self, document_code: str, date: str, day_of_week: str, work_shift: str):
        self.date_and_time = Date_And_Time(document_code, date, day_of_week, work_shift)
        self.human_resources = Human_Resources()
        self.tools_and_equipments = Tools_And_Equipments()
        self.construction_operations = Construction_Operations()
        self.project_issues = Project_Issues()
        self.safety = Safety()
        self.event = Event()
        self.incoming_materials_and_goods = Incoming_Materials_And_Goods()
        self.climate_condition = Climate_Condition()
        
    def add_to_table(self, table_name: str, d: list, item: str = None) -> None:
        if table_name == "human_resources":
            self.human_resources.add_item(item, d)
        elif table_name == "tools_and_equipments":
            self.tools_and_equipments.add_item(item, d)
        elif table_name == "construction_operations":
            self.construction_operations.add_item(d)
        elif table_name == "incoming_materials_and_goods":
            self.incoming_materials_and_goods.add_item(d)
        elif table_name == "climate_condition":
            self.climate_condition.add_item(d)
        elif table_name == "project_issues":
            self.project_issues.add_item(d)
        elif table_name == "safety":
            self.safety.add_item(d)
        elif table_name == "event":
            self.event.add_item(d)

