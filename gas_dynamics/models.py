from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import ast


class ListTextField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return str(value)


class ListIntField(models.IntegerField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListIntField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return str(value)


class ListFloatField(models.IntegerField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListFloatField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return str(value)


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


class MainDataPart(DataPart):   # TODO Добавить степень повышения давления
    mass_rate = models.FloatField()
    T_stag_1 = models.FloatField()
    p_stag_1 = models.FloatField()
    eta_ad_min = models.FloatField()
    stage_number = models.IntegerField(default=1)
    precision = models.FloatField(default=0.03)


class MeanRadiusDataPart(DataPart):
    u_out_1 = models.FloatField()
    d_rel_1 = models.FloatField()

    H_t_rel_first = models.FloatField()
    H_t_rel_last = models.FloatField()
    H_t_rel_max = models.FloatField()
    H_t_rel_max_coord = models.FloatField()

    eta_ad_first = models.FloatField()
    eta_ad_last = models.FloatField()
    eta_ad_max = models.FloatField()
    eta_ad_max_coord = models.FloatField()

    c_a_rel_first = models.FloatField()
    c_a_rel_last = models.FloatField()

    reactivity_first = models.FloatField()
    reactivity_last = models.FloatField()

    inlet_alpha = models.FloatField(blank=True, null=True)
    flow_section_type = ListTextField()


class ProfilingDataPart(DataPart):
    rotor_velocity_law = ListTextField()
    stator_velocity_law = ListTextField()

    rotor_blade_profile = ListTextField()
    stator_blade_profile = ListTextField()

    rotor_blade_elongation = ListTextField()
    stator_blade_elongation = ListTextField()

    rotor_lattice_density = ListTextField()
    stator_lattice_density = ListTextField()







