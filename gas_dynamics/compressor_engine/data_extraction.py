import numpy as np
import pandas as pd
import os.path


def extract_by_condition(data_dir, result_dir, condition, chunk_size=1000):
    result_df = None
    path_indexer = 1
    cnt = 1

    file_names = os.listdir(data_dir)
    data_paths = [os.path.join(data_dir, file_name) for file_name in file_names]

    for data_path in data_paths:
        data_df = pd.read_pickle(data_path)

        try:
            filtered_data_chunk = data_df.ix[condition(data_df).values]
        except Exception as e:
            print(e)
            raise e
        finally:
            print('Processed %d of %d' % (cnt, len(data_paths)))
            cnt += 1

        if str(type(data_df)) == "<class 'NoneType'>":
            result_df = filtered_data_chunk
        else:
            result_df = pd.concat([result_df, filtered_data_chunk])

        if len(result_df) > chunk_size:
            result_path = os.path.join(result_dir, 'file_%d.pkl' % path_indexer)
            path_indexer += 1
            pd.to_pickle(result_df, result_path)
            result_df = None

    try:
        if len(result_df) > 0:
            result_path = os.path.join(result_dir, 'file_%d.pkl' % path_indexer)
            path_indexer += 1
            pd.to_pickle(result_df, result_path)
    except TypeError:
        pass


def extract_compact(data_dir='results/profiled_gamma_constant/total', result_dir='results/profiled_gamma_constant/compact', chunk_size=1000):
    def condition(result_df):
        print(result_df.D_out_1.min())
        return result_df.D_out_1 <= 0.95

    extract_by_condition(data_dir, result_dir, condition, chunk_size)


def extract_non_turbine(data_dir='results/profiled_gamma_constant/total', result_dir='results/profiled_gamma_constant/non_turbine',
                        chunk_size=1000):
    def condition(result_df):
        return (result_df.root_c_u >= 0) & (result_df.betta_out <= 90)

    extract_by_condition(data_dir, result_dir, condition, chunk_size)


def extract_compact_non_turbine(data_dir='results/profiled_gamma_constant/total', result_dir='results/profiled_gamma_constant/compact_non_turbine',
                                chunk_size=1000):
    def condition(result_df):
        return (result_df.root_c_u >= -20) & (result_df.betta_out <= 90) & (result_df.D_out_1 <= 0.95)

    extract_by_condition(data_dir, result_dir, condition, chunk_size)


def extract_pi_stag_trend(data_dir='results/profiled_gamma_constant/total', result_dir='results/profiled_gamma_constant/pi_stag_trend',
                          chunk_size=1000):
    def condition(result_df):
        compressor_list = result_df.compressor.values
        pi_stag_series_list = [compressor.get_stage_info_data_frame().pi_stag for compressor in compressor_list]
        pi_stag_df = pd.DataFrame.from_records(pi_stag_series_list)

        indexer = pi_stag_df[1] == pi_stag_df[1]
        col_names = pi_stag_df.columns

        for curr_name, next_name in zip(col_names[:-1], col_names[1:]):
            temp = pi_stag_df[curr_name] >= pi_stag_df[next_name]
            indexer &= temp

        return indexer

    extract_by_condition(data_dir, result_dir, condition, chunk_size)


def collect_from_dir(data_dir):
    path_list = [os.path.join(data_dir, file_name) for file_name in os.listdir(data_dir)]
    df_list = [pd.read_pickle(path) for path in path_list]

    return pd.concat(df_list)


class DataExtractor:
    @classmethod
    def process_result_df(cls, result_df):
        compressor_series = result_df.compressor

        alpha_in_0 = compressor_series.apply(cls._first_stage_root_inlet_alpha)
        alpha_out_0 = compressor_series.apply(cls._first_stage_root_outlet_alpha)
        delta_alpha = alpha_in_0 - alpha_out_0

        betta_in_0 = compressor_series.apply(cls._first_stage_root_inlet_betta)
        betta_out_0 = compressor_series.apply(cls._first_stage_root_outlet_betta)
        delta_betta = compressor_series.apply(cls._first_stage_root_delta_betta)

        mean_c_a = compressor_series.apply(cls._first_stage_mean_c_a)
        root_c_u = compressor_series.apply(cls._first_stage_root_c_u)
        mean_mach_w_1 = compressor_series.apply(cls._first_stage_mean_mach_w_1)
        mean_mach_c_2 = compressor_series.apply(cls._first_stage_mean_mach_c_2)
        d_rel_1_first = compressor_series.apply(cls._first_stage_d_rel_1)
        d_rel_1_last = compressor_series.apply(cls._last_stage_d_rel_1)

        result_df['alpha_in'] = np.rad2deg(alpha_in_0)
        result_df['alpha_out'] = np.rad2deg(alpha_out_0)
        result_df['delta_alpha'] = np.rad2deg(delta_alpha)

        result_df['betta_in'] = np.rad2deg(betta_in_0)
        result_df['betta_out'] = np.rad2deg(betta_out_0)
        result_df['delta_betta'] = np.rad2deg(delta_betta)

        result_df['inlet_c_a'] = mean_c_a
        result_df['root_c_u'] = root_c_u
        result_df['M_w_1'] = mean_mach_w_1
        result_df['M_c_2'] = mean_mach_c_2
        result_df['inlet_d_rel_1'] = d_rel_1_first
        result_df['outlet_d_rel_1'] = d_rel_1_last


    @classmethod
    def _first_stage_root_inlet_alpha(cls, compressor):
        return compressor.first_stage.rotor_profiler.get_inlet_triangle(0).alpha

    @classmethod
    def _first_stage_root_outlet_alpha(cls, compressor):
        return compressor.first_stage.rotor_profiler.get_outlet_triangle(0).alpha

    @classmethod
    def _first_stage_root_inlet_betta(cls, compressor):
        return compressor.first_stage.rotor_profiler.get_inlet_triangle(0).betta

    @classmethod
    def _first_stage_root_outlet_betta(cls, compressor):
        return compressor.first_stage.rotor_profiler.get_outlet_triangle(0).betta

    @classmethod
    def _first_stage_root_delta_betta(cls, compressor):
        return cls._first_stage_root_outlet_betta(compressor) - cls._first_stage_root_inlet_betta(compressor)

    @classmethod
    def _first_stage_mean_c_a(cls, compressor):
        return compressor.first_stage.rotor_profiler.mean_inlet_triangle.c_a

    @classmethod
    def _first_stage_root_c_u(cls, compressor):
        return compressor.first_stage.rotor_profiler.get_inlet_triangle(0).c_u

    @classmethod
    def _first_stage_mean_mach_w_1(cls, compressor):
        return compressor.first_stage.mach_w_1

    @classmethod
    def _first_stage_mean_mach_c_2(cls, compressor):
        return compressor.first_stage.mach_c_2

    @classmethod
    def _first_stage_d_rel_1(cls, compressor):
        return compressor.first_stage.stage_geometry.d_rel_1

    @classmethod
    def _last_stage_d_rel_1(cls, compressor):
        return compressor.last_stage.stage_geometry.d_rel_1