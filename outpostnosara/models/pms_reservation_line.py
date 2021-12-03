from datetime import datetime
import math

from odoo import api, models


class PmsReservationLine(models.Model):
    _inherit = 'pms.reservation.line'

    def get_reservation_availability(self, room_id, reservation_type_id, start_date, **data):
        # NOTE: Add when MR#6 is merged ('reservation_type_id', '=', int(reservation_type_id)),
        domain = [
            ('room_id', '=', int(room_id)),
            ('state', 'in', ['confirm', 'onboard', 'arrival_delayed']),
        ]
        if data.get('end_date'):
            domain += [
                ('date', '>=', start_date),
                ('date', '<=', data.get('end_date')),
            ]
        else:
            domain += [('date', '=', start_date)]

        return self.search(domain)

    @api.depends(
        "reservation_id", "reservation_id.room_type_id", "reservation_id.reservation_type",
        "reservation_id.pms_property_id", "reservation_id.type_id",
        "reservation_id.arrival_hour", "reservation_id.departure_hour")
    def _compute_price(self):
        res = super()._compute_price()
        for line in self.filtered(lambda res_l: res_l.reservation_id.type_id):
            reservation = line.reservation_id
            price = reservation.type_price
            if reservation.type_id.reservation_type_id.time_type == 'hourly':
                start_hour = datetime.strptime(reservation.arrival_hour, "%H:%M")
                end_hour = datetime.strptime(reservation.departure_hour, "%H:%M")
                hours = math.ceil((end_hour - start_hour).seconds / 3600)
                price = price * hours
            line.price = price
        return res
