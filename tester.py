import django
import os
import os.path
import json
import ast
import pandas as pd
import io
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

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
from gas_dynamics.compressor_engine import geometry_results


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


def test_widgets():
    project = models.Project.objects.all()[0]
    analyzer, _ = models.Analyzer.objects.get_or_create(project=project)
    analyzer.save()

    [print(i) for i in analyzer.plotprofilewidget_set.all()]
    print()

    plot_widget = models.PlotProfileWidget(analyzer=analyzer, name='widget_1')
    plot_widget.append()

    [print(i) for i in analyzer.plotprofilewidget_set.all()]
    print()

    another_widget = models.PlotProfileWidget(analyzer=analyzer, name='widget_2')
    plot_widget.insert(another_widget)

    [print(i) for i in analyzer.plotprofilewidget_set.all()]
    print()

    plot_widget.remove()


def clear_widgets():
    for analyzer in models.Analyzer.objects.all():
        analyzer.delete()


def test_plot_image():
    task = models.Task.objects.get(name='initialized_task')
    h = PlotProfileWidgetHandle.from_task(task)
    widget = h.update_widget(0, 'rotor', 0)
    h.clear_dir()



test_plot_image()

#test_compressor()
#test_tasker()
#print(pd.read_pickle(os.path.join(data_dir, 'profiling_file_0.pkl')))
#test_widgets()
#clear_widgets()





