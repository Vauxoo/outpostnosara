from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _default_property_id(self):
        return self.env.ref('pms.main_pms_property', False)

    pms_property_id = fields.Many2one(default=_default_property_id)
    pms_property_ids = fields.Many2many(default=_default_property_id)
