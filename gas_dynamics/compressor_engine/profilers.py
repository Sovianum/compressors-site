import numpy as np
from scipy.interpolate import interp1d
from . import velocity_laws
from . import gdf


class Profiler:
    def __init__(self, stage_model=None, blade_elongation=None, blade_windage=None, mean_lattice_density=None,
                 velocity_law=velocity_laws.ConstantCirculationLaw):
        self._stage_model = stage_model
        self._stage_geometry = None
        self._mean_inlet_triangle = None
        self._mean_outlet_triangle = None
        self._blade_elongation = blade_elongation
        self._blade_windage = blade_windage
        self._mean_lattice_density = mean_lattice_density

        self.velocity_law = velocity_law(self)
        self.suction_side_attack_angle = np.deg2rad(0.5)

        self._do_if_initialized()

    @classmethod
    def is_monolith(cls):
        return True

    def _is_fully_initialized(self):
        result = True
        result &= bool(self._stage_model)
        result &= bool(self._blade_elongation)
        result &= bool(self._blade_windage)
        result &= bool(self._mean_lattice_density)

        return result

    @staticmethod
    def _is_valid_blade_number(blade_number):
        assert False, 'Profiler class can not be used for real calculation'

    def _correct_lattice_density(self):
        blade_number = round(self.blading_geometry.blade_number)
        if not self._is_valid_blade_number(blade_number):
            blade_number += 1

        D_mean = self.blading_geometry.D_mean

        mean_step = np.pi * D_mean / blade_number

        new_blade_lattice = self.blading_geometry.mean_chord_length / mean_step

        self._mean_lattice_density = new_blade_lattice
        self.blading_geometry.mean_lattice_density = new_blade_lattice

    def _do_if_initialized(self):
        if self._is_fully_initialized():
            self._set_stage_model_parameters()
            self._set_geometrical_parameters()
            self._correct_lattice_density()

    @staticmethod
    def characteristic_angle(triangle):
        assert False, 'Profiler class can not be used for real calculation'

    @classmethod
    def flow_rotation_angle(cls, inlet_triangle, outlet_triangle):
        return cls.characteristic_angle(outlet_triangle) - cls.characteristic_angle(inlet_triangle)

    @staticmethod
    def characteristic_velocity(triangle):
        assert False, 'Profiler class can not be used for real calculation'

    @property
    def blading_geometry(self):
        assert False, 'Profiler class can not be used for real calculation'

    @property
    def mean_inlet_triangle(self):
        return self._mean_inlet_triangle

    @property
    def mean_outlet_triangle(self):
        return self._mean_outlet_triangle

    @property
    def stage_model(self):
        return self._stage_model

    @stage_model.setter
    def stage_model(self, value):
        self._stage_model = value

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

        self._do_if_initialized()

    def get_axis_distance(self, h_rel):
        D_out = self.blading_geometry.D_out
        D_in = self.blading_geometry.D_out * self.blading_geometry.d_rel_inlet
        blade_height = (D_out - D_in) / 2

        return blade_height * h_rel + D_in / 2

    def get_inlet_triangle(self, h_rel):
        r_rel = self.blading_geometry.r_rel_inlet(h_rel)
        triangle = self.velocity_law.get_inlet_velocity_triangle(self._mean_inlet_triangle, r_rel)
        return triangle

    def get_outlet_triangle(self, h_rel):
        r_rel = self.blading_geometry.r_rel_outlet(h_rel)
        triangle = self.velocity_law.get_outlet_velocity_triangle(self._mean_outlet_triangle, r_rel)
        return triangle

    @staticmethod
    def arc_function(radius, chord_length, x_rel, max_bend):
        return (radius**2 - chord_length**2 * (x_rel - 0.5)**2)**0.5 - radius + max_bend

    def get_inlet_mach_number_profile(self, point_num=10):
        h_rel_arr = np.linspace(0, 1, point_num)

        def mach_number(h_rel):
            inlet_triangle = self.get_inlet_triangle(h_rel)

            inlet_velocity = self.characteristic_velocity(inlet_triangle)
            inlet_lambda = self.stage_model.lambda_1(inlet_velocity)
            k = self.stage_model.k

            return gdf.mach(inlet_lambda, k)

        mach_number_arr = [mach_number(h_rel) for h_rel in h_rel_arr]

        return h_rel_arr, mach_number_arr

    def get_outlet_mach_number_profile(self, point_num=100):
        h_rel_num = np.linspace(0, 1, point_num)

        def mach_number(h_rel):
            outlet_velocity = self.characteristic_velocity(self.get_outlet_triangle(h_rel))
            outlet_lambda = self.stage_model.lambda_3(outlet_velocity)
            k = self.stage_model.k

            return gdf.mach(outlet_lambda, k)

        return h_rel_num, mach_number(h_rel_num)

    def get_diffusion_rate(self, h_rel):
        inlet_triangle = self.get_inlet_triangle(h_rel)
        outlet_triangle = self.get_outlet_triangle(h_rel)
        lattice_density = self.blading_geometry.lattice_density(h_rel)

        inlet_velocity = self.characteristic_velocity(inlet_triangle)
        outlet_velocity = self.characteristic_velocity(outlet_triangle)

        inlet_angle = self.characteristic_angle(inlet_triangle)
        outlet_angle = self.characteristic_angle(outlet_triangle)

        term_1 = outlet_velocity / inlet_velocity
        term_2 = (inlet_velocity * np.cos(inlet_angle) - outlet_velocity * np.cos(outlet_angle)) / \
                 (2 * inlet_velocity * lattice_density)

        #term_1 = outlet_triangle.c_a_rel / inlet_triangle.c_a_rel * (np.sin(inlet_angle) / np.sin(outlet_angle))
        #factor_1 = np.sin(inlet_angle) / (2 * lattice_density)
        #factor_2 = 1 / np.tan(inlet_angle) - outlet_triangle.c_a_rel / inlet_triangle.c_a_rel * (1 / np.tan(outlet_angle))
        #term_2 = factor_1 * factor_2

        diffusion_rate = 1 - term_1 + term_2

        return diffusion_rate

    def get_diffusion_rate_profile(self, point_num=100):
        h_rel_list = np.linspace(0, 1, point_num)

        return h_rel_list, self.get_diffusion_rate(h_rel_list)

    def get_inlet_pressure(self, h_rel):
        triangle = self.get_inlet_triangle(h_rel)
        total_velocity = triangle.c_total
        p_stag = self.stage_model.thermal_info.p_stag_1
        a_crit = self.stage_model.thermal_info.a_crit_1
        lambda_ = total_velocity / a_crit

        return p_stag * gdf.pi(lambda_, self.stage_model.k)

    def get_outlet_pressure(self, h_rel):
        triangle = self.get_outlet_triangle(h_rel)
        total_velocity = triangle.c_total
        p_stag = self.stage_model.thermal_info.p_stag_3
        a_crit = self.stage_model.thermal_info.a_crit_3
        lambda_ = total_velocity / a_crit

        return p_stag * gdf.pi(lambda_, self.stage_model.k)

    def get_inlet_temperature(self, h_rel):
        triangle = self.get_inlet_triangle(h_rel)
        total_velocity = triangle.c_total
        T_stag = self.stage_model.thermal_info.T_stag_1
        a_crit = self.stage_model.thermal_info.a_crit_1
        lambda_ = total_velocity / a_crit

        return T_stag * gdf.tau(lambda_, self.stage_model.k)

    def get_outlet_temperature(self, h_rel):
        triangle = self.get_outlet_triangle(h_rel)
        total_velocity = triangle.c_total
        T_stag = self.stage_model.thermal_info.T_stag_3
        a_crit = self.stage_model.thermal_info.a_crit_3
        lambda_ = total_velocity / a_crit

        return T_stag * gdf.tau(lambda_, self.stage_model.k)

    def get_inlet_density(self, h_rel):
        triangle = self.get_outlet_triangle(h_rel)
        total_velocity = triangle.c_total
        density_stag = self.stage_model.thermal_info.density_stag_1
        a_crit = self.stage_model.thermal_info.a_crit_3
        lambda_ = total_velocity / a_crit

        return density_stag * gdf.epsilon(lambda_, self.stage_model.k)

    def get_outlet_density(self, h_rel):
        triangle = self.get_outlet_triangle(h_rel)
        total_velocity = triangle.c_total
        density_stag = self.stage_model.thermal_info.density_stag_3
        a_crit = self.stage_model.thermal_info.a_crit_3
        lambda_ = total_velocity / a_crit

        return density_stag * gdf.epsilon(lambda_, self.stage_model.k)


