import matplotlib.pyplot as plt
from matplotlib.delaunay import interpolate
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import scipy.optimize
import pandas as pd
from . import geometry_results
from scipy import interpolate


def plot_velocity_triangle(velocity_triangle):
    origin = np.array((0, velocity_triangle.c_a))

    c_point_offset = np.array((velocity_triangle.c_u, -velocity_triangle.c_a))
    w_point_offset = np.array((velocity_triangle.c_u - velocity_triangle.u_m, -velocity_triangle.c_a))

    c_vector = origin + c_point_offset
    w_vector = origin + w_point_offset

    c_line_x = (origin[0], c_vector[0])
    c_line_y = (origin[1], c_vector[1])

    w_line_x = (origin[0], w_vector[0])
    w_line_y = (origin[1], w_vector[1])

    plt.plot(c_line_x, c_line_y)
    plt.plot(w_line_x, w_line_y)


def plot_profiler_triangles(profiler, h_rel):

    inlet_triangle = profiler.get_inlet_triangle(h_rel)
    outlet_triangle = profiler.get_outlet_triangle(h_rel)

    plot_velocity_triangle(inlet_triangle)
    plot_velocity_triangle(outlet_triangle)
    plt.title('h_rel = %3.f' % h_rel)
    plt.legend(['c_in', 'w_in', 'c_out', 'w_out'])
    plt.show()


def plot_diffusion_rate(stage):
    plt.plot(*stage.rotor_profiler.get_diffusion_rate_profile())
    plt.plot(*stage.stator_profiler.get_diffusion_rate_profile())
    plt.grid()
    plt.legend(['rotor', 'stator'])


def plot_max_stress(blade):
    stress_list = []
    h_rel_list = []

    for profile in blade.blade_profiles:
        suction_side_max = profile.profile_info_df.suction_side_stress.max()
        pressure_side_max = profile.profile_info_df.pressure_side_stress.max()

        h_rel_list.append(profile.h_rel)
        stress_list.append(max([suction_side_max, pressure_side_max]) / 1e6)

    plt.plot(stress_list, h_rel_list)


def get_lattice_density(compressor):
    result = list()

    for stage in compressor.stages:
        result.append(stage.rotor_profiler.blading_geometry.mean_lattice_density)
        result.append(stage.stator_profiler.blading_geometry.mean_lattice_density)

    return pd.Series(result)


def get_blade_number(compressor):
    result = list()

    for stage in compressor.stages:
        result.append(stage.rotor_profiler.blading_geometry.blade_number)
        result.append(stage.stator_profiler.blading_geometry.blade_number)

    return pd.Series(result)


