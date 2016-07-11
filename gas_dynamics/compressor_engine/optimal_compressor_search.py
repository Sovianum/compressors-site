import numpy as np
import matplotlib.pyplot as plt
import data_extraction
import post_processing
import pandas as pd
import gdf
pd.options.display.float_format = '{:.3f}'.format
pd.set_option('display.width', 1000)

try:
    #from main import *
    pass
except Exception:
    pass

#total = data_extraction.collect_from_dir('results/profiled_gamma_constant/total')
#non_turbine = data_extraction.collect_from_dir('results/profiled_gamma_constant/non_turbine')
print('started pi_trend')
pi_trend = data_extraction.collect_from_dir('results/profiled_gamma_constant/pi_stag_trend')
print('finished pi_trend')
print('started perfect')
perfect = pi_trend.ix[(pi_trend.root_c_u >= 0) & (pi_trend.D_out_1 <= 0.95)]
print('finished perfect')
#df_list = [compressor.get_stage_info_data_frame() for compressor in perfect.compressor]
#mach_list = [df.M_w_1 for df in df_list]
#mach_df = pd.DataFrame.from_records(mach_list)

compressor = perfect.ix[perfect.D_out_1 == perfect.D_out_1.min()].compressor.values[0]

#plt.scatter(total.D_out_1, total.root_c_u)
#plt.grid()


#rotor_profiler = compressor.first_stage.rotor_profiler
#h_rel_list = np.linspace(0, 1)[:-1]
#total_velocity_list = np.array([rotor_profiler.get_inlet_triangle(h_rel).c_total for h_rel in h_rel_list])
