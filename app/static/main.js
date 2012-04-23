jQuery.reduce = function(arr, valueInitial, fnReduce)
{
    jQuery.each( arr, function(i, value) {
        valueInitial = fnReduce.apply(value, [valueInitial, i, value]);
    });
    return valueInitial;
}

jQuery(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-SRFToken", getCookie('csrftoken'));
    }
});

$(document).ready(function() {

    var format_data = function(data) {
        var list = $.parseJSON(data);

        var table = $.map(list, function(obj, n) {
                var tr = $('<tr />');
                var td_title = $('<td class="search-track-title" />');
                var td_artist = $('<td class="search-track-artist" />');
                var td_album = $('<td class="search-track-album" />');
                var td_queue = $('<td class="search-track-queue" />');
                td_title.html(obj.title);
                td_artist.html(obj.artist);
                td_album.html(obj.album);
                tr.append(td_title);
                tr.append(td_artist);
                tr.append(td_album);
                tr.append(td_queue);
                return tr
        });

        tbody = $.reduce(table, $('<tbody />'), function(total, i, item) { return total.append(item) });
        thead_search_results = $('<tr><th>Search Results:</th><th>' + list.length + ' Results</th></tr>');
        thead_titles = $('<tr><th>Title</th><th>Artist</th><th>Album</th><th>Queue?</th></tr>');
        thead = $('<thead />').append(thead_search_results).append(thead_titles);

        return thead.add(tbody);
    }

    $('.recent-track').popover({placement:'bottom'});

    $('[name=search_term]').bindWithDelay("keyup",
            function () {
                $.ajax({
                    url: '/instant-search/',
                    type: 'POST',
                    data: {'search_term': this.value},
                    success: function(data) { $('[name=search_table]').html(format_data(data)) }
                });
            },
            400);

    /*$('.recent-track').bind('hover', function() {
        $track = $(document).find('.popover')
        $.ajax({
            url: 'http://api.wolframalpha.com/v2/query?appid=679H84-GQ872A7K5U&input=' + $track.find('.recent-track-album').text() + '-' + $track.find('.recent-track-album').text() + '&format=image',
            success: function(data) {
                xmlDoc = $.parseXML(data);
                $xml = $( xmlDoc );
                $image = $xml.find('pod[title="Album art"]').find('subpod').find('img');
                $track.find('popover-content').add($image);
            }
        });
    });*/
});
