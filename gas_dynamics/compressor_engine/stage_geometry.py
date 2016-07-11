import numpy as np


class StageGeometry:
    def __init__(self, D_out_1=None, d_rel_1=None, D_out_3=None, d_rel_3=None, form_coef=None):
        self.D_out_1 = D_out_1
        self.d_rel_1 = d_rel_1
        self.D_out_3 = D_out_3
        self.d_rel_3 = d_rel_3
        self.form_coef = form_coef

        self.rotor_geometry = None
        self.stator_geometry = None

    @staticmethod
    def _get_outlet_parameters(D_1, d_rel_1, F_3, form_coef):
        '''
        :param D_1:
        :param d_rel_1:
        :param F_3:
        :param form_coef: параметр, определяющий постоянный диаметр
        :return: функция возвращает значение периферийного диаметра и относительного диаметра втулки на выходе
        '''

        betta = (np.pi / 4 * (D_1 ** 2 / F_3) * (form_coef + d_rel_1 * (1 - form_coef))**2) ** 0.5

        d_rel_3 = (betta * (1 - 2 * form_coef + betta ** 2) ** 0.5 - form_coef * (1 - form_coef)) / \
                  ((1 - form_coef) ** 2 + betta ** 2)
        assert not np.isnan(d_rel_3), 'Impossible_geometry_encountered'

        D_3 = D_1 * (d_rel_1 + form_coef * (1 - d_rel_1)) / (d_rel_3 + form_coef * (1 - d_rel_3))

        return D_3, d_rel_3

    def get_outlet_parameters(self, F_3):
        return self._get_outlet_parameters(self.D_out_1, self.d_rel_1, F_3, self.form_coef)

    @staticmethod
    def _mean_radius_rel(relative_diameter):
        return ((1 + relative_diameter**2) / 2)**0.5

    @property
    def D_out_2(self):
        return (self.D_out_1 + self.D_out_3) / 2

    @property
    def d_rel_2(self):
        return (self.d_rel_1 + self.d_rel_3) / 2

    @property
    def r_m_rel_1(self):
        return self._mean_radius_rel(self.d_rel_1)

    @property
    def r_m_rel_2(self):
        return self._mean_radius_rel(self.d_rel_2)

    @property
    def r_m_rel_3(self):
        return self._mean_radius_rel(self.d_rel_3)

    @property
    def D_mean_1(self):
        return self.D_out_1 * self.r_m_rel_1

    @property
    def D_mean_2(self):
        return self.D_out_2 * self.r_m_rel_2

    @property
    def D_mean_3(self):
        return self.D_out_3 * self.r_m_rel_3

    def set_rotor_geometry(self, blade_elongation, blade_windage, mean_lattice_density):
        rotor_geometry = BladingGeometry()
        rotor_geometry.D_out_inlet = self.D_out_1
        rotor_geometry.D_out_outlet = self.D_out_2

        rotor_geometry.d_rel_inlet = self.d_rel_1
        rotor_geometry.d_rel_outlet = self.d_rel_2

        rotor_geometry.blade_elongation = blade_elongation
        rotor_geometry.blade_windage = blade_windage

        rotor_geometry.mean_lattice_density = mean_lattice_density

        self.rotor_geometry = rotor_geometry

    def set_stator_geometry(self, blade_elongation, blade_windage, mean_lattice_density):
        stator_geometry = BladingGeometry()
        stator_geometry.D_out_inlet = self.D_out_2
        stator_geometry.D_out_outlet = self.D_out_3

        stator_geometry.d_rel_inlet = self.d_rel_2
        stator_geometry.d_rel_outlet = self.d_rel_3

        stator_geometry.blade_elongation = blade_elongation
        stator_geometry.blade_windage = blade_windage

        stator_geometry.mean_lattice_density = mean_lattice_density

        self.stator_geometry = stator_geometry


