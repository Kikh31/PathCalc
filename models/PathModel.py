class PathModel():
    def __init__(self, iid, distance=0.0, speed=0.0, is_eca=False, loading="Ballast", consumption=0.0):
        self.id = iid
        self.distance = distance
        self.speed = speed
        self.is_eca = is_eca
        self.loading = loading
        self.consumption = consumption
