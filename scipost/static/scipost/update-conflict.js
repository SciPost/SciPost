   function csrfSafeMethod(method) {
       // these HTTP methods do not require CSRF protection
       return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
   }
   function getCookie(name) {
       var cookieValue = null;
       if (document.cookie && document.cookie !== '') {
           var cookies = document.cookie.split(';');
           for (var i = 0; i < cookies.length; i++) {
               var cookie = jQuery.trim(cookies[i]);
               // Does this cookie string begin with the name we want?
               if (cookie.substring(0, name.length + 1) === (name + '=')) {
                   cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                   break;
               }
           }
       }
       return cookieValue;
   }
   var csrftoken = getCookie('csrftoken');

   function update_conflict(conflict_id, status, url) {
       $.ajax({
           "method": "POST",
           "url": url,
           "data": {
               'status': status,
               'csrftoken': getCookie('csrftoken'),
           },
           "beforeSend": function(xhr, settings) {
               if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                   xhr.setRequestHeader("X-CSRFToken", csrftoken);
               }
           },
       }).done(function( data ) {
           if ( data['status'] == 'verified' ) {
               $("#conflict-" + data['id'] + " .status").html('<span class="text-success" aria-hidden="true">OK</span> Verified by Admin');
           } else if ( data['status'] == 'deprecated' ) {
               $("#conflict-" + data['id'] ).fadeTo("fast", 0.3).find('.status').html('<span class="text-danger" aria-hidden="true">X</span> <em>Deleted</em>');
           }
       });
   }

   $(document).ready(function () {
       $('.update-conflict-button').on('click', function() {
	   id = $(this).data('conflict-id');
	   status = $(this).data('status');
	   url = $(this).data('urllink');
	   update_conflict(id, status, url);
       });
   });
