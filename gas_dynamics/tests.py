from django.test import TestCase
from .models import MeanRadiusSingleCompressorTask, Project
from django.utils import timezone


class ProjectMethodTest(TestCase):
    @classmethod
    def make_valid_project(cls, name='test project'):
        project = Project(name=name,
                          start_date=timezone.now(),
                          modify_date=timezone.now())
        return project

    def test_addition(self):
        project = self.make_valid_project()
        project.save()


class MeanRadiusSingleCompressorTaskMethodTest(TestCase):
    @classmethod
    def make_valid_task(cls, project, name='test_task'):
        valid_task = project.compressor_set.create(
            name=name,

            mass_rate=128,
            T_stag_1=288,
            p_stag_1=1e5,
            min_eta_ad=0.855,
            stage_number=4,
            precision=0.03,

            u_out_1=475,
            d_rel_1=0.4,

            H_t_rel_first=0.22,
            H_t_rel_last=0.22,
            H_t_rel_max=0.25,
            H_t_rel_max_coord=2,

            eta_ad_first=0.88,
            eta_ad_last=0.86,
            eta_ad_max=0.9,
            eta_ad_max_coord=2.5,

            c_a_rel_first=0.49,
            c_a_rel_last=0.45,

            reactivity_first=0.55,
            reactivity_last=0.6,

            inlet_alpha=85,

            constant_diameter_parameters='1111'
        )
        return valid_task

    def test_task_addition(self):
        project = ProjectMethodTest.make_valid_project('test')
        project.save()
        task = self.make_valid_task(project)
        task.save()
