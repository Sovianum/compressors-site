import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compressor_site.settings")
django.setup()
from gas_dynamics.models import Project, SingleCompressorTask
from gas_dynamics.templatetags import project_content_extras


if __name__ == '__main__':
    task = SingleCompressorTask.objects.all()[2]
    context = {'task': task}
    form_type = 'mean_radius'
    field_name = 'u_out_1'

    print(project_content_extras.get_form_val(context, form_type, field_name))




