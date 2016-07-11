from . import geometry_results
import numpy as np
import copy
import scipy.optimize
import pandas as pd


class DynamicBladeProfile(geometry_results.BladeProfile):
    def __init__(self, pressure_side_x, pressure_side_y, suction_side_x, suction_side_y, height=None, h_rel=None,
                 installation_angle=0, thickness=None):
        geometry_results.BladeProfile.__init__(self, pressure_side_x, pressure_side_y, suction_side_x, suction_side_y,
                                               height, h_rel, installation_angle, thickness)
        self.normal_force = 0
        self.M_q_ksi = 0
        self.M_q_eta = 0
        self.M_omega_ksi = 0
        self.M_omega_eta = 0
        self._M_u = None
        self._M_v = None

    @classmethod
    def from_profiler(cls, profiler, h_rel, point_num=100):
        pressure_side_x, pressure_side_y = profiler.get_pressure_side_points(h_rel, point_num)
        suction_side_x, suction_side_y = profiler.get_suction_side_points(h_rel, point_num)
        profile_height = profiler.get_axis_distance(h_rel)
        installation_angle = profiler.installation_angle(h_rel)

        if profiler.is_stator():
            pressure_side_x, pressure_side_y = cls._reflect(pressure_side_x, pressure_side_y, 0)
            suction_side_x, suction_side_y = cls._reflect(suction_side_x, suction_side_y, 0)

        result = DynamicBladeProfile(pressure_side_x, pressure_side_y, suction_side_x, suction_side_y,
                                     profile_height, h_rel, installation_angle)
        result.chord = profiler.blading_geometry.chord_length(h_rel)
        return result

    @property
    def M_ksi(self):
        return self.M_omega_ksi + self.M_q_ksi

    @property
    def M_eta(self):
        return self.M_omega_eta + self.M_q_eta

    @property
    def M_u(self):
        if not self._M_u:
            bend_moment_vector = np.dot(self._bend_moment_matrix,
                                        np.array((self.M_ksi, self.M_eta)))
            main_bend_moment_vector = np.dot(self._to_main_axes_matrix, bend_moment_vector)

            self._M_u, self._M_v = main_bend_moment_vector

        return self._M_u

    @property
    def M_v(self):
        if not self._M_v:
            bend_moment_vector = np.dot(self._bend_moment_matrix,
                                        np.array((self.M_ksi, self.M_eta)))
            main_bend_moment_vector = np.dot(self._to_main_axes_matrix, bend_moment_vector)

            self._M_u, self._M_v = main_bend_moment_vector

        return self._M_v

    def get_central_main_axes_coords(self, x, y):
        coord_vector = np.array((x, y))
        mass_center_vector = np.array((self.x_c, self.y_c))

        central_vector = coord_vector - mass_center_vector
        main_central_vector = np.dot(self._to_main_axes_matrix, central_vector)

        return main_central_vector

    def get_central_main_axes_stress(self, u, v):
        term_1 = self.M_u / self.inertia_moment_u * v
        term_2 = self.M_v / self.inertia_moment_v * u
        term_3 = self.normal_force / self.area

        return term_1 - term_2 + term_3

    def get_stress(self, x, y):
        return self.get_central_main_axes_stress(*self.get_central_main_axes_coords(x, y))

    @property
    def _to_main_axes_matrix(self):
        # свойство возвращает матрицу поворота в систему главных осей лопатки
        return np.array([[np.cos(self.main_axis_angle), -np.sin(self.main_axis_angle)],
                         [np.sin(self.main_axis_angle), np.cos(self.main_axis_angle)]])

    @property
    def _bend_moment_matrix(self):
        # свойство возвращает матрицу поворота изгибающего момента в систему координат лопатки
        # данная матрица необходима вследствие различных систем координат в прочности и теории компрессоров
        return np.array([[np.cos(-np.pi / 2), -np.sin(-np.pi / 2)],
                         [np.sin(-np.pi / 2), np.cos(-np.pi / 2)]])

    def _neutral_line_angle_coef(self):
        factor_1 = self.M_u / self.M_v
        factor_2 = self.inertia_moment_u / self.inertia_moment_v
        return -factor_1 * factor_2

    def _set_stresses(self):    # TODO еще раз проверить: возможно, преобразования координат проведены неверно
        to_main_axis_rotation_matrix = np.array([[np.cos(self.main_axis_angle), -np.sin(self.main_axis_angle)],
                                                 [np.sin(self.main_axis_angle), np.cos(self.main_axis_angle)]])

        bend_moment_rotation_matrix = np.array([[np.cos(-np.pi / 2), -np.sin(-np.pi / 2)],   # матрица переводит вектор момента в систему координат лопатки
                                                [np.sin(-np.pi / 2), np.cos(-np.pi / 2)]])

        bend_moment_vector = np.array([self.M_ksi, self.M_eta])
        bend_moment_vector = np.dot(bend_moment_rotation_matrix, bend_moment_vector)

        pressure_side_points = np.array([self.profile_info_df.pressure_side_x, self.profile_info_df.pressure_side_y])
        suction_side_points = np.array([self.profile_info_df.suction_side_x, self.profile_info_df.suction_side_y])

        main_bend_moment_vector = np.dot(to_main_axis_rotation_matrix, bend_moment_vector)
        main_pressure_side_points = np.dot(to_main_axis_rotation_matrix, pressure_side_points)
        main_suction_side_points = np.dot(to_main_axis_rotation_matrix, suction_side_points)

        main_pressure_side_u, main_pressure_side_v = main_pressure_side_points
        main_suction_side_u, main_suction_side_v = main_suction_side_points

        m_u_coef = main_bend_moment_vector[0] / self.inertia_moment_u
        m_v_coef = main_bend_moment_vector[1] / self.inertia_moment_v

        normal_coef = self.normal_force / self.area

        pressure_side_stress = m_u_coef * main_pressure_side_v - m_v_coef * main_pressure_side_u + normal_coef
        suction_side_stress = m_u_coef * main_suction_side_v - m_v_coef * main_suction_side_u + normal_coef

        self.profile_info_df['pressure_side_stress'] = pressure_side_stress
        self.profile_info_df['suction_side_stress'] = suction_side_stress


