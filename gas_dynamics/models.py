from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


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
    task = models.OneToOneField(SingleCompressorTask, on_delete=models.CASCADE)
    state = models.CharField(max_length=50)

    class Meta:
        abstract = True


class MainDataPart(DataPart):
    mass_rate = models.FloatField()
    T_stag_1 = models.FloatField()
    p_stag_1 = models.FloatField()
    eta_ad_min = models.FloatField()
    stage_number = models.IntegerField()
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
    constant_diameter_parameters = models.CharField(max_length=200)


class ProfilingDataPart(DataPart):
    rotor_velocity_law = models.CharField(max_length=1000)
    stator_velocity_law = models.CharField(max_length=1000)

    rotor_blade_profile = models.CharField(max_length=1000)
    stator_blade_profile = models.CharField(max_length=1000)

    rotor_blade_elongation = models.CharField(max_length=1000)
    stator_blade_elongation = models.CharField(max_length=1000)

    rotor_lattice_density = models.CharField(max_length=1000)
    stator_lattice_density = models.CharField(max_length=1000)








