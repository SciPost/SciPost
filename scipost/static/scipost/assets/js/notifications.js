var notify_container_class = "notifications_container";
var notify_badge_class = "live_notify_badge";
var notify_menu_class = "live_notify_list";
var notify_api_url_count = "/notifications/api/unread_count/";
var notify_api_url_list = "/notifications/api/list/";
var notify_api_url_toggle_read = "/notifications/mark-toggle/";
var notify_api_url_mark_all_read = "/notifications/mark-all-as-read/";
var notify_fetch_count = "5";
var notify_refresh_period = 60000;
var consecutive_misfires = 0;


// function initiate_popover(reinitiate) {
//     if(typeof reinitiate == 'undefined') {
//         reinitiate = false;
//     }
//
    // var notification_template = '<div class="popover notifications" role="tooltip"><div class="arrow"></div><p class="popover-header"></p><div class="popover-body"></div></div>';
    //
    // function get_notifications() {
    //     var _str = '<ul id="notification-list" class="update_notifications list-group"><div class="w-100 text-center py-4"><i class="fa fa-circle-o-notch fa-2x fa-spin fa-fw"></i><span class="sr-only">Loading...</span></div></ul>';
    //     get_notification_list();
    //     return _str;
    // }
    //
    // $('.popover [data-toggle="tooltip"]').tooltip('dispose')
    // $('#notifications_badge').popover('dispose').popover({
    //     animation: false,
    //     trigger: 'click',
    //     title: 'My inbox',
    //     template: notification_template,
    //     content: get_notifications,
    //     container: 'body',
    //     offset: '0, 9px',
    //     placement: "bottom",
    //     html: true
    // }).on('inserted.bs.popover', function() {
    //     // Bloody js
    //     setTimeout(function() {
    //         $('.popover [data-toggle="tooltip"]').tooltip({
    //             animation: false,
    //             delay: {"show": 500, "hide": 100},
    //             fallbackPlacement: 'clockwise',
    //             placement: 'bottom'
    //         });
    //         $('.popover .actions a').on('click', function() {
    //             mark_toggle(this)
    //         })
    //     }, 1000);
    // });
    // if (reinitiate) {
    //     $('#notifications_badge').popover('show')
    // }
// }
//
// function request_reinitiate(url) {
//     var r = new XMLHttpRequest();
//     r.addEventListener('readystatechange', function(event){
//         if (this.readyState == 4 && this.status == 200) {
//             fetch_api_data()
//             initiate_popover(reinitiate=true)
//         }
//     })
//     r.open("GET", url, true);
//     r.send();
// }
//
// function mark_all_read(el) {
//     request_reinitiate(notify_api_url_mark_all_read + '?json=1')
// }
//

//
//
// function fill_notification_badge(data) {
//     var badges = document.getElementsByClassName(notify_badge_class);
//     var container = $('.' + notify_container_class);
//     if (badges) {
//         for(var i = 0; i < badges.length; i++){
//             badges[i].innerHTML = data.unread_count;
//             if (data.unread_count > 0) {
//                 container.addClass('positive_count');
//             } else {
//                 container.removeClass('positive_count');
//             }
//         }
//     }
// }
//
// function get_notification_list() {
//     fetch_api_data(notify_api_url_list, true, function(data) {
//
//         var messages = data.list.map(function (item) {
//             var message = "<div>";
//             if(typeof item.actor !== 'undefined'){
//                 message += '<strong>' + item.actor + '</strong>';
//             }
//             if(typeof item.verb !== 'undefined'){
//                 message += " " + item.verb;
//             }
//             if(typeof item.target !== 'undefined'){
//                 if(typeof item.forward_link !== 'undefined') {
//                     message += " <a href='" + item.forward_link + "'>" + item.target + "</a>";
//                 } else {
//                     message += " " + item.target;
//                 }
//             }
//             if(typeof item.timesince !== 'undefined'){
//                 message += "<br><small class='text-muted'>" + item.timesince + " ago</small>";
//             }
//             message += "</div>";
//
            // if(item.unread) {
            //     var mark_as_read = '<div class="actions"><a href="javascript:;" data-slug="' + item.slug + '"><i class="fa fa-circle" data-toggle="tooltip" data-placement="auto" title="Mark as read" aria-hidden="true"></i></a></div>';
            // } else {
            //     var mark_as_read = '<div class="actions"><a href="javascript:;" data-slug="' + item.slug + '"><i class="fa fa-circle-o" data-toggle="tooltip" data-placement="auto" title="Mark as unread" aria-hidden="true"></i></a></div>';
            // }
//             return '<li class="list-group-item ' + (item.unread ? ' active' : '') + '">' + message + mark_as_read + '</li>';
//         }).join('');
//
        // if (messages == '') {
        //     messages = '<div class="text-center px-2 py-3"><i class="fa fa-star-o fa-2x" aria-hidden="true"></i><h3>You have no new notifications</h3></div>'
        // }
//
//         document.getElementById('notification-list').innerHTML = messages;
//     });
// }

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
        r.open("GET", url + '?max=' + notify_fetch_count, true);
        r.send();
    }
}

// setTimeout(fetch_api_data, 1000);


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
            message += "<br><small class='text-muted'>" + item.timesince + " ago</small>";
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
        return '<li class="dropdown-item ' + (item.unread ? ' active' : '') + '"><div>' + message + '</div><div class="actions">' + mark_toggle + '</div></li>';
    }).join('');

    if (messages == '') {
        messages = '<li class="dropdown-item px-5"><em>You have no new notifications</em></li>'
    }

    // Fill DOM
    el.find('.live_notify_list').html(messages).trigger('refresh_notify_list');
}

function update_mark_callback(data, args) {
    var el = $(args['element']);
    $(el).parents('.dropdown-item').toggleClass('active');

    // $('.live_notify_badge').each(function(index, el) {
    //     update_counter(el);
    // });
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

$(function(){
    $('.notifications_container')
    .on('show.bs.dropdown', function() {
        $(this).trigger('notification_open_list');
    })
    .on('notification_open_list', function() {
        update_list(this);
    })

    $('.live_notify_badge').on('notification_count_updated', function() {
        update_counter(this);
    }).trigger('notification_count_updated');


    $('.live_notify_list').on('refresh_notify_list', function() {
        // Bloody js
        $(this).find('li.dropdown-item').on('click', function(e) {
            e.stopPropagation();
        });
        $(this).find('[data-toggle="tooltip"]').tooltip({
            animation: false,
            delay: {"show": 500, "hide": 100},
            fallbackPlacement: 'clockwise',
            placement: 'bottom'
        });
        $(this).find('.actions a.mark-toggle').on('click', function(e) {
            e.stopPropagation();
            mark_toggle(this);
        });
    });

    // initiate_popover();
});
