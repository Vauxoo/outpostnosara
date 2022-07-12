# © 2020 Vauxoo, S.A. de C.V.
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
# pylint: disable=too-many-return-statements

import logging

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import WebsitePayment
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def safe_int(value):
    try:
        integer = int(value)
    except (ValueError, TypeError):
        integer = False
    return integer


class FacBacController(http.Controller):

    @http.route('/payment_credomatic/tunnel_credomatic', type="json", website=True, auth='none')
    def _tunnel_credomatic(self, *args, **kw):
        document = self.credomatic_get_related_document(kw).sudo()
        if not document:
            raise UserError(_("Missing order / invoice."))
        acquirer_id = safe_int(kw.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        if not acquirer:
            return {
                'result': False,
                'error': _("Missing payment method."),
            }
        ccexp = "%s%s" % (kw.pop('exp_month'), kw.pop('exp_year'))
        auth_values = acquirer._credomatic_get_values(document.get_credomatic_uuid(), document.amount_total)
        kw.update(ccexp=ccexp, **auth_values)
        if 'invoice_id' in kw:
            kw.pop('invoice_id')
        if 'order_id' in kw:
            kw.pop('order_id')
        response = acquirer._credomatic_call_api(kw)
        transaction = acquirer.credomatic_validate_response(response)
        if transaction:
            token = acquirer.s2s_process({
                'ccnumber': kw.get('ccnumber', ''),
                'partner_id': document.partner_id.id,
                'reference': transaction['transactionid'][0],
            })
            return {'result': True, 'id': token.id, '3d_secure': False}
        _logger.error(
            "An authorization has filed with the following "
            "response: %s", response)
        return {'error': acquirer._credomatic_get_error_message(**response)}

    def credomatic_get_related_document(self, data):
        if data.get('order_id'):
            return request.env['sale.order'].browse(safe_int(data.get('order_id')))
        if data.get('invoice_id'):
            return request.env['account.move'].browse(safe_int(data.get('invoice_id')))
        return request.website.sale_get_order()


class WebsiteSaleSale(WebsiteSale):

    @http.route()
    def payment_validate(self, **kw):
        response = super().payment_validate(**kw)
        success_text = kw.get('success')
        if success_text and success_text == 'False':
            return request.redirect('/shop?sale_error=1&sale_message=%s' % kw.get('error'))
        return response

    @http.route()
    def shop(self, **kw):
        response = super().shop(**kw)
        response.qcontext.update(
            sale_error=kw.get('sale_error'),
            sale_message=kw.get('sale_message'))
        return response


class WebsitePaymentInherit(WebsitePayment):

    @http.route(['/website_payment/pay'], type='http', auth='public', website=True, sitemap=False)
    def pay(self, **kw):
        res = super().pay(**kw)
        reference = kw.get('reference', False)
        if not reference:
            return res
        res.qcontext.update(
            invoice=request.env['account.invoice'].search([('name', '=', reference)], limit=1),
            sale_order=request.env['sale.order'].search([('name', '=', reference)], limit=1),
        )
        return res
