import numpy as np
import pandas as pd


class BladeProfile:
    def __init__(self, pressure_side_x, pressure_side_y, suction_side_x, suction_side_y, height=None, h_rel=None,
                 installation_angle=0, thickness=None, is_monolith=None):
        self.pressure_side_x = np.array(pressure_side_x)
        self.pressure_side_y = np.array(pressure_side_y)
        self.suction_side_x = np.array(suction_side_x)
        self.suction_side_y = np.array(suction_side_y)
        self.height = height
        self.h_rel = h_rel
        self.installation_angle = installation_angle
        self.thickness = thickness
        self.is_monolith = is_monolith
        self.chord = None

        self.profile_info_df = self._get_initial_profile_info_df()

        self.area = None
        self.x_c = None
        self.y_c = None
        self.inertia_moment_u = None
        self.inertia_moment_v = None
        self.inertia_moment_ksi = None
        self.inertia_moment_eta = None
        self.central_centrifugal_moment = None

        self._set_area()
        self._set_mass_center()
        self._set_inertia_moments()
        self._extend_geom_info_df()
        self._correct_position()

    def _get_initial_profile_info_df(self):
        pressure_side_mean_x = (self.pressure_side_x[1:] + self.pressure_side_x[:-1]) / 2
        pressure_side_mean_y = (self.pressure_side_y[1:] + self.pressure_side_y[:-1]) / 2
        suction_side_mean_x = (self.suction_side_x[1:] + self.suction_side_x[:-1]) / 2
        suction_side_mean_y = (self.suction_side_y[1:] + self.suction_side_y[:-1]) / 2

        profile_mean_x = (pressure_side_mean_x + suction_side_mean_x) / 2
        profile_mean_y = (pressure_side_mean_y + suction_side_mean_y) / 2

        profile_dx = self.pressure_side_x[1:] - self.pressure_side_x[:-1]
        profile_dy = abs(pressure_side_mean_y - suction_side_mean_y)

        mass_center_x = profile_mean_x
        mass_center_y = profile_mean_y
        area = profile_dx * profile_dy

        return pd.DataFrame({'pressure_side_x': pressure_side_mean_x, 'pressure_side_y': pressure_side_mean_y,
                             'suction_side_x': suction_side_mean_x, 'suction_side_y': suction_side_mean_y,
                             'x_c': mass_center_x, 'y_c': mass_center_y, 'area': area})

    @property
    def back_edge_x(self):
        return self.pressure_side_x[0]

    @property
    def back_edge_y(self):
        return self.pressure_side_y[0]

    def _set_area(self):
        self.area = sum(self.profile_info_df.area)

    def _set_mass_center(self):
        if not self.x_c:
            static_moment_y = sum(self.profile_info_df.area * self.profile_info_df.x_c)
            static_moment_x = sum(self.profile_info_df.area * self.profile_info_df.y_c)

            self.x_c = static_moment_y / self.area
            self.y_c = static_moment_x / self.area

    def _set_inertia_moments(self):
        inertia_moment_y = sum(self.profile_info_df.area * self.profile_info_df.x_c ** 2)
        inertia_moment_x = sum(self.profile_info_df.area * self.profile_info_df.y_c ** 2)
        inertia_moment_xy = sum(self.profile_info_df.area * self.profile_info_df.x_c * self.profile_info_df.y_c)

        central_inertia_moment_ksi = inertia_moment_x - self.y_c ** 2 * self.area
        central_inertia_moment_eta = inertia_moment_y - self.x_c ** 2 * self.area
        central_inertia_moment_ksi_eta = inertia_moment_xy - self.x_c * self.y_c * self.area

        term_1 = (central_inertia_moment_ksi + central_inertia_moment_eta) / 2
        term_2 = 0.5 * ((central_inertia_moment_ksi - central_inertia_moment_eta)**2 +
                        central_inertia_moment_ksi_eta**2)**0.5

        self.inertia_moment_u = term_1 - term_2
        self.inertia_moment_v = term_1 + term_2
        self.inertia_moment_ksi = central_inertia_moment_ksi
        self.inertia_moment_eta = central_inertia_moment_eta
        self.central_centrifugal_moment = central_inertia_moment_ksi_eta

    def _extend_geom_info_df(self):
        self.profile_info_df['x_c_offset'] = self.profile_info_df.x_c - self.x_c
        self.profile_info_df['y_c_offset'] = self.profile_info_df.y_c - self.y_c

    @property
    def volume(self):
        return self.area * self.thickness

    @property
    def main_axis_angle(self):
        return -self.installation_angle  # используется угол установки потому, что погрешность небольшая,
                                        # а с арктангенсом бороться не нужно

    @classmethod
    def from_profiler(cls, profiler, h_rel, point_num=100):
        pressure_side_x, pressure_side_y = profiler.get_pressure_side_points(h_rel, point_num)
        suction_side_x, suction_side_y = profiler.get_suction_side_points(h_rel, point_num)
        profile_height = profiler.get_axis_distance(h_rel)
        installation_angle = profiler.installation_angle(h_rel)
        is_monolith = profiler.is_monolith()

        if profiler.is_stator():
            pressure_side_x, pressure_side_y = cls._reflect(pressure_side_x, pressure_side_y, np.pi / 2)
            suction_side_x, suction_side_y = cls._reflect(suction_side_x, suction_side_y, np.pi / 2)

            installation_angle = -installation_angle

        result = BladeProfile(pressure_side_x, pressure_side_y, suction_side_x, suction_side_y,
                              profile_height, h_rel, installation_angle, is_monolith)
        result.chord = profiler.blading_geometry.chord_length(h_rel)

        if not is_monolith:
            result.x_c, result.y_c = profiler.get_mass_center(h_rel)

        return result

    @classmethod
    def _rotate(cls, x_arr, y_arr, angle):
        rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])

        point_array = np.array([x_arr, y_arr])

        x_result, y_result = np.dot(rotation_matrix, point_array)

        return x_result, y_result

    @classmethod
    def _translate(cls, x_arr, y_arr, x_offset, y_offset):
        return x_arr + x_offset, y_arr + y_offset

    @classmethod
    def _reflect(cls, x_arr, y_arr, symmetry_axis_angle):
        reflect_matrix = np.array([[np.cos(2 * symmetry_axis_angle), np.sin(2 * symmetry_axis_angle)],
                                   [np.sin(2 * symmetry_axis_angle), -np.cos(2 * symmetry_axis_angle)]])

        point_array = np.array([x_arr, y_arr])

        x_result, y_result = np.dot(reflect_matrix, point_array)

        return x_result, y_result

    @classmethod
    def _scale(cls, x_arr, y_arr, scale_factor):
        return x_arr * scale_factor, y_arr * scale_factor

    def _perform_action(self, foo, *args):
        self.pressure_side_x, self.pressure_side_y = foo(self.pressure_side_x, self.pressure_side_y, *args)
        self.suction_side_x, self.suction_side_y = foo(self.suction_side_x, self.suction_side_y, *args)

        self.profile_info_df.x_c, self.profile_info_df.y_c = \
            foo(self.profile_info_df.x_c, self.profile_info_df.y_c, *args)
        self.profile_info_df.pressure_side_x, self.profile_info_df.pressure_side_y = \
            foo(self.profile_info_df.pressure_side_x, self.profile_info_df.pressure_side_y, *args)
        self.profile_info_df.suction_side_x, self.profile_info_df.suction_side_y = \
            foo(self.profile_info_df.suction_side_x, self.profile_info_df.suction_side_y, *args)

        self._extend_geom_info_df()

        self.x_c, self.y_c = foo(self.x_c, self.y_c, *args)

    def _correct_position(self):
        self.translate(-self.x_c, -self.y_c)

        if self.installation_angle:
            installation_angle = self.installation_angle
            self.installation_angle = 0
            self.rotate(installation_angle)

    def rotate(self, angle):
        x_0, y_0 = self.back_edge_x, self.back_edge_y
        x_c, y_c = self.x_c, self.y_c

        self._perform_action(self._translate, -x_0, -y_0)
        self._perform_action(self._rotate, angle)
        self._perform_action(self._translate, x_c - self.x_c, y_c - self.y_c)

        self.installation_angle += angle

    def translate(self, x_offset, y_offset):
        self._perform_action(self._translate, x_offset, y_offset)

    def reflect(self, symmetry_axis_angle):
        self._perform_action(self._reflect, symmetry_axis_angle)

    def scale(self, scale_factor):
        self._perform_action(self._scale, scale_factor)
        self.height *= scale_factor
        self.chord *= scale_factor


