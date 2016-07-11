import numpy as np
from . import stage_geometry
from . import profile_shape


class Profiler:
    def __init__(self, stage_profiler=None, blade_elongation=None, blade_windage=None, mean_lattice_density=None):
        self._stage_profiler = stage_profiler
        self._blade_elongation = blade_elongation
        self._blade_windage = blade_windage
        self._mean_lattice_density = mean_lattice_density

        self._blading_geometry = None

    @classmethod
    def is_monolith(cls):
        pass

    @classmethod
    def is_stator(cls):
        return True

    @staticmethod
    def _is_valid_blade_number(blade_number):
        return blade_number % 2 == 0

    @staticmethod
    def characteristic_angle(triangle):
        return triangle.alpha

    @property
    def blading_geometry(self):
        return self._blading_geometry

    def _do_if_initialized(self):
        if self._is_fully_initialized():
            self._set_geometrical_parameters()
            self._correct_lattice_density()

    def _correct_lattice_density(self):
        blade_number = round(self.blading_geometry.blade_number)
        if not self._is_valid_blade_number(blade_number):
            blade_number += 1

        D_mean = self.blading_geometry.D_mean

        mean_step = np.pi * D_mean / blade_number

        new_blade_lattice = self.blading_geometry.mean_chord_length / mean_step

        self._mean_lattice_density = new_blade_lattice
        self.blading_geometry.mean_lattice_density = new_blade_lattice

    @classmethod
    def flow_rotation_angle(cls, inlet_triangle, outlet_triangle):
        return cls.characteristic_angle(outlet_triangle) - cls.characteristic_angle(inlet_triangle)

    @property
    def blading_geometry(self):
        assert self._blading_geometry, 'Object is not fully initialized'

        return self._blading_geometry

    @property
    def stage_profiler(self):
        return self._stage_profiler

    @stage_profiler.setter
    def stage_profiler(self, value):
        self._stage_profiler = value

        self._do_if_initialized()

    @property
    def blade_elongation(self):
        return self._blade_elongation

    @blade_elongation.setter
    def blade_elongation(self, value):
        self._blade_elongation = value

        self._do_if_initialized()

    @property
    def blade_windage(self):
        return self._blade_windage

    @blade_windage.setter
    def blade_windage(self, value):
        self._blade_windage = value

    @property
    def mean_lattice_density(self):
        return self._mean_lattice_density

    @mean_lattice_density.setter
    def mean_lattice_density(self, value):
        self._mean_lattice_density = value

        self._do_if_initialized()

    def get_axis_distance(self, h_rel):
        D_out = self.blading_geometry.D_out_inlet
        D_in = self.blading_geometry.D_out_inlet * self.blading_geometry.d_rel_inlet
        blade_height = (D_out - D_in) / 2

        return blade_height * h_rel + D_in / 2

    def installation_angle(self, h_rel):
        return self.inlet_profile_angle(h_rel) + self.inlet_bend_angle(h_rel)


