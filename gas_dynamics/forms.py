import django.utils.timezone
import django.forms
from django.core.validators import RegexValidator
from . import models
import demjson


class LoginForm(django.forms.Form):
    username = django.forms.CharField()
    password = django.forms.CharField()


class GetPlotForm(django.forms.Form):
    plot_name = django.forms.CharField()
    stage_num = django.forms.IntegerField()
    lattice_type = django.forms.ChoiceField(choices=(('rotor', 'rotor'), ('stator', 'stator')))
    h_rel = django.forms.FloatField(min_value=0, max_value=1)


class AddProjectForm(django.forms.Form):
    validator = RegexValidator(r'^[0-9a-zA-Z_]*$', 'Only alphanum and underscore allowed', code=500)
    name = django.forms.CharField(label="Project name", max_length=200)


class AddTaskForm(django.forms.Form):
    validator = RegexValidator(r'^[0-9a-zA-Z_]*$', 'Only alphanum and underscore allowed', code=500)
    name = django.forms.CharField(label="Project name", max_length=200)


class MainParametersForm(django.forms.ModelForm):
    class Meta:
        model = models.MainDataPart
        fields = ['mass_rate', 'T_stag_1', 'p_stag_1', 'eta_ad_min', 'stage_number', 'precision']


class MeanRadiusParametersForm(django.forms.ModelForm):
    class Meta:
        model = models.MeanRadiusDataPart
        fields = ['u_out_1', 'd_rel_1',
                  'H_t_rel_first', 'H_t_rel_last', 'H_t_rel_max', 'H_t_rel_max_coord',
                  'eta_ad_first', 'eta_ad_last', 'eta_ad_max', 'eta_ad_max_coord',
                  'c_a_rel_first', 'c_a_rel_last',
                  'reactivity_first', 'reactivity_last',
                  'inlet_alpha', 'flow_section_type']


class ProfilingParametersForm(django.forms.ModelForm):
    class Meta:
        model = models.ProfilingDataPart
        fields = ['rotor_velocity_law', 'stator_velocity_law',
                  'rotor_blade_profile', 'stator_blade_profile',
                  'rotor_blade_elongation', 'stator_blade_elongation',
                  'rotor_lattice_density', 'stator_lattice_density']


class ListField(django.forms.CharField):
    def to_python(self, value):
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            try:
                return demjson.decode(value)
            except demjson.JSONDecodeError:
                raise TypeError("Value must be of 'list' type or encoded list str: %s" % str(value))

    def validate(self, value):
        super(ListField, self).validate(str(value))

        for val in value:
            super(ListField, self).validate(val)


class AltProfilingParametersForm(django.forms.ModelForm):
    class Meta:
        model = models.ProfilingDataPart
        exclude = ['task', 'state']

    rotor_velocity_law = ListField(widget=django.forms.Textarea)
    stator_velocity_law = ListField(widget=django.forms.Textarea)

    rotor_blade_profile = ListField(widget=django.forms.Textarea)
    stator_blade_profile = ListField(widget=django.forms.Textarea)

    rotor_blade_elongation = ListField(widget=django.forms.Textarea)
    stator_blade_elongation = ListField(widget=django.forms.Textarea)

    rotor_lattice_density = ListField(widget=django.forms.Textarea)
    stator_lattice_density = ListField(widget=django.forms.Textarea)
