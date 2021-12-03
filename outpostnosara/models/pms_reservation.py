import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PmsReservation(models.Model):
    _inherit = 'pms.reservation'

    type_id = fields.Many2one(
        'pms.room.type.lines', string="Reservation Price Type", domain="[('room_type_id', '=', room_type_id)]")
    type_price = fields.Float(related='type_id.price')

    checkin_datetime = fields.Datetime(
        store=True,
    )
    checkout_datetime = fields.Datetime(
        store=True,
    )

    def check_in_out_dates(self):
        """Overwritten this method since outpost needs to register reservations not only for days but hours.
        Now this constraint is performed with exact checkin/checkout info,
        taking into account datetime portion that comes from arrival/departure hour fields.
        """
        for record in self:
            if (record.checkin_datetime and record.checkout_datetime
                    and record.checkin_datetime >= record.checkout_datetime):
                raise UserError(
                    _("Room line Exact Check In Datetime Should be less than the Exact Check Out Datetime!"))

    @api.depends("checkin", "arrival_hour")
    def _compute_checkin_datetime(self):
        """Overwritten in order to avoid error when doing the datetime combine
        since it does not expect boolean values.
        Also, included the call to check_in_out_dates to validate checkin/checkout exact times
        """
        for reservation in self:
            # Here the main change
            if not reservation.checkin:
                return
            checkin_hour = int(reservation.arrival_hour[0:2])
            checkin_minut = int(reservation.arrival_hour[3:5])
            checkin_time = datetime.time(checkin_hour, checkin_minut)
            checkin_datetime = datetime.datetime.combine(
                reservation.checkin, checkin_time
            )
            reservation.checkin_datetime = (
                reservation.pms_property_id.date_property_timezone(checkin_datetime)
            )
            reservation.check_in_out_dates()

    @api.depends("checkout", "departure_hour")
    def _compute_checkout_datetime(self):
        """Overwritten in order to avoid error when doing the datetime combine
        since it does not expect boolean values.
        Also, included the call to check_in_out_dates to validate checkin/checkout exact times
        """
        for reservation in self:
            # Here the main change
            if not reservation.checkout:
                return
            checkout_hour = int(reservation.departure_hour[0:2])
            checkout_minut = int(reservation.departure_hour[3:5])
            checkout_time = datetime.time(checkout_hour, checkout_minut)
            checkout_datetime = datetime.datetime.combine(
                reservation.checkout, checkout_time
            )
            reservation.checkout_datetime = (
                reservation.pms_property_id.date_property_timezone(checkout_datetime)
            )
            reservation.check_in_out_dates()
