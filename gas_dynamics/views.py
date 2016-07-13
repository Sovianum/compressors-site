from django.shortcuts import render, redirect
from django.template.loader import render_to_string
import django.template
from . import forms
from . import models
import django.http
import django.views.generic
import django.utils.timezone
import django.db.utils
import django.db
from django.core.urlresolvers import reverse
from .data_extraction import DebugCompressorHandler
from django.views.decorators.cache import never_cache
import time
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import django.core.exceptions
import json
import demjson
from enum import Enum
import re


class FORM_CLASS(Enum):
    main = forms.MainParametersForm
    mean_radius = forms.MeanRadiusParametersForm
    profiling = forms.ProfilingParametersForm


class MODEL_CLASS(Enum):
    main = models.MainDataPart
    mean_radius = models.MeanRadiusDataPart
    profiling = models.ProfilingDataPart


class AuthMixin:
    def get_response(self, request):
        if request.user.is_authenticated():
            return self.render_registered_template(request)
        else:
            return self.render_unregister_template(request)

    def render_registered_template(self, request):
        pass

    def render_unregister_template(self, request):
        pass


class GetMainPage(django.views.generic.TemplateView):
    template_name = 'gas_dynamics/main_page.html'


class Login(django.views.generic.View):

    def get(self, request):
        if 'auth_fail' in request.session:
            auth_fail = True
        else:
            auth_fail = False
        context = {
            'auth_fail': auth_fail,
        }

        return render(request, 'gas_dynamics/login.html', context)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('gas_dynamics:main_page')
            else:
                pass
        else:
            request.session['auth_fail'] = True
            return redirect('gas_dynamics:login')


class Logout(django.views.generic.View):
    def get(self, request):
        logout(request)
        return redirect('gas_dynamics:main_page')


class ProjectList(django.views.generic.ListView):
    model = models.Project
    context_object_name = 'projects'
    template_name = 'gas_dynamics/project_list/projects_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ProjectList, self).dispatch(request, *args, **kwargs)

    def get_query_set(self):
        return models.Project.objects.all()


class DeleteProject(django.views.generic.View):
    model = models.Project

    def post(self, request, username, project_name):
        if request.is_ajax():
            project_name = request.POST['project_name']
            projects = self.model.objects.filter(name=project_name)

            for project in projects:
                project.delete()

            context = {
                'projects': models.Project.objects.all(),
            }
            return render(request, 'gas_dynamics/project_list/projects_body.html', context)
        else:
            raise django.http.BadHeaderError('This the AJAX only url')


class AddProject(django.views.generic.View):
    model = models.Project

    def post(self, request, username):
        if request.is_ajax():
            project_form = forms.AddProjectForm(request.POST)

            error_message = ''
            if project_form.is_valid():
                try:
                    project = self.model.objects.create(user=request.user, name=project_form.cleaned_data['name'])
                    project.save()
                except django.db.IntegrityError as e:
                    error_message += 'This project already exists.\n'
            else:
                error_message += 'Invalid project name.\n'

            context = {
                'projects': models.Project.objects.all(),
            }

            request_context = django.template.RequestContext(request)
            html_content = render_to_string('gas_dynamics/project_list/projects_body.html', context, request_context)

            return django.http.JsonResponse({
                'html_content': html_content,
                'errors': error_message
            })
        else:
            raise django.http.BadHeaderError('This the AJAX only url')


class ProjectTasks(django.views.generic.View):
    template_name = 'gas_dynamics/project_content/task_container_template.html'

    def get(self, request, username, project_name):
        project = models.Project.objects.get(name=project_name)
        tasks = models.SingleCompressorTask.objects.filter(project=project)

        context = {
            'project': project,
            'tasks': tasks
        }

        return render(request, self.template_name, context=context)


class AddTask(django.views.generic.View):
    model = models.Project

    def post(self, request, username, project_name):
        if request.is_ajax():
            task_form = forms.AddTaskForm(request.POST)

            error_message = ''
            if task_form.is_valid():
                user = request.user
                project = models.Project.objects.get(user=user, name=project_name)

                try:
                    task = models.SingleCompressorTask.objects.create(project=project, name=task_form.cleaned_data['name'])
                    task.save()
                except django.db.IntegrityError as e:
                    error_message += str(e)
                    print(project, task_form.cleaned_data['name'], '\n\n\n')


            else:
                error_message += 'Invalid task name.\n'

            if not error_message:
                context = {
                    'tasks': models.SingleCompressorTask.objects.filter(project=project),
                    'project': project
                }
            else:
                context = {}

            request_context = django.template.RequestContext(request)
            html_content = render_to_string('gas_dynamics/project_content/task_container.html', context, request_context)

            return django.http.JsonResponse({
                'html_content': html_content,
                'errors': error_message
            })
        else:
            raise django.http.BadHeaderError('This the AJAX only url')


