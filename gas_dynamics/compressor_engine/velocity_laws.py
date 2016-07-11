import numpy as np


class VelocityLaw:
    def __init__(self, profiler):
        self._profiler = profiler

    def _get_inlet_c_u_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        return None

    def _get_outlet_c_u_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        return None

    def _get_inlet_c_a_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        return None

    def _get_outlet_c_a_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        return None

    def get_inlet_velocity_triangle(self, mean_radius_inlet_velocity_triangle, r_rel):
        c_u_rel = self._get_inlet_c_u_rel(mean_radius_inlet_velocity_triangle, r_rel)
        c_a_rel = self._get_inlet_c_a_rel(mean_radius_inlet_velocity_triangle, r_rel)
        u_out_1 = mean_radius_inlet_velocity_triangle.u_out_1

        velocity_triangle = type(mean_radius_inlet_velocity_triangle)(u_out_1, r_rel, c_u_rel, c_a_rel)

        return velocity_triangle

    def get_outlet_velocity_triangle(self, mean_radius_outlet_velocity_triangle, r_rel):
        c_u_rel = self._get_outlet_c_u_rel(mean_radius_outlet_velocity_triangle, r_rel)
        c_a_rel = self._get_outlet_c_a_rel(mean_radius_outlet_velocity_triangle, r_rel)
        u_out_1 = mean_radius_outlet_velocity_triangle.u_out_1

        velocity_triangle = type(mean_radius_outlet_velocity_triangle)(u_out_1, r_rel, c_u_rel, c_a_rel)

        return velocity_triangle


class ExponentialVelocityLaw(VelocityLaw):
    def __init__(self, profiler, power_coef):
        VelocityLaw.__init__(self, profiler)
        self.power_coef = power_coef

    def _get_inlet_c_u_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        c_u_rel_mean = mean_radius_inlet_velocity_triangle.c_u_rel
        r_m_rel = mean_radius_inlet_velocity_triangle.r_m_rel

        return c_u_rel_mean * (r_m_rel / r_rel)**(1 / self.power_coef)

    def _get_outlet_c_u_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        c_u_rel_mean = mean_radius_outlet_velocity_triangle.c_u_rel
        r_m_rel = mean_radius_outlet_velocity_triangle.r_m_rel

        return c_u_rel_mean * (r_m_rel / r_rel)**(1 / self.power_coef)

    def _get_inlet_c_a_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        c_u_rel_mean = mean_radius_inlet_velocity_triangle.c_u_rel
        c_a_rel_mean = mean_radius_inlet_velocity_triangle.c_a_rel
        r_m_rel = mean_radius_inlet_velocity_triangle.r_m_rel

        factor_1 = self.power_coef - 1
        factor_2 = c_u_rel_mean**2
        factor_3 = (r_m_rel / r_rel)**(2 / self.power_coef) - 1

        c_a_rel = (factor_1 * factor_2 * factor_3 + c_a_rel_mean**2)**0.5

        c_a_rel_arr = np.array(c_a_rel)
        assert not np.any(np.iscomplex(c_a_rel_arr)), 'complex number'
        assert not np.any(np.isnan(c_a_rel_arr)), 'nan'

        return c_a_rel

    def _get_outlet_c_a_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        c_u_rel_mean = mean_radius_outlet_velocity_triangle.c_u_rel
        c_a_rel_mean = mean_radius_outlet_velocity_triangle.c_a_rel
        r_m_rel = mean_radius_outlet_velocity_triangle.r_m_rel

        factor_1 = self.power_coef - 1
        factor_2 = c_u_rel_mean**2
        factor_3 = (r_m_rel / r_rel)**(2 / self.power_coef) - 1

        c_a_rel = (factor_1 * factor_2 * factor_3 + c_a_rel_mean**2)**0.5

        c_a_rel_arr = np.array(c_a_rel)
        assert not np.any(np.iscomplex(c_a_rel_arr)), 'complex number'
        assert not np.any(np.isnan(c_a_rel_arr)), 'nan'

        return c_a_rel


class ConstantCirculationLaw(ExponentialVelocityLaw):
    def __init__(self, profiler):
        ExponentialVelocityLaw.__init__(self, profiler, 1)


class SolidBodyLaw(ExponentialVelocityLaw):
    def __init__(self, profiler):
        ExponentialVelocityLaw.__init__(self, profiler, -1)


class ConstantReactivityLaw(VelocityLaw):
    def _get_inlet_c_u_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        R = self._profiler.stage_model.R_mean
        H_t_rel = self._profiler.stage_model.H_t_rel

        return r_rel * (1 - R) - H_t_rel / (2 * r_rel)

    def _get_outlet_c_u_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        R = self._profiler.stage_model.R_mean
        H_t_rel = self._profiler.stage_model.H_t_rel

        return r_rel * (1 - R) + H_t_rel / (2 * r_rel)

    def _get_inlet_c_a_rel(self, mean_radius_inlet_velocity_triangle, r_rel):
        c_a_rel_mean = mean_radius_inlet_velocity_triangle.c_a_rel
        R = self._profiler.stage_model.R_mean
        r_rel_mean = mean_radius_inlet_velocity_triangle.r_m_rel

        term_1 = c_a_rel_mean**2
        term_3 = 2 * (1 - R)**2 * (r_rel**2 - r_rel_mean**2)

        return (term_1 - term_3)**0.5

    def _get_outlet_c_a_rel(self, mean_radius_outlet_velocity_triangle, r_rel):
        c_a_rel_mean = mean_radius_outlet_velocity_triangle.c_a_rel
        R = self._profiler.stage_model.R_mean
        r_rel_mean = mean_radius_outlet_velocity_triangle.r_m_rel

        term_1 = c_a_rel_mean**2
        term_3 = 2 * (1 - R)**2 * (r_rel**2 - r_rel_mean**2)

        return (term_1 - term_3)**0.5


def get_exponential_velocity_law_class(power_coef):
    class CustomVelocityLaw(ExponentialVelocityLaw):
        def __init__(self, profiler):
            ExponentialVelocityLaw.__init__(self, profiler, power_coef)

    return CustomVelocityLaw
