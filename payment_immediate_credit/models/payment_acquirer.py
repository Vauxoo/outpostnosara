# Copyright 2022 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).

from odoo import fields, models


class AcquirerImmediateCredit(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[
            ('immediate_credit', 'Immediate Credit')],
        ondelete={'immediate_credit': 'set default'})

    def immediate_credit_get_form_action_url(self):
        return '/payment/immediate_credit/feedback'
