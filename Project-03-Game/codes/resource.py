class Resource:
    def __init__(self, name:str, capacity:int, gain_rate:float, decay:float):
        """gain_rate: $/hour"""
        self.name = name
        self.capacity = capacity
        self.gain_rate = gain_rate
        self.decay = decay
        
    def hourly_gain(self, player_skill:float, occupied_number:int):
        return self.gain_rate * player_skill / (1 + self.decay * (occupied_number-1))
        
    def __str__(self):
        return f"{self.name}"
    def __repr__(self):
        return f"{self.name}"