/*!
    SciPost NewsTicker

 */

var NewsTicker;


NewsTicker = (function() {
    NewsTicker.prototype.items = [];

    NewsTicker.prototype.defaults = {
        url: '/api',
        interval: 10000,
    };

    function NewsTicker(element, options) {
        this.element = element;
        this.options = $.extend({}, this.defaults, options);

        // Start building...
        this.start_ticker()
    };

    NewsTicker.prototype.get_item = function(item) {
        var self = this

        $.get(this.options.url + '/' + item.id + '/?format=html')
        .done(function(data) {
            self.element.fadeOut(function() {
                self.element.html(data).fadeIn()
            })
        })
    };

    NewsTicker.prototype.start_ticker = function() {
        var self = this
        var time = 0;

        $.get(this.options.url + '?format=json')
        .done(function(data) {
            $.each(data, function(index, item) {
                setTimeout( function(){ self.get_item(item); }, time)
                time += self.options.interval;
            })
        });
    };

    return NewsTicker;
})();


(function($) {
    // Extend jQuery
    $.fn.scipost_newsticker = function(options) {
        var ticker = new NewsTicker(this, options)
        console.log('SciPost NewTicker')
        return this;
    }

    // Start
    $('#news ul').scipost_newsticker({
        url: 'api/news',
        interval: 6000
    })
}(jQuery));
