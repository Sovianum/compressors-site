import os
import time
import pandas as pd
import numpy as np
import re
from enum import Enum
from . import compressor_models
from . import data_extraction
from . import compressor_optimizer
from . import compressor_stage_models
from . import velocity_laws
from . import profilers
from . import engine_logging


class STAGE_CLASS(Enum):
    ConstantOuterDiameterStageModel = compressor_stage_models.ConstantOuterDiameterStageModel
    ConstantMeanDiameterStageModel = compressor_stage_models.ConstantMeanDiameterStageModel
    ConstantInnerDiameterStageModel = compressor_stage_models.ConstantInnerDiameterStageModel


class VELOCITY_LAW(Enum):
    gamma_constant = velocity_laws.ConstantCirculationLaw
    rho_constant = velocity_laws.ConstantReactivityLaw


class PROFILER_CLASS(Enum):
    rotor_sub_sound = profilers.A40SubSoundRotorProfiler
    stator_sub_sound = profilers.A40SubSoundStatorProfiler

    rotor_trans_sound = profilers.TransSoundProfileRotorProfiler
    stator_trans_sound = profilers.TransSoundArcStatorProfiler


class DataBlock:
    def set_attribute(self, data_model, *args):
        for arg in args:
            value = getattr(data_model, arg)
            setattr(self, arg, value)


class MainDataBlock(DataBlock):
    def __init__(self, main_data_model):
        self.set_attribute(main_data_model, 'pi_c', 'T_stag_1', 'p_stag_1', 'eta_ad_min', 'precision')  # TODO Не забыть, что переименовал min_eta_ad
        self.G = main_data_model.mass_rate
        self.p_stag_1 = main_data_model.p_stag_1 * 1e6


class MeanRadiusDataBlock(DataBlock):
    def __init__(self, mean_radius_model):
        self.set_attribute(mean_radius_model, 'u_out_1', 'd_rel_1',
                           'H_t_rel_first', 'H_t_rel_last', 'H_t_rel_max', 'H_t_rel_max_coord',
                           'eta_ad_first', 'eta_ad_last', 'eta_ad_max', 'eta_ad_max_coord',
                           'c_a_rel_first', 'c_a_rel_last')

        self.R_mean_first = mean_radius_model.reactivity_first
        self.R_mean_last = mean_radius_model.reactivity_last

        self.inlet_alpha = np.deg2rad(mean_radius_model.inlet_alpha)

        self.stage_class_list = [STAGE_CLASS[item].value for item in mean_radius_model.flow_section_type]


class ProfilingDataBlock(DataBlock):
    def __init__(self, profiling_data_model):
        self.rotor_velocity_law_list = [VELOCITY_LAW[item].value for item in profiling_data_model.rotor_velocity_law]
        self.stator_velocity_law_list = [VELOCITY_LAW[item].value for item in profiling_data_model.stator_velocity_law]

        self.rotor_profiler_class_list = [PROFILER_CLASS[item].value for item in profiling_data_model.rotor_blade_profile]
        self.stator_profiler_class_list = [PROFILER_CLASS[item].value for item in profiling_data_model.stator_blade_profile]

        self.rotor_blade_elongation_list = self._to_float(profiling_data_model.rotor_blade_elongation)
        self.stator_blade_elongation_list = self._to_float(profiling_data_model.stator_blade_elongation)

        self.rotor_mean_blade_lattice_list = self._to_float(profiling_data_model.rotor_lattice_density)
        self.stator_mean_blade_lattice_list = self._to_float(profiling_data_model.stator_lattice_density)

        self.rotor_blade_windage_list = self._to_float(profiling_data_model.rotor_blade_windage)
        self.stator_blade_windage_list = self._to_float(profiling_data_model.stator_blade_windage)

    @classmethod
    def _to_float(cls, value_list):
        return [float(value) for value in value_list]


