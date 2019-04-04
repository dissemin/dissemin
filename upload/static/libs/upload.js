$(function(){

    var resultDiv = $('#uploadedResult');
    var uploadForm = $('#uploadForm');
    var filename = "";

    function addFileWidget(name, size) {
        var tpl = $('<div class="uploadFileItem uploadWorking"><div class="progress progress-striped active"><div class="progress-bar" style="width:100%"></div></div>    <div class="fileDetails"></div><div style="clear:left"></div></div>');

        // Append the file name and file size
        filename = name;
        var formattedSize = 'Uploading...';
        if(size > 0) {
            formattedSize = formatFileSize(size);
        }
        tpl.find('span').append('<i>' + formattedSize + '</i>');

        // Add the HTML to the UL element
        resultDiv.empty();
        return tpl.appendTo(resultDiv);
    }

    function removeBar() {
        var progressDiv = $('.progress');
        progressDiv.fadeOut(function(){
            progressDiv.remove();
        });
    }

    function updateProgress(tpl, progress) {
        //var progressBar = $('.progress-bar');
        //progressBar.css('width', progress+'%').attr('aria-valuenow', progress);
    }

    function uploadComplete(tpl, data) {

        $('#globalError').removeClass('error').empty();
        removeBar();
        var uploadInputs = $('#uploadInputs');
        uploadInputs.fadeOut(function(){
            var fd = tpl.find('.fileDetails');
            fd.empty().append($('<p>'+filename+'</p><i>'+data['num_pages']+' pages<br/>'
                        +formatFileSize(data['size'])+'</i><p><a id="changeFile" href="#">Change</a></p>'));
            tpl.prepend(
                '<img src="'+data['thumbnail']+'" class="uploadThumbnail" alt="Thumbnail" />');

            $('#uploadFileId').val(data['file_id']).change();

            tpl.removeClass('uploadWorking');

            $('#changeFile').click(function(){
                var uploadFileItem = tpl;
                uploadFileItem.fadeOut(function(){
                  $('#uploadFileId').val('').change();
                   uploadFileItem.remove();
                   uploadInputs.show();
                });
        });
        //function(){
        //    uploadInputs.hide();
        //});

        });

    }

    function displayErrorMessage(tpl, msg) {
        tpl.find('.fileDetails').append($('<p>'+filename+'</p><i>'+msg+'</i>'));
        tpl.addClass('error');
        removeBar();
    }


    // Initialize the jQuery File Upload plugin
    uploadForm.fileupload({

        // This element will accept file drag/drop uploading
        dropZone: $('#dropZone'),

        // This function is called when a file is added to the queue;
        // either via the browse button, or via drag/drop:
        add: function (e, data) {

            data.context = addFileWidget(data.files[0].name, data.files[0].size);

           // Listen for clicks on the cancel icon
            data.context.find('span').click(function(){

                if(data.context.hasClass('working')){
                    jqXHR.abort();
                }

                data.context.fadeOut(function(){
                    data.context.remove();
                });

            });

            // Automatically upload the file once it is added to the queue
            var jqXHR = data.submit();
        },

        progress: function(e, data){
            // Calculate the completion percentage of the upload
            var progress = parseInt(data.loaded / data.total * 100, 10);

            updateProgress(data.context, progress);
        },

        done: function(e, data) {
            uploadComplete(data.context, data.jqXHR.responseJSON);
        },

        fail:function(e, data){
            var resp = data.jqXHR.responseJSON;
            if(typeof resp != 'undefined' && 'upl' in resp) {
                displayErrorMessage(data.context, resp['upl']);
            } else if(resp != undefined && 'message' in resp) {
                $('#globalError').addClass('error').text(resp['message']);
                removeBar();
            } else {
                $('#globalError').addClass('error').text(
                        "Dissemin encountered an error, please try again later.");
                removeBar();
            }
        }
    });

    // Prevent the default action when a file is dropped on the window
    $(document).on('drop dragover', function (e) {
        e.preventDefault();
    });

    // Helper function that formats the file sizes
    function formatFileSize(bytes) {
        if (typeof bytes !== 'number') {
            return '';
        }

        if (bytes >= 1000000000) {
            return (bytes / 1000000000).toFixed(2) + ' GB';
        }

        if (bytes >= 1000000) {
            return (bytes / 1000000).toFixed(2) + ' MB';
        }

        return (bytes / 1000).toFixed(2) + ' KB';
    }

    // Function triggered when an URL is submitted
    function uploadUrl() {
        var data = $('#urlForm').serialize();

        var tpl = addFileWidget($('#uploadUrl').val(),0);

        updateProgress(tpl, 10);
        $.post('/ajax-upload/download-url', data, null, 'json').fail(function(data) {
                if(!data.responseJSON)
                {
                    $('#globalError').text(data.responseText);
                }
                else
                {
                    var resp = data.responseJSON;
                    displayErrorMessage(tpl, resp['message']);
                }
            }).done(function(data) {
                if(data['status'] == 'error') {
                    $('#globalError').text(data['message']);
                }
                if(data['status'] == 'success') {
                    updateProgress(tpl, 100);
                    uploadComplete(tpl, data);
                }
        });
    }

    $('#submitUploadUrl').click(function(event) {
        event.preventDefault();
        uploadUrl();
    });

});
