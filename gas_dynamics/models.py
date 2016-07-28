from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import ast


class ListField(models.TextField):
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, context):
        if not value:
            value = []

        if isinstance(value, list):
            return value
        if isinstance(value, str):
            result = ast.literal_eval(value)

            if isinstance(result, list):
                return result
            elif isinstance(result, int) or isinstance(result, float):
                return [result]

        raise ValueError('Inappropriate value type: %s (%s)' % (value, type(value)))

    def get_prep_value(self, value):
        if not value:
            return value
        if isinstance(value, int) or isinstance(value, float):
            return str([value])
        if isinstance(value, list):
            return str(value)
        if isinstance(value, str):
            result = ast.literal_eval(value)

            if isinstance(result, list):
                return value
            elif isinstance(result, int) or isinstance(result, float):
                return '[' + value + ']'
        else:
            raise ValueError('Inappropriate value type: %s (%s)' % (value, type(value)))


class Project(models.Model):
    def __str__(self):
        return self.name

    user = models.ForeignKey(User)
    name = models.CharField(max_length=200, unique=True)
    start_date = models.DateTimeField('date started', default=timezone.now())

    class Meta:
        unique_together = (('user', 'name'),)


class TaskPrototype(models.Model):
    def __str__(self):
        return self.project.name + ': ' + self.name

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('project', 'name'),)
        abstract = True


class SingleCompressorTask(TaskPrototype):
    pass


class DataPart(models.Model):
    def __str__(self):
        return '%s: %s' % (str(self.task), self.__class__.__name__)

    task = models.OneToOneField(SingleCompressorTask, on_delete=models.CASCADE)
    state = models.CharField(max_length=50)

    class Meta:
        abstract = True


class MainDataPart(DataPart):
    pi_c = models.FloatField()
    mass_rate = models.FloatField()
    T_stag_1 = models.FloatField()
    p_stag_1 = models.FloatField()
    eta_ad_min = models.FloatField()
    stage_number = models.IntegerField(default=1)
    precision = models.FloatField(default=0.03)


class MeanRadiusDataPart(DataPart):
    u_out_1 = ListField()
    d_rel_1 = ListField()

    H_t_rel_first = ListField()
    H_t_rel_last = ListField()
    H_t_rel_max = ListField()
    H_t_rel_max_coord = ListField()

    eta_ad_first = ListField()
    eta_ad_last = ListField()
    eta_ad_max = ListField()
    eta_ad_max_coord = ListField()

    c_a_rel_first = ListField()
    c_a_rel_last = ListField()

    reactivity_first = ListField()
    reactivity_last = ListField()

    inlet_alpha = ListField(blank=True, default=[90])
    flow_section_type = ListField()


class ProfilingDataPart(DataPart):
    rotor_velocity_law = ListField()
    stator_velocity_law = ListField()

    rotor_blade_profile = ListField()
    stator_blade_profile = ListField()

    rotor_blade_elongation = ListField()
    stator_blade_elongation = ListField()

    rotor_lattice_density = ListField()
    stator_lattice_density = ListField()

    rotor_blade_windage = ListField()
    stator_blade_windage = ListField()







