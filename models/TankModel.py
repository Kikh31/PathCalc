class TankModel:
    def __init__(self, name="", current_m3=0.0, capacity_m3=0.0, active=True):
        self.name = name
        self.current_m3 = float(current_m3)
        self.capacity_m3 = float(capacity_m3)
        self.active = bool(active)

    def to_dict(self):
        return {
            "name": self.name,
            "current_m3": self.current_m3,
            "capacity_m3": self.capacity_m3,
            "active": self.active,
        }

    @staticmethod
    def from_dict(d):
        return TankModel(
            name=d.get("name", ""),
            current_m3=d.get("current_m3", 0.0),
            capacity_m3=d.get("capacity_m3", 0.0),
            active=d.get("active", True),
        )
