import numpy as np
from . import gases
from . import gdf
from . import stage_geometry
from . import velocity_triangles


class ThermalInfo:
    def __init__(self):
        self.gas = gases.Air()
        self.T_stag_1 = None
        self.T_stag_3 = None
        self.p_stag_1 = None
        self.pi_stag = None

    @property
    def p_stag_3(self):
        return self.p_stag_1 * self.pi_stag

    @property
    def a_crit_1(self):
        k = self.gas.k(self.T_stag_1)
        R = self.gas.R
        return gdf.a_crit(k, R, self.T_stag_1)

    @property
    def a_crit_3(self):
        k = self.gas.k(self.T_stag_3)
        R = self.gas.R
        return gdf.a_crit(k, R, self.T_stag_3)

    @property
    def density_stag_1(self):
        return self.p_stag_1 / (self.gas.R * self.T_stag_1)

    @property
    def density_stag_3(self):
        return self.p_stag_3 / (self.gas.R * self.T_stag_3)


class StageModel:
    def __init__(self, rotor_velocity_law=None, stator_velocity_law=None, rotor_profiler=None, stator_profiler=None):
        self.rotor_velocity_law = rotor_velocity_law
        self.stator_velocity_law = stator_velocity_law
        self.rotor_profiler = rotor_profiler
        self.stator_profiler = stator_profiler

        self.gas = gases.Air()
        self.thermal_info = ThermalInfo()
        self.stage_geometry = stage_geometry.StageGeometry()
        self.triangle_1 = velocity_triangles.VelocityTriangle()
        self.triangle_2 = velocity_triangles.VelocityTriangle()
        self.triangle_3 = velocity_triangles.IncompleteVelocityTriangle()

        self.G = None
        self.n = None
        self._u_out_1 = None
        self.eta_ad = None
        self.H_t_rel = None
        self._R_mean = None
        self.k_h = 0.98

        self.rotor_profiler = None
        self.stator_profiler = None

    @property
    def R_mean(self):
        return self._R_mean

    @R_mean.setter
    def R_mean(self, value):
        self._R_mean = value

    @property
    def T_stag_1(self):
        return self.thermal_info.T_stag_1

    @T_stag_1.setter
    def T_stag_1(self, value):
        self.thermal_info.T_stag_1 = value

    @property
    def p_stag_1(self):
        return self.thermal_info.p_stag_1

    @p_stag_1.setter
    def p_stag_1(self, value):
        self.thermal_info.p_stag_1 = value

    @property
    def D_out_1(self):
        return self.stage_geometry.D_out_1

    @D_out_1.setter
    def D_out_1(self, value):
        self.stage_geometry.D_out_1 = value

    @property
    def d_rel_1(self):
        return self.stage_geometry.d_rel_1

    @d_rel_1.setter
    def d_rel_1(self, value):
        self.stage_geometry.d_rel_1 = value

    @property
    def c_a_rel(self):
        return self.triangle_1.c_a_rel

    @c_a_rel.setter
    def c_a_rel(self, value):
        self.triangle_1.c_a_rel = value
        self.triangle_2.c_a_rel = value
        self.triangle_3.c_a_rel = value

    @property
    def u_out_1(self):
        return self._u_out_1

    @u_out_1.setter
    def u_out_1(self, value):
        self._u_out_1 = value

        self.triangle_1.u_out_1 = value
        self.triangle_2.u_out_1 = value
        self.triangle_3.u_out_1 = value

    @property
    def H_t(self):
        return self.H_t_rel * self.u_out_1**2

    @property
    def L_z(self):
        return self.k_h * self.H_t

    @property
    def H_ad(self):
        return self.L_z * self.eta_ad

    @property
    def C_p(self):
        return self.gas.C_p(self.T_stag_1)

    @property
    def k(self):
        return self.gas.k(self.T_stag_1)

    @property
    def R(self):
        return self.gas.R

    def lambda_1(self, velocity):
        a_crit = self.thermal_info.a_crit_1
        return velocity / a_crit

    @property
    def lambda_c_1(self):
        return self.lambda_1(self.triangle_1.c_total)

    @property
    def lambda_w_1(self):
        return self.lambda_1(self.triangle_1.w_total)

    def lambda_2(self, velocity):
        a_crit = self.thermal_info.a_crit_3
        return velocity / a_crit

    @property
    def lambda_c_2(self):
        return self.lambda_2(self.triangle_2.c_total)

    @property
    def lambda_w_2(self):
        return self.lambda_2(self.triangle_2.w_total)

    def lambda_3(self, velocity):
        a_crit = self.thermal_info.a_crit_3
        return velocity / a_crit

    @property
    def lambda_c_3(self):
        return self.lambda_3(self.triangle_3.c_total)

    @property
    def mach_c_1(self):
        lambda_ = self.lambda_c_1
        k = self.k

        return gdf.mach(lambda_, k)

    @property
    def mach_w_1(self):
        lambda_ = self.lambda_w_1
        k = self.k

        return gdf.mach(lambda_, k)

    @property
    def mach_c_2(self):
        lambda_ = self.lambda_c_2
        k = self.k

        return gdf.mach(lambda_, k)

    @property
    def mach_w_2(self):
        lambda_ = self.lambda_w_2
        k = self.k

        return gdf.mach(lambda_, k)

    @property
    def mach_c_3(self):
        lambda_ = self.lambda_c_3
        k = self.k

        return gdf.mach(lambda_, k)

    @staticmethod
    def get_r_rel(h_rel, d_rel):
        return d_rel + h_rel * (1 - d_rel)

    @staticmethod
    def get_velocity_triangle(mean_radius_velocity_triangle, velocity_law, h_rel, d_rel):
        r_rel = StageModel.get_r_rel(h_rel, d_rel)

        return velocity_law.get_velocity_triangle(mean_radius_velocity_triangle, r_rel)

    def get_rotor_inlet_triangle(self, h_rel):
        return self.get_velocity_triangle(self.triangle_1, self.rotor_velocity_law, h_rel, self.stage_geometry.d_rel_1)

    def get_rotor_outlet_triangle(self, h_rel):
        return self.get_velocity_triangle(self.triangle_2, self.rotor_velocity_law, h_rel, self.stage_geometry.d_rel_2)

    def get_stator_inlet_triangle(self, h_rel):
        return self.get_velocity_triangle(self.triangle_2, self.stator_velocity_law, h_rel, self.stage_geometry.d_rel_2)

    def get_stator_outlet_triangle(self, h_rel):
        return self.get_velocity_triangle(self.triangle_3, self.stator_velocity_law, h_rel, self.stage_geometry.d_rel_3)


class ConstantCustomDiameterStageModel(StageModel):
    def __init__(self, form_coef):
        StageModel.__init__(self)
        self.stage_geometry = stage_geometry.StageGeometry(form_coef=form_coef)


class ConstantOuterDiameterStageModel(StageModel):
    def __init__(self):
        StageModel.__init__(self)
        self.stage_geometry = stage_geometry.ConstantOuterDiameterStageGeometry()


class ConstantInnerDiameterStageModel(StageModel):
    def __init__(self):
        StageModel.__init__(self)
        self.stage_geometry = stage_geometry.ConstantInnerDiameterStageGeometry()


class ConstantMeanDiameterStageModel(StageModel):
    def __init__(self):
        StageModel.__init__(self)
        self.stage_geometry = stage_geometry.ConstantMeanDiameterStageGeometry()


