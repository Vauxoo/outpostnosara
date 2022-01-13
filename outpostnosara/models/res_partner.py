from odoo import fields, models
from odoo.addons.website.models import ir_http


class ResPartner(models.Model):
    _inherit = "res.partner"

    last_website_invoice_id = fields.Many2one('account.move',
                                              compute='_compute_last_website_invoice_id',
                                              string='Last Online Invoice')
    is_harmony = fields.Boolean()
    pin = fields.Char(string='PIN', size=8, help="PIN code for the door locks.")

    def _compute_last_website_invoice_id(self):
        account_move = self.env['account.move']
        for partner in self:
            is_public = any(u._is_public() for u in partner.with_context(active_test=False).user_ids)
            website = ir_http.get_request_website()
            reservation = website.get_reservation('reservation_id', invoice_create=True) if website else False
            if website and not is_public and reservation:
                folio = reservation.folio_id
                invoices = folio.move_ids.filtered(lambda i: i.website_id.id == website.id and i.state == 'draft')
                partner.last_website_invoice_id = invoices[:1]
            else:
                partner.last_website_invoice_id = account_move

    def toggle_is_harmony(self):
        for record in self:
            record.is_harmony = not record.is_harmony
