

function Repeater(caller) {
    Repeater.stageCodeBlockClass = '.js-stage-repeating-block';
    Repeater.stageLabelClass = '.js-stage-parameter';
    Repeater.stageInputClass = '.js-stage-input'

    this.repeateAll = function() {
        var stageNumber = this.caller.value;
        if (isNaN(stageNumber)) {
            alert('Stage number must be integer')
            return
        }

        for (var i = 0; i != this.toRepeate.length; i++) {
            this._repeatElement(this.toRepeate[i], stageNumber);
        }
    }

    this._getElementGroup = function(repeatingElement, selector) {
        return $(repeatingElement).find(selector)
    }

    this._applyToElementGroup = function(repeatingElement, selector, extractor) {
        var elements = this._getElementGroup(repeatingElement, selector);
        return $.map(elements, extractor);
    }

    this._getElementGroupAttr = function(repeatingElement, selector, attrName) {
        var elements = this._getElementGroup(repeatingElement, selector);
        return $.map(elements, function(element) {return element[attrName]});
    }

    this._getStageLabels = function(repeatingElement) {
        return this._getElementGroup(repeatingElement, Repeater.stageLabelClass);
    }

    this._getStageCaptions = function(repeatingElement) {
        return this._applyToElementGroup(repeatingElement, 
                                         Repeater.stageLabelClass, 
                                         function(label) {return label.innerHTML});
    }

    this._getStageInputs = function(repeatingElement) {
        return this._getElementGroup(repeatingElement, Repeater.stageInputClass);
    }

    this._getStageInputNames = function(repeatingElement) {
        return this._applyToElementGroup(repeatingElement, 
                                         Repeater.stageInputClass, 
                                         function(input) {
                                             return input.name
                                         })
    }

    this._clearContainer = function(container) {
        $(container).find(Repeater.stageCodeBlockClass).remove()
    }

    this._renumerateElementProps = function(repeatingElement, stageNumber, selector, 
                                            attrName, splitter) {
        function detachNumber(strProp) {
            var words = strProp.split(splitter);
            var lastWord = words[words.length - 1];

            if (!isNaN(parseInt(lastWord))) {
                words = words.slice(0, words.length - 1);
            }

            return words.join(splitter)
        }

        var elements = this._getElementGroup(repeatingElement, selector);
        var props = $.map(elements, function(element) {return element[attrName]});

        for (var i = 0; i != props.length; i++) {
            var cutProp = detachNumber(props[i]);
            elements[i][attrName] = cutProp + splitter + stageNumber;
        }        
    }

    this._renameStageLabels = function(repeatingElement, stageNumber) {
        this._renumerateElementProps(repeatingElement=repeatingElement,
                                     stageNumber=stageNumber, 
                                     selector=Repeater.stageLabelClass, 
                                     attrName='innerHTML', 
                                     splitter=' ')
    }

    this._renameStageInputs = function(repeatingElement, stageNumber) {
        this._renumerateElementProps(repeatingElement=repeatingElement,
                                     stageNumber=stageNumber, 
                                     selector=Repeater.stageInputClass, 
                                     attrName='name', 
                                     splitter='__')
    }

    this._repeatElement = function(repeatingElement, stageNumber) {
        var container = $(repeatingElement).parent();
        this._clearContainer(container);

        for (var i = 0; i != stageNumber; i++) {
            $(container).append(repeatingElement.outerHTML);
            
            var repeatingElements = container.find(Repeater.stageCodeBlockClass);
            var lastElement = repeatingElements[repeatingElements.length - 1];
            
            this._renameStageLabels(lastElement, i);
            this._renameStageInputs(lastElement, i);
        }
    }
    
    this.caller = caller;
    this.toRepeate = $(Repeater.stageCodeBlockClass);
}


