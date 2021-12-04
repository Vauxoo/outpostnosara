odoo.define("outpostnosara.reservation_widget", function (require) {
    "use strict";

    require("outpostnosara.daterangepicker");
    var publicWidget = require("web.public.widget");
    var {_t, qweb} = require("web.core");

    publicWidget.registry.ReservationWidget = publicWidget.Widget.extend({
        selector: ".ou-reservation",
        xmlDependencies: ["/outpostnosara/static/src/xml/reservation.xml"],
        events: {
            "change select[name='reservation_type_id']": "_onChangeReservationType",
            "change select[name='room_id']": "_setReservedDate",
            "change select[name='room_type_id']": "_onChangeRoomType",
            "apply.daterangepicker .ou-daterangepicker": "_onApplyDaterange",
        },
        init: function () {
            this._super.apply(this, arguments);
            this._invalid_dates = [];
        },
        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------
        async _onChangeReservationType(ev) {
            if (!this._isConfigComplete()) return [];
            var reservation_code = $(ev.currentTarget).children('option:selected').data('code');
            this.$('[class*="js_reservation_"]').addClass('d-none');
            await this._setReservedDate();
            this.$(`.js_reservation_${reservation_code}`).removeClass('d-none');
        },
        _onApplyDaterange(ev, picker) {
            var $input = $(ev.currentTarget);
            if ($input.data('singledatepicker')) {
                $input.val(picker.startDate.format('DD/MM/YYYY'));
                return;
            }
            if (this._getInvalidDates(picker).length)
                return false;
            this.$('.ou-daterangepicker[name="checkin"]').val(picker.startDate.format('DD/MM/YYYY'));
            this.$('.ou-daterangepicker[name="checkout"]').val(picker.endDate.format('DD/MM/YYYY'));
        },
        async _setReservedDate() {
            this._invalid_dates = await this._getReservedDate();
            this.$('.ou-daterangepicker').data('dom:invalidDates', this._invalid_dates);
        },
        _getReservedDate() {;
            if (!this._isConfigComplete()) return [];
            return this._rpc({
                route: "/outpost/reserved_date",
                params: {
                    room_id: this.$('[name="room_id"]').val(),
                },
            })
        },
        _isConfigComplete() {
            return this.$('[name="room_id"]').val() && this.$('[name="reservation_type_id"]').val();
        },
        async _onChangeRoomType(ev) {
            var filters = await this._getRoomsAvailables();
            var $room_filter = this.$("select[name='room_id']");
            var $reservation_filter = this.$("select[name='reservation_type_id']");

            $room_filter.html(
                qweb.render("outpostnosara.room_select", {
                    room_ids: filters.room_ids || [],
                })
            )

            $reservation_filter.html(
                qweb.render("outpostnosara.reservation_select", {
                    reservation_types: filters.reservation_types || [],
                })
            )

            this.$('[class*="js_reservation_"]').addClass('d-none');

        },
        _getRoomsAvailables() {
            return this._rpc({
                route: "/outpost/rooms_availables",
                params: {
                    room_type_id: this.$('[name="room_type_id"]').val(),
                },
            })
        },
        _getInvalidDates(picker) {
            var date_range = [];
            var current = picker.startDate.clone();

            while (current < picker.endDate) {
                date_range.push(current.format('YYYY-MM-DD'));
                current.add(1, 'days');
            }
            return date_range.filter(x => this._invalid_dates.includes(x))
        },
    });
});


