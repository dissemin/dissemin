
function makeDeletable(elem) {
    console.log(elem.data('undotext'));
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

function makeTextEditable(domElement, ajaxUrl, pk, field) {
    var pencilCode = '<a href="#"><span class="glyphicon glyphicon-pencil small-glyphicon" aria-hidden="true"></span></a>'; 
    domElement.parent().append(pencilCode);
    var pencilElem = domElement.parent().children().last();
    var tabId = pencilElements.length;
    pencilElements[tabId] = pencilElem;

    domElement.editable({
        type: 'text',
        pk: pk,
        name: field,
        escape: false,
        url: ajaxUrl,
        success: function(response, newValue) {
            response=JSON.parse(response);
            console.log(response);
            console.log(response["value"]);
            console.log(response.value);
            console.log({newValue:response.value});
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

