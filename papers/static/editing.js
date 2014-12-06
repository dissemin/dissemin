
$(function(){

$('.paperDeleteButton').click( function (evt) {
    var domElem = $(this);
    $.ajax({url:'/ajax/'+$(this).attr('id')}).done(
            function() {
                    var li = domElem.closest('li');
                    var ul = li.parent()
                    li.remove();
                    if(ul.children().length == 0)
                        ul.parent().remove();
            }).fail(
            function() {
              alert('Error');  
            });
    evt.preventDefault();
});

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
        url: ajaxUrl,
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