class Blade:
    def __init__(self, blade_profiles):
        self.blade_profiles = blade_profiles

        self.blade_deflection_x_func = None
        self.blade_deflection_y_func = None
        self.is_stator = None

    @classmethod
    def from_profiler(cls, profiler, blade_profile_num=50, profile_point_num=100):
        h_rel_list = np.linspace(0, 1, blade_profile_num)
        blade_profile_list = list()

        for h_rel in h_rel_list:
            blade_profile_list.append(BladeProfile.from_profiler(profiler, h_rel, profile_point_num))

        blade = Blade(blade_profile_list)
        blade._set_profiles_thickness()
        blade.is_stator = profiler.is_stator()

        return blade

    @property
    def root_profile(self):
        inner_profile = self.blade_profiles[0]
        outer_profile = self.blade_profiles[-1]

        inner_proj = abs(inner_profile.chord * np.sin(inner_profile.installation_angle))
        outer_proj = abs(outer_profile.chord * np.sin(outer_profile.installation_angle))

        if inner_proj > outer_proj:
            return inner_profile
        else:
            return outer_profile

    @property
    def root_x_c(self):
        return self.root_profile.x_c

    @property
    def root_y_c(self):
        return self.root_profile.y_c

    @property
    def root_z_c(self):
        return self.root_profile.height

    @property
    def root_chord(self):
        return self.root_profile.chord

    @property
    def root_chord_axial_projection(self):
        root_profile = self.root_profile
        return abs(root_profile.chord * np.sin(root_profile.installation_angle))

    @property
    def root_max_axial_coord(self):
        root_profile = self.root_profile
        max_coord = max(root_profile.profile_info_df.pressure_side_y.max(),
                        root_profile.profile_info_df.suction_side_y.max())
        return max_coord

    @property
    def root_min_axial_coord(self):
        root_profile = self.root_profile
        min_coord = max(root_profile.profile_info_df.pressure_side_y.min(),
                        root_profile.profile_info_df.suction_side_y.min())
        return min_coord

    def root_x_offset(self, profile):
        return profile.x_c - self.root_x_c

    def root_y_offset(self, profile):
        return profile.y_c - self.root_y_c

    def root_z_offset(self, profile):
        return profile.height - self.root_z_c

    def translate(self, x_offset, y_offset):
        for profile in self.blade_profiles:
            profile.translate(x_offset, y_offset)

    def scale(self, scale_factor):
        for profile in self.blade_profiles:
            profile.scale(scale_factor)

    def reflect(self, axis_angle):
        for profile in self.blade_profiles:
            profile.reflect(axis_angle)

    def rebuild_axis(self):
        if not self.blade_deflection_x_func:
            self.blade_deflection_x_func = lambda h_rel: h_rel * 0

        if not self.blade_deflection_y_func:
            self.blade_deflection_y_func = lambda h_rel: h_rel * 0

        h_rel_array = np.array([profile.h_rel for profile in self.blade_profiles])

        # назначение выносов ведется таким образом для того, чтобы соответствовать системе координат, используемой при
        # расчете прочности
        blade_deflection_x_array = self.blade_deflection_y_func(h_rel_array)
        blade_deflection_y_array = -self.blade_deflection_x_func(h_rel_array)

        for profile, blade_deflection_x, blade_deflection_y in zip(self.blade_profiles,
                                                                   blade_deflection_x_array, blade_deflection_y_array):
            profile.translate(blade_deflection_x, blade_deflection_y)

    def _set_profiles_thickness(self):
        height_list = np.array([profile.height for profile in self.blade_profiles])
        mean_height_list = list((height_list[1:] + height_list[:-1]) / 2)
        mean_height_list = np.array([self.blade_profiles[0].height] + mean_height_list +
                                    [self.blade_profiles[-1].height])
        thickness_arr = mean_height_list[1:] - mean_height_list[:-1]

        for profile, thickness in zip(self.blade_profiles, thickness_arr):
            profile.thickness = thickness


