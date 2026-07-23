from pathlib import Path
from codes.resource import Resource

class Country:
    data_path = Path("/Users/keivanjamali/Projects/Game/data/countries")
    def __init__(self, name:str):
        self.name = name
        self.resources = []
        self.capacity = None
        self.house_worth = None
        self._create_country()
        
    def _create_country(self):
        file_name = self.name + ".txt"
        if Path(self.data_path/file_name).exists():
            with open(self.data_path/file_name, "r") as f:
                data = f.read()
        else:
            raise ValueError("[ERROR] No such country in database!")
        data = data.split("## ")
        for i in range(len(data)):
            d = data[i].strip().split("\n")
            if d[0] == "Resources" and len(d[0])>1:
                for res in d[1:]:
                    items = res.split(", ")
                    self.resources.append(Resource(name=items[0],
                                                   gain_rate=float(items[1]),
                                                   capacity=int(items[2]),
                                                   decay=float(items[3])))
            elif d[0] == "Capacity" and len(d[0])>1:
                self.capacity = int(d[1])
            
            elif d[0] == "HouseWorth" and len(d[0])>1:
                self.house_worth = int(d[1])
                
    def __str__(self):
        return f"{self.name} with resources: {self.resources}, capacity: {self.capacity}, house worth: {self.house_worth}"
    def __repr__(self):
        return f"{self.name} with resources: {self.resources}, capacity: {self.capacity}, house worth: {self.house_worth}"
                
