import os
import time
import pandas as pd
from . import compressor_models
from . import data_extraction
from . import compressor_optimizer

from . import config


def get_compressor_template():
    compressor_template = compressor_models.CompressorModel(config.stage_class_list)
    compressor_template.rotor_velocity_law_list = config.rotor_velocity_law_list
    compressor_template.stator_velocity_law_list = config.stator_velocity_law_list
    compressor_template.set_G(config.G)
    compressor_template.set_T_stag_1(config.T_stag_1)
    compressor_template.set_p_stag_1(config.p_stag_1)
    return compressor_template


"""
def get_compressor_template(stage_num, stage_class_list, rotor_velocity_law_list,
                            stator_velocity_law_list, mass_rate, T_stag_1, p_stag_1):
    assert len(stage_class_list) == len(rotor_velocity_law_list) == len(stator_velocity_law_list) == stage_num
    compressor_template = compressor_models.CompressorModel(stage_class_list)
    compressor_template.rotor_velocity_law_list = rotor_velocity_law_list
    compressor_template.stator_velocity_law_list = stator_velocity_law_list
    compressor_template.set_G(mass_rate)
    compressor_template.set_T_stag_1(T_stag_1)
    compressor_template.set_p_stag_1(p_stag_1)
    return compressor_template
"""


def get_mean_radius_compressor_optimizer():
    compressor_template = get_compressor_template()
    optimizer = compressor_optimizer.MeanRadiusCompressorOptimizer(compressor_template, pi_c=config.pi_c,
                                                                   min_eta_ad=config.min_eta_ad,
                                                                   precision=config.precision)
    optimizer.u_out_1 = config.u_out_1
    optimizer.d_rel_1 = config.d_rel_1

    optimizer.H_t_rel_first = config.H_t_rel_first
    optimizer.H_t_rel_last = config.H_t_rel_last
    optimizer.H_t_rel_max = config.H_t_rel_max
    optimizer.H_t_rel_max_coord = config.H_t_rel_max_coord

    optimizer.eta_ad_first = config.eta_ad_first
    optimizer.eta_ad_last = config.eta_ad_last
    optimizer.eta_ad_max = config.eta_ad_max
    optimizer.eta_ad_max_coord = config.eta_ad_max_coord

    optimizer.c_a_rel_first = config.c_a_rel_first
    optimizer.c_a_rel_last = config.c_a_rel_last

    optimizer.R_mean_first = config.R_mean_first
    optimizer.R_mean_last = config.R_mean_last

    optimizer.inlet_alpha = config.inlet_alpha_list

    return optimizer


def profile_compressor(compressor):
    compressor.rotor_profiler_class_list = config.rotor_profiler_class_list
    compressor.stator_profiler_class_list = config.stator_profiler_class_list

    compressor.rotor_blade_elongation_list = config.rotor_blade_elongation_list
    compressor.stator_blade_elongation_list = config.stator_blade_elongation_list

    compressor.rotor_blade_windage_list = config.rotor_blade_windage_list
    compressor.stator_blade_windage_list = config.stator_blade_windage_list

    compressor.rotor_mean_lattice_density_list = config.trans_sound_rotor_mean_blade_lattice_list
    compressor.stator_mean_lattice_density_list = config.trans_sound_stator_mean_blade_lattice_list

    compressor.rotor_velocity_law_list = config.rotor_velocity_law_list
    compressor.stator_velocity_law_list = config.stator_velocity_law_list

    compressor.set_profilers()


def set_profiling_data(result_df):
    compressor_list = result_df.compressor

    for compressor in compressor_list:
        profile_compressor(compressor)

    result_df.compressor = compressor_list


def calculate_mean_radius(save_dir='results/mean_radius_calculation', file_name='file'):
    file_list = [os.path.join(save_dir, file_name) for file_name in os.listdir(save_dir)]

    for file in file_list:
        os.remove(file)

    mean_radius_compressor_optimizer = get_mean_radius_compressor_optimizer()
    mean_radius_compressor_optimizer.get_variants_df(save_dir=save_dir, file_name=file_name)
    print('saved')


def do_profiling(data_dir='results/mean_radius_calculation', result_dir='results/profiled_gamma_constant/total'):
    result_files = [os.path.join(result_dir, file_name) for file_name in os.listdir(result_dir)]

    for file in result_files:
        os.remove(file)

    data_file_names = os.listdir(data_dir)
    path_indexer = 1

    for file_name in data_file_names:
        start = time.time()
        mean_radius_calculation_result = pd.read_pickle(os.path.join(data_dir, file_name))
        set_profiling_data(mean_radius_calculation_result)

        data_extraction.DataExtractor.process_result_df(mean_radius_calculation_result)

        total_path = os.path.join(result_dir, 'file_%d.pkl' % path_indexer)
        pd.to_pickle(mean_radius_calculation_result, total_path)

        print('Profiled %d of %d.' % (path_indexer, len(data_file_names)))
        print('Time took: ', time.time() - start)
        print()

        path_indexer += 1