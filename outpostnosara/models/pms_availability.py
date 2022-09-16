import datetime

from odoo import api, models


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

        # Search by datetime
        diff_days = (checkout - checkin).days + 1
        # TODO: Check if it is possible to search in just one search, all in just one domain
        for day in range(0, diff_days):
            day_checkin = checkin + datetime.timedelta(days=day)
            day_checkout = checkout - datetime.timedelta(days=diff_days - 1) + datetime.timedelta(days=day)
            date_time_domain = room_lines.get_datetime_domain(day_checkin, day_checkout, domain, occupied_room_ids)
            occupied_room_ids.extend(room_lines.search(date_time_domain).mapped("room_id.id"))
        return occupied_room_ids
