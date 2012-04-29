jQuery.reduce = function(arr, valueInitial, fnReduce)
{
    jQuery.each( arr, function(i, value) {
        valueInitial = fnReduce.apply(value, [valueInitial, i, value]);
    });
    return valueInitial;
}

$(document).ready(function() {
    var format_data = function(data) {
        var list = $.parseJSON(data);
        
        var table = $.map(list, function(obj, n) {
            var tr = $('<tr />');
            var td_title = $('<td />');
            var td_artist = $('<td />');
            var td_album = $('<td />');
            var td_queue = $('<td />');
            var button_queue = $('<button />');
            var icon = $('<i />');
            
            icon.addClass('icon-plus-sign').addClass('icon-white');
            
            button_queue.addClass('queue-track-link').addClass('btn').addClass('btn-success');
            button_queue.attr('name',obj.pk);
            button_queue.append(icon);
            
            td_title.html(obj.fields.title).addClass('search-track-title');
            td_artist.html(obj.fields.artist).addClass('search-track-artist');
            td_album.html(obj.fields.album).addClass('search-track-album');
            td_queue.append(button_queue).addClass('search-track-queue');
            
            tr.append(td_title);
            tr.append(td_artist);
            tr.append(td_album);
            tr.append(td_queue);
            
            return tr
        });

        tbody = $.reduce(table, $('<tbody />'), function(total, i, item) { return total.append(item) });
        thead_search_results = $('<tr><th>Search Results:</th><th>' + list.length + ' Results</th></tr>');
        thead_titles = $('<tr><th>Title</th><th>Artist</th><th>Album</th><th>Queue</th></tr>');
        thead = $('<thead />').append(thead_search_results).append(thead_titles);
        
        return thead.add(tbody);
    }
    
    $('.recent-track').popover({placement:'bottom'});
    
    $('[name=search_term]').bindWithDelay("keyup",  function () {
        $.ajax({
            url: '/instant-search/',
            type: 'POST',
            data: {'search_term': this.value},
            success: function(data) { $('[name=search_table]').html(format_data(data)) }
        });
    },
    400);
    
    $('#confirmModal').modal({
        keyboard: true,
        show: false
    });
    
    $('#confirmModal').modal('hide');
    
    $('#successModal').modal({
        keyboard: true,
        show: false
    });
    
    $('#successModal').modal('hide');
});

$(document).on('click','.queue-track-link', function(event) {
    button_data = $(this);
    $.ajax({
        url: '/queue-track/',
        type: 'POST',
        data: {'track-pk': button_data.attr('name')},
        success: function(data) { 
            if(data == 'confirm') {
                $('.queue-track-link-confirm').attr('name', button_data.attr('name'));
                $('#confirmModal').modal('show');
            }
            else
            {
                $('#successModal').modal('show');
                button_data.attr('disabled','disabled');
            }
        }
    });
});

$(document).on('click', '.queue-track-link-confirm', function(event) {
    button_data = $(this);
    $('#confirmModal').modal('hide');
    $.ajax({
        url: '/queue-track/',
        type: 'POST',
        data: {'track-pk': button_data.attr('name'), 'confirm': true},
        success: function(data) {
            $('#successModal').modal('show');
            $('.queue-track-link[name=' + button_data.attr('name') + ']').attr('disabled','disabled');
        }
    });
});

$(document).on('shown', '#successModal', function() {
    window.setTimeout(function() {
        $('#successModal').modal('hide');
    }, 1000);
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
