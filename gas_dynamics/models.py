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


class CompressorPartPlot(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=200)
    compressor_name = models.CharField(max_length=500)
    plot_image = models.ImageField()


class BladeProfilePlot(CompressorPartPlot):
    blade_number = models.IntegerField()
    h_rel = models.FloatField()


class TaskMainPart(models.Model):
    def __str__(self):
        return self.project.name + ': ' + self.name

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    mass_rate = models.FloatField(blank=True, null=True)
    T_stag_1 = models.FloatField(blank=True, null=True)
    p_stag_1 = models.FloatField(blank=True, null=True)
    min_eta_ad = models.FloatField(blank=True, null=True)
    stage_number = models.IntegerField(blank=True, null=True)

    precision = models.FloatField(default=0.03, blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = (('project', 'name'),)


class SingleCompressorTask(TaskMainPart):

    u_out_1 = models.FloatField(blank=True, null=True)
    d_rel_1 = models.FloatField(blank=True, null=True)

    H_t_rel_first = models.FloatField(blank=True, null=True)
    H_t_rel_last = models.FloatField(blank=True, null=True)
    H_t_rel_max = models.FloatField(blank=True, null=True)
    H_t_rel_max_coord = models.FloatField(blank=True, null=True)

    eta_ad_first = models.FloatField(blank=True, null=True)
    eta_ad_last = models.FloatField(blank=True, null=True)
    eta_ad_max = models.FloatField(blank=True, null=True)
    eta_ad_max_coord = models.FloatField(blank=True, null=True)

    c_a_rel_first = models.FloatField(blank=True, null=True)
    c_a_rel_last = models.FloatField(blank=True, null=True)

    reactivity_first = models.FloatField(blank=True, null=True)
    reactivity_last = models.FloatField(blank=True, null=True)

    inlet_alpha = models.FloatField(blank=True, null=True)
    constant_diameter_parameters = models.CharField(max_length=200, blank=True, null=True)







