var notify_badge_class = "live_notify_badge";
var notify_menu_class = "live_notify_list";
var notify_api_url_count = "/notifications/api/unread_count/";
var notify_api_url_list = "/notifications/api/list/";
var notify_api_url_toggle_read = "/notifications/mark-toggle/";
var notify_api_url_mark_all_read = "/notifications/mark-all-as-read/";
var notify_fetch_count = "5";
var notify_refresh_period = 15000;
var consecutive_misfires = 0;
var registered_functions = [fill_notification_badge];


function initiate_popover(reinitiate) {
    if(typeof reinitiate == 'undefined') {
        reinitiate = false;
    }

    var notification_template = '<div class="popover notifications" role="tooltip"><div class="arrow"></div><h3 class="popover-header h2"></h3><div class="popover-body"></div></div>';

    function get_notifications_title() {
        return 'Latest notifications <div class="badge badge-warning badge-pill live_notify_badge"></div><div class="mt-1"><small><a href="/notifications">See all my notifications</a> &middot; <a href="javascript:;" class="mark_all_read">Mark all as read</a></small></div>';
    }

    function get_notifications() {
        var _str = '<ul id="notification-list" class="update_notifications list-group"><div class="w-100 text-center py-4"><i class="fa fa-circle-o-notch fa-2x fa-spin fa-fw"></i><span class="sr-only">Loading...</span></div></ul>';
        get_notification_list();
        return _str;
    }

    $('.popover [data-toggle="tooltip"]').tooltip('dispose')
    $('#notifications_badge').popover('dispose').popover({
        animation: false,
        trigger: 'click',
        title: get_notifications_title,
        template: notification_template,
        content: get_notifications,
        container: 'body',
        offset: '0, 9px',
        placement: "bottom",
        html: true
    }).on('inserted.bs.popover', function() {
        // Bloody js
        setTimeout(function() {
            $('.popover [data-toggle="tooltip"]').tooltip({
                animation: false,
                delay: {"show": 500, "hide": 100},
                fallbackPlacement: 'clockwise',
                placement: 'bottom'
            });
            $('.popover .actions a').on('click', function() {
                mark_toggle(this)
            })
            $('.popover a.mark_all_read').on('click', function() {
                mark_all_read(this)
            })
        }, 1000);
    });
    if (reinitiate) {
        $('#notifications_badge').popover('show')
    }
}

function request_reinitiate(url) {
    var r = new XMLHttpRequest();
    r.addEventListener('readystatechange', function(event){
        if (this.readyState == 4 && this.status == 200) {
            fetch_api_data()
            initiate_popover(reinitiate=true)
        }
    })
    r.open("GET", url, true);
    r.send();
}

function mark_all_read(el) {
    request_reinitiate(notify_api_url_mark_all_read + '?json=1')
}

function mark_toggle(el) {
    request_reinitiate(notify_api_url_toggle_read + $(el).data('slug') + '/?json=1')
}


function fill_notification_badge(data) {
    var badges = document.getElementsByClassName(notify_badge_class);
    if (badges) {
        for(var i = 0; i < badges.length; i++){
            badges[i].innerHTML = data.unread_count;
        }
    }
}

function get_notification_list() {
    var data = fetch_api_data(notify_api_url_list, function(data) {

        var messages = data.list.map(function (item) {
            var message = '';
            if(typeof item.actor !== 'undefined'){
                message += '<strong>' + item.actor + '</strong>';
            }
            if(typeof item.verb !== 'undefined'){
                message += " " + item.verb;
            }
            if(typeof item.target !== 'undefined'){
                if(typeof item.forward_link !== 'undefined') {
                    message += " <a href='" + item.forward_link + "'>" + item.target + "</a>";
                } else {
                    message += " " + item.target;
                }
            }
            if(typeof item.timesince !== 'undefined'){
                message += " <div class='text-muted'>" + item.timesince + " ago</div>";
            }

            if(item.unread) {
                var mark_as_read = '<div class="actions"><a href="javascript:;" data-slug="' + item.slug + '"><i class="fa fa-circle" data-toggle="tooltip" data-placement="auto" title="Mark as read" aria-hidden="true"></i></a></div>';
            } else {
                var mark_as_read = '<div class="actions"><a href="javascript:;" data-slug="' + item.slug + '"><i class="fa fa-circle-o" data-toggle="tooltip" data-placement="auto" title="Mark as unread" aria-hidden="true"></i></a></div>';
            }
            return '<li class="list-group-item ' + (item.unread ? ' active' : '') + '">' + mark_as_read + message + '</li>';
        }).join('');

        if (messages == '') {
            messages = '<div class="text-center px-2 py-3"><i class="fa fa-star-o fa-2x" aria-hidden="true"></i><h3>You have no new notifications</h3></div>'
        }

        document.getElementById('notification-list').innerHTML = messages;
    });
}

function fetch_api_data(url, callback) {
    if (!url) {
        var url = notify_api_url_count;
    }

    if (registered_functions.length > 0) {
        //only fetch data if a function is setup
        var r = new XMLHttpRequest();
        r.addEventListener('readystatechange', function(event){
            if (this.readyState === 4){
                if (this.status === 200){
                    consecutive_misfires = 0;
                    var data = JSON.parse(r.responseText);
                    registered_functions.forEach(function (func) { func(data); });
                    if (callback) {
                        return callback(data);
                    }
                }else{
                    consecutive_misfires++;
                }
            }
        })
        r.open("GET", url + '?max=' + notify_fetch_count, true);
        r.send();
    }
    if (consecutive_misfires < 10) {
        setTimeout(fetch_api_data,notify_refresh_period);
    } else {
        var badges = document.getElementsByClassName(notify_badge_class);
        if (badges) {
            for (var i=0; i < badges.length; i++){
                badges[i].innerHTML = "!";
                badges[i].title = "Connection lost!"
            }
        }
    }
}

setTimeout(fetch_api_data, 1000);

$(function(){
    initiate_popover();
});
