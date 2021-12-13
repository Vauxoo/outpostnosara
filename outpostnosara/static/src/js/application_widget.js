odoo.define("outpostnosara.application_widget", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var {qweb, _t} = require("web.core");
    var ajax = require('web.ajax');


    publicWidget.registry.ApplicationWidget = publicWidget.Widget.extend({
        selector: ".ou-membership",
        xmlDependencies: ["/outpostnosara/static/src/xml/application.xml"],
        events: {
            "change select[name='country_id']": "_onChangeState",
            "click .membership_type": "_selectMembership",
            "click .s_website_form_send": "_onCreateSubscription",
        },
        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------
        async _onChangeState() {
            var info_states = await this._getCountryStates();
            if (!info_states.states.length){
                return []
            }
            var $state_select = this.$("#select_state")
            $state_select.html(qweb.render("outpostnosara.states_select", {states: info_states.states, }))
        },
        _selectMembership(event) {
            var $memberships = this.$('.js_membership_type');
            if ($memberships.hasClass('text-danger')){
                $memberships.removeClass('text-danger');
            }
            this.$('.membership_type').removeClass('selected');
            var $membership_type = $(event.currentTarget)
            $membership_type.addClass('selected');
            var product_id =  $membership_type.data('product-id');
            $membership_type.parent().find('input').val(product_id);
        },
        _getCountryStates() {
            return this._rpc({
                route: "/website/state_infos/" + this.$('[name="country_id"]').val(),
            })
        },
        _createPartnerOrder(form_values) {
            return this._rpc({
                route: "/outpost/membership/order",
                params: form_values,
            })
        },
        _getFormValues($form) {
            var unindexed_array = $form.serializeArray();
            var indexed_array = {};
            $.map(unindexed_array, function (n, i) {
                indexed_array[n.name] = n.value;
            });
            return indexed_array;
        },
        async _onCreateSubscription(event) {
            if (!this._validateForm()) {
                return false;
            }
            var form_fields = this.$('.membership-field');
            var form_values = this._getFormValues(form_fields);
            var [ partner ] = await this._createPartnerOrder(form_values);
            this.$('input[name="partner_id"]').val(partner.id);
            $('#o_payment_form_pay').trigger('click');
        },
        _validateForm() {
            var $inputs = this.$('.required_input');
            var $invalidate_inputs = $inputs.not(':filled');
            var $filled_inputs = $inputs.filter(':filled');
            var $membership = this.$('input[name="product_id"]').not(':filled');
            var $email = this.$('input[name="email"]');
            var $confirm_email = this.$('input[name="confirm_email"]');

            $filled_inputs.removeClass('missing');
            $invalidate_inputs.addClass('missing');

            if ($invalidate_inputs.length){
                $invalidate_inputs.filter(':first').trigger('focus');
                this.do_notify(_t("Error"), _t('Some fields are required'));
            }

            if ($membership.length){
                $invalidate_inputs.push($membership);
                this.do_notify(_t("Error"), _t('Please, Select a Membership Type'));
                this.$('.js_membership_type').addClass('text-danger');
            }

            if ($email.val() !== $confirm_email.val()){
                $invalidate_inputs.push($confirm_email);
                $confirm_email.addClass('missing');
                this.do_notify(_t("Error"), _t('Email Address do not match; please retype them.'));
            } else {
                $confirm_email.removeClass('missing');
            }

            return !$invalidate_inputs.length;
        },
    });
});