class InletStatorProfiler(Profiler):
    def __init__(self, stage_profiler=None, D_out_inlet=None, d_rel_inlet=None, blade_elongation=None,
                 blade_windage=None, mean_lattice_density=None, line_frac=0.4):
        Profiler.__init__(self, stage_profiler, blade_elongation, blade_windage, mean_lattice_density)
        self._D_out_inlet = D_out_inlet
        self._d_rel_inlet = d_rel_inlet
        self.line_frac = line_frac

        self._blading_geometry = None

    @classmethod
    def is_monolith(cls):
        return False

    def _is_fully_initialized(self):
        result = True
        result &= bool(self._stage_profiler)
        result &= bool(self._D_out_inlet)
        result &= bool(self._d_rel_inlet)
        result &= bool(self._blade_elongation)
        result &= bool(self._blade_windage)
        result &= bool(self._mean_lattice_density)

        return result

    def _set_geometrical_parameters(self):
        blading_geometry = stage_geometry.BladingGeometry()

        blading_geometry.D_out_inlet = self._D_out_inlet
        blading_geometry.D_out_outlet = self.stage_profiler.blading_geometry.D_out_inlet

        blading_geometry.d_rel_inlet = self._d_rel_inlet
        blading_geometry.d_rel_outlet = self.stage_profiler.blading_geometry.d_rel_inlet

        blading_geometry.blade_elongation = self.blade_elongation
        blading_geometry.blade_windage = self.blade_windage

        blading_geometry.mean_lattice_density = self._mean_lattice_density

        self._blading_geometry = blading_geometry

    @property
    def D_out_inlet(self):
        return self._D_out_inlet

    @D_out_inlet.setter
    def D_out_inlet(self, value):
        self._D_out_inlet = value

        self._do_if_initialized()

    @property
    def d_rel_inlet(self):
        return self._d_rel_inlet

    @d_rel_inlet.setter
    def d_rel_inlet(self, value):
        self._d_rel_inlet = value

        self._do_if_initialized()

    @classmethod
    def _k_delta_coef(cls, alpha):
        alpha = np.rad2deg(alpha)

        if alpha <= 46:
            return np.deg2rad(1.54)
        else:
            return np.deg2rad(3.15 - 0.035 * alpha)

    def profile_bend_angle(self, h_rel):
        alpha = self.stage_profiler.inlet_profile_angle(h_rel)
        lattice_density = self.blading_geometry.lattice_density(h_rel)
        theta = 4 / 3 * ((np.deg2rad(90) - alpha) - self._k_delta_coef(alpha) * lattice_density)

        return theta

    @property
    def mean_profile_bend_angle(self):
        return self.profile_bend_angle(0.3)
        # return self.profile_bend_angle(self.blading_geometry.h_m_rel())

    def inlet_bend_angle(self, h_rel):
        return self.mean_profile_bend_angle * 0.3    # коэффициент 0.3 назначен просто так

    def outlet_bend_angle(self, h_rel):
        return self.profile_bend_angle(h_rel) - self.inlet_bend_angle(h_rel)

    def lag_angle(self, h_rel):
        alpha = self.stage_profiler.inlet_profile_angle(h_rel)
        lattice_density = self.blading_geometry.lattice_density(h_rel)

        return 0.25 * self.profile_bend_angle(h_rel) - self._k_delta_coef(alpha) * lattice_density

    def inlet_profile_angle(self, h_rel):
        return np.pi / 2

    def outlet_profile_angle(self, h_rel):
        return self.stage_profiler.inlet_profile_angle(h_rel) + self.lag_angle(h_rel)

    def get_mean_line_points(self, h_rel, point_num=100):
        x_rel_arr = np.linspace(0, 1, point_num)

        chord_length = self.blading_geometry.chord_length(h_rel)
        inlet_bend_angle = self.inlet_bend_angle(h_rel)
        outlet_bend_angle = self.outlet_bend_angle(h_rel)
        line_frac = self.line_frac

        mean_line = profile_shape.LineBezierProfile(inlet_bend_angle, outlet_bend_angle, line_frac)

        y_rel_arr = mean_line.get_profile(x_rel_arr)

        return x_rel_arr * chord_length, y_rel_arr * chord_length

    def get_mass_center(self, h_rel):
        return np.array((1, np.tan(self.inlet_bend_angle(h_rel)))) * self.blading_geometry.chord_length(h_rel)


