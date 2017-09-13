var notify_badge_class = 'live_notify_badge';
var notify_menu_class = 'live_notify_list';
var notify_api_url_count = '/notifications/api/unread_count/';
var notify_api_url_list = '/notifications/api/unread_list/';
var notify_fetch_count = '5';
var notify_refresh_period = 15000;
var consecutive_misfires = 0;
var registered_functions = [fill_notification_badge];


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

        var messages = data.unread_list.map(function (item) {
            var message = "";
            if(typeof item.actor !== 'undefined'){
                message = '<strong>' + item.actor + '</strong>';
            }
            if(typeof item.verb !== 'undefined'){
                message = message + " " + item.verb;
            }
            if(typeof item.target !== 'undefined'){
                if(typeof item.forward_link !== 'undefined') {
                    message += " <a href='" + item.forward_link + "'>" + item.target + "</a>";
                } else {
                    message += " " + item.target;
                }
            }
            if(typeof item.timestamp !== 'undefined'){
                message = message + " " + item.timestamp;
            }
            return '<li class="list-group-item ' + (item.unread ? ' active' : '') + '">' + message + '</li>';
        }).join('')

        document.getElementById('notification-list').innerHTML = messages;
    });
}

function fetch_api_data(url=null, callback=null) {
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
        r.open("GET", url +'?max='+notify_fetch_count, true);
        r.send();
    }
    if (consecutive_misfires < 10) {
        setTimeout(fetch_api_data,notify_refresh_period);
    } else {
        var badges = document.getElementsByClassName(notify_badge_class);
        if (badges) {
            for (var i = 0; i < badges.length; i++){
                badges[i].innerHTML = "!";
                badges[i].title = "Connection lost!"
            }
        }
    }
}

setTimeout(fetch_api_data, 1000);

$(function(){
    var notification_template = '<div class="popover notifications" role="tooltip"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';

    var get_notifications_title = function() {
        return 'New notifications <div class="badge badge-warning live_notify_badge"></div>';
    }

    var get_notifications = function() {
        var _str = '<ul id="notification-list" class="update_notifications list-group"><div class="w-100 text-center"><i class="fa fa-circle-o-notch fa-spin fa-fw"></i><span class="sr-only">Loading...</span></div></ul>';
        get_notification_list();
        return _str;
    }

    $('#notifications_badge').popover({
        animation: false,
        trigger: 'click',
        title: get_notifications_title,
        template: notification_template,
        content: get_notifications,
        container: 'body',
        offset: '0, 9px',
        placement: "bottom",
        html: true
    });
});
