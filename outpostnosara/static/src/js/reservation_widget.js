odoo.define("outpostnosara.reservation_widget", function (require) {
    "use strict";

    require("outpostnosara.daterangepicker");
    var publicWidget = require("web.public.widget");
    var {_t, qweb} = require("web.core");

    publicWidget.registry.ReservationWidget = publicWidget.Widget.extend({
        selector: ".ou-reservation",
        // xmlDependencies: ["/theme_canada/static/src/xml/donations.xml"],
        events: {
            "change select[name='type']": "_onChangeReservationType",
            "apply.daterangepicker .ou-daterangepicker": "_onApplyDaterange",
        },
        _onChangeReservationType(ev) {
            var reservation_type = $(ev.currentTarget).val();
            this.$('[class*="js_reservation_"]').addClass('d-none');
            this.$(`.js_reservation_${reservation_type}`).removeClass('d-none');
        },
        _onApplyDaterange(ev, picker) {
            this.$('.ou-daterangepicker[name="checkin"]').val(picker.startDate.format('MM/DD/YYYY'));
            this.$('.ou-daterangepicker[name="checkout"]').val(picker.endDate.format('MM/DD/YYYY'));

        },
    });
});


