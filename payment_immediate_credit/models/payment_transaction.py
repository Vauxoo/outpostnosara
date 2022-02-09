# Copyright 2022 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
import logging
import pprint

from odoo import api, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class ImmediateCreditPaymentTransaction(models.Model):

    _inherit = 'payment.transaction'

    @api.model
    def _immediate_credit_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        tx = self.search([('reference', '=', reference)])

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _immediate_credit_form_get_invalid_parameters(self, data):
        """Get  invalid parameters."""
        invalid_parameters = []

        # verifies that the amount to pay is equal to the total of the order
        if float_compare(float(data.get('amount') or '0.0'), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        # verifies that the currency to pay is equal to the order
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _immediate_credit_form_validate(self, data):
        _logger.info('Validated credit payment for tx %s: set as pending', pprint.pformat(self.reference))
        self._set_transaction_pending()
        return True
