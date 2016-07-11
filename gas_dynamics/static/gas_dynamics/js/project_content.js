

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


function DataSaver(splitter='__') {
    this.splitter = splitter
    
    this.saveTaskData = function(taskHolder) {
        var forms = $(taskHolder).find('form');
        var formTypes = ['main', 'mean_radius', 'profiling'];
        var urls = $.map(forms, function(form) {$(form).attr('data-host')});

        var formContents = {};
        for (var i = 0; i != formTypes.length; i++) {
            formContents[formTypes[i]] = this._customSerialize(form);
        }

        var result = {};
        result['content'] = formContents;
    }

    this.saveDataBlockForm = function(form, formType) {
        var url = $(form).attr('data-host');
        var dataContent = this._customSerialize(form, formType)
        var data = {
            'data': dataContent,
        }
        var successFunction = (response) => {
            console.log(response);
        }

        this._processDataBlock(url, data, successFunction);

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


function TestRepeater() {
    this.incStage = function() {
        var stageInput = $('.js-stage-number')[0];
        var stageNumber = stageInput.value;
        stageNumber = parseInt(stageNumber);

        if (!Boolean(stageNumber)) {
            stageNumber = 1;
        }

        stageNumber += 1;
        stageInput.value = stageNumber; 

        $(stageInput).trigger('change');    
    }

    this.test_getStageLabels = function() {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];

        return rep._getStageLabels(temp);

    }

    this.test_getStageCaptions = function() {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];

        return rep._getStageCaptions(temp);   
    }

    this.test_clearContainer = function() {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];
        var container = $(temp).parent();

        rep._clearContainer(container);    
    }

    this.test_renameStageLabels = function(stageNumber=3) {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];

        return rep._renameStageLabels(temp, stageNumber);  

    }

    this.test_repeatElement = function(stageNumber=3) {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];

        rep._repeatElement(temp, stageNumber)

    }

    this.test_repeatAll = function(stageNumber=3) {
        var caller = $('.js-stage-number')[0];
        var rep = new Repeater(caller);

        var temp = $('.js-stage-repeating-block')[3];

        rep.repeateAll(stageNumber)
    }
}


function test_classifyData() {
    var saver = new DataSaver();

    var testOb = {
        'a': 'a', 
        'b__1': 'b_1',
        'b__2': 'b_2'
    }

    return saver._classifyData(testOb)
}

function test_customSerialize(form) {
    var saver = new DataSaver();

    return saver._customSerialize(form)
}

function test_saveDataBlock(form=undefined) {
    if (form == undefined) {
        form = $($('form')[0])
    }
    var saver = new DataSaver();

    saver.saveDataBlockForm(form, 'main');
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
})

