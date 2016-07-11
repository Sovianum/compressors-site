
class Material:
    def __init__(self):
        self.density = None
        self.E = None
        self.sigma_v = None
        self.fatigue_strength = None
        self.ultimate_strength = None


class Steel(Material):
    def __init__(self):
        Material.__init__(self)
        self.density = 7800
        self.E = 2e11


class VT9(Material):
    def __init__(self):
        Material.__init__(self)
        self.density = 4510
        self.E = 1.18e11
        self.fatigue_strength = 519e6     # из расчета на 2e7 циклов
        self.ultimate_strength = 1127e6
