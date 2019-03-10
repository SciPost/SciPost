function fetch_api_data(url, callback, args) {
    if (callback) {
        //only fetch data if a function is setup
        var r = new XMLHttpRequest();
        r.addEventListener('readystatechange', function(event){
            if (this.readyState === 4){
                if (this.status === 200){
                    consecutive_misfires = 0;
                    var data = JSON.parse(r.responseText);
                    return callback(data, args);
                } else {
                    consecutive_misfires++;
                }
            }
        })
        r.open("GET", url, true);
        r.send();
    }
}


function update_count() {
    var el = '#live_notify_badge';
    fetch_api_data("/notifications/api/unread_count/", update_count_callback, {'element': el});
}

function update_count_callback(data, args) {
    var el = $(args['element']);
    var count = data['unread_count'];
    if( count > 0 ) {
        el.html(count).parent().addClass('positive_count');
    } else {
        el.html(count).parent().removeClass('positive_count');
    }
}


function update_list(el) {
    var el = $(el);
    var offset = typeof el.data('count') == 'undefined' ? 0 : el.data('count');
    $('#load-notifications').addClass('loading');
    fetch_api_data("/notifications/api/list/?mark_as_read=1&offset=" + offset, update_list_callback, {'element': el});
}

function update_list_callback(data, args) {
    var items = data['list'];
    var el = $(args['element']);
    var template = el.find('.template').html();
    var re = {
        actor: new RegExp("{actor}","g"),
        verb: new RegExp("{verb}","g"),
        forward_link: new RegExp("{forward_link}","g"),
        target: new RegExp("{target}","g"),
        timesince: new RegExp("{timesince}","g"),
        unread: new RegExp("{unread}","g"),
        slug: new RegExp("{slug}","g"),
    };
    var messages = items.map(function (item) {
        // Notification content
        var message = '',
            link = '';

        t = template.replace(re.actor, item.actor);
        t = t.replace(re.verb, item.verb);
        t = t.replace(re.forward_link, item.forward_link);
        t = t.replace(re.target, item.target);
        t = t.replace(re.timesince, item.timesince);
        t = t.replace(re.slug, item.slug);
        if(item.unread) {
            t = t.replace(re.unread, 'unread');
        } else {
            t = t.replace(re.unread, 'read');
        }
        return t;
    });

    if(messages == '') {
        messages = '<li class="item"><em>You have no new notifications</em></li>'
    }

    // Fill DOM
    var count = typeof el.data('count') == 'undefined' ? 0 : el.data('count');
    el.append(messages).data('count', count + items.length).trigger('refresh-notifications');
    $('#load-notifications').removeClass('loading');
}

$(function(){
    update_count();
    setInterval(update_count, 600000);

    $('#notification_center').on('show.bs.modal', function(e) {
        if( typeof $('#notification_center').data('reload') == 'undefined' ) {
            update_list('#notifications-list');
            $('#notification_center').data('reload', 1);
        }
    }).on('hide.bs.modal', function() {
        $('body > .tooltip').remove();
    });

    $('#load-notifications a').on('click', function(e) {
        e.preventDefault();
        update_list('#notifications-list');
    });

    $('body').on('refresh-notifications', function(e) {
        var list = $(e.target.children).filter('[data-refresh=1]');

        list.find('[data-toggle="tooltip"]').tooltip({
            animation: false,
            delay: {"show": 500, "hide": 100},
            fallbackPlacement: 'clockwise',
            placement: 'bottom'
        });

        list.removeAttr('data-refresh');
        update_count();
    });
});
