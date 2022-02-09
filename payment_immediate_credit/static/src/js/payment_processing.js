odoo.define('payment_immediate_credit.payment_processing', function (require){
    'use strict';

    require('payment.processing')
    var publicWidget = require('web.public.widget');
    var PaymentProcessing = publicWidget.registry.PaymentProcessing;

    PaymentProcessing.include({
        processPolledData: function (transactions) {
            if (transactions.length > 0 && transactions[0].acquirer_provider == 'immediate_credit') {
                window.location = transactions[0].return_url;
                return;
            }
            this._super.apply(this, arguments);
        },
    });

});
