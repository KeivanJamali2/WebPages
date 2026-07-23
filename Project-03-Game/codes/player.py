from pathlib import Path
from datetime import datetime
from codes.countries import Country

class Player:
    data_path = Path("/Users/keivanjamali/Projects/Game/data/players")
    def __init__(self, name:str, new:str = None):
        """new: Is non if the player already exists, otherwise it is the country name of the player."""
        self.name = name
        self.country = new
        self.file_path = Path(self.data_path / Path(self.name + ".txt"))
        if new:
            self._create_player()
        else:
            self._get_player_info()
        
    def _get_player_info(self):
        if self.file_path.exists():
            print(f"[INFO] Getting info about player: {self.name} .")
            with open(self.file_path, "r") as f:
                data = f.read()
            data = data.split("## ")
            for i in range(len(data)):
                d = data[i].strip().split("\n")
                if d[0] == "Basic" and len(d[0])>1:
                    self.country, self.created_at, self.last_updated = d[1].split(", ")
                elif d[0] == "Location" and len(d[0])>1:
                    self.location = d[1]
                elif d[0] == "Money" and len(d[0])>1:
                    self.money = int(d[1])
                elif d[0] == "Skills" and len(d[0])>1:
                    self.skills = None if d[1]=="None" else d[1:]
                elif d[0] == "Job" and len(d[0])>1:
                    self.job = None if d[1]=="None" else d[1]
                elif d[0] == "Energy" and len(d[0])>1:
                    self.energy = int(d[1])
                elif d[0] == "Health" and len(d[0])>1:
                    self.health = int(d[1])
                elif d[0] == "Transportation" and len(d[0])>1:
                    self.transportation = d[1:]
                elif d[0] == "Houses" and len(d[0])>1:
                    self.houses = []
                    for hou in d[1:]:
                        items = hou.split(", ")
                        self.houses.append({"country": items[0],
                                            "worth": int(items[1]),
                                            "number": int(items[2]),
                                            "occupied": int(items[3]),
                                            "am_i_there": items[4]=="True"})
        else:
            raise ValueError("[ERROR] No such player in database!")     

    def _create_player(self):
        self.data_path.mkdir(parents=True, exist_ok=True)
        house_worth = Country(self.country).house_worth
        now = datetime.utcnow().isoformat()

        content = f"""## Basic
{self.country}, {now}, {now}

## Location
{self.country}

## Money
0

## Skills
None

## Job
None

## Energy
0

## Health
60

## Transportation
walk

## Houses
{self.country}, {house_worth}, 1, 1, True

## Log
[created at {now}]
"""

        with open(self.file_path, "w") as f:
            f.write(content)

        print(f"[INFO] Player {self.name} created successfully.")