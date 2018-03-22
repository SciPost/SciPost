function fetch_api_data(callback, url, args) {
    if (!url) {
        var url = notify_api_url_count;
    }

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


function update_counter_callback(data, args) {
    var counter = data['unread_count'];
    var el = $(args['element']);

    if (typeof counter == 'undefined') {
        counter = 0;
    }

    el.html(counter);
    if (counter > 0) {
        el.parents('.notifications_container').addClass('positive_count')
    } else {
        el.parents('.notifications_container').removeClass('positive_count')
    }
}

function update_list_callback(data, args) {
    var items = data['list'];
    var el = $(args['element']);

    var messages = items.map(function (item) {
        // Notification content
        var message = '',
            link = '';

        if(typeof item.actor !== 'undefined'){
            message += '<strong>' + item.actor + '</strong>';
        }
        if(typeof item.verb !== 'undefined'){
            message += " " + item.verb;
        }
        if(typeof item.target !== 'undefined'){
            if(typeof item.forward_link !== 'undefined') {
                link = item.forward_link;
                message += " <a href='" + item.forward_link + "'>" + item.target + "</a>";
            } else {
                message += " " + item.target;
            }
        }
        if(typeof item.timesince !== 'undefined'){
            message += "<div class='meta'>";
            if(typeof item.forward_link !== 'undefined') {
                message += " <a href='" + item.forward_link + "'>Direct link</a> &middot; ";
            }
            message += "<span class='text-muted'>" + item.timesince + " ago</span></div>";
        }

        // Notification actions
        if(item.unread) {
            var mark_toggle = '<a href="javascript:;" class="mark-toggle" data-slug="' + item.slug + '"><i class="fa fa-circle" data-toggle="tooltip" data-placement="auto" title="Mark as read" aria-hidden="true"></i></a>';
        } else {
            var mark_toggle = '<a href="javascript:;" class="mark-toggle" data-slug="' + item.slug + '"><i class="fa fa-circle-o" data-toggle="tooltip" data-placement="auto" title="Mark as unread" aria-hidden="true"></i></a>';
        }

        if(typeof item.forward_link !== 'undefined') {
            mark_toggle += "<br><a href='" + item.forward_link + "' data-toggle='tooltip' data-placement='auto' title='Go to item'><i class='fa fa-share' aria-hidden='true'></i></a>";
        }

        // Complete list html
        if(link !== '') {
            return '<li href="' + link + '" class="item ' + (item.unread ? ' active' : '') + '"><div>' + message + '</div><div class="actions">' + mark_toggle + '</div></li>';
        } else {
            return '<li class="item ' + (item.unread ? ' active' : '') + '"><div>' + message + '</div><div class="actions">' + mark_toggle + '</div></li>';
        }

    }).join('');

    if (messages == '') {
        messages = '<li class="item px-5"><em>You have no new notifications</em></li>'
    }

    // Fill DOM
    el.find('.live_notify_list').html(messages).parents('body').trigger('refresh_notify_list');
}

function update_mark_callback(data, args) {
    var el = $(args['element']);
    $(el).parents('.item').toggleClass('active');
    trigger_badge();
}


function update_counter(el) {
    fetch_api_data(update_counter_callback, "/notifications/api/unread_count/", {'element': el});
}

function mark_toggle(el) {
    var url = "/notifications/mark-toggle/" + $(el).data('slug') + "?json=1";
    fetch_api_data(update_mark_callback, url, {'element': el});
}

function update_list(el) {
    fetch_api_data(update_list_callback, "/notifications/api/list/?mark_as_read=1", {'element': el});
}

function trigger_badge() {
    $('.live_notify_badge').trigger('notification_count_updated');
}
// Update Badge count every minute
var badge_timer = setInterval(trigger_badge, 60000);

function initiate_popover() {
    var template = $('.notifications_container .popover-template').html();
    $('.notifications_container a[data-toggle="popover"]').popover({
        trigger: 'focus',
        animation: false,
        offset: '0, 10px',
        template: template,
        placement: 'bottom',
        boundary: 'viewport',
        title: 'empty-on-purpose'
    })
    .on('inserted.bs.popover', function() {
        $('body').trigger('notification_open_list');
    })
    .on('hide.bs.popover', function() {
        // Bug: force removal of tooltip
        $('body > .tooltip').remove();
    });
}

$(function(){
    $('body').on('notification_open_list', function() {
        update_list(this);
    })

    $('.live_notify_badge').on('notification_count_updated', function() {
        update_counter(this);
    }).trigger('notification_count_updated');


    $('body').on('refresh_notify_list', function() {
        // Bloody js
        var list = $('.live_notify_list');
        list.find('li.item').on('click', function(e) {
            e.stopPropagation();
        })
        .filter('[href]').on('click', function(e) {
            window.location.href = $(this).attr('href')
        });
        list.find('[data-toggle="tooltip"]').tooltip({
            animation: false,
            delay: {"show": 500, "hide": 100},
            fallbackPlacement: 'clockwise',
            placement: 'bottom'
        });
        list.find('.actions a.mark-toggle').on('click', function(e) {
            e.stopPropagation();
            mark_toggle(this);
        });
    });

    initiate_popover();
});
