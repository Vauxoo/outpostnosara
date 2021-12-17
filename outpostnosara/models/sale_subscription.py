import string
import random


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form


class SaleSubscriptionTemplate(models.Model):
    _inherit = 'sale.subscription.template'

    room_type_id = fields.Many2one('pms.room.type')


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    room_type_id = fields.Many2one(
        'pms.room.type', help="If set will try to create a reservation when the subscription starts.")
    folio_ids = fields.One2many(
        'pms.folio', 'subscription_id', help="PMS Folio related to this subscription.")

    pin = fields.Char(string='PIN', size=8, index=True, help="PIN code for the door locks.")

    @api.model
    def create(self, vals):
        subscription = super().create(vals)
        if subscription.room_type_id and not subscription.folio_ids and subscription.stage_category == "progress":
            subscription.create_reservation()
        return subscription

    def write(self, vals):
        old_not_in_progress = self.filtered(lambda sub: sub.stage_category != "progress")
        result = super().write(vals)
        for subscription in old_not_in_progress.filtered(
                lambda sub: sub.stage_category == "progress" and sub.room_type_id and not sub.folio_ids):
            subscription.create_reservation()
        return result

    def create_reservation(self):
        self.ensure_one()
        reservation = self.env['pms.reservation']
        try:
            self.onchange_date_start()
            self.set_pin()
            with Form(reservation) as reservation_form:
                reservation_form.partner_id = self.partner_id
                reservation_form.checkin = self.date_start
                if self.date:
                    reservation_form.checkout = self.date
                reservation_form.room_type_id = self.room_type_id
            reservation = reservation_form.save()
            reservation.reservation_line_ids.write({'price': 0})
        except BaseException as error:
            raise UserError(_('An error occurred during the creation of the reservation\n\n%s') % error)
        return reservation

    def set_pin(self):
        self.ensure_one()
        pin = ''
        duplicated = True
        while duplicated:
            pin = ''.join((random.choice(string.digits) for x in range(8)))
            duplicated = self.search([('pin', '=', pin)], limit=1)
        self.pin = pin