class RotorProfiler(Profiler):
    @staticmethod
    def _is_valid_blade_number(blade_number):
        return blade_number % 2 != 0

    def is_stator(self):
        return False

    def _set_geometrical_parameters(self):
        self._stage_geometry.set_rotor_geometry(self.blade_elongation, self.blade_windage, self._mean_lattice_density)

    def _set_stage_model_parameters(self):
        self._stage_geometry = self.stage_model.stage_geometry
        self._mean_inlet_triangle = self.stage_model.triangle_1
        self._mean_outlet_triangle = self.stage_model.triangle_2

    @staticmethod
    def characteristic_angle(triangle):
        return triangle.betta

    @staticmethod
    def characteristic_velocity(triangle):
        return triangle.w_total

    @property
    def blading_geometry(self):
        return self._stage_geometry.rotor_geometry


class StatorProfiler(Profiler):
    def is_stator(self):
        return True

    @staticmethod
    def _is_valid_blade_number(blade_number):
        return blade_number % 2 == 0

    def _set_geometrical_parameters(self):
        self._stage_geometry.set_stator_geometry(self.blade_elongation, self.blade_windage, self.mean_lattice_density)

    def _set_stage_model_parameters(self):
        self._stage_geometry = self.stage_model.stage_geometry
        self._mean_inlet_triangle = self.stage_model.triangle_2
        self._mean_outlet_triangle = self.stage_model.triangle_3

    @staticmethod
    def characteristic_angle(triangle):
        return triangle.alpha

    @staticmethod
    def characteristic_velocity(triangle):
        return triangle.c_total

    @property
    def blading_geometry(self):
        return self._stage_geometry.stator_geometry


