# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ReservationType(models.Model):
    _name = 'pms.reservation.type'
    _description = 'Reservation Type'

    name = fields.Char(help='Reservation Type')
    code = fields.Char(size=4)
    time_type = fields.Selection(
        selection=[
            ('daily', "Daily"),
            ('hourly', "Hourly"),
        ],
        help="Type of time of the reservation, in case of hourly it will compute prices based on reserved hours.")


class RoomTypeLines(models.Model):
    _name = 'pms.room.type.lines'
    _description = 'Reservation Type'

    room_type_id = fields.Many2one(
        'pms.room.type',
        help="Room Type.",
    )
    reservation_type_id = fields.Many2one(
        'pms.reservation.type',
        help="Reservation Type.",
        required=True,
    )
    price = fields.Float(required=True, digits='Product Price', default=0.0)
    name = fields.Char(related='reservation_type_id.name')
    code = fields.Char(related='reservation_type_id.code', store=True)


class PmsRoomType(models.Model):
    _inherit = 'pms.room.type'

    type_lines_ids = fields.One2many('pms.room.type.lines', 'room_type_id', string="Custom Values", copy=True)
    # We can't use active because active remove it in backend too
    website_published = fields.Boolean(
        default=True, help="Set active to false to hide in reservation page without removing it.")
    show_harmony = fields.Boolean(
        help="Set active to show this room for harmony users.")
