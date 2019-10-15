/* This is the central Dissemin JavaScript library */
/* Every function should be inside this file */

/* When changing language in dropdown, submit the form */
$(function() {
    $("#select-language").change(function() {
        $("#select-language").submit();
    });
});