class TransSoundRotorProfiler(RotorProfiler):
    @property
    def mean_lattice_density(self):
        return self._mean_lattice_density

    @mean_lattice_density.setter
    def mean_lattice_density(self, value):
        self._mean_lattice_density = value

        self._do_if_initialized()

    @staticmethod
    def relative_profile_bend_coord(h_rel):
        # принимается форма лопатки в виде дуги окружности
        return 0.5

    @staticmethod
    def relative_profile_thickness(h_rel):
        h_rel_list = [0, 0.25, 0.5, 0.75, 1]
        c_rel_list = [0.12, 0.095, 0.07, 0.05, 0.03]

        return interp1d(h_rel_list, c_rel_list)(h_rel)

    def max_profile_thickness(self, h_rel):
        return self.blading_geometry.chord_length(h_rel) * self.relative_profile_thickness(h_rel)

    def attack_angle(self, h_rel):
        return self.suction_side_attack_angle + np.deg2rad(np.arctan(1.9 * self.relative_profile_thickness(h_rel)))

    def inlet_profile_angle(self, h_rel):
        return self.characteristic_angle(self.get_inlet_triangle(h_rel)) + self.attack_angle(h_rel)

    def _sub_sound_lag_angle(self, h_rel):
        inlet_triangle = self.get_inlet_triangle(h_rel)
        outlet_triangle = self.get_outlet_triangle(h_rel)

        flow_rotation_angle = np.rad2deg(self.flow_rotation_angle(inlet_triangle, outlet_triangle))
        attack_angle = np.rad2deg(self.attack_angle(h_rel))
        lattice_density = self.blading_geometry.lattice_density(h_rel)

        m = 0.18 + 0.92 * self.relative_profile_bend_coord(h_rel) ** 2 - \
            0.002 * np.rad2deg(self.characteristic_angle(outlet_triangle))

        return np.deg2rad((flow_rotation_angle - attack_angle) / (lattice_density**0.5 / m - 1))

    def _epsilon_lag_angle_correction(self, h_rel):
        inlet_triangle = self.get_inlet_triangle(h_rel)
        outlet_triangle = self.get_outlet_triangle(h_rel)

        flow_rotation_angle = np.rad2deg(self.characteristic_angle(outlet_triangle) - self.characteristic_angle(inlet_triangle))
        rel_profile_thickness = self.relative_profile_thickness(h_rel)

        result = np.deg2rad(12.5 * (rel_profile_thickness * (1 - flow_rotation_angle / 8)))

        if result > 0:
            return result
        else:
            return 0

    def _m_lag_angle_correction(self, h_rel):
        inlet_velocity = self.characteristic_velocity(self.get_inlet_triangle(h_rel))
        inlet_lambda = self.stage_model.lambda_1(inlet_velocity)

        if inlet_lambda <= 0.75:
            return 0
        elif inlet_lambda >= 1.3:
            inlet_lambda = 1.3

        return np.deg2rad(3.5 * (inlet_lambda - 0.75))

    def _c_lag_angle_correction(self, h_rel):
        c_a_1 = self.get_inlet_triangle(h_rel).c_a
        c_a_2 = self.get_outlet_triangle(h_rel).c_a

        return np.deg2rad(9 * (1 - c_a_2 / c_a_1))

    def lag_angle(self, h_rel):
        return self._sub_sound_lag_angle(h_rel) + self._epsilon_lag_angle_correction(h_rel) + \
               self._c_lag_angle_correction(h_rel) + self._m_lag_angle_correction(h_rel)

    def outlet_profile_angle(self, h_rel):
        return self.characteristic_angle(self.get_outlet_triangle(h_rel)) + self.lag_angle(h_rel)

    def profile_bend_angle(self, h_rel):
        return self.outlet_profile_angle(h_rel) - self.inlet_profile_angle(h_rel)

    def inlet_bend_angle(self, h_rel):
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return profile_bend_angle / 2 * (1 + 2 * (1 - 2 * self.relative_profile_bend_coord(h_rel)))

    def outlet_bend_angle(self, h_rel):
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return profile_bend_angle / 2 * (1 - 2 * (1 - 2 * self.relative_profile_bend_coord(h_rel)))

    def installation_angle(self, h_rel):
        return self.inlet_profile_angle(h_rel) + self.inlet_bend_angle(h_rel)

    def max_profile_mean_line_bend(self, h_rel):
        chord_length = self.blading_geometry.chord_length(h_rel)
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return (1 - np.cos(profile_bend_angle / 2)) / (2 * np.sin(profile_bend_angle / 2)) * chord_length

    def max_profile_pressure_side_bend(self, h_rel):
        result = self.max_profile_mean_line_bend(h_rel) - self.max_profile_thickness(h_rel) / 2

        assert result > 0, 'Negative profile bend obtained.'

        return result

    def max_profile_suction_side_bend(self, h_rel):
        return self.max_profile_mean_line_bend(h_rel) + self.max_profile_thickness(h_rel) / 2

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

    def get_pressure_side_points(self, h_rel, point_num=100):
        raise TypeError('This class can not be used for profiling')

    def get_suction_side_points(self, h_rel, point_num=100):
        raise TypeError('This class can not be used for profiling')


