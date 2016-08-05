from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import os
import os.path
import ast
import itertools
from . import compressor_engine_handle


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
    class TASK_KIND:
        unset = 'unset'
        single = 'single'
        multi = 'multi'

    class TASK_STATE:
        unset = 'unset'
        mean_radius = 'mean_radius'
        profiled = 'profiled'

    def __str__(self):
        return self.project.name + ': ' + self.name

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    is_single = models.BooleanField(default=True)

    kind = models.CharField(max_length=30, default=TASK_KIND.unset)
    state = models.CharField(max_length=30, default=TASK_STATE.unset)

    class Meta:
        unique_together = (('project', 'name'),)
        abstract = True


class Task(TaskPrototype):
    pass


class DataPart(models.Model):
    def __str__(self):
        return '%s: %s' % (str(self.task), self.__class__.__name__)

    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    state = models.CharField(max_length=50)

    def get_task_kind(self):
        return Task.TASK_KIND.single

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

    def get_task_kind(self):
        field_names = [
            'u_out_1', 'd_rel_1',
            'H_t_rel_first', 'H_t_rel_last', 'H_t_rel_max', 'H_t_rel_max_coord',
            'eta_ad_first', 'eta_ad_last', 'eta_ad_max', 'eta_ad_max_coord',
            'c_a_rel_first', 'c_a_rel_last',
            'reactivity_first', 'reactivity_last',
            'inlet_alpha'
        ]

        def to_list(value): #TODO Разобраться, почему в некоторых случаях не работет ListField: возвращает строку вместо списка
            '''
                This function is a workaround of the problem with a ListField.
                While updating task it in some cases returns a string instead of a list.
                The reason is unknown
            '''
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

        for name in field_names:
            if len(to_list(getattr(self, name))) > 1:
                return Task.TASK_KIND.multi
        return Task.TASK_KIND.single


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


class Result(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, null=True)

    kind = models.CharField(max_length=30, default=Task.TASK_KIND.unset)
    state = models.CharField(max_length=30, default=Task.TASK_STATE.unset)

    @classmethod
    def from_task(cls, task: Task):
        return cls(
            name=task.name,
            project=task.project,
            task=task,
            kind=task.kind,
            state=task.state
        )

    def get_profiling_paths(self):
        assert self.profiling_ready, 'Profiling calculation has not been performed yet'

        return [os.path.join(self.profiling_dir, filename) for filename in os.listdir(self.profiling_dir)]

    def get_mean_radius_paths(self):
        assert self.mean_radius_ready, 'Mean radius calculation has not been performed yet'

        return [os.path.join(self.mean_radius_dir, filename) for filename in os.listdir(self.mean_radius_dir)]

    @property
    def mean_radius_dir(self):
        return os.path.join(self._result_dir, 'mean_radius')

    @property
    def profiling_dir(self):
        return os.path.join(self._result_dir, 'profiling')

    @property
    def _result_dir(self):
        media_root = settings.MEDIA_ROOT
        app_name = os.path.split(os.path.dirname(os.path.realpath(__file__)))[1]
        user = self.project.user

        return os.path.join(media_root, app_name, user.username, self.project.name, self.name)


class Analyzer(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    widget_num = models.IntegerField(default=0)

    widget_set_names = None


class AnalysisWidget(models.Model):
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='NoName')
    position = models.IntegerField(unique=True)

    HOLDER_CLASS = Analyzer

    def __str__(self):
        return '%(name)s: %(pos)d' % {
            'name': self.name,
            'pos': self.position
        }

    def remove(self):
        assert self.position, 'Can not remove unsaved widget'

        position = self.position
        analyzer = self.analyzer
        to_renumerate = self._get_widgets_gt_position(position, self.analyzer)
        self.delete()

        self._decrement_widgets(to_renumerate)

        analyzer.widget_num -= 1
        analyzer.save()

    def insert(self, widget):
        assert not self.position, 'Widget has been inserted already'

        position = self.position + 1

        to_renumerate = self._get_widgets_gt_position(position, self.analyzer)
        self._increment_widgets(to_renumerate)

        widget.position = position
        widget.save()

        self.analyzer.widget_num += 1
        self.save()

    def append(self):
        assert not self.position, 'Widget has been inserted already'

        self.position = self.analyzer.widget_num
        self.save()

        self.analyzer.widget_num += 1
        self.analyzer.save()

    @classmethod
    def _increment_widgets(cls, widgets):
        for widget in widgets:
            widget.position += 1

        for widget in widgets:
            widget.save()

    @classmethod
    def _decrement_widgets(cls, widgets):
        for widget in widgets:
            widget.position -= 1

        for widget in widgets:
            widget.save()

    @classmethod
    def _get_widgets_gt_position(cls, position, analyzer):
        """
        :param position:
        :return: all widgets: widget.position >= position
        """

        widget_set_names = cls._get_widget_set_names()
        widget_sets = [getattr(analyzer, widget_set_name).filter(position__gt=position).all()
                       for widget_set_name in widget_set_names]
        widget_list = list(itertools.chain(*widget_sets))
        return widget_list

    @classmethod
    def _get_widget_in_position(cls, position, analyzer):
        widget_set_names = cls._get_widget_set_names()

        for widget_set_name in widget_set_names:
            widget_set = getattr(analyzer, widget_set_name).filter(position=position).all()

            if widget_set:
                assert len(widget_set) <= 1, 'Non unique position'
                return widget_set[0]

        raise compressor_engine_handle.OperationFailedError('Widget on specified position not found')

    def _check_widget_position(self, position):
        assert position >= 0, 'Position can not be negative'
        assert position <= self.analyzer.widget_num, 'Max position is %(max)d. Tried to set %(try)d.' % {
            'max': self.analyzer.widget_num,
            'try': position
        }

    @classmethod
    def _get_widget_set_names(cls):

        if cls.HOLDER_CLASS.widget_set_names is None:
            parent_class = AnalysisWidget
            cls.HOLDER_CLASS.widget_set_names = cls._get_subclasses_derivative(parent_class,
                                                                               lambda class_: class_.__name__.lower() + '_set')

        return cls.HOLDER_CLASS.widget_set_names

    @staticmethod
    def _get_subclasses_derivative(class_, func):
        def _get_subclasses(class_, subclass_set):
            subclasses = class_.__subclasses__()

            if not subclasses:
                return subclass_set
            else:
                for subclass in subclasses:
                    subclass_set.add(func(subclass))
                    _get_subclasses(subclass, subclass_set)
                return subclass_set

        return _get_subclasses(class_, set())

    @property
    def _result_dir(self):
        media_root = settings.MEDIA_ROOT
        app_name = os.path.split(os.path.dirname(os.path.realpath(__file__)))[1]
        user = self.analyzer.project.user
        project = self.analyzer.project

        return os.path.join(media_root, app_name, user.username, project.name, 'analysis_files')

    class Meta:
        abstract = True


class PlotProfileWidget(AnalysisWidget):
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE)
    image_name = models.CharField(max_length=255, default='')

    stage_number = models.IntegerField(default=0)
    lattice_type = models.CharField(max_length=10, default='rotor')
    h_rel = models.FloatField(default=0)


class ComparingWidget(AnalysisWidget):
    tasks = models.ManyToManyField(to=Task)



    







