import pandas
import numpy as np
from . import gdf


class CompressorModel:
    def __init__(self, stage_class_list=list(), inlet_alpha=None, eta_ad_list=list(), H_t_rel_list=list(),
                 R_mean_list=list(), c_a_rel_list=list(), rotor_velocity_law_list=list(),
                 stator_velocity_law_list=list(), rotor_profiler_class_list=list(), stator_profiler_class_list=list(),
                 rotor_blade_elongation_list=list(), stator_blade_elongation_list=list(),
                 rotor_blade_windage_list=list(), stator_blade_windage_list=list(),
                 rotor_mean_lattice_density_list=list(), stator_mean_lattice_density_list=list()):

        self._rotor_velocity_law_list = rotor_velocity_law_list
        self._stator_velocity_law_list = stator_velocity_law_list

        self._stage_class_list = stage_class_list
        self._inlet_alpha = inlet_alpha
        self._eta_ad_list = eta_ad_list
        self._H_t_rel_list = H_t_rel_list
        self._R_mean_list = R_mean_list
        self._c_a_rel_list = c_a_rel_list

        self.dzeta_in = 0.04
        self.dzeta_out = 0.04

        self.stages = list()

        self.rotor_profiler_class_list = rotor_profiler_class_list
        self.stator_profiler_class_list = stator_profiler_class_list

        self.rotor_blade_elongation_list = rotor_blade_elongation_list
        self.stator_blade_elongation_list = stator_blade_elongation_list

        self.rotor_blade_windage_list = rotor_blade_windage_list
        self.stator_blade_windage_list = stator_blade_windage_list

        self.rotor_mean_lattice_density_list = rotor_mean_lattice_density_list
        self.stator_mean_lattice_density_list = stator_mean_lattice_density_list

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def first_stage(self):
        if not self.stages:
            self.stages.append(self.stage_class_list[0]())

        return self.stages[0]

    @property
    def last_stage(self):
        return self.stages[-1]

    def _is_fully_initialized(self):
        result = True
        result &= bool(len(self._eta_ad_list))
        result &= bool(len(self._H_t_rel_list))
        result &= bool(len(self._R_mean_list))
        result &= bool(len(self._c_a_rel_list))
        result &= bool(len(self._rotor_velocity_law_list))
        result &= bool(len(self._stator_velocity_law_list))
        result &= (self._inlet_alpha != None)

        return result

    def _initialize_first_stage(self):
        self.first_stage.H_t_rel = self.H_t_rel_list[0]
        self.first_stage.eta_ad = self.eta_ad_list[0]
        self.first_stage.c_a_rel = self.c_a_rel_list[0]
        self.first_stage.triangle_2.c_a_rel = (self.c_a_rel_list[0] + self.c_a_rel_list[1]) / 2
        self.first_stage.triangle_3.c_a_rel = self.c_a_rel_list[1]

        self.first_stage.rotor_velocity_law = self._rotor_velocity_law_list[0]
        self.first_stage.stator_velocity_law = self._stator_velocity_law_list[0]

        self.first_stage.R_mean = self.R_mean_list[0]

        def get_first_R_mean(c_a_rel, r_rel, H_t_rel, alpha_1):
            if self._inlet_alpha == 0:
                return 1 - H_t_rel / (2 * r_rel**2)

            return 1 - c_a_rel / (r_rel * np.tan(alpha_1)) - H_t_rel / (2 * r_rel**2)

        self.first_stage.R_mean = get_first_R_mean(self.first_stage.c_a_rel, self.first_stage.stage_geometry.r_m_rel_1,
                                                   self.first_stage.H_t_rel, self._inlet_alpha)

    @property
    def rotor_velocity_law_list(self):
        return self._rotor_velocity_law_list

    @rotor_velocity_law_list.setter
    def rotor_velocity_law_list(self, value):
        self._rotor_velocity_law_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def stator_velocity_law_list(self):
        return self._stator_velocity_law_list

    @stator_velocity_law_list.setter
    def stator_velocity_law_list(self, value):
        self._stator_velocity_law_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def stage_class_list(self):
        return self._stage_class_list

    @stage_class_list.setter
    def stage_class_list(self, value):
        self._stage_class_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def H_t_rel_list(self):
        return self._H_t_rel_list

    @H_t_rel_list.setter
    def H_t_rel_list(self, value):
        self._H_t_rel_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def eta_ad_list(self):
        return self._eta_ad_list

    @eta_ad_list.setter
    def eta_ad_list(self, value):
        self._eta_ad_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def R_mean_list(self):
        return self._R_mean_list

    @R_mean_list.setter
    def R_mean_list(self, value):
        self._R_mean_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def c_a_rel_list(self):
        return self._c_a_rel_list

    @c_a_rel_list.setter
    def c_a_rel_list(self, value):
        self._c_a_rel_list = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    @property
    def inlet_alpha(self):
        return self._inlet_alpha

    @inlet_alpha.setter
    def inlet_alpha(self, value):
        self._inlet_alpha = value

        if self._is_fully_initialized():
            self._initialize_first_stage()

    def set_G(self, value):
        self.first_stage.G = value

    def set_n(self, value):
        self.first_stage.n = value

    def set_T_stag_1(self, value):
        self.first_stage.T_stag_1 = value

    def set_p_stag_1(self, value):
        self.first_stage.p_stag_1 = value   #TODO учесть падение полного давления во входном патрубке

    def sigma_in(self):
        lambda_c_in = self.first_stage.lambda_c_1
        k = self.first_stage.k
        eps_in = gdf.epsilon(lambda_c_in, k)

        return 1 / (1 + self.dzeta_in * k / (k + 1) * eps_in * lambda_c_in**2)

    def sigma_out(self):
        lambda_c_out = self.last_stage.lambda_c_3

        k = self.first_stage.k

        eps_out = gdf.epsilon(lambda_c_out, k)

        return 1 - self.dzeta_out * k / (k + 1) * eps_out * lambda_c_out**2

    def pi_stag_blading(self):
        result = 1

        for compressor_stage in self.stages:
            result *= compressor_stage.thermal_info.pi_stag

        return result

    def pi_stag_compressor(self):
        return self.pi_stag_blading() * self.sigma_in() * self.sigma_out()

    def eta_ad_blading(self):
        T_stag_in = self.first_stage.thermal_info.T_stag_1
        T_stag_out = self.last_stage.thermal_info.T_stag_3

        k = self.first_stage.k

        pi_ad_blading = self.pi_stag_blading()

        return T_stag_in / (T_stag_out - T_stag_in) * (pi_ad_blading ** ((k - 1) / k) - 1)

    def eta_ad_compressor(self):
        T_in = self.first_stage.thermal_info.T_stag_1
        T_out = self.last_stage.thermal_info.T_stag_3
        k = self.first_stage.k
        pi_c = self.pi_stag_compressor()

        eta_ad = T_in / (T_out - T_in) * (pi_c**((k - 1) / k) - 1)

        assert eta_ad < 1, 'Eta_ad > 1. Check your input data.'

        return eta_ad

    def get_incomplete_copy(self):
        incomplete_copy = CompressorModel(self.stage_class_list)
        incomplete_copy.set_G(self.first_stage.G)
        incomplete_copy.set_n(self.first_stage.n)
        incomplete_copy.set_T_stag_1(self.first_stage.T_stag_1)
        incomplete_copy.set_p_stag_1(self.first_stage.p_stag_1)

        return incomplete_copy

    def get_stage_info_data_frame(self):
        D_out_1 = [stage.stage_geometry.D_out_1 for stage in self.stages]
        d_rel_1 = [stage.stage_geometry.d_rel_1 for stage in self.stages]
        pi_stag = [stage.thermal_info.pi_stag for stage in self.stages]
        R_mean = [stage.R_mean for stage in self.stages]
        c_a_rel_2 = [stage.triangle_2.c_a_rel for stage in self.stages]
        c_u_rel_2 = [stage.triangle_2.c_u_rel for stage in self.stages]
        u_out_1 = [stage.triangle_1.u_out_1 for stage in self.stages]
        c_a = [stage.triangle_1.c_a for stage in self.stages]
        w_u_1 = [stage.triangle_1.w_u for stage in self.stages]
        c_u_2 = [stage.triangle_3.c_u for stage in self.stages]
        n = [stage.n for stage in self.stages]
        mach_w_1 = [stage.mach_w_1 for stage in self.stages]
        mach_c_2 = [stage.mach_c_2 for stage in self.stages]
        betta_1 = [np.rad2deg(stage.triangle_1.betta) for stage in self.stages]
        betta_2 = [np.rad2deg(stage.triangle_2.betta) for stage in self.stages]
        delta_betta = [betta_2_item - betta_1_item for betta_2_item, betta_1_item in zip(betta_2, betta_1)]
        alpha_2 = [np.rad2deg(stage.triangle_2.alpha) for stage in self.stages]
        alpha_3 = [np.rad2deg(stage.triangle_3.alpha) for stage in self.stages]
        delta_alpha = [alpha_3_item - alpha_2_item for alpha_3_item, alpha_2_item in zip(alpha_3, alpha_2)]

        rotor_mean_lattice_density = None
        stator_mean_lattice_density = None
        rotor_blade_number = None
        stator_blade_number = None

        try:
            rotor_mean_lattice_density = [stage.rotor_profiler.blading_geometry.mean_lattice_density for stage in
                                          self.stages]
            stator_mean_lattice_density = [stage.stator_profiler.blading_geometry.mean_lattice_density for stage in
                                           self.stages]
            rotor_blade_number = [stage.rotor_profiler.blading_geometry.blade_number for stage in self.stages]
            stator_blade_number = [stage.stator_profiler.blading_geometry.blade_number for stage in self.stages]
        except Exception:
            pass

        result_df = pandas.DataFrame(index=range(1, len(self.stages) + 1))
        result_df['D_out_1'] = D_out_1
        result_df['d_rel_1'] = d_rel_1
        result_df['pi_stag'] = pi_stag
        result_df['R_mean'] = R_mean
        result_df['c_a_rel_2'] = c_a_rel_2
        result_df['c_u_rel_2'] = c_u_rel_2
        result_df['u_out_1'] = u_out_1
        result_df['c_a'] = c_a
        result_df['w_u_1'] = w_u_1
        result_df['c_u_2'] = c_u_2
        result_df['u_out_1'] = u_out_1
        result_df['n'] = n
        result_df['betta_1'] = betta_1
        result_df['betta_2'] = betta_2
        result_df['delta_betta'] = delta_betta
        result_df['alpha_2'] = alpha_2
        result_df['alpha_3'] = alpha_3
        result_df['delta_alpha'] = delta_alpha
        result_df['M_w_1'] = mach_w_1
        result_df['M_c_2'] = mach_c_2

        if rotor_mean_lattice_density:
            result_df['(b/t)_rotor'] = rotor_mean_lattice_density
        if stator_mean_lattice_density:
            result_df['(b/t)_stator'] = stator_mean_lattice_density
        if rotor_blade_number:
            result_df['z_rotor'] = rotor_blade_number
        if stator_blade_number:
            result_df['z_stator'] = stator_blade_number

        return result_df

    def get_rotor_inlet_triangle(self, stage_number, h_rel):
        return self.stages[stage_number - 1].get_rotor_inlet_triangle(h_rel)

    def get_rotor_outlet_triangle(self, stage_number, h_rel):
        return self.stages[stage_number - 1].get_rotor_outlet_triangle(h_rel)

    def get_stator_inlet_triangle(self, stage_number, h_rel):
        return self.stages[stage_number - 1].get_stator_inlet_triangle(h_rel)

    def get_stator_outlet_triangle(self, stage_number, h_rel):
        return self.stages[stage_number - 1].get_stator_outlet_triangle(h_rel)

    def set_profilers(self):
        profilers_iterator = zip(self.rotor_profiler_class_list, self.stator_profiler_class_list)
        rotor_parameters_iterator = zip(self.rotor_blade_elongation_list, self.rotor_blade_windage_list,
                                        self.rotor_mean_lattice_density_list, self.rotor_velocity_law_list)
        stator_parameters_iterator = zip(self.stator_blade_elongation_list, self.stator_blade_windage_list,
                                         self.stator_mean_lattice_density_list, self.stator_velocity_law_list)
        for stage in self.stages:
            rotor_profiler_class, stator_profiler_class = next(profilers_iterator)
            stage.rotor_profiler = rotor_profiler_class(stage, *next(rotor_parameters_iterator))
            stage.stator_profiler = stator_profiler_class(stage, *next(stator_parameters_iterator))