class TransSoundStatorProfiler(StatorProfiler, TransSoundRotorProfiler):
    pass


class SubSoundRotorProfiler(RotorProfiler):
    def __init__(self, stage_model=None, blade_elongation=None, blade_windage=None, mean_lattice_density=None,
                 velocity_law=velocity_laws.ConstantCirculationLaw, thk_factor=1.0):
        Profiler.__init__(self, stage_model, blade_elongation, blade_windage, mean_lattice_density, velocity_law)
        self.thk_factor = thk_factor

    def _is_fully_initialized(self):
        result = True
        result &= bool(self._stage_model)
        result &= bool(self._blade_elongation)
        result &= bool(self._blade_windage)
        result &= bool(self._mean_lattice_density)

        return result

    @staticmethod
    def _eps_identity_density(lattice_outlet_angle):    # метод не используется
        x_p = [np.deg2rad(40), np.deg2rad(110)]
        y_p = [np.deg2rad(10), np.deg2rad(42)]

        return np.interp(lattice_outlet_angle, x_p, y_p)

    @staticmethod
    def _lattice_density_law(relative_rotation_angle):  # метод не используется
        x_p = [0.6, 0.8, 1.0, 1.2, 1.4, 1.5]
        y_p = [0.57, 0.7, 1.0, 1.37, 1.9, 2.3]

        return np.interp(relative_rotation_angle, x_p, y_p)

    @property
    def mean_lattice_density(self):
        return self._mean_lattice_density

    @mean_lattice_density.setter
    def mean_lattice_density(self, value):
        self._mean_lattice_density = value

        self._do_if_initialized()

    def _correct_lattice_density(self):
        #outlet_flow_angle = self.characteristic_angle(self.mean_outlet_triangle)
        #eps_identity_density = self._eps_identity_density(outlet_flow_angle)
        #relative_rotation_angle = self.flow_rotation_angle(self.mean_inlet_triangle, self.mean_outlet_triangle) / \
        #                          eps_identity_density

        #self._mean_lattice_density = self._lattice_density_law(relative_rotation_angle)
        self.blading_geometry.mean_lattice_density = self._mean_lattice_density

        blade_number = round(self.blading_geometry.blade_number)
        if not self._is_valid_blade_number(blade_number):
            blade_number += 1

        D_mean = self.blading_geometry.D_mean

        mean_step = np.pi * D_mean / blade_number

        new_blade_lattice = self.blading_geometry.mean_chord_length / mean_step

        self._mean_lattice_density = new_blade_lattice
        self.blading_geometry.mean_lattice_density = new_blade_lattice

    def attack_angle(self, h_rel):
        return np.deg2rad(2.5 * (self.blading_geometry.mean_lattice_density - 1))

    @staticmethod
    def relative_profile_bend_coord(h_rel):
        # принимается форма лопатки в виде дуги окружности
        return 0.5

    def _m_angle_coef(self, h_rel):
        outlet_flow_angle = self.characteristic_angle(self.get_outlet_triangle(h_rel))
        return 0.23 * (2 * self.relative_profile_bend_coord(h_rel))**2 + 0.18 - 0.002 * np.rad2deg(outlet_flow_angle)

    def profile_bend_angle(self, h_rel):
        flow_rotation_angle = self.flow_rotation_angle(self.get_inlet_triangle(h_rel), self.get_outlet_triangle(h_rel))
        return (flow_rotation_angle - self.attack_angle(h_rel)) / \
               (1 - self._m_angle_coef(h_rel) * self.blading_geometry.lattice_density(h_rel) ** 0.5)

    def lag_angle(self, h_rel):
        return self._m_angle_coef(h_rel) * self.profile_bend_angle(h_rel) * \
               self.blading_geometry.lattice_density(h_rel) ** 0.5

    def installation_angle(self, h_rel):
        hi_coef = 0.5
        inlet_flow_angle = self.characteristic_angle(self.get_inlet_triangle(h_rel))
        return hi_coef * self.profile_bend_angle(h_rel) + inlet_flow_angle + self.attack_angle(h_rel)

    def inlet_bend_angle(self, h_rel):
        return self.profile_bend_angle(h_rel) / 2

    def outlet_bend_angle(self, h_rel):
        return self.profile_bend_angle(h_rel) - self.inlet_bend_angle(h_rel)

    def max_profile_mean_line_bend(self, h_rel):
        chord_length = self.blading_geometry.chord_length(h_rel)
        profile_bend_angle = self.profile_bend_angle(h_rel)

        return (1 - np.cos(profile_bend_angle / 2)) / (2 * np.sin(profile_bend_angle / 2)) * chord_length

    def profile_mean_line_radius(self, h_rel):
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
        return self._get_arc_points(self.profile_mean_line_radius, self.max_profile_mean_line_bend, h_rel,
                                    point_num)

    @classmethod
    def get_profile_y_rel(cls, x_rel):
        assert False, 'SubSoundRotorProfiler does not have a profile'

    def get_thk_correction(self, h_rel):
        return 1 + (1/self.thk_factor - 1) * h_rel

    def get_pressure_side_points(self, h_rel, point_num=100):
        x_rel_arr = np.linspace(0, 1, point_num)
        y_offset_arr = self.get_profile_y_rel(x_rel_arr) * self.blading_geometry.chord_length(h_rel)
        y_offset_arr *= self.get_thk_correction(h_rel)

        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)

        pressure_side_x = mean_line_x
        pressure_side_y = mean_line_y - y_offset_arr

        return pressure_side_x, pressure_side_y

    def get_suction_side_points(self, h_rel, point_num=100):
        x_rel_arr = np.linspace(0, 1, point_num)
        y_offset_arr = self.get_profile_y_rel(x_rel_arr) * self.blading_geometry.chord_length(h_rel)
        y_offset_arr *= self.get_thk_correction(h_rel)

        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)

        pressure_side_x = mean_line_x
        pressure_side_y = mean_line_y + y_offset_arr

        return pressure_side_x, pressure_side_y


