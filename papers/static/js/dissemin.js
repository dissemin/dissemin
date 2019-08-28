/* *** */
/* Paper View related JS */
/* *** */

/* Enables JS functionality to claim or mark for later upload (todolist) and undo that after refreshing result */

function add_claim_mark_handlers () {
    // Claiming
    $(".unclaim-button").click(claim_unclaim);
    $(".claim-button").click(claim_unclaim);
    // Todolist
    $(".todolist-button").click(todolist);
}

/* Add or remove paper from todolist */
function todolist (evt) {
    var obj = $(evt.target);
    var pk = obj.attr('data-pk');
    var action = obj.attr('data-action');

    if (action == 'mark') {
        obj.text(gettext('Adding to todolist'));
        var ajax_url = '/ajax/todolist-add';
    }
    else if (action == 'unmark') {
        obj.text(gettext('Removing from todolist'));
        var ajax_url = '/ajax/todolist-remove';
    }
    else {
        // action currently ongoing
        return
    }
    
    $.ajax({
        method: 'post',
        url: ajax_url,
        data: {
            "paper_pk": pk,
            "csrfmiddlewaretoken": csrf_token
        },
        dataType: 'json',
        cache: false,
        success: function (data) {
            obj.text(data['success_msg']);
            obj.attr('data-action', data['data-action']);
        },
        error: function (data) {
            obj.text(data['error_msg']);
        }
    });
}
