from odoo import models


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
