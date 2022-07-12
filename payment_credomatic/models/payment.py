# Copyright 2020 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).

import logging
import requests
import calendar

from hashlib import md5
from urllib.parse import parse_qs
from datetime import datetime
from odoo import fields, models, api, _


_logger = logging.getLogger(__name__)

CREDOMATIC_ERRORS = {
    'cvvresponse': {
        'M': 'CVV2/CVC2 Match',
        'N': 'CVV2/CVC2 No Match',
        'P': 'Not Processed',
        'S': ('Merchant has indicated that'
              'CVV2/CVC2 is not present on card'),
        'U': ('Issuer is not certified and/or has'
              'not provided Visa encryption keys')
    },
    'avsresponse': {
        'X': 'Exact match, 9-character numeric ZIP',
        'Y': 'Exact match, 5-character numeric ZIP',
        'D': 'Exact match, 5-character numeric ZIP',
        'M': 'Exact match, 5-character numeric ZIP',
        'A': 'Address match only',
        'B': 'Address match only',
        'W': '9-character numeric ZIP match only',
        'Z': '5-character Zip match only',
        'P': '5-character Zip match only',
        'L': '5-character Zip match only',
        'N': 'No address or ZIP match',
        'C': 'No address or ZIP match',
        'U': 'Address unavailable',
        'G': 'Non-U.S. Issuer does not participate',
        'I': 'Non-U.S. Issuer does not participate',
        'R': 'Issuer system unavailable',
        'E': 'Not a mail/phone order',
        'S': 'Service not supported',
        '0': 'AVS Not Available',
        'O': 'AVS Not Available',
    }
}


def get_utc():
    utc_date = datetime.utcnow()
    return calendar.timegm(utc_date.utctimetuple())


class PaymentAcquirerCredomatic(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('credomatic', 'Credomatic')], ondelete={'credomatic': 'cascade'})
    credomatic_gateway_url = fields.Char(
        string='Merchant transaction url',
        required_if_provider='credomatic',
        groups='base.group_user')
    credomatic_private_api_key = fields.Char(
        string='Merchant private key',
        groups='base.group_user')
    credomatic_public_id = fields.Char(
        string='Merchant key public id',
        groups='base.group_user')
    error_ref = fields.Char(default="REFID")

    def toggle_environment_value(self):
        self.ensure_one()
        response = super().toggle_environment_value()
        if self.provider == 'credomatic':
            self.write({
                'credomatic_private_api_key': False,
                'credomatic_public_id': False
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'payment_credomatic.alert_environment_js',
                'name': _('Acquirer credentials removed'),
                'target': 'new',
                'state': self.environment
            }
        return response

    def _credomatic_call_api(self, params, raw=False):
        self.ensure_one()
        assert self.provider == 'credomatic'
        _logger.warning('CREDOMATIC API CALL: %s', params)
        response = requests.get(self.get_form_action_url(), params=params, timeout=10)
        response.raise_for_status()
        return parse_qs(response.text)

    def credomatic_s2s_form_process(self, data):
        self.ensure_one()
        token = self.env['payment.token'].create({
            'name': '**** **** **** %s' % data.get('ccnumber', '')[-4:],
            'acquirer_id': self.id,
            'partner_id': data.get('partner_id'),
            'acquirer_ref': data.get('reference'),
            'verified': True,
        })
        return token

    def _credomatic_get_error_message(self, **values):
        for variant in ['cvvresponse', 'avsresponse']:
            code = values.get(variant)
            if not code:
                continue
            return CREDOMATIC_ERRORS[variant][code[0]]
        return self._credomatic_remove_tech_ref(
            values['responsetext'][0])

    def _credomatic_remove_tech_ref(self, text):
        indexof = text.find(self.error_ref)
        no_tech = text if indexof == -1 else text[:indexof - 1]
        withdot = no_tech if no_tech.endswith(".") else "%s." % no_tech
        return _('%s Please refresh the page.') % withdot

    @api.model
    def credomatic_validate_response(self, response):
        """Validates a response make to Credomatic API.
        """
        return response if response.get('response')[0] == '1' else False

    def _credomatic_get_md5(self, orderid, amount, epoch):
        self.ensure_one()
        hashstring = u'%(orderid)s|%(amount)s|%(epoch)d|%(key)s' % {
            'orderid': orderid,
            'amount': amount,
            'epoch': epoch,
            'key': self.credomatic_private_api_key
        }
        return md5(hashstring.encode('utf-8')).hexdigest()

    def credomatic_get_form_action_url(self):
        self.ensure_one()
        return self.credomatic_gateway_url

    def _credomatic_get_values(self, reference, amount):
        self.ensure_one()
        epoch = get_utc()
        return {
            'hash': self._credomatic_get_md5(reference, amount, epoch),
            'orderid': reference,
            'amount': amount,
            'time': epoch,
            'type': 'auth',
            'tx_url': self.credomatic_get_form_action_url(),
            'key_id': self.credomatic_public_id
        }


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def confirm_sale_token(self):
        confirmation = super().confirm_sale_token()
        if self.acquirer_id.provider == 'credomatic' \
                and self.acquirer_id.save_token == 'none' and self.payment_token_id:
            self.payment_token_id.unlink()
        return confirmation

    def credomatic_s2s_do_transaction(self, **data):
        self.ensure_one()
        response = self._credomatic_s2s_do_transaction(data)
        return self._credomatic_s2s_validate(response)

    def _credomatic_s2s_do_transaction(self, data):
        self.ensure_one()
        values = self.acquirer_id._credomatic_get_values('', self.amount)
        values.update(type='capture', transactionid=self.payment_token_id.acquirer_ref)
        values.pop('orderid')
        return self.acquirer_id._credomatic_call_api(values)

    def _credomatic_s2s_validate(self, data):
        """Processs data from credomatic for updating itself
        """
        assert self.acquirer_id.provider == 'credomatic'
        if self.payment_token_id:
            self.payment_token_id.unlink()
        if self.state in ['done', 'refunded']:
            _logger.warning(
                _('Credomatic: trying to validate a validated tx (ref %s)'), self.reference)
            return True
        message = data.get('responsetext')[0] if data.get('responsetext') else False
        if self.acquirer_id.credomatic_validate_response(data):
            self.write({
                'state_message': message,
                'date': fields.Datetime.now(),
                'state': 'authorized' if self.acquirer_id.capture_manually else 'done',
            })
            self.execute_callback()
            return True
        _logger.error(_("Credomatic: Error in transaction: %s"), message)
        self.write({
            'state': 'error',
            'state_message': message,
            'date': fields.datetime.now(),
        })
        return False
