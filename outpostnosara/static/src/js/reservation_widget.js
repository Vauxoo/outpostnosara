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
            "change .ou-reset": "_resertValidation",
            "click #validate_reservation": "_onValidateReservation",
            "apply.daterangepicker .ou-daterangepicker": "_onApplyDaterange",
        },
        init: function () {
            this._super.apply(this, arguments);
            this._invalid_dates = [];
            this._startDate;
            this._endDate;
            this._code;
        },
        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------
        async _onChangeReservationType() {
            this.$('[class*="js_reservation_"]').addClass('d-none');
            if (!this._isConfigComplete()) return [];
            this._code = this.$('[name="reservation_type_id"]').children('option:selected').data('code');
            await this._setReservedDate();
            if (this._code)
                this.$(`.js_reservation_${this._code},.js_reservation_button`).removeClass('d-none');
        },
        _onApplyDaterange(ev, picker) {
            if (this._getInvalidDates(picker).length) return false;
            var $input = $(ev.currentTarget);
            this._startDate = picker.startDate.clone();
            this._endDate = picker.endDate.clone();
            this._resertValidation();

            if ($input.data('singledatepicker')) {
                 $input.val(picker.startDate.format('DD/MM/YYYY'));
                return;
            }

            this.$('.ou-daterangepicker[name="checkin"]').val(picker.startDate.format('DD/MM/YYYY'));
            this.$('.ou-daterangepicker[name="checkout"]').val(picker.endDate.format('DD/MM/YYYY'));

            this.$('.js_reservation_button').removeClass('d-none');
            this.$('.js_reservation_payment,.js_reservation_price').addClass('d-none');
        },
        async _setReservedDate() {
            this._invalid_dates = await this._getReservedDate();
            this.$('.ou-daterangepicker').data('dom:invalidDates', this._invalid_dates);
        },
        _isConfigComplete() {
            return this.$('[name="room_id"]').val() && this.$('[name="reservation_type_id"]').val();
        },
        async _onChangeRoomType() {
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
        async _onValidateReservation() {
            if (!this._validateForm()) return false;
            var reservation = await this._getValidateReservation();
            this.$('.js_reservation_price .oe_currency_value').html(reservation[0].price_room_services_set);
            this.$('.js_reservation_payment,.js_reservation_price').removeClass('d-none');
            this.$('.js_reservation_button').addClass('d-none');
        },
        _validateForm() {
            var $inputs = this.$(`.js_reservation_${this._code} input`);
            var $empty_inputs = $inputs.not(':filled');
            var $filled_inputs = $inputs.filter(':filled');

            $filled_inputs.removeClass('missing');
            $empty_inputs.addClass('missing');

            if ($empty_inputs.length){
                $empty_inputs.filter(':first').trigger('focus');
                this.do_notify(_t("Error"), 'Some fields are required');
            } 
            return !$empty_inputs.length;
        },
        _resertValidation() {
            this.$('.js_reservation_button').removeClass('d-none');
            this.$('.js_reservation_payment,.js_reservation_price').addClass('d-none');
        },
        // --------------------------------------------------------------------------
        // Geters
        // --------------------------------------------------------------------------
        _getReservedDate() {
            if (!this._isConfigComplete()) return [];
            return this._rpc({
                route: "/outpost/reserved_date/" + this.$('[name="room_id"]').val(),
            })
        },
        _getRoomsAvailables() {
            return this._rpc({
                route: "/outpost/rooms_availables/" + this.$('[name="room_type_id"]').val(),
            })
        },
        _getValidateReservation() {
            var params = {
                start_date: this._startDate.format('YYYY-MM-DD'),
                end_date: this._endDate.format('YYYY-MM-DD'),
                reservation_type_id: this.$('[name="reservation_type_id"]').val(),
            }
            switch (this._code) {
                case 'hour':
                    params.end_date = params.start_date;
                    params.arrival_hour = this.$('[name="arrival_hour"]').val();
                    params.departure_hour = this.$('[name="departure_hour"]').val();
                break;
                case 'half':
                    var hour = this.$('[name="hour"]').val().split("-");
                    params.end_date = params.start_date;
                    params.arrival_hour = hour[0];
                    params.departure_hour = hour[1];
                break;
            }
            return this._rpc({
                route: "/outpost/validate_reservation/" + this.$('[name="room_id"]').val(),
                params,
            })
        },
    });
});


