odoo.define("outpostnosara.daterangepicker", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.OuDaterangepicker = publicWidget.Widget.extend({
        selector: ".ou-daterangepicker",
        jsLibs: [
            '/web/static/lib/daterangepicker/daterangepicker.js',
            '/web/static/src/js/libs/daterangepicker.js',
        ],
        cssLibs: [
            '/web/static/lib/daterangepicker/daterangepicker.css',
        ],

        start() {
            return this._super.apply(this, arguments).then(() => {
                this.$el.daterangepicker({
                    minDate: new Date(),
                    autoUpdateInput: false,
                    locale: {
                        cancelLabel: 'Clear'
                    },
                    ...(this.$el.data('singledatepicker') && {singleDatePicker: true}),
                    isInvalidDate:(date) => {
                        var invalid_dates = this.$el.data('dom:invalidDates') || [];
                        if (invalid_dates.includes(date.format('YYYY-MM-DD')))
                            return true;
                    }
                });
            });
        },
    });
});


