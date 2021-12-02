from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_subscription_data(self, template):
        values = super()._prepare_subscription_data(template)
        values.update({
            'room_type_id': template.room_type_id.id,
        })
        return values
