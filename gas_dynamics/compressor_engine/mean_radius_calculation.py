import numpy as np
from . import gdf


class MeanRadiusStageSolver:
    def __init__(self):
        self.stage_model = None

    @staticmethod
    def _lambda(c_a_rel, u_out_1, alpha, a_crit):
        '''
        :param c_a_rel: коэффициент расхода в данной точке
        :param u_out_1: окружная скорость на входе в ступень
        :param alpha: направление потока в данной точке
        :param a_crit: критическая скорость в данной точке
        :return: приведенная скорость в данной точке
        '''
        return c_a_rel * u_out_1 / (np.sin(alpha) * a_crit)

    @staticmethod
    def _c_u_rel(r_rel, R_mean, H_t_rel):
        '''
        :param r_rel: относительный средний радиус
        :param R_mean: реактивность на среднем радиусе
        :param H_t_rel: коэффициент теоретического напора
        :return: безразмерная окружная составляющая абсолютной скорости
        '''
        return r_rel * (1 - R_mean) - H_t_rel / (2 * r_rel)

    def _set_T_stag_3(self):
        T_stag_1 = self.stage_model.thermal_info.T_stag_1
        L_z = self.stage_model.L_z
        C_p = self.stage_model.C_p
        self.stage_model.thermal_info.T_stag_3 = T_stag_1 + L_z / C_p

    def _set_pi_stag(self):
        H_ad = self.stage_model.H_ad
        C_p = self.stage_model.C_p
        T_stag_1 = self.stage_model.thermal_info.T_stag_1
        k = self.stage_model.k
        self.stage_model.thermal_info.pi_stag = (1 + H_ad / (C_p * T_stag_1)) ** (k / (k - 1))

    def _set_c_u_1_rel(self):
        r_m_rel = self.stage_model.stage_geometry.r_m_rel_1
        R_mean = self.stage_model.R_mean
        H_t_rel = self.stage_model.H_t_rel

        self.stage_model.triangle_1.c_u_rel = self._c_u_rel(r_m_rel, R_mean, H_t_rel)

    def _get_lambda_1(self):
        c_a_rel_1 = self.stage_model.triangle_1.c_a_rel
        u_out_1 = self.stage_model.u_out_1
        alpha_1 = self.stage_model.triangle_1.alpha
        a_crit_1 = self.stage_model.thermal_info.a_crit_1

        lambda_1 = self._lambda(c_a_rel_1, u_out_1, alpha_1, a_crit_1)

        return lambda_1

    def _get_F_1(self):
        T_stag_1 = self.stage_model.thermal_info.T_stag_1
        p_stag_1 = self.stage_model.thermal_info.p_stag_1
        alpha_1 = self.stage_model.triangle_1.alpha
        lambda_1 = self._get_lambda_1()
        G = self.stage_model.G

        F_1 = (G * T_stag_1**0.5 / p_stag_1) * \
              (1 / (gdf.q(lambda_1, self.stage_model.k, self.stage_model.R) * np.sin(alpha_1)))
        return F_1

    def _set_D_out_1(self):
        if not self.stage_model.D_out_1:
            F_1 = self._get_F_1()
            D_out_1 = (4 / np.pi * F_1 / (1 - self.stage_model.stage_geometry.d_rel_1**2))**0.5
            self.stage_model.stage_geometry.D_out_1 = D_out_1

    def _get_outlet_geom_parameters(self, alpha_3):
        c_a_rel_3 = self.stage_model.triangle_3.c_a_rel
        u_out_1 = self.stage_model.u_out_1
        a_crit_3 = self.stage_model.thermal_info.a_crit_3

        lambda_3 = self._lambda(c_a_rel_3, u_out_1, alpha_3, a_crit_3)
        lambda_1 = self._get_lambda_1()
        F_1 = self._get_F_1()

        q_relation = gdf.q(lambda_1, self.stage_model.k, self.stage_model.R) / \
                     gdf.q(lambda_3, self.stage_model.k, self.stage_model.R)
        p_stag_relation = self.stage_model.thermal_info.p_stag_1 / self.stage_model.thermal_info.p_stag_3
        T_stag_relation = self.stage_model.thermal_info.T_stag_1 / self.stage_model.thermal_info.T_stag_3

        F_3 = F_1 * q_relation * p_stag_relation / T_stag_relation**0.5

        D_3, d_rel_3 = self.stage_model.stage_geometry.get_outlet_parameters(F_3)

        return D_3, d_rel_3

    def _get_next_alpha_3(self, current_alpha_3, next_R_mean, next_H_t_rel):
        D_3, d_rel_3 = self._get_outlet_geom_parameters(current_alpha_3)

        self.stage_model.stage_geometry.D_out_3 = D_3
        self.stage_model.stage_geometry.d_rel_3 = d_rel_3

        r_m_rel_3 = self.stage_model.stage_geometry.r_m_rel_3

        c_u_rel_3 = self._c_u_rel(r_m_rel_3, next_R_mean, next_H_t_rel)
        self.stage_model.triangle_3.c_u_rel = c_u_rel_3

        return self.stage_model.triangle_3.alpha

    def _set_outlet_geom_parameters(self, next_R_mean, next_H_t_rel, eps):
        current_alpha_3 = self.stage_model.triangle_1.alpha
        new_alpha_3 = self._get_next_alpha_3(current_alpha_3, next_R_mean, next_H_t_rel)

        while abs(new_alpha_3 - current_alpha_3) / current_alpha_3 > eps:
            new_alpha_3 = self._get_next_alpha_3(current_alpha_3, next_R_mean, next_H_t_rel)
            # предыдущая команда также устанавливает выходной втулочный и периферийный диаметры
            current_alpha_3 = new_alpha_3

    def _set_n(self):
        self.stage_model.n = 60 / np.pi * self.stage_model.u_out_1 / self.stage_model.D_out_1

    def _set_relative_parameters(self):
        self.stage_model.triangle_1.r_m_rel = self.stage_model.stage_geometry.r_m_rel_1
        self.stage_model.triangle_2.r_m_rel = self.stage_model.stage_geometry.r_m_rel_2
        self.stage_model.triangle_3.r_m_rel = self.stage_model.stage_geometry.r_m_rel_3

        r_m_rel_1 = self.stage_model.stage_geometry.r_m_rel_1
        r_m_rel_2 = self.stage_model.stage_geometry.r_m_rel_2
        c_u_rel_1 = self.stage_model.triangle_1.c_u_rel
        H_t_rel = self.stage_model.H_t_rel

        c_u_2_rel = 1 / r_m_rel_2 * (H_t_rel + c_u_rel_1 * r_m_rel_1)

        self.stage_model.triangle_2.c_u_rel = c_u_2_rel

    def solve(self, stage_model, next_R_mean, next_H_t_rel, eps=0.01):  # Передается степень реактивности и коэффициент
                                                                    # теоретического напора ступени
        self.stage_model = stage_model

        self._set_T_stag_3()
        self._set_pi_stag()
        self._set_c_u_1_rel()
        self._set_D_out_1()
        self._set_outlet_geom_parameters(next_R_mean, next_H_t_rel, eps)
        self._set_n()
        self._set_relative_parameters()

        return stage_model

    def get_next_stage_model(self, stage_class, eta_ad, H_t_rel, R_mean, c_a_rel):
        next_stage_model = stage_class()

        next_stage_model.G = self.stage_model.G
        next_stage_model.T_stag_1 = self.stage_model.thermal_info.T_stag_3
        next_stage_model.p_stag_1 = self.stage_model.thermal_info.p_stag_3
        next_stage_model.n = self.stage_model.n
        next_stage_model.u_out_1 = np.pi / 60 * self.stage_model.n * self.stage_model.stage_geometry.D_out_3
        next_stage_model.D_out_1 = self.stage_model.stage_geometry.D_out_3
        next_stage_model.d_rel_1 = self.stage_model.stage_geometry.d_rel_3

        next_stage_model.eta_ad = eta_ad
        next_stage_model.H_t_rel = H_t_rel
        next_stage_model.R_mean = R_mean
        next_stage_model.c_a_rel = c_a_rel

        if self.stage_model.k_h <= 0.95:
            next_stage_model.k_h = self.stage_model.k_h
        else:
            next_stage_model.k_h = self.stage_model.k_h - 0.005

        return next_stage_model


