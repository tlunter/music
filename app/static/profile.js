$(document).ready(function() {
    $('.recent-track').popover({placement:'bottom'});
});

$(document).on('click', '.delete-queue-item', function(event) {
    button_data = $(this);
    $.ajax({
        url: '/delete-queue-item/',
        type: 'POST',
        data: {'queue-item-pk': button_data.attr('name')},
        success: function(data) {
            var td = button_data.parent();
            var tr = td.parent();
            $(tr).popover('hide');
            tr.remove();
        }
    });
});

