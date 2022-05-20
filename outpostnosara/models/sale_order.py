from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_default_l10n_cr_edi_economic_activity(self):
        company = self.company_id or self.env.company
        return company._get_default_l10n_cr_edi_economic_activity()

    def domain_economic_activity(self):
        return [('id', 'in', self.env.company.l10n_cr_edi_economic_activity_ids.ids)]

    l10n_cr_edi_economic_activity_id = fields.Many2one(
        'l10n.cr.account.invoice.economic.activity',
        help='Economic activity whicih corresponds to electronic document. Required', string='Economic Activity',
        default=_get_default_l10n_cr_edi_economic_activity, domain=lambda self: self.domain_economic_activity())

    def _prepare_invoice(self):
        """Set economic activity by default if assigned in sale order.
        """
        invoice_vals = super()._prepare_invoice()
        if self.l10n_cr_edi_economic_activity_id:
            invoice_vals.update({
                'l10n_cr_edi_economic_activity_id': self.l10n_cr_edi_economic_activity_id
            })
        return invoice_vals

    def _prepare_subscription_data(self, template):
        values = super()._prepare_subscription_data(template)
        values.update({
            'room_type_id': template.room_type_id.id,
        })
        return values
