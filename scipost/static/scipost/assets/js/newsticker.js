/*!
    SciPost NewsTicker

 */

var NewsTicker;


NewsTicker = (function() {
    NewsTicker.prototype.items = [];

    NewsTicker.prototype.cached_items = [];

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

    NewsTicker.prototype.set_item = function(item_id) {
        var self = this

        this.element.fadeOut(function() {
            self.element.html(self.cached_items[item_id]).fadeIn()
        })
    };

    NewsTicker.prototype.get_item = function(item) {
        var self = this

        if(typeof(this.cached_items[item.id]) == 'undefined') {
            $.get(this.options.url + item.id + '/?format=html')
            .done(function(data) {
                self.cached_items[item.id] = data
                self.set_item(item.id)
            })
        } else {
            self.set_item(item.id)
        }
    };

    NewsTicker.prototype.start_ticker = function() {
        var self = this
        var time = 0;

        $.get(this.options.url + '?format=json')
        .done(function(data) {
            var counter = 1
            var total = data.count

            setInterval(function(){
                self.get_item(data.results[counter % total]);
                counter += 1
            }, self.options.interval);
        })
    };

    return NewsTicker;
})();


(function($) {
    // Extend jQuery
    $.fn.scipost_newsticker = function(options) {
        var ticker = new NewsTicker(this, options)
        return this;
    }

    // Start
    $('#news ul').scipost_newsticker({
        url: 'api/news/',
        interval: 6000
    })
}(jQuery));
