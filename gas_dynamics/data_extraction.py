import pandas as pd
import os
import os.path
from .compressor_engine import post_processing
from .compressor_engine import geometry_results
import matplotlib.pyplot as plt
import re

'''
    Устаревший файл. Использовался ранее для построения профилей лопатки.
'''


class CompressorHandler:
    def __init__(self, compressor):
        self.compressor = compressor

    def _get_file_name(self, plot_name, time_stamp):
        return '%s_%d.png' % (plot_name, int(time_stamp))

    def _clear_img_dir(self, plot_name, dir):
        regex = re.compile('^%s_[0-9]+\.png' % plot_name)
        remove_names = [file_name for file_name in os.listdir(dir) if regex.match(file_name)]
        for file_name in remove_names:
            os.remove(os.path.join(dir, file_name))

    def get_profile_plot(self, stage_number, lattice_type, h_rel, plot_name, time_stamp):
        if lattice_type == 'rotor':
            profiler = self.compressor.stages[stage_number].rotor_profiler
        elif lattice_type == 'stator':
            profiler = self.compressor.stages[stage_number].stator_profiler
        else:
            raise ValueError('incorrect lattice type')

        profile = geometry_results.BladeProfile.from_profiler(profiler, h_rel)

        fig = plt.figure(figsize=(12, 10))
        post_processing.PostProcessor.plot_profile(profile)
        plt.grid()

        img_dir = (os.path.join(os.path.dirname(__file__), 'static', 'gas_dynamics', 'images'))
        self._clear_img_dir(plot_name, img_dir)
        file_name = self._get_file_name(plot_name, time_stamp)
        plt.savefig(os.path.join(img_dir, file_name))

        plt.close(fig)
        plt.close()

        return os.path.join('/', 'static', 'gas_dynamics', 'images', file_name)


class DebugCompressorHandler(CompressorHandler):
    def __init__(self):
        compressor = pd.read_pickle(os.path.join(os.path.dirname(__file__), 'results',
                                                 'chosen_compressor', 'compressor.pkl'))

        CompressorHandler.__init__(self, compressor)