class SubSoundStatorProfiler(StatorProfiler, SubSoundRotorProfiler):
    def __init__(self, stage_model=None, blade_elongation=None, blade_windage=None, mean_lattice_density=None,
                 velocity_law=velocity_laws.ConstantCirculationLaw, thk_factor=5):
            SubSoundRotorProfiler.__init__(self, stage_model, blade_elongation, blade_windage, mean_lattice_density,
                                           velocity_law, thk_factor)

    def get_thk_correction(self, h_rel):
        return 1 / self.thk_factor + (1 - 1 / self.thk_factor) * h_rel

    @staticmethod
    def _is_valid_blade_number(blade_number):
        return blade_number % 2 == 0


class TransSoundArcRotorProfiler(TransSoundRotorProfiler):
    def _profile_pressure_side_radius(self, h_rel):
        max_bend = self.max_profile_pressure_side_bend(h_rel)
        chord_length = self.blading_geometry.chord_length(h_rel)

        return max_bend / 2 + chord_length**2 / (8 * max_bend)

    def _profile_suction_side_radius(self, h_rel):
        max_bend = self.max_profile_suction_side_bend(h_rel)
        chord_length = self.blading_geometry.chord_length(h_rel)

        return max_bend / 2 + chord_length**2 / (8 * max_bend)

    def get_pressure_side_points(self, h_rel, point_num=100):
        pressure_side_points = self._get_arc_points(self._profile_pressure_side_radius,
                                                    self.max_profile_pressure_side_bend, h_rel, point_num)
        return pressure_side_points

    def get_suction_side_points(self, h_rel, point_num=100):
        return self._get_arc_points(self._profile_suction_side_radius, self.max_profile_suction_side_bend,
                                    h_rel, point_num)


