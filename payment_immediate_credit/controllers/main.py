# © 2022 Vauxoo, S.A. de C.V.
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentController(http.Controller):

    @http.route(['/payment/immediate_credit/feedback'], type='http', auth='user', website=True)
    def immediate_credit_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))
        transaction = request.env['payment.transaction'].sudo()
        transaction.form_feedback(post, 'immediate_credit')
        return request.redirect('/payment/process')
