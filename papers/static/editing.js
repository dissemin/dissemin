
$(function(){

$('.paperDeleteButton').click( function (evt) {
    var domElem = $(this);
    $.ajax({url:'/ajax/'+$(this).attr('id')}).done(
            function() {
                    domElem.closest('li').remove();
            }).fail(
            function() {
              alert('Error');  
            });
    evt.preventDefault();
});

});