class TransSoundArcStatorProfiler(TransSoundStatorProfiler, TransSoundArcRotorProfiler):
    pass


class TransSoundProfileRotorProfiler(TransSoundRotorProfiler):
    def _get_default_profile_points(self, h_rel, point_num=100):
        x_rel_array_0 = np.array([0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0])
        y_rel_array_0 = np.array([0.0045, 0.0132, 0.0208, 0.0282, 0.0342, 0.0430, 0.0482, 0.05, 0.0482, 0.0430, 0.0342,
                                  0.0282, 0.0208, 0.0132, 0.0045])

        x_rel_array = np.linspace(0, 1, point_num)
        y_rel_array = np.interp(x_rel_array, x_rel_array_0, y_rel_array_0)

        chord_length = self.blading_geometry.chord_length(h_rel)
        max_profile_thickness = self.relative_profile_thickness(h_rel)

        x_array = x_rel_array * chord_length
        y_array = y_rel_array * chord_length * max_profile_thickness / 0.1

        return x_array, y_array

    def get_pressure_side_points(self, h_rel, point_num=100):
        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)
        _, default_profile_y = self._get_default_profile_points(h_rel, point_num)

        return mean_line_x, mean_line_y - default_profile_y

    def get_suction_side_points(self, h_rel, point_num=100):
        mean_line_x, mean_line_y = self.get_mean_line_points(h_rel, point_num)
        _, default_profile_y = self._get_default_profile_points(h_rel, point_num)

        return mean_line_x, mean_line_y + default_profile_y


class TransSoundProfileStatorProfiler(TransSoundStatorProfiler, TransSoundProfileRotorProfiler):
    pass


class A40SubSoundRotorProfiler(SubSoundRotorProfiler):
    @classmethod
    def get_profile_y_rel(cls, x_rel):
        x_percent_list = [1, 1.5, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 95, 100]
        y_percent_list = [1.14, 1.43, 1.85, 2.55, 3.09, 3.525, 4.16, 4.55, 4.788, 4.927, 4.936, 5, 4.858,
                          4.443, 3.783, 2.85, 1.722, 1.003, 0]

        return np.interp((1 - x_rel) * 100, x_percent_list, y_percent_list) / 100


class A40SubSoundStatorProfiler(SubSoundStatorProfiler):
    @classmethod
    def get_profile_y_rel(cls, x_rel):
        return A40SubSoundRotorProfiler.get_profile_y_rel(x_rel)