class PostProcessor:
    @classmethod
    def plot_profile(cls, profile):
        plt.plot(profile.pressure_side_x, profile.pressure_side_y, color='blue')
        plt.plot(profile.suction_side_x, profile.suction_side_y, color='blue')
        plt.axis('equal')

    @classmethod
    def plot_profile_stresses(cls, profile, fig):
        def get_stress_func_coefs(profile):
            median_coord = len(profile.pressure_side_x) // 2

            coord_matrix = np.array(
                [[profile.pressure_side_x[0] - profile.x_c, profile.pressure_side_y[0] - profile.y_c, 1],
                 [profile.pressure_side_x[-1] - profile.x_c, profile.pressure_side_y[-1] - profile.y_c, 1],
                 [profile.pressure_side_x[median_coord] - profile.x_c,
                  profile.pressure_side_y[median_coord] - profile.y_c, 1]])

            stress_vector = np.array([profile.get_stress(point[0], point[1]) for point in coord_matrix])
            k_1, k_2, b = np.dot(np.linalg.inv(coord_matrix), stress_vector)

            return k_1, k_2, b

        def plot_moment_vector(profile, subplot):
            M_ksi = profile.M_q_ksi + profile.M_omega_ksi
            M_eta = profile.M_q_eta + profile.M_omega_eta
            rotation_matrix = np.array([[np.cos(np.pi / 2), np.sin(np.pi / 2)],
                                        [-np.sin(np.pi / 2), np.cos(np.pi / 2)]])

            M_x, M_y = np.dot(rotation_matrix, (M_ksi, M_eta))

            chord_length = profile.chord

            moment_vector_length = (M_x ** 2 + M_y ** 2) ** 0.5
            normal_moment_vector = np.array([M_x, M_y]) / moment_vector_length * chord_length * 0.4

            start_vector = np.array([profile.x_c, profile.y_c])
            offset_vector = np.array(normal_moment_vector)
            text_correction_vector = np.array([offset_vector[0], 0]) * 0.3

            #plt.arrow(profile.x_c, profile.y_c, *normal_moment_vector, head_width=0.005, linewidth=5e-5, color='blue')
            #plt.text(*(start_vector + 0.5 * offset_vector + text_correction_vector), r'$\vec{M}$', fontsize=20)
            subplot.arrow(profile.x_c, profile.y_c, *normal_moment_vector, head_width=0.005, linewidth=5e-5, color='blue')
            subplot.text(*(start_vector + 0.5 * offset_vector + text_correction_vector), r'$\vec{M}$', fontsize=20)

        def plot_neutral_line(profile, subplot):
            k_1, k_2, _ = get_stress_func_coefs(profile)

            neutral_line_func = lambda x: profile.y_c - k_1 / k_2 * (x - profile.x_c)

            x_min_0 = profile.pressure_side_x.min()
            x_max_0 = profile.pressure_side_x.max()
            delta_x = x_max_0 - x_min_0

            x_min = x_min_0 - 0.1 * delta_x
            x_max = x_max_0 + 0.1 * delta_x

            x_arr = np.array([x_min, x_max])
            y_arr = neutral_line_func(x_arr)

            subplot.plot(x_arr, y_arr, color='blue')
            subplot.text(x_arr[-1], y_arr[-1], '$Нейтральная \/\ линия$', fontsize=16, horizontalalignment='center')

        def plot_stress_diagram_axis(profile, subplot):
            k_1, k_2, _ = get_stress_func_coefs(profile)

            axis_func = lambda x: profile.y_c + k_2 / k_1 * (x - profile.x_c)

            x_min_0 = profile.pressure_side_x.min()
            x_max_0 = profile.pressure_side_x.max()
            delta_x = x_max_0 - x_min_0

            x_min = x_min_0 - 0.1 * delta_x
            x_max = x_max_0 + 0.1 * delta_x

            x_arr = np.array([x_min, x_max])
            y_arr = axis_func(x_arr)

            subplot.plot(x_arr, y_arr, color='green')

        def get_coord_masks(profile):
            k_1, k_2, _ = get_stress_func_coefs(profile)
            axis_rotation_angle = np.arctan(-k_1 / k_2)

            axis_distance_func = lambda x, y: abs(-x * np.sin(axis_rotation_angle) + y * np.cos(axis_rotation_angle))

            pressure_side_distance_array = np.array([axis_distance_func(x, y) for x, y in
                                                     zip(profile.pressure_side_x, profile.pressure_side_y)])
            suction_side_distance_array = np.array([axis_distance_func(x, y) for x, y in
                                                    zip(profile.suction_side_x, profile.suction_side_y)])

            pressure_side_mask = pressure_side_distance_array == max(pressure_side_distance_array)
            suction_side_mask = suction_side_distance_array == max(suction_side_distance_array)

            return pressure_side_mask, suction_side_mask

        def get_extremal_point_projections(profile):
            k_1, k_2, _ = get_stress_func_coefs(profile)

            def get_point_projection(x, y):
                k = k_2 / k_1

                x_proj = (y - profile.y_c + k * profile.x_c + x / k) / (k + 1 / k)
                y_proj = k * (x_proj - profile.x_c) + profile.y_c

                return x_proj, y_proj

            pressure_side_mask, suction_side_mask = get_coord_masks(profile)

            pressure_side_x = profile.pressure_side_x[pressure_side_mask][0]
            pressure_side_y = profile.pressure_side_y[pressure_side_mask][0]

            suction_side_x = profile.suction_side_x[suction_side_mask][0]
            suction_side_y = profile.suction_side_y[suction_side_mask][0]

            pressure_side_proj = get_point_projection(pressure_side_x, pressure_side_y)
            suction_side_proj = get_point_projection(suction_side_x, suction_side_y)

            return np.array(pressure_side_proj), np.array(suction_side_proj)

        def get_diagram_polygons(profile):
            k_1, k_2, _ = get_stress_func_coefs(profile)
            pressure_side_proj, suction_side_proj = get_extremal_point_projections(profile)

            pressure_side_len = np.linalg.norm(pressure_side_proj)
            suction_side_len = np.linalg.norm(suction_side_proj)

            pressure_side_offset = 0.25 * profile.chord
            suction_side_offset = -suction_side_len / pressure_side_len * pressure_side_offset

            neutral_line_vec = -np.array([1, -k_1 / k_2]) / (1 + (k_1 / k_2)**2)**0.5

            pressure_side_point = pressure_side_proj + pressure_side_offset * neutral_line_vec
            suction_side_point = suction_side_proj + suction_side_offset * neutral_line_vec

            pressure_side_triangle = [np.array((profile.x_c, profile.y_c)), pressure_side_proj, pressure_side_point]
            suction_side_triangle = [np.array((profile.x_c, profile.y_c)), suction_side_proj, suction_side_point]

            return pressure_side_triangle, suction_side_triangle

        def plot_triangle_hatch(triangle, subplot, hatch_dist):
            start_point = triangle[0]

            axis_vec = triangle[1] - triangle[0]
            line_vec = triangle[2] - triangle[0]

            max_axis_dist = np.linalg.norm(axis_vec)

            hatch_num = int(max_axis_dist // hatch_dist)

            for i in range(hatch_num):
                weight = i / hatch_num
                axis_point = start_point + axis_vec * weight
                line_point = start_point + line_vec * weight

                subplot.plot((axis_point[0], line_point[0]), (axis_point[1], line_point[1]), color='green')

        def plot_diagram_polygons(profile, subplot):
            pressure_side_triangle, suction_side_triangle = get_diagram_polygons(profile)

            subplot.add_patch(plt.Polygon(pressure_side_triangle, closed=True, fill=False, hatch=None, color='green'))
            subplot.add_patch(plt.Polygon(suction_side_triangle, closed=True, fill=False, hatch=None, color='green'))

            plot_triangle_hatch(pressure_side_triangle, subplot, 0.001)
            plot_triangle_hatch(suction_side_triangle, subplot, 0.001)

        def add_stress_labels(profile, subplot):
            pressure_side_mask, suction_side_mask = get_coord_masks(profile)

            pressure_side_point = np.array([profile.pressure_side_x[pressure_side_mask][0],
                                            profile.pressure_side_y[pressure_side_mask][0]])

            suction_side_point = np.array([profile.suction_side_x[suction_side_mask][0],
                                           profile.suction_side_y[suction_side_mask][0]])

            pressure_side_triangle, suction_side_triangle = get_diagram_polygons(profile)

            pressure_side_proj = pressure_side_triangle[1]
            suction_side_proj = suction_side_triangle[1]

            k_1, k_2, _ = get_stress_func_coefs(profile)
            pressure_side_stress = k_1 * pressure_side_point[0] + k_2 * pressure_side_point[1]
            suction_side_stress = k_1 * suction_side_point[0] + k_2 * suction_side_point[1]

            pressure_side_correction = np.array([0, 0])
            suction_side_correction = np.array([-0.05, 0])

            pressure_side_proj += pressure_side_correction
            suction_side_proj += suction_side_correction

            subplot.text(pressure_side_proj[0], pressure_side_proj[1], '$\sigma = %.1f \/\ МПа$' % (pressure_side_stress / 1e6), fontsize=16)
            subplot.text(suction_side_proj[0], suction_side_proj[1], '$\sigma = %.1f \/\ МПа$' % (suction_side_stress / 1e6), fontsize=16)

        ax = fig.add_subplot(111)

        plot_neutral_line(profile, ax)
        plot_stress_diagram_axis(profile, ax)
        plot_moment_vector(profile, ax)
        plot_diagram_polygons(profile, ax)
        add_stress_labels(profile, ax)
        cls.plot_profile(profile)


    @classmethod
    def plot_blade(cls, blade):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        for profile in blade.blade_profiles:
            ax.plot(profile.pressure_side_x, profile.pressure_side_y, profile.height, color='blue')
            ax.plot(profile.suction_side_x, profile.suction_side_y, profile.height, color='blue')

        plt.xlabel('x')
        plt.ylabel('y')
        plt.axis('equal')

    @classmethod
    def plot_blade_contour(cls, blade):
        inlet_line_df = cls._get_blade_inlet_line(blade)
        outlet_line_df = cls._get_blade_outlet_line(blade)

        plt.plot(inlet_line_df.x, inlet_line_df.y, color='blue')
        plt.plot(outlet_line_df.x, outlet_line_df.y, color='blue')
        plt.axis('equal')
        plt.legend(['inlet', 'outlet'])
        plt.ylim(ymin=0)

    @classmethod
    def plot_compressor_blading(cls, compressor_blading):
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_subplot(111, projection='3d')

        for blade in compressor_blading.blades:
            cls._plot_blade(ax, blade)

    @classmethod
    def plot_compressor_blading_contour(cls, compressor_blading, point_num=50):
        for blade in compressor_blading.blades:
            cls.plot_blade_contour(blade)

        inner_line = cls._get_inner_line(compressor_blading)
        outer_line = cls._get_outer_line(compressor_blading)

        plt.plot(inner_line.x, inner_line.y, color='red')
        plt.plot(outer_line.x, outer_line.y, color='red')

        smooth_inner_line = cls._get_smooth_inner_line(compressor_blading, point_num)
        plt.plot(smooth_inner_line.x, smooth_inner_line.y, color='green')

        shaft_contour = cls._get_shaft_contour(compressor_blading)
        plt.plot(shaft_contour.x, shaft_contour.y, color='magenta')

    @classmethod
    def get_profile_pressure_side_df(cls, profile):
        df = pd.DataFrame({'x': profile.pressure_side_x, 'y': profile.pressure_side_y})
        return df

    @classmethod
    def get_profile_suction_side_df(cls, profile):
        return pd.DataFrame({'x': profile.suction_side_x, 'y': profile.suction_side_y})

    @classmethod
    def get_blade_pressure_side_df(cls, blade, save_path=None):
        profile_df_list = list()

        for profile in blade.blade_profiles:
            profile_df_list.append(cls.get_profile_pressure_side_df(profile))

        result = pd.concat(profile_df_list)

        z = result['z']
        z -= z.min()
        result['z'] = z

        if save_path:
            result.to_csv(save_path)

        return result

    @classmethod
    def get_blade_suction_side_df(cls, blade, save_path=None):
        profile_df_list = list()

        for profile in blade.blade_profiles:
            profile_df_list.append(cls.get_profile_suction_side_df(profile))

        result = pd.concat(profile_df_list)

        z = result['z']
        z -= z.min()
        result['z'] = z

        if save_path:
            result.to_csv(save_path)

        return result

    @classmethod
    def get_profile_boundary_coordinates(cls, profile, excel_writer=None):
        profile_x_in, profile_y_in = cls._get_profile_inlet_point(profile)
        profile_x_out, profile_y_out = cls._get_profile_outlet_point(profile)

        df = pd.DataFrame({'x_in': [profile_x_in], 'x_out': [profile_x_out],
                           'y_in': [profile_y_in], 'y_out': [profile_y_out]})

        if excel_writer:
            df.to_excel(excel_writer)

        return df

    @classmethod
    def get_blade_boundary_coordinates(cls, blade, excel_writer=None):
        profile_in = blade.blade_profiles[0]
        profile_out = blade.blade_profiles[-1]

        df_in = cls.get_profile_boundary_coordinates(profile_in)
        df_in.columns += '_root'

        df_out = cls.get_profile_boundary_coordinates(profile_out)
        df_out.columns += '_per'

        df = df_in.join(df_out)

        df.index = range(1, len(df) + 1)

        if excel_writer:
            df.to_excel(excel_writer)

        return df

    @classmethod
    def get_blading_boundary_coordinates(cls, blading, excel_writer=None):
        df_list = list()

        for blade in blading.blades:
            df_list.append(cls.get_blade_boundary_coordinates(blade))

        df = pd.concat(df_list)

        df.index = range(1, len(df) + 1)

        if excel_writer:
            df.to_excel(excel_writer)

        return df
    
    @classmethod
    def get_smooth_blading_boundary_coordinates(cls, blading, func=lambda x, a, b, c: a * x**2 + b * x + c):
        coord_df = cls.get_blading_boundary_coordinates(blading)
        x_ser = coord_df.x_in_root
        y_ser = coord_df.y_in_root
        
        params, _ = scipy.optimize.curve_fit(func, x_ser, y_ser)
        fit_func = lambda x: func(x, *params)
        
        coord_df.y_in_root = fit_func(x_ser)
        return coord_df

    @classmethod
    def _plot_blade(cls, subplot, blade):
        for profile in blade.blade_profiles:
            subplot.plot(profile.pressure_side_x, profile.pressure_side_y, profile.height, color='blue')
            subplot.plot(profile.suction_side_x, profile.suction_side_y, profile.height, color='blue')
            plt.xlabel('x')
            plt.ylabel('y')

        plt.axis('equal')

    @classmethod
    def _get_profile_inlet_point(cls, profile):
        inlet_y = profile.pressure_side_y.min()
        return inlet_y, profile.height

    @classmethod
    def _get_profile_outlet_point(cls, profile):
        outlet_y = profile.pressure_side_y.max()
        return outlet_y, profile.height

    @classmethod
    def _get_blade_inlet_line(cls, blade):
        point_list = list()
        for profile in blade.blade_profiles:
            point_list.append(cls._get_profile_inlet_point(profile))

        line = pd.DataFrame.from_records(point_list, columns=('x', 'y'))

        return line

    @classmethod
    def _get_blade_outlet_line(cls, blade):
        point_list = list()
        for profile in blade.blade_profiles:
            point_list.append(cls._get_profile_outlet_point(profile))

        line = pd.DataFrame.from_records(point_list, columns=('x', 'y'))

        return line

    @classmethod
    def _get_inner_line(cls, blading):
        point_list = list()

        for blade in blading.blades:
            root_profile = blade.blade_profiles[0]
            point_list.append(cls._get_profile_inlet_point(root_profile))
            point_list.append(cls._get_profile_outlet_point(root_profile))

        line = pd.DataFrame.from_records(point_list, columns=('x', 'y'))
        return line

    @classmethod
    def _get_outer_line(cls, blading):
        point_list = list()

        for blade in blading.blades:
            peripherical_profile = blade.blade_profiles[-1]
            point_list.append(cls._get_profile_inlet_point(peripherical_profile))
            point_list.append(cls._get_profile_outlet_point(peripherical_profile))

        line = pd.DataFrame.from_records(point_list, columns=('x', 'y'))
        return line

    @classmethod
    def _get_smooth_inner_line(cls, blading, point_num=50):
        point_list = list()

        for blade in blading.blades:
            root_profile = blade.blade_profiles[0]
            point_list.append(cls._get_profile_inlet_point(root_profile))

        inner_line = pd.DataFrame.from_records(point_list, columns=('x', 'y')).sort_values(by='x')

        spline = interpolate.interp1d(inner_line.x, inner_line.y)

        x = np.linspace(inner_line.x.min(), inner_line.x.max(), point_num)
        y = spline(x)

        return pd.DataFrame({'x': x, 'y': y})

    @classmethod
    def _get_shaft_contour(cls, blading):
        inlet_point_x, inlet_point_y = cls._get_profile_inlet_point(blading.blades[0].blade_profiles[0])
        outlet_point_x, outlet_point_y = cls._get_profile_outlet_point(blading.blades[-1].blade_profiles[0])

        x_list = [inlet_point_x] * 2 + [outlet_point_x] * 2
        y_list = [inlet_point_y, 0, 0, outlet_point_y]

        return pd.DataFrame({'x': x_list, 'y': y_list})







