from datetime import datetime, timedelta
import math

from odoo import _, api, models, fields
from odoo.osv import expression

from odoo.exceptions import ValidationError


class PmsReservationLine(models.Model):
    _inherit = 'pms.reservation.line'

    checkin_datetime = fields.Datetime(
        string="Date Start",
        store=True,
        compute="_compute_out_dates",
        help="The date start of the reservation line, will be used to search if this room is available",
    )

    checkout_datetime = fields.Datetime(
        string="Date End",
        store=True,
        compute="_compute_out_dates",
        help="The date end of the reservation line, will be used to search if this room is available",
    )

    # OVERWRITING the constrain, use an api.constrains to be available to add more business logic
    _sql_constraints = [("rule_availability", "Check(1=1)", "Room Occupied")]

    @api.constrains('checkin_datetime', 'checkout_datetime', 'occupies_availability')
    def _unique_reservation_dates_for_room(self):
        for record in self.filtered(lambda r: r.occupies_availability):
            domain = [
                ("room_id", "in", record.room_id.ids),
                ("occupies_availability", "=", True),
                ("id", "!=", record.id),
            ]
            domain = self.get_datetime_domain(record.checkin_datetime, record.checkout_datetime, domain)
            equivalent_lines = self.search(domain)
            if equivalent_lines:
                raise ValidationError(_("Room Occupied"))

    @api.depends('date', 'reservation_id', 'reservation_id.checkin_datetime', 'reservation_id.checkout_datetime')
    def _compute_out_dates(self):
        for record in self:
            if not (record.reservation_id and record.reservation_id.checkin and record.reservation_id.checkout):
                record.checkin_datetime = False
                record.checkout_datetime = False
                continue
            date = record.date
            # Get clean datetime to get the difference, and be available to convert the datetime directly
            checkin = datetime.combine(record.reservation_id.checkin, datetime.min.time())
            hours_difference = record.reservation_id.checkin_datetime - checkin
            record.checkin_datetime = datetime.combine(date, datetime.min.time()) + hours_difference
            # Same but with date end
            checkout = datetime.combine(record.reservation_id.checkout, datetime.min.time())
            hours_difference = record.reservation_id.checkout_datetime - checkout
            record.checkout_datetime = datetime.combine(date, datetime.min.time()) + hours_difference

    @api.model
    def get_datetime_domain(self, checkin, checkout, domain=False, occupied_room_ids=False):
        """Get a valid domain which will get the four cases where a reservation period can collapse with others"""
        # Be available to reserve a room collapsing checkout hours
        # For example: 6:00 Am to 12:00 pm and then other with 12:00pm to 6pm
        checkout = checkout - timedelta(seconds=1)

        domain = domain or []
        if occupied_room_ids:
            domain += [('id', 'not in', occupied_room_ids)]

        dates_part = expression.OR([
            # Case 1:
            [("checkin_datetime", "<=", checkin),
             ("checkin_datetime", "<=", checkout),
             ("checkout_datetime", ">=", checkin),
             ("checkout_datetime", "<=", checkout)],
            # Case 2:
            [("checkin_datetime", ">=", checkin),
             ("checkin_datetime", "<=", checkout),
             ("checkout_datetime", ">=", checkin),
             ("checkout_datetime", "<=", checkout)],
            # Case 3:
            [("checkin_datetime", "<=", checkin),
             ("checkin_datetime", "<=", checkout),
             ("checkout_datetime", ">=", checkin),
             ("checkout_datetime", ">=", checkout)],
            # Case 4:
            [("checkin_datetime", ">=", checkin),
             ("checkin_datetime", "<=", checkout),
             ("checkout_datetime", ">=", checkin),
             ("checkout_datetime", ">=", checkout)],
        ])
        return expression.AND([domain, dates_part])

    def get_reservation_availability(self, room_id, start_date=False, end_date=False, date=False, **data):
        """Get the daily reservations for day."""

        # _sql_constraints_rule_availability in /pms/models/pms_reservation_line.py#L116
        domain = [
            ('room_id', '=', int(room_id)),
            ('occupies_availability', '=', True),
        ]

        if self:
            domain += [('id', 'not in', self.ids)]
        if start_date:
            domain += [('date', '>=', start_date)]
        if end_date:
            domain += [('date', '<=', end_date)]
        if date:
            domain += [('date', '=', date)]
        if self._context.get('code'):
            domain += [('reservation_id.type_id.code', '=', self._context.get('code'))]

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

    @api.depends("reservation_id.room_type_id", "reservation_id.preferred_room_id")
    def _compute_room_id(self):
        """OVERWRITTEN"""
        for line in self.filtered("reservation_id.room_type_id").sorted(key=lambda r: (r.reservation_id, r.date)):
            reservation = line.reservation_id
            if not ((
                reservation.preferred_room_id and reservation.preferred_room_id != line.room_id
            ) or (
                (reservation.preferred_room_id or reservation.room_type_id) and not line.room_id
            )):
                continue

            free_room_select = bool(reservation.preferred_room_id)

            # we get the rooms available for the entire stay
            # Here is the change, propagate reservation checkin and checkout with datetimes
            pms_property = line.pms_property_id.with_context(
                checkin=reservation.checkin_datetime,
                checkout=reservation.checkout_datetime,
                room_type_id=reservation.room_type_id.id if not free_room_select else False,
                arrival_hour=reservation.arrival_hour,
                departure_hour=reservation.departure_hour,
                annual_reservation=reservation.annual_reservation,
                current_lines=reservation.reservation_line_ids.ids,
                pricelist_id=reservation.pricelist_id.id,
            )
            rooms_available = pms_property.free_room_ids

            # Check if the room assigment is manual or automatic to set the
            # to_assign value on reservation
            manual_assigned = (free_room_select and reservation.preferred_room_id.id
                               not in reservation.reservation_line_ids.room_id.ids)
            # if there is availability for the entire stay
            if rooms_available:
                # Avoid that reservation._compute_splitted set the
                # reservation like splitted in intermediate calculations
                reservation = reservation.with_context(not_split=True)
                # if the reservation has a preferred room
                if reservation.preferred_room_id:
                    # if the preferred room is available
                    if reservation.preferred_room_id in rooms_available:
                        line.room_id = reservation.preferred_room_id
                        reservation.to_assign = (False if manual_assigned else reservation.to_assign)
                        continue

                    # if the preferred room is NOT available
                    if self.env.context.get("force_overbooking"):
                        reservation.overbooking = True
                        line.room_id = reservation.preferred_room_id
                        continue

                    raise ValidationError(
                        _("%s: No room available in %s <-> %s.")
                        % (
                            reservation.preferred_room_id.name,
                            reservation.checkin,
                            reservation.checkout,
                        )
                    )
                # otherwise we assign the first of those
                # available for the entire stay
                line.room_id = rooms_available[0]
                continue
            # check that the reservation cannot be allocated even by dividing it
            # Here is the change, propagate reservation checkin and checkout with datetimes
            if not self.env["pms.property"].splitted_availability(
                checkin=reservation.checkin_datetime,
                checkout=reservation.checkout_datetime,
                room_type_id=reservation.room_type_id.id,
                current_lines=line._origin.reservation_id.reservation_line_ids.ids,
                pricelist=reservation.pricelist_id,
                pms_property_id=line.pms_property_id.id,
            ):
                if not self.env.context.get("force_overbooking"):
                    raise ValidationError(_("%s: No room type available") % (reservation.room_type_id.name))
                reservation.overbooking = True
                line.room_id = reservation.room_type_id.room_ids[0]
                continue
            # the reservation can be allocated into several rooms
            self._allocate_reservation_several_rooms(reservation, line)

    def _allocate_reservation_several_rooms(self, reservation, line):
        rooms_ranking = {}
        reservation_line = self.env["pms.reservation.line"]
        # we go through the rooms of the type
        for room in self.env["pms.room"].search(
            [
                ("room_type_id", "=", reservation.room_type_id.id),
                ("pms_property_id", "=", reservation.pms_property_id.id),
            ]
        ):
            # we iterate the dates from the date of the line to the checkout
            for date_iterator in [
                    line.date + timedelta(days=x) for x in range(0, (reservation.checkout - line.date).days)]:
                # if the room is already assigned for
                # a date we go to the next room
                search_domain = [
                    ("date", "=", date_iterator),
                    ("room_id", "=", room.id),
                    ("id", "not in", reservation.reservation_line_ids.ids),
                    ("occupies_availability", "=", True),
                ]
                if reservation_line.search(search_domain):
                    break
                # if the room is not assigned for a date we
                # add it to the ranking / update its ranking
                rooms_ranking[room.id] = (1 if room.id not in rooms_ranking else rooms_ranking[room.id] + 1)

        if rooms_ranking:
            # we get the best score in the ranking
            best = max(rooms_ranking.values())

            # we keep the rooms with the best ranking
            bests = {
                key: value
                for (key, value) in rooms_ranking.items()
                if value == best
            }

            room_id = list(bests.keys())[0]
            # if there is a tie in the rankings
            if len(bests) > 1:
                # we get the line from last night
                date_last_night = line.date + timedelta(days=-1)
                line_past_night = self.env["pms.reservation.line"].search([
                    ("date", "=", date_last_night),
                    ("reservation_id", "=", reservation.id)], limit=1)
                # if there is the night before and if the room
                # from the night before is in the ranking
                # if the room from the night before is not in the ranking or there is no night before,
                # at this point we set the room with the best ranking, no matter what it is
                if line_past_night and line_past_night.room_id.id in bests:
                    room_id = line_past_night.room_id.id
            line.room_id = room_id
