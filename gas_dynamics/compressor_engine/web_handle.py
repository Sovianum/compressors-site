import os
import time
import pandas as pd
from enum import Enum
from . import compressor_models
from . import data_extraction
from . import compressor_optimizer
from . import compressor_stage_models
from . import velocity_laws
from . import profilers

######################################################################################
# Параметры, задаваемые для расчета по средней линии тока
######################################################################################
H_t_rel_last = np.arange(0.22, 0.24, 0.005)
H_t_rel_max = np.arange(0.25, 0.27, 0.005)
H_t_rel_max_coord = [1.5, 2.0, 2.5, 3.0]

eta_ad_first = [0.88]
eta_ad_last = [0.86]
eta_ad_max = [0.90]
eta_ad_max_coord = [2.5]

c_a_rel_first = np.arange(0.48, 0.50, 0.01)
c_a_rel_last = [0.45]

R_mean_first = [0.55]
R_mean_last = [0.6]

inlet_alpha_list = [np.deg2rad(85), np.rad2deg(90)]

stage_class_list = [compressor_stage_models.ConstantOuterDiameterStageModel] * 4 + \
                   [compressor_stage_models.ConstantInnerDiameterStageModel] * 0


######################################################################################


#################################################################################################
# Параметры, задаваемые для получения газодинамической информации по высоте ступени
#################################################################################################

rotor_velocity_law_list = [velocity_laws.ConstantReactivityLaw] * 0 + [velocity_laws.ConstantCirculationLaw] * 4
stator_velocity_law_list = [velocity_laws.ConstantCirculationLaw] * 5
##################################################################################################


############################################################
# Данные, необходимые для профилирования лопаток компрессора
############################################################
rotor_profiler_class_list = [profilers.TransSoundProfileRotorProfiler] * 3 + [profilers.A40SubSoundRotorProfiler] * 4
stator_profiler_class_list = [profilers.TransSoundProfileStatorProfiler] * 3 + [profilers.A40SubSoundStatorProfiler] * 4

rotor_blade_elongation_list = [1.5, 2, 2, 2, 2]
stator_blade_elongation_list = [2, 2, 2, 2, 2]

rotor_blade_windage_list = [1, 1, 1, 1, 1]
stator_blade_windage_list = [1, 1, 1, 1, 1]

trans_sound_rotor_mean_blade_lattice_list = [1.8, 1.6, 1.6, 1.6, 1]     # Используются только при инциализации сверхзвуковых ступеней
trans_sound_stator_mean_blade_lattice_list = [1.4, 1.4, 1.5, 1.5, 1]    # при использовании дозвуковых ступеней густота рассчитывается
############################################################
def get_compressor_template():
    compressor_template = compressor_models.CompressorModel(config.stage_class_list)
    #compressor_template.rotor_velocity_law_list = config.rotor_velocity_law_list
    #compressor_template.stator_velocity_law_list = config.stator_velocity_law_list
    compressor_template.set_G(config.G)
    compressor_template.set_T_stag_1(config.T_stag_1)
    compressor_template.set_p_stag_1(config.p_stag_1)
    return compressor_template


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
    def to_list(self, value):
        return list(value)


class MainDataBlock(DataBlock):
    def __init__(self, main_data_model):
        self.pi_c = self.to_list(main_data_model.pi_c)
        self.G = self.to_list(main_data_model.mass_rate)
        self.T_stage_1 = self.to_list(main_data_model.T_stag_1)
        self.p_stag_1 = self.to
        self.eta_ad_min = main_data_model.eta_ad_min    # TODO Не забыть, что переименовал min_eta_ad
        self.precision = main_data_model.precision

class MeanRadiusData:
    def __init__(self, mean_radius_model):
        self.u_out_1 = mean_radius_model.u_out_1
        self.d_rel_1 = mean_radius_model.d_rel_1
        self.H_t_rel_first = mean_radius_model.H_t_rel_first




class Handler:
    def get_compressor_template(self, main_data, mean_radius_data):
        stage_class_list =

    def get_main_data
