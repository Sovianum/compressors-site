import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compressor_site.settings")
django.setup()
from gas_dynamics.models import Project, SingleCompressorTask


if __name__ == '__main__':
    project = Project.objects.get(name='Project_67')

    def get_project(task_number):
        data_1 = {
            'name': 'test_task_%d' % task_number,
            'mass_rate': 125,
            'T_stag_1': 273,
            'p_stag_1': 1e5,
            'min_eta_ad': 0.85,
            'stage_number': 4,
            'precision': 0.03
        }
        task = SingleCompressorTask(project=project, **data_1)
        task.save()

    for i in range(10, 30):
        get_project(i)


