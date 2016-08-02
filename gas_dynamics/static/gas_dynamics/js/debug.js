function calculate_task(task_holder, calc_type) {
    url = $(task_holder).attr('data-solve-task');


    $.ajax({
        type: 'POST',
        url: url,
        data: {
            calc_type: calc_type
        },
        success: function(response) {
            console.log(response);
        },

        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });
}

function wrapper (calc_type='profiling') {
    var task_holder = $('.js-task-holder')[1];
    calculate_task(task_holder, calc_type);
}