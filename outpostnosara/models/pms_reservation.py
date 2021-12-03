from odoo import fields, models


class PmsReservation(models.Model):
    _inherit = 'pms.reservation'

    type_id = fields.Many2one(
        'pms.room.type.lines', string="Reservation Price Type", domain="[('room_type_id', '=', room_type_id)]")
    type_price = fields.Float(related='type_id.price')