class CompressorBlading:
    def __init__(self, blades):
        self.blades = blades

    @classmethod
    def from_compressor(cls, compressor, blade_profile_num=10, profile_point_num=20, blade_axial_offset=0.15):
        blade_list = list()

        try:
            blade_axial_offset_list = list(blade_axial_offset)
        except TypeError:
            blade_axial_offset_list = [blade_axial_offset] * len(compressor.stages) * 2

        for stage in compressor.stages:
            blade_list.append(Blade.from_profiler(stage.rotor_profiler, blade_profile_num, profile_point_num))
            blade_list.append(Blade.from_profiler(stage.stator_profiler, blade_profile_num, profile_point_num))

        for curr_blade, prev_blade, extra_offset_coef in zip(blade_list[1:], blade_list[:-1], blade_axial_offset_list):
            mass_center_offset = prev_blade.root_y_c

            prev_blade_chord_offset = prev_blade.root_min_axial_coord - prev_blade.root_y_c
            curr_blade_chord_offset = curr_blade.root_y_c - curr_blade.root_max_axial_coord
            extra_offset = -curr_blade.root_chord * extra_offset_coef

            axial_offset = mass_center_offset + curr_blade_chord_offset + prev_blade_chord_offset + extra_offset
            curr_blade.translate(0, axial_offset)

        blading = CompressorBlading(blade_list)
        blading.reflect(0)

        return blading

    @classmethod
    def aligned_from_compressor(cls, compressor, blade_profile_num=10, profile_point_num=20, blade_axial_offset=0.15):
        compressor_blading = cls.from_compressor(compressor, blade_profile_num, profile_point_num, blade_axial_offset)
        compressor_blading._align()

        return compressor_blading

    def insert_first_blade(self, blade_model, blade_axial_offset_coef=0.15):
        blade_model.reflect(0)
        first_blade = self.blades[0]

        first_blade_chord_setup = first_blade.root_min_axial_coord   # центр масс ВНА устанавливается в лобовую точку первой лопатки
        blade_model_chord_offset = blade_model.root_max_axial_coord - blade_model.root_y_c    # конец хорды ВНА устанавливается в лобовую точку первой лопатки
        extra_offset = blade_model.root_chord * blade_axial_offset_coef     # утанавливается необходимый зазор

        axial_offset = first_blade_chord_setup - blade_model_chord_offset - extra_offset

        blade_model.translate(0, axial_offset)

        self.blades = [blade_model] + self.blades

    def insert_last_blade(self, blade_model, blade_axial_offset_coef=0.3):
        blade_model.reflect(0)
        last_blade = self.blades[-1]

        last_blade_chord_setup = last_blade.root_max_axial_coord   # центр масс ВНА устанавливается в заднюю точку последней лопатки
        blade_model_chord_offset = blade_model.root_y_c - blade_model.root_min_axial_coord  # конец хорды ВНА устанавливается в заднюю точку последней лопатки
        extra_offset = last_blade.root_chord * blade_axial_offset_coef

        axial_offset = last_blade_chord_setup + blade_model_chord_offset + extra_offset

        blade_model.translate(0, axial_offset)

        self.blades.append(blade_model)

    def translate(self, x_offset, y_offset):
        for blade in self.blades:
            blade.translate(x_offset, y_offset)

    def scale(self, scale_factor):
        for blade in self.blades:
            blade.scale(scale_factor)

    def reflect(self, axis_angle):
        for blade in self.blades:
            blade.reflect(axis_angle)

    def _align(self):
        root_profile = self.blades[0].root_profile
        y_offset = -root_profile.pressure_side_y.max()

        self.translate(0, y_offset)
        self.scale(1000)