function DataSaver(caller, splitter='__') {
    this.splitter = splitter;
    this._saveBtnClass = '.js-update-task';
    this._taskHolderClass = '.js-task-holder';

    this.saveData = function() {
        var result = this._getTaskData(this.taskHolder);

        var url = result['url'];
        var data = {
            data: JSON.stringify(result['data'])
        };

        var success = (data) => {
            console.log(data);

            /*
            var message = '';
            for (key in data){
                var innerData = data[key];
                var content = innerData.messages;

                message += key + ': ' + content + '\n';
            }
            alert(message);
            */
        };

        this._processDataBlock(url, data, success)
    }

    this._getTaskData = function(taskHolder) {
        var forms = $(taskHolder).find('form');
        var formTypes = ['main', 'mean_radius', 'profiling'];

        var formContents = {};
        for (var i = 0; i != formTypes.length; i++) {
            formContents[formTypes[i]] = this._customSerialize(forms[i]);
        }

        var result = {};
        result['data'] = formContents;
        result['url'] = $(this.updateBtn).attr('data-update-task');

        return result
    }

    this._processDataBlock = function(url, data, success) {
         $.ajax({
            type: 'POST',
            url: url,
            data: data,
            success: success,
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
            }
        });
    }

    this._customSerialize = function(form, formType=undefined) {
        var arr = $(form).serializeArray();

        var keyValuePairs = {};
        for (var i = 0; i != arr.length; i++) {
            var obj = arr[i];
            keyValuePairs[obj.name] = obj.value;
        }
        
        keyValuePairs = this._classifyData(keyValuePairs);
        
        if (Boolean(formType)) {
            keyValuePairs['form_type'] = formType;
        }

        return JSON.stringify(keyValuePairs)
    }

    this._classifyData = function(keyValuePairs) {
        var isCompositeKey = (key) => {
            var cutKey = this._detachNumber(key, this.splitter);
            return !(key == cutKey)
        }

        var result = {};

        for (var key in keyValuePairs) {
            if (!isCompositeKey(key)) {
                result[key] = keyValuePairs[key];
            } else {
                var cutKey = this._detachNumber(key, this.splitter);

                if (result[cutKey] == undefined) {
                    result[cutKey] = [keyValuePairs[key]];
                } else {
                    result[cutKey].push(keyValuePairs[key]);
                }
            }
        }

        return result
    }

    this._detachNumber = function(strProp, splitter) {
        var words = strProp.split(splitter);
        var lastWord = words[words.length - 1];

        if (!isNaN(parseInt(lastWord))) {
            words = words.slice(0, words.length - 1);
        }

        return words.join(splitter)
    }

    this.taskHolder = $(caller).closest(this._taskHolderClass);
    this.updateBtn = caller;
}


function DataDeleter(caller) {
    DataDeleter.taskHolderClass = '.js-task-holder';
    DataDeleter.taskContainerClass = '.js-task-container';

    this.deleteTask = function() {
        var success = (data) => {
            this.taskContainer.outerHTML = data;
        }

        args = {
            url: this.deleteURL,
            success: success
        }

        this._deleteRequest(args);
    }

    this._deleteRequest = function(args) {
         url = args.url;

         if (args.data == undefined) {
            data = {};
         } else {
            data = args.data;
         }

         if (args.success == undefined) {
            success = function(data) {};
         } else {
            success = args.success;
         }

         $.ajax({
            type: 'POST',
            url: url,
            data: data,
            success: success,
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
            }
        });
    }

    this.caller = caller;
    this.taskHolder = $(caller).closest(DataDeleter.taskHolderClass);
    this.taskContainer = $(caller).parents().find(DataDeleter.taskContainerClass)[0];
    this.deleteURL = $(this.taskHolder).attr('data-delete-task');
}


function TaskAdder(caller) {
    TaskAdder.bodyPanelClass = 'div.js-global-task-holder'
    
    this.addTask = function() {
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

        var loadHtml = (data) => {
            html_content = data.html_content;

            var modal = $(caller).closest('#add-task-modal');
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
    
    this.bodyPanel = $(TaskAdder.bodyPanelClass)
    this.form = this._getForm(caller);
    this.url = this._getUrl(caller);
}


$(document).ready(function() {
    $('body').on('click', '.js-delete-task', function(event) {
        var deleter = new DataDeleter(this);
        deleter.deleteTask();
    })

    $('body').on('change', '.js-stage-number', function(event) {
        var repeater = new Repeater(this);
        repeater.repeateAll();
    });

    $('body').on('submit', 'form.add-task', function(event) {
        event.preventDefault();
        var taskAdder = new TaskAdder(this);
        taskAdder.addTask();
    })

    $('body').on('click', '.js-update-task', function(event) {
        var saver = new DataSaver(this);
        saver.saveData()
    })
})

