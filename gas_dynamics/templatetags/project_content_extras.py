from .. import forms
from django import template
import json

register = template.Library()


def _get_form_info(form_type):
    def get_info(form_class):
        return form_class, form_class().instance.__class__.__name__.lower()

    if form_type == 'main':
        return get_info(forms.MainParametersForm)
    elif form_type == 'mean_radius':
        return get_info(forms.MeanRadiusParametersForm)
    elif form_type == 'profiling':
        return get_info(forms.ProfilingParametersForm)
    else:
        raise RuntimeError('Unknown form type')


def get_form_val(context, form_type, field_name, index=None):
    task = context['task']
    form_class, data_block_name = _get_form_info(form_type)

    if hasattr(task, data_block_name):
        field_value = getattr(getattr(task, data_block_name), field_name)

        if index is None:
            return {'value': field_value}

    else:
        return {'value': ''}


@register.inclusion_tag('gas_dynamics/project_content/inclusion_tags/form_value_setter.html', takes_context=True)
def get_main_val(context, field_name):
    return get_form_val(context, 'main', field_name)


@register.inclusion_tag('gas_dynamics/project_content/inclusion_tags/form_value_setter.html', takes_context=True)
def get_mean_rad_val(context, field_name):
    return get_form_val(context, 'mean_radius', field_name)


@register.inclusion_tag('gas_dynamics/project_content/inclusion_tags/form_value_setter.html', takes_context=True)
def get_prof_val(context, field_name):
    return get_form_val(context, 'profiling', field_name)


@register.filter
def get_stage_num_range(task):
    field_name = 'stage_number'
    form_class, data_block_name = _get_form_info('main')

    if hasattr(task, data_block_name):
        field_value = getattr(getattr(task, data_block_name), field_name)
        return range(field_value)
    else:
        return range(1)

