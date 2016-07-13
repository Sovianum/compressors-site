from django.conf.urls import url

from . import views

app_name = 'gas_dynamics'
urlpatterns = [
    url(r'^main/$', views.GetMainPage.as_view(), name='main_page'),
    url(r'^login/$', views.Login.as_view(), name='login'),
    url(r'^logout/$', views.Logout.as_view(), name='logout'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/$', views.ProjectList.as_view(), name='project_list'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/delete/(?P<project_name>[0-9A-Za-z_]+)/$', views.DeleteProject.as_view(),
        name='delete_project'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/add_project/$', views.AddProject.as_view(),
        name='add_project'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/(?P<project_name>[0-9A-Za-z_]+)/tasks/$', views.ProjectTasks.as_view(),
        name='project_tasks'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/(?P<project_name>[0-9A-Za-z_]+)/tasks/add/$',
        views.AddTask.as_view(), name='add_task'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/(?P<project_name>[0-9A-Za-z_]+)/tasks/delete/(?P<task_name>[0-9A-Za-z_]+)/$',
        views.DeleteTask.as_view(), name='delete_task'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/(?P<project_name>[0-9A-Za-z_]+)/tasks/update/(?P<task_name>[0-9A-Za-z_]+)/$',
        views.UpdateTask.as_view(), name='update_task'),
    url(r'^(?P<username>[0-9A-Za-z_]+)/projects/(?P<project_name>[0-9A-Za-z_]+)/tasks/(?P<task_name>[0-9A-Za-z_]+)/get_value/$',
        views.GetValue.as_view(), name='get_value'),



    url(r'^get_plot/render_plot$', views.render_plot, name='render_plot'),
    url(r'^get_plot/$', views.get_plot, name='get_plot'),
    url(r'^plot_page/$', views.plot_page, name='plot_page'),
    #url(r'^projects/$', views.ProjectIndexView.as_view(), name='project_list'),
    #url(r'^add_project/$', views.get_project_addition_form, name='add_project'),
    #url(r'^project_added/$', views.add_project, name='project_added'),
    #url(r'^single_compressor$', views.render_single_compressor_form, name='single_compressor_form'),
]