class SolverTaskCreator:
    def __init__(self, main_data_block=None, mean_radius_data_block=None, profiling_data_block=None,
                 mean_radius_file_prefix='mean_radius_file', profiling_file_prefix='profiling_file'):
        self.main_data_block = main_data_block
        self.mean_radius_data_block = mean_radius_data_block
        self.profiling_data_block = profiling_data_block

        self.mean_radius_file_prefix = mean_radius_file_prefix
        self.profiling_file_prefix = profiling_file_prefix

    def do_profiling(self, input_data_dir, output_data_dir):
        self._assert_profiling_ready()

        self._clean_data_dir(output_data_dir, self.profiling_file_prefix)

        input_file_name_list = self._get_data_file_list(input_data_dir, self.mean_radius_file_prefix)
        input_data_path_list = [os.path.join(input_data_dir, file_name) for file_name in input_file_name_list]

        logger = engine_logging.CompressorProfilingInfo(total=len(input_data_path_list))

        for file_name, input_data_path, file_index in zip(input_file_name_list, input_data_path_list,
                                                          range(len(input_data_path_list))):
            logger.start()

            mean_radius_calculation_result = pd.read_pickle(input_data_path)
            self._set_profiling_data(mean_radius_calculation_result, self.profiling_data_block)

            data_extraction.DataExtractor.process_result_df(mean_radius_calculation_result)

            output_data_path = os.path.join(output_data_dir, '%s_%d.pkl' % (self.profiling_file_prefix, file_index))
            pd.to_pickle(mean_radius_calculation_result, output_data_path)

            logger.finish()

    def calculate_mean_radius(self, save_dir):
        self._assert_mean_radius_ready()
        self._clean_data_dir(save_dir, self.mean_radius_file_prefix)

        mean_radius_compressor_optimizer = self._get_mean_radius_compressor_optimizer(self.main_data_block,
                                                                                      self.mean_radius_data_block)
        mean_radius_compressor_optimizer.get_variants_df(save_dir=save_dir, file_prefix=self.mean_radius_file_prefix)

    def _assert_mean_radius_ready(self):
        result = True
        result &= not (self.main_data_block is None)
        result &= not (self.mean_radius_data_block is None)

        assert result, 'Not enough data for mean_radius calculation'

    def _assert_profiling_ready(self):
        result = True
        result &= not (self.main_data_block is None)
        result &= not (self.mean_radius_data_block is None)
        result &= not (self.profiling_data_block is None)

        assert result, 'Not enough data for mean_radius calculation'

    @classmethod
    def _clean_data_dir(cls, data_dir, file_prefix):
        prev_data_file_names = cls._get_data_file_list(data_dir, file_prefix)

        for file_path in [os.path.join(data_dir, file_name) for file_name in prev_data_file_names]:
            os.remove(file_path)

    @classmethod
    def _get_data_file_list(cls, data_dir, file_prefix):
        existing_file_list = [file_name for file_name in os.listdir(data_dir)]
        is_data_item_list = map(lambda name: re.match(r'^%s' % file_prefix, name), existing_file_list)

        prev_data_file_names = [file_name for file_name, is_data_item in zip(existing_file_list, is_data_item_list)
                                if is_data_item]

        return prev_data_file_names

    @classmethod
    def _set_profiling_data(cls, result_df, profiling_data_block):
        compressor_list = result_df.compressor

        for compressor in compressor_list:
            cls._profile_compressor(compressor, profiling_data_block)

        result_df.compressor = compressor_list

    @classmethod
    def _profile_compressor(cls, compressor, profiling_data_block):
        compressor.rotor_profiler_class_list = profiling_data_block.rotor_profiler_class_list
        compressor.stator_profiler_class_list = profiling_data_block.stator_profiler_class_list

        compressor.rotor_blade_elongation_list = profiling_data_block.rotor_blade_elongation_list
        compressor.stator_blade_elongation_list = profiling_data_block.stator_blade_elongation_list

        compressor.rotor_blade_windage_list = profiling_data_block.rotor_blade_windage_list
        compressor.stator_blade_windage_list = profiling_data_block.stator_blade_windage_list

        compressor.rotor_mean_lattice_density_list = profiling_data_block.rotor_mean_blade_lattice_list
        compressor.stator_mean_lattice_density_list = profiling_data_block.stator_mean_blade_lattice_list

        compressor.rotor_velocity_law_list = profiling_data_block.rotor_velocity_law_list
        compressor.stator_velocity_law_list = profiling_data_block.stator_velocity_law_list

        compressor.set_profilers()

    @classmethod
    def _get_mean_radius_compressor_optimizer(cls, main_data_block, mean_radius_data_block):
        compressor_template = cls._get_compressor_template(main_data_block, mean_radius_data_block)
        optimizer = compressor_optimizer.MeanRadiusCompressorOptimizer(compressor_template,
                                                                       pi_c=main_data_block.pi_c,
                                                                       min_eta_ad=main_data_block.eta_ad_min,
                                                                       precision=main_data_block.precision)
        optimizer.u_out_1 = mean_radius_data_block.u_out_1
        optimizer.d_rel_1 = mean_radius_data_block.d_rel_1

        optimizer.H_t_rel_first = mean_radius_data_block.H_t_rel_first
        optimizer.H_t_rel_last = mean_radius_data_block.H_t_rel_last
        optimizer.H_t_rel_max = mean_radius_data_block.H_t_rel_max
        optimizer.H_t_rel_max_coord = mean_radius_data_block.H_t_rel_max_coord

        optimizer.eta_ad_first = mean_radius_data_block.eta_ad_first
        optimizer.eta_ad_last = mean_radius_data_block.eta_ad_last
        optimizer.eta_ad_max = mean_radius_data_block.eta_ad_max
        optimizer.eta_ad_max_coord = mean_radius_data_block.eta_ad_max_coord

        optimizer.c_a_rel_first = mean_radius_data_block.c_a_rel_first
        optimizer.c_a_rel_last = mean_radius_data_block.c_a_rel_last

        optimizer.R_mean_first = mean_radius_data_block.R_mean_first
        optimizer.R_mean_last = mean_radius_data_block.R_mean_last

        optimizer.inlet_alpha = mean_radius_data_block.inlet_alpha

        return optimizer

    @classmethod
    def _get_compressor_template(cls, main_data_block, mean_radius_data_block):
        compressor_template = compressor_models.CompressorModel(mean_radius_data_block.stage_class_list)

        compressor_template.set_G(main_data_block.G)
        compressor_template.set_T_stag_1(main_data_block.T_stag_1)
        compressor_template.set_p_stag_1(main_data_block.p_stag_1)
        return compressor_template

