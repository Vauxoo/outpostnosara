import datetime

from odoo import api, models
from odoo.osv import expression


class PmsAvailability(models.Model):
    _inherit = "pms.availability"

    @api.model
    def get_rooms_not_avail(self, checkin, checkout, room_ids, pms_property_id, current_lines=False):
        """OVERWRITTEN"""
        room_lines = self.env["pms.reservation.line"]
        occupied_room_ids = []
        # TODO: In the regular PMS code: here are considered the parent_id and child_ids Rooms. For Outpost it is not
        # necessary, but implement it, if it is needed in the future.
        # The parameter room_ids is used by parent/child, was not deleted from the method to avoid inherence problems

        domain = [
            ("room_id", "in", room_ids),
            ("pms_property_id", "=", pms_property_id),
            ("occupies_availability", "=", True),
            ("id", "not in", current_lines if current_lines else []),
        ]

        # By default, give priority to those rooms that are not being used this day
        if not self._context.get('use_datetimes'):
            date_domain = [("date", ">=", checkin), ("date", "<=", checkout)] + domain
            occupied_room_ids.extend(room_lines.search(date_domain).mapped("room_id.id"))
            return occupied_room_ids

        arrival_hour = self._context.get("arrival_hour", False)
        departure_hour = self._context.get("departure_hour", False)
        room_type_id = self._context.get("room_type_id", False)
        annual_reservation = self._context.get("annual_reservation", False)

        reserved_domain = [
            ("pms_property_id", "=", pms_property_id),
            ("room_type_id", "=", room_type_id),
            ("state", "!=", "cancel"),
        ]
        if isinstance(checkin, datetime.datetime):
            checkin = checkin.date()
            checkout = checkout.date()
        dates_part = expression.OR([
            [("checkin", "<=", checkin), ("checkout", ">=", checkin)],
            [("checkin", "<=", checkout), ("checkout", ">=", checkout)],
        ])
        times_part = []
        if not annual_reservation:
            times_part = expression.OR([
                [("annual_reservation", "=", True)],
                [("arrival_hour", "<=", departure_hour), ("departure_hour", ">=", departure_hour)],
                [("arrival_hour", "<=", arrival_hour), ("departure_hour", ">=", arrival_hour)],
            ])
        reserved_domain = expression.AND([reserved_domain, dates_part, times_part])

        occupied_room_ids.extend(self.env['pms.reservation'].search(reserved_domain).mapped('preferred_room_id.id'))

        return occupied_room_ids
