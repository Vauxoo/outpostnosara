odoo.define('payment_credomatic.credomatic_s2s_form', (require) => {
    'use strict';

    const PaymentForm = require('payment.payment_form');

    PaymentForm.include({
        events: _.extend(PaymentForm.prototype.events, {
            'click div.o_payment_acquirer_select': 'onCredomaticForm',
            'keyup .credomatic-input[name="exp_month"]': 'setup_month_mask',
            'keyup .credomatic-input[name="exp_year"]': 'setup_year_mask',
            'keyup .credomatic-input[data-value-type="number"]:not(#cc_number)': 'number_validation'
        }),
        onCredomaticForm (ev) {
            const target = $(ev.currentTarget).find('input[data-acquirer-id]');
            this._onCredomatic = target.data('provider') == 'credomatic';
        },
        start () {
            this._super();
            this.onCredomaticForm({ currentTarget: this.$('.o_payment_acquirer_select').eq(0) });
        },
        isDeleting(keyCode){
            return keyCode === 8 || keyCode === 46;
        }, isNumber(value){
            return value !== "" && !isNaN(value);
        }, setup_year_mask(ev){
            if(this.isDeleting(ev.keyCode) && ev.currentTarget.value === ""){
                this.$('.credomatic-input[name="exp_month"]').focus();
            }
        }, setup_month_mask(ev){
            if(ev.currentTarget.value.length === 2){
                this.$('.credomatic-input[name="exp_year"]').focus();
            }
        }, number_validation(ev){
            if(ev.currentTarget.value !== "" && this.validate_field(ev.currentTarget) && this.isDeleting(ev.keyCode)){
                $(ev.currentTarget).removeClass('alert-danger');
            }
        }, validate_field(input){
            const value = input.value.split(" ").join("");
            const valid = this.isNumber(value);
            const $input = $(input);
            const $errorhoder = $input.hasClass('false-input') ? $input.parents('.labeled-div') : $input;
            if(valid){
                $errorhoder.removeClass('alert-danger');
            }else{
                $errorhoder.addClass('alert-danger');
            }
            return valid;
        }, validate(){
            if (!this._onCredomatic) {
                return true;
            }
            return this.$('.credomatic-input[data-value-type="number"]').toArray().reduce((valid, current) => {
                const _valid = this.validate_field(current);
                return _valid ? valid : false;
            }, true);
        }, payEvent(ev){
            ev.preventDefault();
            return this.validate() ? this._super.apply(this, arguments) : null;
        }
    });
});
