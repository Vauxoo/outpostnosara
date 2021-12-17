from odoo import fields, models


class PmsFolio(models.Model):
    _inherit = 'pms.folio'

    subscription_id = fields.Many2one('sale.subscription', string="Subscription")