class OutletStatorProfiler(Profiler):
    def __init__(self, stage_profiler=None, D_out_outlet=None, d_rel_outlet=None, outlet_flow_angle=None,
                 blade_elongation=None, blade_windage=None, mean_lattice_density=None):
        Profiler.__init__(self, stage_profiler, blade_elongation, blade_windage, mean_lattice_density)
        self._D_out_outlet = D_out_outlet
        self._d_rel_outlet = d_rel_outlet
        self._outlet_flow_angle = outlet_flow_angle

        self._blading_geometry = None

    @classmethod
    def is_monolith(cls):
        return True

    def _is_fully_initialized(self):
        result = True
        result &= bool(self._stage_profiler)
        result &= bool(self._D_out_outlet)
        result &= bool(self._d_rel_outlet)
        result &= bool(self._outlet_flow_angle)
        result &= bool(self._blade_elongation)
        result &= bool(self._blade_windage)
        result &= bool(self._mean_lattice_density)

        return result

    def _set_geometrical_parameters(self):
        blading_geometry = stage_geometry.BladingGeometry()

        blading_geometry.D_out_inlet = self.stage_profiler.blading_geometry.D_out_outlet
        blading_geometry.D_out_outlet = self._D_out_outlet

        blading_geometry.d_rel_inlet = self.stage_profiler.blading_geometry.d_rel_outlet
        blading_geometry.d_rel_outlet = self._d_rel_outlet

        blading_geometry.blade_elongation = self.blade_elongation
        blading_geometry.blade_windage = self.blade_windage

        blading_geometry.mean_lattice_density = self._mean_lattice_density

        self._blading_geometry = blading_geometry

    @property
    def D_out_outlet(self):
        return self._D_out_outlet

    @D_out_outlet.setter
    def D_out_outlet(self, value):
        self._D_out_outlet = value

        self._do_if_initialized()

    @property
    def d_rel_outlet(self):
        return self._d_rel_outlet

    @d_rel_outlet.setter
    def d_rel_outlet(self, value):
        self._d_rel_outlet = value

        self._do_if_initialized()

    @property
    def outlet_flow_angle(self):
        return self.outlet_flow_angle

    @outlet_flow_angle.setter
    def outlet_flow_angle(self, value):
        self._outlet_flow_angle = value

        self._do_if_initialized()

    @staticmethod
    def arc_function(radius, chord_length, x_rel, max_bend):
        return (radius ** 2 - chord_length ** 2 * (x_rel - 0.5) ** 2) ** 0.5 - radius + max_bend

    def max_profile_mean_line_bend(self, h_rel):
        chord_length = self.blading_geometry.chord_length(h_rel)
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return (1 - np.cos(profile_bend_angle / 2)) / (2 * np.sin(profile_bend_angle / 2)) * chord_length

    def inlet_bend_angle(self, h_rel):
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return profile_bend_angle / 2 * (1 + 2 * (1 - 2 * self.relative_profile_bend_coord(h_rel)))

    def outlet_bend_angle(self, h_rel):
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return profile_bend_angle / 2 * (1 - 2 * (1 - 2 * self.relative_profile_bend_coord(h_rel)))

    def _m_angle_coef(self, h_rel):
        outlet_flow_angle = self._outlet_flow_angle
        return 0.23 * (2 * self.relative_profile_bend_coord(h_rel))**2 + 0.18 - 0.002 * np.rad2deg(outlet_flow_angle)

    def profile_bend_angle(self, h_rel):
        inlet_flow_angle = self.characteristic_angle(self.stage_profiler.get_outlet_triangle(h_rel))
        outlet_flow_angle = self._outlet_flow_angle
        flow_rotation_angle = outlet_flow_angle - inlet_flow_angle
        attack_angle = 0
        return (flow_rotation_angle - attack_angle) / \
               (1 - self._m_angle_coef(h_rel) * self.blading_geometry.lattice_density(h_rel) ** 0.5)

    def lag_angle(self, h_rel):
        return self._m_angle_coef(h_rel) * self.profile_bend_angle(h_rel) * \
               self.blading_geometry.lattice_density(h_rel) ** 0.5

    @staticmethod
    def relative_profile_bend_coord(h_rel):
        # принимается форма лопатки в виде дуги окружности
        return 0.5

    def inlet_profile_angle(self, h_rel):
        return self.characteristic_angle(self.stage_profiler.get_outlet_triangle(h_rel))

    def outlet_profile_angle(self, h_rel):
        return self._outlet_flow_angle - self.lag_angle(h_rel)

    def _profile_mean_line_radius(self, h_rel):
        chord_length = self.blading_geometry.chord_length(h_rel)
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return chord_length / (2 * np.sin(profile_bend_angle / 2))

    def _get_arc_points(self, radius_function, max_bend_function, h_rel, point_num):
        x_rel_arr = np.linspace(0, 1, point_num)
        radius = radius_function(h_rel)

        chord_length = self.blading_geometry.chord_length(h_rel)
        max_bend = max_bend_function(h_rel)

        arc_func = lambda x_rel: self.arc_function(radius, chord_length, x_rel, max_bend)

        return x_rel_arr * chord_length, arc_func(x_rel_arr)

    def get_mean_line_points(self, h_rel, point_num=100):
        return self._get_arc_points(self._profile_mean_line_radius, self.max_profile_mean_line_bend, h_rel,
                                    point_num)


class SubSoundInletStatorProfiler(InletStatorProfiler):
    @classmethod
    def get_profile_y_rel(cls, x_rel):
        assert False, 'SubSoundRotorProfiler does not have a profile'

    def get_pressure_side_points(self, h_rel, point_num=100):
        x_rel_arr = np.linspace(0, 1, point_num)
        y_offset_arr = self.get_profile_y_rel(x_rel_arr) * self.blading_geometry.chord_length(h_rel)

        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)

        pressure_side_x = mean_line_x
        pressure_side_y = mean_line_y - y_offset_arr

        return pressure_side_x, pressure_side_y

    def get_suction_side_points(self, h_rel, point_num=100):
        x_rel_arr = np.linspace(0, 1, point_num)
        y_offset_arr = self.get_profile_y_rel(x_rel_arr) * self.blading_geometry.chord_length(h_rel)

        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)

        pressure_side_x = mean_line_x
        pressure_side_y = mean_line_y + y_offset_arr

        return pressure_side_x, pressure_side_y


class SubSoundOutletStatorProfiler(OutletStatorProfiler, SubSoundInletStatorProfiler):
    pass


class A40Profile:
    @classmethod
    def get_profile_y_rel(cls, x_rel):
        x_percent_list = [1, 1.5, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 95, 100]
        y_percent_list = [1.14, 1.43, 1.85, 2.55, 3.09, 3.525, 4.16, 4.55, 4.788, 4.927, 4.936, 5, 4.858,
                          4.443, 3.783, 2.85, 1.722, 1.003, 0]

        return np.interp((1 - x_rel) * 100, x_percent_list, y_percent_list) / 100


class A40InletStatorProfiler(A40Profile, SubSoundInletStatorProfiler):
    pass


class A40OutletStatorProfiler(A40Profile, SubSoundOutletStatorProfiler):
    pass
