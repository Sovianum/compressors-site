import django
import os
import os.path
import json
import ast
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compressor_site.settings")
django.setup()

from gas_dynamics.compressor_engine_handle import *
from gas_dynamics import forms
from gas_dynamics import models
from django.conf import settings
from django.core.files import File
import gas_dynamics.models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pickle


def test_tasker():
    full_task = models.Task.objects.get(name='initialized_task')

    tasker = CompressorSolver(full_task)
    
    tasker.calculate_mean_radius()
    tasker.do_profiling()


def test_file_storage():
    #temp_model = gas_dynamics.models.FileModel.objects.create(name='temp')
    path_to_file = os.path.join(settings.MEDIA_ROOT, 'temp_dir', 'some_file.pkl')
    obj = {
        'a': 1,
        'b': 2,
    }
    file = ContentFile(pickle.dumps(obj))
    path = default_storage.save(path_to_file, file)
    print(path)

test_tasker()
#print(pd.read_pickle(os.path.join(data_dir, 'profiling_file_0.pkl')))







