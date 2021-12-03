# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models



class ReservationType(models.Model):
    _name = 'pms.reservation.type'
    _description = 'Reservation Type'

    name = fields.Char(string='Name', help='Reservation Type')
    code = fields.Char(size=4)

class RoomTypeLines(models.Model):
    _name = 'pms.room.type.lines'
    _description = 'Reservation Type'

    room_type_id = fields.Many2one(
        'pms.room.type',
        string="Room Type",
        help="Room Type.",
    )
    reservation_type_id = fields.Many2one(
        'pms.reservation.type',
        string="Reservation Type",
        help="Reservation Type.",
    )
    price = fields.Float('Price', required=True, digits='Product Price', default=0.0)


class PmsRoomType(models.Model):
    _inherit = 'pms.room.type'

    type_lines_ids = fields.One2many('pms.room.type.lines', 'room_type_id', string="Custom Values", copy=True)
