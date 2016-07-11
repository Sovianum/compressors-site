import django.utils.timezone
import django.forms
from django.core.validators import RegexValidator

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


class MainParametersForm(django.forms.Form):
    precision = django.forms.FloatField()
    stage_number = django.forms.IntegerField()
    mass_rate = django.forms.FloatField()
    T_stag_1 = django.forms.FloatField()
    eta_ad_min = django.forms.FloatField(min_value=0, max_value=1)


class MeanRadiusForm(django.forms.Form):
    stage_number = django.forms.IntegerField(label='stage_number')
    mass_rate = django.forms.FloatField(label='Mass rate')
    T_stag_1 = django.forms.FloatField(label='T_stag_1')
    p_stag_1 = django.forms.FloatField(label='p_stag_1')
    min_eta_ad = django.forms.FloatField(label='min_eta_ad')


class MeanRadiusSingleCompressorForm(MeanRadiusForm):

    u_out_1 = django.forms.FloatField(label='u_out_1')
    d_rel_1 = django.forms.FloatField(label='d_rel_1')

    H_t_rel_first = django.forms.FloatField(label='H_t_rel_first')
    H_t_rel_last = django.forms.FloatField(label='H_t_rel_last')
    H_t_rel_max = django.forms.FloatField(label='H_t_rel_max')
    H_t_rel_max_coord = django.forms.FloatField(label='H_t_rel_max_coord')

    eta_ad_first = django.forms.FloatField(label='eta_ad_first')
    eta_ad_last = django.forms.FloatField(label='eta_ad_last')
    eta_ad_max = django.forms.FloatField(label='eta_ad_max')
    eta_ad_max_coord = django.forms.FloatField(label='eta_ad_max_coord')

    c_a_rel_first = django.forms.FloatField(label='c_a_rel_first')
    c_a_rel_last = django.forms.FloatField(label='c_a_rel_last')

    reactivity_first = django.forms.FloatField(label='reactivity_first')
    reactivity_last = django.forms.FloatField(label='reactivity_last')

    inlet_alpha = django.forms.FloatField(label='inlet_alpha')

