import numpy as np

from . import compressor_stage_models
from . import velocity_laws
from . import profilers


#####################################
# Исходные условия для проектирования
#####################################
G = 128
T_stag_1 = 288
p_stag_1 = 1e5
pi_c = 5.5
min_eta_ad = 0.845
precision = 0.03
#####################################


######################################################################################
# Параметры, задаваемые для расчета по средней линии тока
######################################################################################
u_out_1 = np.arange(440, 500, 5)
d_rel_1 = [0.3, 0.4, 0.5, 0.6]

H_t_rel_first = np.arange(0.22, 0.245, 0.005)
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