class DynamicBlade(geometry_results.Blade):
    def __init__(self, blade_profiles, material=None):
        geometry_results.Blade.__init__(self, blade_profiles)
        self.material = material
        self.omega = 0
        self.aerodynamic_load_x = list()
        self.aerodynamic_load_y = list()

    @classmethod
    def from_profiler(cls, profiler, material=None, blade_profile_num=50, profile_point_num=100):
        h_rel_list = np.linspace(0, 1, blade_profile_num)
        blade_profile_list = list()

        for h_rel in h_rel_list:
            blade_profile_list.append(DynamicBladeProfile.from_profiler(profiler, h_rel, profile_point_num))

        blade = DynamicBlade(blade_profile_list, material)
        blade._set_profiles_thickness()

        blade.omega = np.pi / 30 * profiler.stage_model.n
        blade.aerodynamic_load_x, blade.aerodynamic_load_y = cls._get_aerodynamic_load(profiler, blade)

        blade._calculate_loads()
        blade._set_stresses()

        return blade

    def recalculate_loads(self):
        self.rebuild_axis()
        self._calculate_loads()
        self._set_stresses()

    def get_max_stress_list(self):
        stress_list = []
        for profile in self.blade_profiles:
            suction_side_max = profile.profile_info_df.suction_side_stress.max()
            pressure_side_max = profile.profile_info_df.pressure_side_stress.max()

            stress_list.append(max(suction_side_max, pressure_side_max))

        return stress_list

    def get_optimal_blade_deflection_coefs(self, point_num=10):
        blade_copy = copy.deepcopy(self)

        def optimization_func(deflection_vector):
            deflection_coef_x, deflection_coef_y = deflection_vector

            deflection_func_x = lambda h_rel: deflection_coef_x * h_rel
            deflection_func_y = lambda h_rel: deflection_coef_y * h_rel

            blade_copy.blade_deflection_x_func = deflection_func_x
            blade_copy.blade_deflection_y_func = deflection_func_y

            blade_copy.recalculate_loads()
            stress_array = np.array(blade_copy.get_max_stress_list())

            return max(abs(stress_array))

        h_rel_array = [profile.h_rel for profile in blade_copy.blade_profiles[1:]]
        optimal_deflection_x_list = blade_copy._get_optimal_blade_deflection_x_array()
        optimal_deflection_y_list = blade_copy._get_optimal_blade_deflection_y_array()

        secant_coef_x_list = [optimal_deflection / h_rel for optimal_deflection, h_rel in
                              zip(optimal_deflection_x_list, h_rel_array)]
        secant_coef_y_list = [optimal_deflection / h_rel for optimal_deflection, h_rel in
                              zip(optimal_deflection_y_list, h_rel_array)]

        secant_coef_x_array = np.linspace(min(secant_coef_x_list), max(secant_coef_x_list), point_num)
        secant_coef_y_array = np.linspace(min(secant_coef_y_list), max(secant_coef_y_list), point_num)

        indexer = pd.MultiIndex.from_product([secant_coef_x_array, secant_coef_y_array])

        result = (0, 0)
        min_stress = 1e50

        for item in indexer:
            curr_stress = optimization_func(item)

            if curr_stress < min_stress:
                min_stress = curr_stress
                result = item

        return result

    def get_optimal_blade_deflection_funcs(self, point_num=10):
        deflection_x_coef, deflection_y_coef = self.get_optimal_blade_deflection_coefs(point_num)

        return lambda h_rel: deflection_x_coef * h_rel, lambda h_rel: deflection_y_coef * h_rel

    def make_momentless_blade(self, point_num=10):
        self.blade_deflection_x_func, self.blade_deflection_y_func = self.get_optimal_blade_deflection_funcs(point_num)
        self.recalculate_loads()

    @classmethod
    def _get_aerodynamic_load(cls, profiler, blade):
        h_rel_list = [profile.h_rel for profile in blade.blade_profiles]

        load_x_list = []
        load_y_list = []

        for h_rel, profile in zip(h_rel_list, blade.blade_profiles):
            inlet_triangle = profiler.get_inlet_triangle(h_rel)
            outlet_triangle = profiler.get_outlet_triangle(h_rel)

            c_1_x = inlet_triangle.c_a
            c_2_x = outlet_triangle.c_a

            c_1_y = inlet_triangle.c_u
            c_2_y = outlet_triangle.c_u

            inlet_pressure = profiler.get_inlet_pressure(h_rel)
            outlet_pressure = profiler.get_outlet_pressure(h_rel)
            inlet_gas_density = profiler.get_inlet_density(h_rel)

            geom_factor = 2 * np.pi * profile.height / profiler.blading_geometry.blade_number

            load_x = geom_factor * ((inlet_pressure - outlet_pressure) - inlet_gas_density * c_1_x * (c_2_x - c_1_x))
            load_y = -geom_factor * inlet_gas_density * c_1_x * (c_2_y - c_1_y)

            load_x_list.append(load_x)
            load_y_list.append(load_y)

        return np.array(load_x_list), np.array(load_y_list)

    def _calculate_loads(self):
        for i in range(len(self.blade_profiles)):
            root_profile = self.blade_profiles[i]
            profiles = self.blade_profiles[i:]

            root_profile.normal_force = self._normal_force(profiles)
            root_profile.M_q_ksi = self._aerodynamic_bend_moment_ksi(profiles)
            root_profile.M_q_eta = self._aerodynamic_bend_moment_eta(profiles)

            root_profile.M_omega_ksi = self._centrifugal_bend_moment_ksi(profiles)
            root_profile.M_omega_eta = self._centrifugal_bend_moment_eta(profiles)

    def _normal_force(self, profiles):
        blade_part_static_moment = sum([profile.volume * profile.height for profile in profiles])
        return self.material.density * self.omega**2 * blade_part_static_moment

    def _centrifugal_bend_moment_ksi(self, profiles):
        if not self.blade_deflection_y_func:
            return 0

        load_factor = self.material.density * self.omega**2

        z = profiles[0].height
        y = self.blade_deflection_y_func(profiles[0].h_rel)

        h_rel_arr = np.array([profile.h_rel for profile in profiles])

        z_arr = np.array([profile.height for profile in profiles])
        y_arr = self.blade_deflection_y_func(h_rel_arr)

        thickness_arr = np.array([profile.thickness for profile in profiles])
        area_arr = np.array([profile.area for profile in profiles])

        term_1 = z * sum(area_arr * y_arr * thickness_arr)
        term_2 = y * sum(area_arr * z_arr * thickness_arr)

        return load_factor * (term_1 - term_2)

    def _centrifugal_bend_moment_eta(self, profiles):
        if not self.blade_deflection_x_func:
            return 0

        load_factor = self.material.density * self.omega**2

        z = profiles[0].height
        x = self.blade_deflection_x_func(profiles[0].h_rel)

        h_rel_arr = np.array([profile.h_rel for profile in profiles])

        z_arr = np.array([profile.height for profile in profiles])
        x_arr = self.blade_deflection_x_func(h_rel_arr)

        thickness_arr = np.array([profile.thickness for profile in profiles])
        area_arr = np.array([profile.area for profile in profiles])

        term_1 = z * sum(area_arr * x_arr * thickness_arr)
        term_2 = x * sum(area_arr * z_arr * thickness_arr)

        return load_factor * (term_2 - term_1)

    def _aerodynamic_bend_moment_ksi(self, profiles):
        z = profiles[0].height
        aerodynamic_load_y = self.aerodynamic_load_y[len(self.aerodynamic_load_y) - len(profiles):]
        thickness_arr = np.array([profile.thickness for profile in profiles])
        z_arr = np.array([profile.height for profile in profiles])

        result = sum(aerodynamic_load_y * (z - z_arr) * thickness_arr)

        return result

    def _aerodynamic_bend_moment_eta(self, profiles):
        z = profiles[0].height
        aerodynamic_load_x = self.aerodynamic_load_x[len(self.aerodynamic_load_x) - len(profiles):]
        thickness_arr = np.array([profile.thickness for profile in profiles])
        z_arr = np.array([profile.height for profile in profiles])

        result = sum(aerodynamic_load_x * (z_arr - z) * thickness_arr)

        return result

    @classmethod
    def _static_moment_function(cls, profiles):
        z = profiles[0].height
        thickness_arr = np.array([profile.thickness for profile in profiles])
        area_arr = np.array([profile.area for profile in profiles])
        z_arr = np.array([profile.height for profile in profiles])

        return sum(area_arr * (z_arr - z) * thickness_arr)

    def _set_stresses(self):
        for profile in self.blade_profiles:
            profile._set_stresses()

    def _get_optimal_blade_deflection_y_array(self):

        def get_optimal_blade_deflection_y(profiles, border_index):

            def inner_integral_func(outer_profiles):
                aerodynamic_load_y_arr = self.aerodynamic_load_y[len(self.aerodynamic_load_y) - len(outer_profiles):]
                z_arr = np.array([profile.height for profile in outer_profiles])
                thickness_arr = np.array([profile.thickness for profile in outer_profiles])

                return sum(aerodynamic_load_y_arr * z_arr * thickness_arr)

            def integrand_func(outer_profiles):
                root_profile = outer_profiles[0]

                root_static_moment = self._static_moment_function(outer_profiles)
                root_height = root_profile.height
                integral = inner_integral_func(outer_profiles)

                return 1 / (root_static_moment * root_height**2) * integral

            def outer_integral_func(profiles, border_index):
                result = 0

                for i in range(border_index):
                    outer_profiles = profiles[i:]
                    thickness = outer_profiles[0].thickness

                    result += integrand_func(outer_profiles) * thickness

                return result

            factor = profiles[border_index].height / (self.material.density * self.omega**2)

            return factor * outer_integral_func(profiles, border_index)

        result = list()

        for border_index in range(len(self.blade_profiles)):
            deflection_x = get_optimal_blade_deflection_y(self.blade_profiles, border_index)
            result.append(deflection_x)

        return result

    def _get_optimal_blade_deflection_x_array(self):

        def get_optimal_blade_deflection_x(profiles, border_index):

            def inner_integral_func(outer_profiles):
                aerodynamic_load_x_arr = self.aerodynamic_load_x[len(self.aerodynamic_load_x) - len(outer_profiles):]
                thickness_arr = np.array([profile.thickness for profile in outer_profiles])

                return sum(aerodynamic_load_x_arr * thickness_arr)

            def integrand_func(outer_profiles):
                root_static_moment = self._static_moment_function(outer_profiles)
                integral = inner_integral_func(outer_profiles)

                return 1 / root_static_moment * integral

            def outer_integral_func(profiles, border_index):
                result = 0

                for i in range(border_index):
                    outer_profiles = profiles[i:]
                    thickness = outer_profiles[0].thickness

                    result += integrand_func(outer_profiles) * thickness

                return result

            factor = 1 / (self.material.density * self.omega**2)

            return factor * outer_integral_func(profiles, border_index)

        result = list()

        for border_index in range(len(self.blade_profiles)):
            deflection_y = get_optimal_blade_deflection_x(self.blade_profiles, border_index)
            result.append(deflection_y)

        return result