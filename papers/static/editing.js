
function makeDeletable(elem) {
    elem.click( function (evt) {
    var domElem = $(this);
    console.log($(this));
    var undotext = $(this).data('undotext');
    var undoclass = $(this).data('undoclass');
    var undolink = $(this).data('undolink');
    var undoundo = $(this).data('undoundo');
    console.log(undotext);
    console.log($(this).attr('data-undotext'));
    $.ajax({url:'/ajax/'+$(this).attr('id')}).done(
            function() {
                    var li = domElem.closest('li');
                    var ul = li.parent()
                    var oldElem = li.replaceWith("<li class=\""+undoclass+"\">"+undotext+"<a href=\"#\" id=\""+undolink+"\">"+undoundo+"</a></li>");
                    var undoLinkElem = $("#"+undolink);
                    undoLinkElem.click( function(evt) {
                    $.ajax({url:'/ajax/'+undolink}).done(
                    function () {
                        var newOldElem = oldElem.clone();
                        undoLinkElem.parent().replaceWith(newOldElem);
                    });
                    });

                     if(ul.children().length == 0)
                        ul.parent().remove();
            }).fail(
            function(message) {
              alert('Error: '+message);  
            });
    evt.preventDefault();
});
}


$(function(){
    makeDeletable($('.researcherDeleteButton'));
    makeDeletable($('.paperDeleteButton'));
});

var pencilElements = new Array();

var pencilCode = '<a href="#"><span class="glyphicon glyphicon-pencil small-glyphicon" aria-hidden="true"></span></a>'; 
var pencilCodeNbsp = '<a href="#">&nbsp;<span class="glyphicon glyphicon-pencil small-glyphicon" aria-hidden="true"></span></a>'; 
    
function makeAuthorEditable(domElement, mergedCallback) {
    domElement.parent().append(pencilCodeNbsp);
    var pencilElem = domElement.parent().children().last();
    var tabId = pencilElements.length;
    pencilElements[tabId] = pencilElem;
    pencilElem.detach();

    domElement.editable({
        type:'name',
        name: 'name',
        value:{first: domElement.data('first'), last: domElement.data('last') },
        url: '/ajax/change-author',
        success: function(response, newValue) {
            resp = JSON.parse(response);
            console.logl(resp);
            if(resp.merged != '') {
                setTimeout(function() { mergedCallback(domElement, resp); }, 1000);
            }
            return {newValue: resp.value}; },
        toggle: 'manual',
        showbuttons: false,
    });

    pencilElem.click(function(e){
        // pencilElements[tabId].detach();
        e.stopPropagation();
        domElement.editable('toggle');
        e.preventDefault();
     });

    domElement.parent().hover(
            function () {
                domElement.parent().append(pencilElements[tabId]);
            },
            function () {
                pencilElements[tabId].detach();
            });

}

function makeTextEditable(domElement, ajaxUrl, field, merge_callback) {
    domElement.parent().append(pencilCode);
    var pencilElem = domElement.parent().children().last();
    var tabId = pencilElements.length;
    pencilElements[tabId] = pencilElem;

    domElement.editable({
        type: 'text',
        name: field,
        escape: false,
        url: ajaxUrl,
        success: function(response, newValue) {
            response=JSON.parse(response);
            if(response.merged != '') {
                setTimeout(function() { merge_callback(domElement, response); }, 1000);
            }
            return {newValue:response.value}; },
        mode: 'inline',
        toggle: 'manual',
        inputclass: 'editable-long-input',
        showbuttons: false,
    }).on('hidden', function (e,reason) {
        domElement.parent().append(pencilElements[tabId]);
    });

    pencilElem.click(function(e){
        pencilElements[tabId].detach();
        e.stopPropagation();
        domElement.editable('toggle');
        e.preventDefault();
     });
}