class BladingGeometry:
    def __init__(self):
        self.D_out_inlet = None
        self.D_out_outlet = None

        self.d_rel_inlet = None
        self.d_rel_outlet = None

        self.blade_elongation = None
        self.blade_windage = None

        self.mean_lattice_density = None

    @staticmethod
    def _mean_radius_rel(relative_diameter):
        return ((1 + relative_diameter**2) / 2)**0.5

    def r_rel_inlet(self, h_rel):
        return self.d_rel_inlet + h_rel * (1 - self.d_rel_inlet)

    def r_rel_outlet(self, h_rel):
        return self.d_rel_outlet + h_rel * (1 - self.d_rel_outlet)

    def r_rel(self, h_rel):
        #return self.d_rel_inlet + h_rel * (1 - self.d_rel_inlet)    # TODO проверить правильность исправлений
        return self.d_rel_mean + h_rel * (1 - self.d_rel_mean)

    def h_m_rel(self):
        r_rel = self._mean_radius_rel(self.d_rel_mean)
        return (r_rel - self.d_rel_mean) / (1 - self.d_rel_mean)

    def h_rel_inlet(self, r_rel):
        return (r_rel - self.d_rel_inlet) / (1 - self.d_rel_inlet)

    def h_rel_outlet(self, r_rel):
        return (r_rel - self.d_rel_outlet) / (1 - self.d_rel_outlet)

    @property
    def D_mean_inlet(self):
        return self.D_out_inlet * self._mean_radius_rel(self.d_rel_inlet)

    @property
    def D_in_inlet(self):
        return self.D_out_inlet * self.d_rel_inlet

    @property
    def D_mean_outlet(self):
        return self.D_out_outlet * self._mean_radius_rel(self.d_rel_outlet)

    @property
    def D_in_outlet(self):
        return self.D_out_outlet * self.d_rel_outlet

    @property
    def D_out(self):
        return self.D_out_inlet     # TODO проверить правильность исправления
        #return (self.D_out_inlet + self.D_out_outlet) / 2

    @property
    def D_mean(self):
        #return self.D_mean_inlet    # TODO проверить правильность исправления
        return (self.D_mean_inlet + self.D_mean_outlet) / 2

    @property
    def D_in(self):
        return self.D_in_inlet      # TODO проверить правильность исправления
        #return (self.D_in_inlet + self.D_in_outlet) / 2

    @property
    def d_rel_mean(self):
        return self.d_rel_inlet         # TODO вернуть как было
        #return (self.d_rel_inlet + self.d_rel_outlet) / 2

    @property
    def F_inlet(self):
        return np.pi / 4 * self.D_out_inlet**2 * (1 - self.d_rel_inlet**2)

    @property
    def F_outlet(self):
        return np.pi / 4 * self.D_out_outlet**2 * (1 - self.d_rel_outlet**2)

    @property
    def blade_length(self):
        return (self.D_out - self.D_in) / 2

    @property
    def mean_chord_length(self):
        return self.blade_length / self.blade_elongation

    @classmethod
    def _get_chord_length(cls, h_rel, d_rel, blade_windage, mean_chord_length):
        r_m_rel = cls._mean_radius_rel(d_rel)
        r_rel = d_rel + h_rel * (1 - d_rel)

        enum = (blade_windage - 1) * r_rel + 1 - blade_windage * d_rel
        denum = (blade_windage - 1) * r_m_rel + 1 - blade_windage * d_rel

        return enum / denum * mean_chord_length

    def chord_length(self, h_rel):
        return self._get_chord_length(h_rel, self.d_rel_inlet, self.blade_windage, self.mean_chord_length)

    @property
    def out_chord_length(self):
        return self.chord_length(1)

    @property
    def in_chord_length(self):
        return self.chord_length(0)

    def step(self, h_rel):
        r_rel = self.r_rel(h_rel)
        diameter = self.D_out * r_rel

        return np.pi * diameter / self.blade_number

    @property
    def out_step(self):
        return np.pi * self.D_out / self.blade_number

    @property
    def mean_step(self):
        return self.mean_chord_length / self.mean_lattice_density

    @property
    def in_step(self):
        return np.pi * self.D_in / self.blade_number

    @property
    def out_lattice_density(self):
        return self.out_chord_length / self.out_step

    @property
    def in_lattice_density(self):
        return self.in_chord_length / self.in_step

    def lattice_density(self, h_rel):
        chord_length = self.chord_length(h_rel)
        step = np.pi * self.D_out * self.r_rel(h_rel) / self.blade_number

        return chord_length / step

    @property
    def blade_number(self):
        return np.pi * self.D_mean / self.mean_step


class ConstantOuterDiameterStageGeometry(StageGeometry):
    def __init__(self, D_out_1=None, d_rel_1=None, D_out_3=None, d_rel_3=None):
        StageGeometry.__init__(self, D_out_1, d_rel_1, D_out_3, d_rel_3, form_coef=1)


class ConstantInnerDiameterStageGeometry(StageGeometry):
    def __init__(self, D_out_1=None, d_rel_1=None, D_out_3=None, d_rel_3=None):
        StageGeometry.__init__(self, D_out_1, d_rel_1, D_out_3, d_rel_3, form_coef=0)


class ConstantMeanDiameterStageGeometry(StageGeometry):
    def __init__(self, D_out_1=None, d_rel_1=None, D_out_3=None, d_rel_3=None):
        StageGeometry.__init__(self, D_out_1, d_rel_1, D_out_3, d_rel_3)

    @property
    def form_coef(self):
        return (((1 + self.d_rel_1**2) / 2)**0.5 - self.d_rel_1) / (1 - self.d_rel_1)

    @form_coef.setter
    def form_coef(self, value):
        pass
