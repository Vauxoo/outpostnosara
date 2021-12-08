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
            "change select[name='room_id']": "_onChangeReservationType",
            "change select[name='room_type_id']": "_onChangeRoomType",
            "click #validate_reservation": "_onValidateReservation",
            "apply.daterangepicker .ou-daterangepicker": "_onApplyDaterange",
        },
        init: function () {
            this._super.apply(this, arguments);
            this._invalid_dates = [];
            this._startDate;
            this._endDate;
        },
        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------
        async _onChangeReservationType(ev) {
            this.$('[class*="js_reservation_"]').addClass('d-none');
            if (!this._isConfigComplete()) return [];
            var reservation_code = this.$('[name="reservation_type_id"]').children('option:selected').data('code');
            await this._setReservedDate();
            if (reservation_code)
                this.$(`.js_reservation_${reservation_code},.js_reservation_button`).removeClass('d-none');

        },
        _onApplyDaterange(ev, picker) {
            if (this._getInvalidDates(picker).length) return false;
            var $input = $(ev.currentTarget);
            this._startDate = picker.startDate.clone();

            if ($input.data('singledatepicker')) {
                $input.val(picker.startDate.format('DD/MM/YYYY'));
                return;
            }

            this._endDate = picker.endDate.clone();
            this.$('.ou-daterangepicker[name="checkin"]').val(picker.startDate.format('DD/MM/YYYY'));
            this.$('.ou-daterangepicker[name="checkout"]').val(picker.endDate.format('DD/MM/YYYY'));

            this.$('.js_reservation_button').removeClass('d-none');
            this.$('.js_reservation_payment').addClass('d-none');
        },
        async _setReservedDate() {
            this._invalid_dates = await this._getReservedDate();
            this.$('.ou-daterangepicker').data('dom:invalidDates', this._invalid_dates);
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
        _getInvalidDates(picker) {
            var date_range = [];
            var current = picker.startDate.clone();

            while (current < picker.endDate) {
                date_range.push(current.format('YYYY-MM-DD'));
                current.add(1, 'days');
            }
            return date_range.filter(x => this._invalid_dates.includes(x))
        },
        async _onValidateReservation(ev) {
            await this._getValidateReservation();
            this.$('.js_reservation_payment').removeClass('d-none');
            this.$('.js_reservation_button').addClass('d-none');

        },
        // --------------------------------------------------------------------------
        // Geters
        // --------------------------------------------------------------------------
        _getReservedDate() {;
            if (!this._isConfigComplete()) return [];
            return this._rpc({
                route: "/outpost/reserved_date",
                params: {
                    room_id: this.$('[name="room_id"]').val(),
                },
            })
        },
        _getRoomsAvailables() {
            return this._rpc({
                route: "/outpost/rooms_availables",
                params: {
                    room_type_id: this.$('[name="room_type_id"]').val(),
                },
            })
        },
        _getValidateReservation() {
            return this._rpc({
                route: "/outpost/validate_reservation/" + this.$('[name="room_id"]').val(),
                params: {
                    start_date: this._startDate.format('YYYY-MM-DD'),
                    end_date: this._endDate.format('YYYY-MM-DD'),
                    reservation_type_id: this.$('[name="reservation_type_id"]').val(),
                },
            })
        },
    });
});


