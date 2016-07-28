import numpy as np
import pandas
import numpy
from . import mean_radius_calculation
from . import engine_logging
import os.path


def get_parabolic_shape_function(x1, x2, x_max, y1, y2, y_max):
    LHS_matrix = [[x1**2, x1, 1, 0, 0, 0],
                  [0, 0, 0, x2**2, x2, 1],
                  [2 * x_max, 1, 0, 0, 0, 0],
                  [0, 0, 0, 2 * x_max, 1, 0],
                  [x_max**2, x_max, 1, 0, 0, 0],
                  [0, 0, 0, x_max**2, x_max, 1]]
    RHS_column = [y1, y2, 0, 0, y_max, y_max]

    result_column = numpy.linalg.solve(LHS_matrix, RHS_column)
    left_coef_column = result_column[:3]
    right_coef_column = result_column[3:]

    def shape_function(x):
        mononom_vector = [x**2, x, 1]
        if x <= x_max:
            return sum([coef * mononom for coef, mononom in zip(left_coef_column, mononom_vector)])
        else:
            return sum([coef * mononom for coef, mononom in zip(right_coef_column, mononom_vector)])

    return shape_function


class MeanRadiusCompressorOptimizer:
    def __init__(self, compressor_prototype, pi_c, min_eta_ad, precision=0.05):
        self.compressor = compressor_prototype
        self.non_linear_func_gen = get_parabolic_shape_function
        self.compressor_solver = mean_radius_calculation.MeanRadiusCompressorSolver()
        self.pi_c = pi_c
        self.min_eta_ad = min_eta_ad
        self.precision = precision

        self.u_out_1 = list()
        self.d_rel_1 = list()

        self.H_t_rel_first = list()
        self.H_t_rel_last = list()
        self.H_t_rel_max = list()
        self.H_t_rel_max_coord = list()

        self.eta_ad_first = list()
        self.eta_ad_last = list()
        self.eta_ad_max = list()
        self.eta_ad_max_coord = list()

        self.c_a_rel_first = list()
        self.c_a_rel_last = list()

        self.R_mean_first = list()
        self.R_mean_last = list()

        self.inlet_alpha = list()

    def get_total_variant_number(self):
        result = 1
        result *= len(self.u_out_1)
        result *= len(self.d_rel_1)

        result *= len(self.H_t_rel_first)
        result *= len(self.H_t_rel_last)
        result *= len(self.H_t_rel_max)
        result *= len(self.H_t_rel_max_coord)

        result *= len(self.eta_ad_first)
        result *= len(self.eta_ad_last)
        result *= len(self.eta_ad_max)
        result *= len(self.eta_ad_max_coord)

        result *= len(self.c_a_rel_first)
        result *= len(self.c_a_rel_last)

        result *= len(self.R_mean_first)
        result *= len(self.R_mean_last)

        #result *= len(self.inlet_alpha)    TODO Разобраться, как раньше проводилась инициализация

        return result

    def _is_fully_initialized(self):
        return self.get_total_variant_number() > 0

    @staticmethod
    def _get_non_linear_parameter_value_list(parameter_func_gen, parameter_first, parameter_last, parameter_max, stage_num,
                                             parameter_max_coord):
        parameter_function = parameter_func_gen(1, stage_num, parameter_max_coord,
                                                parameter_first, parameter_last, parameter_max)

        parameter_value_list = [parameter_function(stage_ind) for stage_ind in range(1, stage_num + 1)]
        return parameter_value_list

    @staticmethod
    def _get_linear_parameter_list(parameter_first, parameter_last, stage_num):
        return np.linspace(parameter_first, parameter_last, stage_num)

    @staticmethod
    def _get_H_t_rel_list(H_t_rel_func_gen, H_t_rel_first, H_t_rel_last, H_t_rel_max, stage_num, H_t_rel_max_coord):
        return MeanRadiusCompressorOptimizer._get_non_linear_parameter_value_list(H_t_rel_func_gen, H_t_rel_first, H_t_rel_last,
                                                                                  H_t_rel_max, stage_num, H_t_rel_max_coord)

    @staticmethod
    def _get_eta_ad_list(eta_ad_func_gen, eta_ad_first, eta_ad_last, eta_ad_max, stage_num, eta_ad_max_coord):
        return MeanRadiusCompressorOptimizer._get_non_linear_parameter_value_list(eta_ad_func_gen, eta_ad_first, eta_ad_last,
                                                                                  eta_ad_max, stage_num, eta_ad_max_coord)

    @staticmethod
    def _get_c_a_rel_list(c_a_rel_first, c_a_rel_last, stage_num):
        return MeanRadiusCompressorOptimizer._get_linear_parameter_list(c_a_rel_first, c_a_rel_last, stage_num)

    @staticmethod
    def _get_R_mean_list(R_mean_first, R_mean_last, stage_num):
        return MeanRadiusCompressorOptimizer._get_linear_parameter_list(R_mean_first, R_mean_last, stage_num)

    def _get_compressor_model(self, u_out_1, d_rel_1, H_t_rel_first, H_t_rel_last, H_t_rel_max, H_t_rel_max_coord,
                              eta_ad_first, eta_ad_last, eta_ad_max, eta_ad_max_coord, c_a_rel_first, c_a_rel_last,
                              R_mean_first, R_mean_last, inlet_alpha):
        compressor_copy = self.compressor.get_incomplete_copy()
        stage_num = len(compressor_copy.stage_class_list)

        H_t_rel_list = self._get_H_t_rel_list(self.non_linear_func_gen, H_t_rel_first, H_t_rel_last, H_t_rel_max,
                                              stage_num, H_t_rel_max_coord)
        eta_ad_list = self._get_eta_ad_list(self.non_linear_func_gen, eta_ad_first, eta_ad_last, eta_ad_max, stage_num,
                                            eta_ad_max_coord)
        c_a_rel_list = self._get_c_a_rel_list(c_a_rel_first, c_a_rel_last, stage_num)
        R_mean_list = self._get_R_mean_list(R_mean_first, R_mean_last, stage_num)

        compressor_copy.first_stage.u_out_1 = u_out_1
        compressor_copy.first_stage.d_rel_1 = d_rel_1
        compressor_copy.H_t_rel_list = H_t_rel_list
        compressor_copy.eta_ad_list = eta_ad_list
        compressor_copy.c_a_rel_list = c_a_rel_list
        compressor_copy.R_mean_list = R_mean_list
        compressor_copy.rotor_velocity_law_list = self.compressor.rotor_velocity_law_list
        compressor_copy.stator_velocity_law_list = self.compressor.stator_velocity_law_list
        compressor_copy.inlet_alpha = inlet_alpha

        return compressor_copy

    def _get_index(self):
        iterable_list = list()
        name_list = list()

        iterable_list.append(self.u_out_1)
        name_list.append('u_out_1')
        iterable_list.append(self.d_rel_1)
        name_list.append('d_rel_1')

        iterable_list.append(self.H_t_rel_first)
        name_list.append('H_t_rel_first')
        iterable_list.append(self.H_t_rel_last)
        name_list.append('H_t_rel_last')
        iterable_list.append(self.H_t_rel_max)
        name_list.append('H_t_rel_max')
        iterable_list.append(self.H_t_rel_max_coord)
        name_list.append('H_t_rel_max_coord')

        iterable_list.append(self.eta_ad_first)
        name_list.append('eta_ad_first')
        iterable_list.append(self.eta_ad_last)
        name_list.append('eta_ad_last')
        iterable_list.append(self.eta_ad_max)
        name_list.append('eta_ad_max')
        iterable_list.append(self.eta_ad_max_coord)
        name_list.append('eta_ad_max_coord')

        iterable_list.append(self.c_a_rel_first)
        name_list.append('c_a_rel_first')
        iterable_list.append(self.c_a_rel_last)
        name_list.append('c_a_rel_last')

        iterable_list.append(self.R_mean_first)
        name_list.append('R_mean_first')
        iterable_list.append(self.R_mean_last)
        name_list.append('R_mean_last')
        iterable_list.append(self.inlet_alpha)
        name_list.append('inlet_alpha')

        index = pandas.MultiIndex.from_product(iterable_list, names=name_list)

        return index

    def _is_valid_pi_c(self, pi_c):
        residual = abs((pi_c - self.pi_c)) / self.pi_c
        return (residual < self.precision) and (pi_c >= self.pi_c)

    def _is_valid_pi_c_trend(self, compressor):
        pi_c = 1e10

        for stage in compressor.stages:
            if stage.thermal_info.pi_stag > pi_c:
                return False
            else:
                pi_c = stage.thermal_info.pi_stag

        return True

    def _is_valid_eta_ad(self, eta_ad):
        return eta_ad >= self.min_eta_ad

    @staticmethod
    def _get_compressor_info(index, names):
        result = dict(zip(names, index))

        return result

    @staticmethod
    def _get_compressor_variants_info(compressor_list, valid_index_list, parameter_names):
        variant_dicts = [MeanRadiusCompressorOptimizer._get_compressor_info(index, parameter_names)
                         for index in valid_index_list]

        for variant_dict, compressor in zip(variant_dicts, compressor_list):
            variant_dict['pi_c'] = compressor.pi_stag_compressor()
            variant_dict['eta_ad'] = compressor.eta_ad_compressor()
            variant_dict['inlet_alpha'] = np.rad2deg(compressor.inlet_alpha)

        if not variant_dicts:
            return 'Solution not found'

        info_frame = pandas.DataFrame.from_records(variant_dicts)
        info_frame = info_frame[['pi_c', 'eta_ad'] + parameter_names]

        return info_frame

    def _get_validator(self, frequency=1000):
        optimizer = self

        class Validator:
            def __init__(self, frequency):
                self.frequency = frequency
                self.optimizer = optimizer
                self.processed_num = 0
                self.valid_num = 0
                self.quasi_valid_num = 0
                self.total_num = optimizer.get_total_variant_number()
                self.start_time = None

                self.max_eta = 0
                self.max_pi_c = 0
                self.min_eta = 1e10
                self.min_pi_c = 1e10

                self.logger = engine_logging.CompressorSearchInfo(compressor_validator=self)

            def validate(self, compressor):
                if not self.logger.started:
                    self.logger.start()

                pi_c = compressor.pi_stag_compressor()
                eta_ad = compressor.eta_ad_compressor()

                if pi_c > self.max_pi_c:
                    self.max_pi_c = pi_c
                if eta_ad > self.max_eta:
                    self.max_eta = eta_ad
                if pi_c < self.min_pi_c:
                    self.min_pi_c = pi_c
                if eta_ad < self.min_eta:
                    self.min_eta = eta_ad

                self.processed_num += 1
                if self.optimizer._is_valid_pi_c(pi_c) and self.optimizer._is_valid_eta_ad(eta_ad):
                    self.quasi_valid_num += 1
                    if self.optimizer._is_valid_pi_c_trend(compressor):
                        is_valid = True
                        self.valid_num += 1
                    else:
                        is_valid = False
                else:
                    is_valid = False

                if self.processed_num % frequency == 0:
                    self.logger.finish()

                    self.max_pi_c = 0
                    self.max_eta = 0
                    self.min_eta = 1e10
                    self.min_pi_c = 1e10

                return is_valid

        return Validator(frequency)

    def get_variants_df(self, save_dir, file_prefix, eps=0.01, chunk_size=1000):
        assert self._is_fully_initialized(), 'Object is not fully initialized.'

        index = self._get_index()

        compressor_list = list()
        valid_index_list = list()

        validator = self._get_validator()
        file_index = 1

        for item in index:
            try:
                compressor = self._get_compressor_model(*item)

                self.compressor_solver.solve(compressor, eps)

                if validator.validate(compressor):
                    compressor_list.append(compressor)
                    valid_index_list.append(item)

            except AssertionError as e:
                logger = engine_logging.CaughtErrorsLogger()
                logger.log()
                continue

            if len(valid_index_list) == chunk_size:
                compressor_variant_info = self._get_compressor_variants_info(compressor_list,
                                                                             valid_index_list, index.names)
                compressor_variant_info['compressor'] = compressor_list
                compressor_variant_info['D_out_1'] = [compressor.stages[0].D_out_1 for compressor in compressor_list]

                path = os.path.join(save_dir,  '%s_%d.pkl' % (file_prefix, file_index))

                compressor_variant_info.to_pickle(path)

                file_index += 1

                valid_index_list = list()
                compressor_list = list()

        if len(valid_index_list) > 0:
            compressor_variant_info = self._get_compressor_variants_info(compressor_list,
                                                                             valid_index_list, index.names)
            compressor_variant_info['compressor'] = compressor_list
            compressor_variant_info['D_out_1'] = [compressor.stages[0].D_out_1 for compressor in compressor_list]

            path = os.path.join(save_dir,  '%s_%d.pkl' % (file_prefix, file_index))

            compressor_variant_info.to_pickle(path)
