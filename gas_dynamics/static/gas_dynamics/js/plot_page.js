function Navigator() {
    Navigator.getClosestPlotHolder = function(caller) {
        var caller = $(caller);
        var plotHolder = caller.closest(Navigator.localPlotHolderClass);
        return plotHolder;
    }

    Navigator.globalPlotHolderClass = 'div.js-global-plot-holder-container';
    Navigator.localPlotHolderClass = 'div.js-plot-holder-container';
    Navigator.deleteBtnClass = '.js-delete-plot-btn'
    Navigator.appendBtnClass = '.js-append-plot-btn'
}


function Renumerator() { 
    
    this.renumerateDataLinks = function(ancestor) {
        this.renumerateAttributeList(ancestor, ['id', 'data-target'])
    }

    this.renumerateIDs = function(ancestor) {
        this.renumerateAttribute(ancestor, 'id')
    }

    this.renumerateDataTargets = function(ancestor) {
        this.renumerateAttribute(ancestor, 'data-target')
    }

    this.renumerateAttributeList = function(ancestor, attrNameList) {
        for (var i = 0; i != attrNameList.length; i++) {
            this.renumerateAttribute(ancestor, attrNameList[i]);
            this.index -= 1;
        }

        this.index += 1;
    }

    this.renumerateAttribute = function(ancestor, attrName) {
        var descendants = $(ancestor).find('*');
        var index = this.getIndex();
        
        for (var i = 0; i != descendants.length; i++) {
            if (descendants[i].hasAttribute(attrName)) {
                $(descendants[i]).attr(attrName, $(descendants[i]).attr(attrName) + '_' + index)
            }
        }
    }

    this.getIndex = function() {
        this.index += 1;
        return this.index;
    }


    this.index = 0;
}


function PlotModifier(applier){
    this.modifyImage = function() {
        var imageSetup = this._cleanImageSetup(this._getImageSetup());
        
        this.image.attr('width', imageSetup.width + ' px');
        this.image.attr('height', imageSetup.height + ' px');
    }

    this._getImageSetup = function() {
        var searchArea = this.plotModifierForm.children(); 

        var width = searchArea.find(PlotModifier.widthClass).val();
        var height = searchArea.find(PlotModifier.heightClass).val();

        return {
            'width': width,
            'height': height,
            'name': name
        }
    }

    this._cleanImageSetup = function(imageSetup) {
        imageSetup.width = parseInt(imageSetup.width);
        imageSetup.height = parseInt(imageSetup.height);

        return imageSetup
    }

    this.plotModifierForm = Navigator.getClosestPlotHolder(applier).children().find(PlotModifier.formClass);
    this.image = Navigator.getClosestPlotHolder(applier).children().find('img');

    PlotModifier.formClass = '.js-image-setup-form';
    PlotModifier.widthClass = '.js-plot-width';
    PlotModifier.heightClass = '.js-plot-height';
    PlotModifier.applyBtnClass = 'button.js-resize-plot-btn';
}


function PlotGetter(applier) {

    this.refreshImage = function(data) {
        var plotPath = data.plot_path;
        var image = Navigator.getClosestPlotHolder(this.getPlotForm).children().find('img');
        image.attr('src', plotPath);  
    }

    this.getNewPlotPath = function() {
        var postData = this._getPOSTData();
        var url = this._get_url();
        var curr_item = this;

        $.ajax({
            type: 'POST',
            url: this._get_url(),
            data: this._getPOSTData(),
            success: function(data){
                console.log(data);
                curr_item.refreshImage(data);    
            },
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
            }
        });
    }

    this._getPOSTData = function() {
        var POSTData = {
            'plot_name': this.getPlotForm.children().find(PlotGetter.nameClass).val(),
            'stage_num': this.getPlotForm.children().find(PlotGetter.stageNumClass).val(),
            'lattice_type': this.getPlotForm.children().find(PlotGetter.latticeType).val(),
            'h_rel': this.getPlotForm.children().find(PlotGetter.h_rel).val(),
        }

        return POSTData
    }

    this._get_url = function(){
        return this.getPlotForm.attr('data-host');
    }
    
    this.getPlotForm = Navigator.getClosestPlotHolder(applier).children().find(PlotGetter.getPlotFormClass);

    PlotGetter.getPlotFormClass = '.js-content-setup-form';
    PlotGetter.nameClass = '.js-plot-name';
    PlotGetter.getPlotBtnClass = '.js-get-plot-btn';
    PlotGetter.stageNumClass = '.js-stage-number';
    PlotGetter.latticeType = '.js-lattice-type';
    PlotGetter.h_rel = '.js-h_rel';
}


function addPlot() {
    var url = $(this).attr('data-host');
    if (!url) {
        url = $(Navigator.globalPlotHolderClass).attr('data-host');
    }

    $.get(url, function(data) {
        var closestPlotHolder = Navigator.getClosestPlotHolder(this);
        if (!closestPlotHolder.length) {
            $(Navigator.globalPlotHolderClass).append(data);
            var insertedPlotHolder = $(Navigator.localPlotHolderClass).last();
        } else {
            closestPlotHolder.after(data);
            var insertedPlotHolder = closestPlotHolder.next();
        }
        
        renumenator.renumerateDataLinks(insertedPlotHolder);

        insertedPlotHolder.children().hide();
        insertedPlotHolder.children().fadeIn('fast');
    });
}


function deletePlot() {
    var plotHolder = Navigator.getClosestPlotHolder(this);
    var plotHolders = $(Navigator.localPlotHolderClass);
    if (plotHolders.length > 1) {
        plotHolder.children().fadeOut('fast', function() {
            plotHolder.remove();
        });
    }
}

function makePreparations() {
    window.renumenator = new Renumerator();
    Navigator();
    PlotGetter(document);
    PlotModifier(document);
}

$(document).ready(function() {
    makePreparations();
    addPlot();
});

$(document).ready(function() {
    $(Navigator.globalPlotHolderClass).on('click', Navigator.appendBtnClass, addPlot);
});

$(document).ready(function() {
    $(Navigator.globalPlotHolderClass).on('click', Navigator.deleteBtnClass, deletePlot);
});

$(document).ready(function() {
    $(Navigator.globalPlotHolderClass).on('click', PlotModifier.applyBtnClass, function(){
        var plotModifier = new PlotModifier(this);
        plotModifier.modifyImage();
    });
});


$(document).ready(function() {
    $(Navigator.globalPlotHolderClass).on('click', PlotGetter.getPlotBtnClass, function() {
        var plotGetter = new PlotGetter(this); 
        plotGetter.getNewPlotPath();
    });
});

