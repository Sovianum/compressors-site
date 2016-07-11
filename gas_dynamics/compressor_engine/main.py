import data_extraction
from post_processing import *
from start_functions import calculate_mean_radius, do_profiling
import blade_strength
import geometry_results
import post_processing
import materials
import supporting_blade_profilers

pd.options.display.float_format = '{:.3f}'.format
pd.set_option('display.width', 1000)


result = data_extraction.collect_from_dir('results/fit_dir/optimal')
compressor = result.compressor.values[0]

lattice_density = 1.2
blade_elongation = 3
blade_windage = 1
profiler = compressor.first_stage.rotor_profiler

D_out_inlet = profiler.blading_geometry.D_out_inlet
d_rel_inlet = profiler.blading_geometry.d_rel_inlet

temp = supporting_blade_profilers.A40InletStatorProfiler()
temp.stage_profiler = profiler
temp.mean_lattice_density = lattice_density
temp.blade_elongation = blade_elongation
temp.blade_windage = blade_windage
temp.D_out_inlet = D_out_inlet
temp.d_rel_inlet = d_rel_inlet

h_rel = 1
theta = temp.installation_angle(h_rel)

x, y = temp.get_mean_line_points(h_rel)
x_1, y_1 = geometry_results.BladeProfile._reflect(x, y, 0)

x_r, y_r = geometry_results.BladeProfile._rotate(x, y, theta)
x_1_r, y_1_r = geometry_results.BladeProfile._rotate(x_1, y_1, theta - 2 * temp.inlet_bend_angle(h_rel))

plt.plot(x, y, x_1, y_1)
plt.plot(x_r, y_r, x_1_r, y_1_r)
plt.grid()
plt.axis('equal')
plt.show()

'''
x_p, y_p = temp.get_pressure_side_points(h_rel)
x_s, y_s = temp.get_suction_side_points(h_rel)
profile = geometry_results.BladeProfile.from_profiler(temp, h_rel)
theta = temp.installation_angle(h_rel)

x_p_r, y_p_r = geometry_results.BladeProfile._reflect(x_p, y_p, 0)
x_s_r, y_s_r = geometry_results.BladeProfile._reflect(x_s, y_s, 0)

x_p_r, y_p_r = geometry_results.BladeProfile._rotate(x_p_r, y_p_r, theta)
x_s_r, y_s_r = geometry_results.BladeProfile._rotate(x_s_r, y_s_r, theta)

x_p, y_p = geometry_results.BladeProfile._rotate(x_p, y_p, theta)
x_s, y_s = geometry_results.BladeProfile._rotate(x_s, y_s, theta)

plt.plot(x_p, y_p, x_p_r, y_p_r)
plt.plot(x_s, y_s, x_s_r, y_s_r)
#post_processing.PostProcessor.plot_profile(profile)
plt.grid()
plt.axis('equal')
plt.show()
'''