class MeanRadiusCompressorSolver:
    def __init__(self):
        self._mean_radius_stage_solver = MeanRadiusStageSolver()

    def solve(self, compressor_model, eps=0.01):
        stages = list()

        stage_class_list = compressor_model.stage_class_list[1:]
        eta_ad_list = compressor_model.eta_ad_list[1:]

        H_t_rel_list = compressor_model.H_t_rel_list[1:]
        next_H_t_rel = list(H_t_rel_list[1:]) + [H_t_rel_list[-1]]

        R_mean_list = compressor_model.R_mean_list[1:]
        next_R_mean_list = list(R_mean_list[1:]) + [R_mean_list[-1]]

        c_a_rel_list = compressor_model.c_a_rel_list[1:]
        next_c_a_rel_list = list(c_a_rel_list[1:]) + [c_a_rel_list[-1]]

        stages.append(self._mean_radius_stage_solver.solve(compressor_model.first_stage, R_mean_list[0],
                                                           H_t_rel_list[0], eps))

        parameter_iterator = zip(stage_class_list, eta_ad_list, H_t_rel_list, R_mean_list, c_a_rel_list)
        next_stage_parameter_iterator = zip(next_R_mean_list, next_H_t_rel, next_c_a_rel_list)

        for parameter_tuple in parameter_iterator:
            next_stage = self._mean_radius_stage_solver.get_next_stage_model(*parameter_tuple)
            next_R_mean, next_H_t_rel, next_c_a_rel = next(next_stage_parameter_iterator)

            curr_c_a_rel = next_stage.triangle_1.c_a_rel
            next_stage.triangle_2.c_a_rel = (curr_c_a_rel + next_c_a_rel) / 2
            next_stage.triangle_3.c_a_rel = next_c_a_rel

            stages.append(self._mean_radius_stage_solver.solve(next_stage, next_R_mean, next_H_t_rel, eps))

        compressor_model.stages = stages
