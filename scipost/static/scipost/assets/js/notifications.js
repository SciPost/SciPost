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
        r.open("GET", url + '?max=5', true);
        r.send();
    }
}


function update_list(el) {
    fetch_api_data("/notifications/api/list/?mark_as_read=1", update_list_callback, {'element': el});
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
    el.append(messages).trigger('refresh-notifications');
}

$(function(){
    $('#notification_center').on('show.bs.modal', function(e) {
        update_list('#notifications-list');
    }).on('hide.bs.modal', function() {
        $('body > .tooltip').remove();
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
    });
});