class UpdateTask(django.views.generic.View):
    def post(self, request, username, project_name, task_name):
        if request.is_ajax():
            user = models.User.objects.get(username=username)
            project = models.Project.objects.get(user=user, name=project_name)
            task = models.SingleCompressorTask.objects.get(project=project, name=task_name)
            task_dict = json.loads(request.POST['data'])

            process_results = dict()
            for form_type in task_dict:
                data = {
                    'user': user,
                    'project': project,
                    'task': task,
                    'content': json.loads(task_dict[form_type])
                }

                process_results[form_type] = self._process_wrapper(request, data, form_type)

            return django.http.JsonResponse(process_results)
        else:
            raise django.http.BadHeaderError('This the AJAX only url')

    def _process_wrapper(self, request, data, form_type):
        form_class = FORM_CLASS[form_type].value
        model_class = MODEL_CLASS[form_type].value
        return self._process_form_data(request, data, form_class, model_class)

    def _process_form_data(self, request, data, form_class, model_class):
        form = form_class(data['content'])
        result = dict()

        for key in data['content']:
            print('%s: %s (%s)' % (key, data['content'][key], type(data['content'][key])))

        if form.is_valid():
            model, is_created = model_class.objects.get_or_create(task=data['task'], defaults=form.cleaned_data)
            print(hasattr(model, 'flow_section_type'))
            print('\n\n\n')

            for key in form.cleaned_data:
                setattr(model, key, form.cleaned_data[key])

            model.save()

            result['messages'] = 'Data block saved'
            result['errors'] = ''
        else:
            result['messages'] = 'Data block not saved'
            result['errors'] = form.errors

        return result


class DeleteTask(django.views.generic.View):
    def post(self, request, username, project_name, task_name):
        if request.is_ajax():
            user = models.User.objects.get(username=username)
            project = models.Project.objects.get(user=user, name=project_name)
            task = models.SingleCompressorTask.objects.get(project=project, name=task_name)
            task.delete()

            template = 'gas_dynamics/project_content/task_container.html'
            context = {
                'tasks': models.SingleCompressorTask.objects.filter(project=project),
                'project': project
            }
            return render(request, template, context)
        else:
            raise django.http.BadHeaderError('This the AJAX only url')


class GetValue(django.views.generic.View):

    def get(self, request, username, project_name, task_name):
        data = json.loads(request.GET['data'])

        return self.request_dispatcher(username, project_name, task_name, data)

    def request_dispatcher(self, username, project_name, task_name, data):
        if data['request_type'] == 'get_field_value':
            return self._get_field_value(username, project_name, task_name, data['request_content'])

    def _get_field_value(self, username, project_name, task_name, data):
        user = models.User.objects.get(username=username)
        project = models.Project.objects.get(user=user, name=project_name)
        task = models.SingleCompressorTask.objects.get(project=project, name=task_name)
        form_type = data['form_type']
        field_name = data['field_name']

        return self._get_model_value(task, form_type, field_name)

    def _get_model_value(self, task, form_type, field_name):
        model_class = MODEL_CLASS[form_type].value

        try:
            model = model_class.objects.get(task=task)
        except django.core.exceptions.ObjectDoesNotExist as e:
            return django.http.HttpResponse('')

        regex = re.compile('.*__[0-9]+$')
        if regex.match(field_name):
            field_name, index = field_name.split('__')
            index = int(index)

            value_list_str = getattr(model, field_name)

            if not value_list_str:
                return django.http.HttpResponse('')

            value_list = demjson.decode(getattr(model, field_name))

            try:
                result_value = value_list[index]
            except IndexError:
                result_value = ''

            return django.http.HttpResponse(result_value)
        else:
            return django.http.HttpResponse(getattr(model, field_name))



@never_cache
def get_plot(request):
    if request.is_ajax():
        data = {
            'stage_number': range(4),
            'lattice_type': ['rotor', 'stator'],
            'render_image_url': request.build_absolute_uri(reverse('gas_dynamics:render_plot'))
        }
        return render(request, 'gas_dynamics/plot_holder.html', data)
    else:
        raise django.http.BadHeaderError('This the AJAX only url')


def render_plot(request):
    if request.is_ajax():
        if request.method == 'POST':
            form = forms.GetPlotForm(request.POST)

            if form.is_valid():
                cleaned_data = form.cleaned_data

                compressor_handler = DebugCompressorHandler()

                plot_path = compressor_handler.get_profile_plot(cleaned_data['stage_num'],
                                                                cleaned_data['lattice_type'],
                                                                cleaned_data['h_rel'],
                                                                cleaned_data['plot_name'],
                                                                time.time())
                return django.http.JsonResponse({'plot_path': plot_path})

            else:
                django.http.UnreadablePostError()
        else:
            raise django.http.BadHeaderError('POST method is required')
    else:
        raise django.http.BadHeaderError('This the AJAX only url')


def plot_page(request):
    return render(request, 'gas_dynamics/plot_page.html', {
        'plot_uri': request.build_absolute_uri(reverse('gas_dynamics:get_plot'))
    })
