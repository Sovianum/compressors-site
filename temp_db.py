import django
import os
import json
import ast

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compressor_site.settings")
django.setup()
from gas_dynamics import forms
from gas_dynamics.models import Project, SingleCompressorTask, MeanRadiusDataPart, ProfilingDataPart
from gas_dynamics.templatetags import project_content_extras
from django.forms.models import model_to_dict


#if __name__ == '__main__':


profilings = ProfilingDataPart.objects.all()
print(profilings)
temp = profilings[1]
form = forms.AltProfilingParametersForm(model_to_dict(temp))

print(form.is_valid())
print(form.errors)







