import django
import os
import os.path
import json
import ast
import pandas as pd
from gas_dynamics.compressor_engine.web_handle import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compressor_site.settings")
django.setup()
from gas_dynamics import forms
from gas_dynamics import models


full_task = models.SingleCompressorTask.objects.get(name='initialized_task')

main_data_model = models.MainDataPart.objects.get(task=full_task)
mean_radius_data_model = models.MeanRadiusDataPart.objects.get(task=full_task)
profiling_data_model = models.ProfilingDataPart.objects.get(task=full_task)

main = MainDataBlock(main_data_model)
mean_radius = MeanRadiusDataBlock(mean_radius_data_model)
profiling = ProfilingDataBlock(profiling_data_model)

tasker = SolverTaskCreator(main, mean_radius, profiling)

data_dir = os.path.join(os.getcwd(), 'gas_dynamics', 'results', 'test_dir')
tasker.calculate_mean_radius(data_dir)
tasker.do_profiling(data_dir, data_dir)

#print(pd.read_pickle(os.path.join(data_dir, 'profiling_file_0.pkl')))





