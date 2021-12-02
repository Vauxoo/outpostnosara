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
    reservation_id = fields.Many2one(
        'pms.reservation', help="PMS Reservation related to this subscription."
    )
    folio_id = fields.Many2one(
        'pms.folio', related='reservation_id.folio_id', store=True, help="PMS Folio related to this subscription.")

    @api.model
    def create(self, vals):
        subscription = super().create(vals)
        if subscription.room_type_id and not subscription.folio_id and subscription.stage_category == "progress":
            subscription.create_reservation()
        return subscription

    def write(self, vals):
        old_not_in_progress = self.filtered(lambda sub: sub.stage_category != "progress")
        result = super().write(vals)
        for subscription in old_not_in_progress.filtered(
                lambda sub: sub.stage_category == "progress" and sub.room_type_id and not sub.folio_id):
            subscription.create_reservation()
        return result

    def create_reservation(self):
        self.ensure_one()
        if self.reservation_id:
            return self.reservation_id
        reservation = self.env['pms.reservation']
        try:
            self.onchange_date_start()
            with Form(reservation) as reservation_form:
                reservation_form.partner_id = self.partner_id
                reservation_form.checkin = self.date_start
                if self.date:
                    reservation_form.checkout = self.date
                reservation_form.room_type_id = self.room_type_id
            reservation = reservation_form.save()
            reservation.reservation_line_ids.write({'price': 0})
            self.write({
                'reservation_id': reservation.id,
            })
        except BaseException as error:
            raise UserError(_('An error occurred during the creation of the reservation\n\n%s') % error)
        return reservation
