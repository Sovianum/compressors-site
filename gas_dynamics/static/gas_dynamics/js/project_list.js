function ProjectDeleter(caller) {     

    this.deleteProject = function() {
        var self = this;
        
        $.ajax({
            type: 'POST',
            url: this.url,
            data: {'project_name': this.project_name},
            success: function(data) {
                self._successFunction(data);
            },
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
            }
        });
    }

    this._getProjectName = function(caller) {
        return $(caller).attr('project_name');
    }

    this._getUrl = function(caller) {
        return $(caller).attr('data-host');
    }

    this._getBodyPanel = function(caller) {
        return $(caller).parents().find('.js-panel-body');
    }

    this._successFunction = function(data){
        var modal = $(caller).closest('#delete-' + this.project_name + '-modal');
        modal.modal('toggle');
        $('.modal-backdrop').remove();
        this.bodyPanel.html(data);
    }

    this.project_name = this._getProjectName(caller);
    this.url = this._getUrl(caller);
    this.bodyPanel = this._getBodyPanel(caller)

}


function ProjectAdder(caller) {
    this.addProject = function() {
        var self = this;
        var form_data = $(this.form).serialize();
                
        $.ajax({
            type: 'POST',
            url: self.url,
            data: form_data,
            success: function(data) {
                self._successFunction(data, self);
            },
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
            }
        });

    }

    this._getForm = function(caller) {
        return $(caller).closest('form');
    }

    this._getUrl = function(caller) {
        return $(caller).closest('form').attr('action');
    }

    this._successFunction = function(data, self){

        function loadHtml(data) {
            html_content = data.html_content;

            var modal = $(caller).closest('#add-project-modal');
            modal.modal('toggle');
            $('.modal-backdrop').remove();
            self.bodyPanel.html(html_content);
        }

        function showErrors(data) {
            errors = data.errors;
            if (Boolean(errors)) {
                alert(errors);   
            }
        }

        loadHtml(data);
        showErrors(data);
    }

    this._getBodyPanel = function(caller) {
        return $('.js-panel-body');
    }


    this.form = this._getForm(caller);
    this.url = this._getUrl(caller);
    this.bodyPanel = this._getBodyPanel(caller);
}


$(document).ready(function() {
    $('div.js-project-list-panel').on('click', 'button.js-delete-project-btn', function() {
        var projectDeleter = new ProjectDeleter(this);
        projectDeleter.deleteProject();
    });

    $('div.js-project-list-panel').on('submit', 'form', function(event){
       event.preventDefault();
       var projectAdder = new ProjectAdder(this);
       projectAdder.addProject();
    });
});
