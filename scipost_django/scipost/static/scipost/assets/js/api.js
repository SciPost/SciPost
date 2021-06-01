window.drf = {
    csrfHeaderName: document.getElementById('drf_csrf_header_name').textContent,
    csrfToken: document.getElementById('drf_csrf_token').textContent
};

// csrf.js script, move here
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

function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
  // test that a given url is a same-origin URL
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

var csrftoken = window.drf.csrfToken;

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
      // Send the token to same-origin, relative URLs only.
      // Send the token only if the method warrants CSRF protection
      // Using the CSRFToken value acquired earlier
      xhr.setRequestHeader(window.drf.csrfHeaderName, csrftoken);
    }
  }
});


// default.js script, moved here
$(document).ready(function() {
  // JSON highlighting.
  prettyPrint();

  // Bootstrap tooltips.
  $('.js-tooltip').tooltip({
    delay: 1000,
    container: 'body'
  });

  // Deal with rounded tab styling after tab clicks.
  $('a[data-toggle="tab"]:first').on('shown', function(e) {
    $(e.target).parents('.tabbable').addClass('first-tab-active');
  });

  $('a[data-toggle="tab"]:not(:first)').on('shown', function(e) {
    $(e.target).parents('.tabbable').removeClass('first-tab-active');
  });

  $('a[data-toggle="tab"]').click(function() {
    document.cookie = "tabstyle=" + this.name + "; path=/";
  });

  // Store tab preference in cookies & display appropriate tab on load.
  var selectedTab = null;
  var selectedTabName = getCookie('tabstyle');

  if (selectedTabName) {
    selectedTabName = selectedTabName.replace(/[^a-z-]/g, '');
  }

  if (selectedTabName) {
    selectedTab = $('.form-switcher a[name=' + selectedTabName + ']');
  }

  if (selectedTab && selectedTab.length > 0) {
    // Display whichever tab is selected.
    selectedTab.tab('show');
  } else {
    // If no tab selected, display rightmost tab.
    $('.form-switcher a:first').tab('show');
  }

  $(window).on('load', function() {
    $('#errorModal').modal('show');
  });
});


// ajax-form.js script, moved here
function replaceDocument(docString) {
  var doc = document.open("text/html");

  doc.write(docString);
  doc.close();
}

function doAjaxSubmit(e) {
  var form = $(this);
  var btn = $(this.clk);
  var method = (
    btn.data('method') ||
    form.data('method') ||
    form.attr('method') || 'GET'
  ).toUpperCase();

  if (method === 'GET') {
    // GET requests can always use standard form submits.
    return;
  }

  var contentType =
    form.find('input[data-override="content-type"]').val() ||
    form.find('select[data-override="content-type"] option:selected').text();

  if (method === 'POST' && !contentType) {
    // POST requests can use standard form submits, unless we have
    // overridden the content type.
    return;
  }

  // At this point we need to make an AJAX form submission.
  e.preventDefault();

  var url = form.attr('action');
  var data;

  if (contentType) {
    data = form.find('[data-override="content"]').val() || ''

    if (contentType === 'multipart/form-data') {
      // We need to add a boundary parameter to the header
      // We assume the first valid-looking boundary line in the body is correct
      // regex is from RFC 2046 appendix A
      var boundaryCharNoSpace = "0-9A-Z'()+_,-./:=?";
      var boundaryChar = boundaryCharNoSpace + ' ';
      var re = new RegExp('^--([' + boundaryChar + ']{0,69}[' + boundaryCharNoSpace + '])[\\s]*?$', 'im');
      var boundary = data.match(re);
      if (boundary !== null) {
        contentType += '; boundary="' + boundary[1] + '"';
      }
      // Fix textarea.value EOL normalisation (multipart/form-data should use CR+NL, not NL)
      data = data.replace(/\n/g, '\r\n');
    }
  } else {
    contentType = form.attr('enctype') || form.attr('encoding')

    if (contentType === 'multipart/form-data') {
      if (!window.FormData) {
        alert('Your browser does not support AJAX multipart form submissions');
        return;
      }

      // Use the FormData API and allow the content type to be set automatically,
      // so it includes the boundary string.
      // See https://developer.mozilla.org/en-US/docs/Web/API/FormData/Using_FormData_Objects
      contentType = false;
      data = new FormData(form[0]);
    } else {
      contentType = 'application/x-www-form-urlencoded; charset=UTF-8'
      data = form.serialize();
    }
  }

  var ret = $.ajax({
    url: url,
    method: method,
    data: data,
    contentType: contentType,
    processData: false,
    headers: {
      'Accept': 'text/html; q=1.0, */*'
    },
  });

  ret.always(function(data, textStatus, jqXHR) {
    if (textStatus != 'success') {
      jqXHR = data;
    }

    var responseContentType = jqXHR.getResponseHeader("content-type") || "";

    if (responseContentType.toLowerCase().indexOf('text/html') === 0) {
      replaceDocument(jqXHR.responseText);

      try {
        // Modify the location and scroll to top, as if after page load.
        history.replaceState({}, '', url);
        scroll(0, 0);
      } catch (err) {
        // History API not supported, so redirect.
        window.location = url;
      }
    } else {
      // Not HTML content. We can't open this directly, so redirect.
      window.location = url;
    }
  });

  return ret;
}

function captureSubmittingElement(e) {
  var target = e.target;
  var form = this;

  form.clk = target;
}

$.fn.ajaxForm = function() {
  var options = {}

  return this
    .unbind('submit.form-plugin  click.form-plugin')
    .bind('submit.form-plugin', options, doAjaxSubmit)
    .bind('click.form-plugin', options, captureSubmittingElement);
};


// Last script from api.html
$(document).ready(function() {
    $('form').ajaxForm();
});
