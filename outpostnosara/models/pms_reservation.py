import datetime
import string
import random

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import const_eval

ARRIVAL_FORMAT = "%I:%M %p"


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
    pin = fields.Char(string='PIN', size=8, index=True, readonly=True, help="PIN code for the door locks.")
    pin_state = fields.Selection(
        selection=[
            ('active', "Active"),
            ('inactive', "Inactive"),
        ],
        string='PIN State', default='inactive',
        help="Indicates if the PIN code is active in the door locks for this reservation.")
    state = fields.Selection(selection_add=[('in_payment', 'Waiting for payment')])
    arrival_hour_formatted = fields.Char(help="AM/PM format of the arrival hour",
                                         store=True,
                                         compute="_compute_arrival_hour_formatted")
    departure_hour_formatted = fields.Char(help="AM/PM format of the departure hour",
                                           store=True,
                                           compute="_compute_departure_hour_formatted")

    def set_pin(self):
        for rec in self:
            if rec.pin:
                continue
            subscription = rec.folio_id.subscription_id
            if subscription and not subscription.partner_id.is_harmony and subscription.pin:
                rec.pin = rec.folio_id.subscription_id.pin
                continue
            pin = ''
            duplicated = True
            while duplicated:
                pin = ''.join((random.choice(string.digits) for x in range(8)))
                domain = [('pin', '=', pin)]
                duplicated = rec.search(domain, limit=1) or rec.env['sale.subscription'].search(domain, limit=1)
            rec.pin = pin

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not vals.get('pin'):
            record.set_pin()
        return record

    @api.depends("arrival_hour")
    def _compute_arrival_hour_formatted(self):
        for res in self:
            arrival_datetime = datetime.datetime.strptime(res.arrival_hour, '%H:%M')
            arrival = arrival_datetime.strftime(ARRIVAL_FORMAT) if arrival_datetime else False
            res.arrival_hour_formatted = arrival

    @api.depends("departure_hour")
    def _compute_departure_hour_formatted(self):
        for res in self:
            departure_datetime = datetime.datetime.strptime(res.departure_hour, '%H:%M')
            departure = departure_datetime.strftime(ARRIVAL_FORMAT) if departure_datetime else False
            res.departure_hour_formatted = departure

    def confirm(self):
        response = super().confirm()
        if response:
            message_post = self.env.context.get('message_post')
            values = self.env.context.get('values')
            guest_name = values.get('guest_name') if values else False
            guest_email = values.get('guest_email') if values else False
            template = self.env.ref('pms.confirmed_reservation_email', raise_if_not_found=False)
            for record in self:
                if template:
                    partner_id = record.partner_id.id
                    property_email = self.pms_property_id.partner_id.email
                    emails = ','.join(email for email in [property_email, record.email, guest_email] if email)
                    email_values = {'email_to': emails}
                    if partner_id:
                        email_values.update({'recipient_ids': [(4, partner_id)]})
                    template.sudo().with_context(guest_name=guest_name).send_mail(
                        record.id, email_values=email_values, force_send=True)
                if message_post:
                    msg_body = _("A Reservation has been confirmed by a Harmony User.\n")
                    if guest_name:
                        msg_name = _("The reservation is for %s") % (guest_name)
                        msg_body = "%s %s" % (msg_body, msg_name)
                    if guest_email:
                        msg_email = _("with the email %s") % (guest_email)
                        msg_body = "%s %s" % (msg_body, msg_email)
                    record.message_post(body=msg_body)
        return response

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
            arrival_hour = reservation.arrival_hour or '00:00'
            reservation._check_arrival_hour()
            checkin_time = datetime.datetime.strptime(arrival_hour, "%H:%M").time()
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
            departure_hour = reservation.departure_hour or '00:00'
            reservation._check_departure_hour()
            checkout_time = datetime.datetime.strptime(departure_hour, "%H:%M").time()
            checkout_datetime = datetime.datetime.combine(
                reservation.checkout, checkout_time
            )
            reservation.checkout_datetime = (
                reservation.pms_property_id.date_property_timezone(checkout_datetime)
            )
            reservation.check_in_out_dates()

    @api.depends("checkin", "checkout", "room_type_id")
    def _compute_reservation_line_ids(self):
        """Overwritten this function in order to change how reservation lines
        are created, now they are created each by day since checkin date to
        checkout date including the checkout date"""
        for reservation in self:
            cmds = []
            if reservation.checkout and reservation.checkin:
                # Here the main change. we are adding one more day
                days_diff = (reservation.checkout - reservation.checkin).days + 1
                for i in range(0, days_diff):
                    idate = reservation.checkin + datetime.timedelta(days=i)
                    old_line = reservation.reservation_line_ids.filtered(lambda r: r.date == idate)
                    if not old_line:
                        cmds.append((0, False, {"date": idate}))
                reservation.reservation_line_ids -= (
                    # Here other change, we include the checkout date, before the domains was like
                    # date >= checkout, now like following
                    reservation.reservation_line_ids.filtered_domain(
                        [
                            "|",
                            ("date", ">", reservation.checkout),
                            ("date", "<", reservation.checkin),
                        ]
                    )
                )
                reservation.reservation_line_ids = cmds
            else:
                if not reservation.reservation_line_ids:
                    reservation.reservation_line_ids = False
            reservation.check_in_out_dates()

    @api.depends("reservation_line_ids", "checkin")
    def _compute_checkout(self):
        """Overwritten this method in order to avoid increase checkout date when reservation lines changed"""
        for record in self:
            if record.reservation_line_ids:
                # Here the main change. we are avoiding add one more day
                checkout_line_date = max(record.reservation_line_ids.mapped("date"))
                # check if the checkout was created directly as reservation_line_id:
                if checkout_line_date != record.checkout:
                    record.checkout = checkout_line_date
            # default checkout if checkin is set
            elif record.checkin and not record.checkout:
                if len(record.folio_id.reservation_ids) > 1:
                    record.checkin = record.folio_id.reservation_ids[0].checkout
                else:
                    # Here the main change. we are avoiding add one more day
                    record.checkout = record.checkin
            elif not record.checkout:
                record.checkout = False
            # date checking
            record.check_in_out_dates()

    @api.model
    def auto_departure_delayed(self):
        res = super().auto_departure_delayed()
        delay = const_eval(self.env['ir.config_parameter'].sudo().get_param(
            'outpostnosara.delay_checkin_reserve_lock', 1))
        now = fields.Datetime.now() + datetime.timedelta(minutes=delay)

        reservations = self.env["pms.reservation"].search([
            ("state", "in", ("onboard",)),
            ("checkout_datetime", "<=", now),
            ("pin_state", "=", "active"),
        ])
        for reservation in reservations:
            reservation.preferred_room_id._clear_lock(reservation.pin)
            reservation.pin_state = 'inactive'
        return res

    @api.model
    def auto_arrival_delayed(self):
        res = super().auto_arrival_delayed()
        delay = const_eval(self.env['ir.config_parameter'].sudo().get_param(
            'outpostnosara.delay_checkout_reserve_lock', 1))
        now = fields.Datetime.now() + datetime.timedelta(minutes=delay)

        reservations = self.env["pms.reservation"].search([
            ("state", "in", ("draft", "confirm")),
            ("checkin_datetime", "<=", now),
            ("pin_state", "=", "inactive"),
        ])
        for reservation in reservations:
            reservation.preferred_room_id._set_lock(reservation.pin)
            reservation.pin_state = 'active'
        return res

    @api.depends(
        "reservation_line_ids.date", "reservation_line_ids.room_id",
        "reservation_line_ids.occupies_availability", "preferred_room_id",
        "pricelist_id", "pms_property_id",
    )
    def _compute_allowed_room_ids(self):
        """OVERWRITTEN"""
        for reservation in self:
            if not (reservation.checkin and reservation.checkout):
                reservation.allowed_room_ids = False
                continue

            if reservation.overbooking or reservation.state == "cancel":
                reservation.allowed_room_ids = self.env["pms.room"].search([("active", "=", True)])
                return
            # Here is the change, propagate reservation checkin and checkout with datetimes
            pms_property = reservation.pms_property_id.with_context(
                checkin=reservation.checkin_datetime,
                checkout=reservation.checkout_datetime,
                room_type_id=reservation.room_type_id.id or False,  # Force to uses always a room type. # noqa
                current_lines=reservation.reservation_line_ids.ids,
                pricelist_id=reservation.pricelist_id.id,
            )
            reservation.allowed_room_ids = pms_property.free_room_ids

    def open_reservation_wizard(self):
        """OVERWRITTEN"""
        # Here is the change, propagate reservation checkin and checkout with datetimes
        pms_property = self.pms_property_id.with_context(
            checkin=self.checkin_datetime,
            checkout=self.checkout_datetime,
            current_lines=self.reservation_line_ids.ids,
            pricelist_id=self.pricelist_id.id,
        )
        return {
            "view_type": "form",
            "view_mode": "form",
            "name": "Unify the reservation",
            "res_model": "pms.reservation.split.join.swap.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": {
                "rooms_available": pms_property.free_room_ids.ids,
            },
        }
