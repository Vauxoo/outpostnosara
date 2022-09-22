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
        if subscription.stage_category == "progress":
            subscription.create_reservation()
        return subscription

    def write(self, vals):
        old_not_in_progress = self.filtered(lambda sub: sub.stage_category != "progress")
        result = super().write(vals)
        for subscription in old_not_in_progress.filtered(lambda sub: sub.stage_category == "progress"):
            subscription.create_reservation()
        return result

    def create_reservation(self):
        self.ensure_one()
        if not self.folio_ids:
            self.create_folio()
        reservation = self.env['pms.reservation']
        if not self.room_type_id:
            return reservation
        try:
            self.onchange_date_start()
            self.set_pin()
            with Form(reservation) as reservation_form:
                reservation_form.folio_id = self.folio_ids[0]
                reservation_form.partner_id = self.partner_id
                reservation_form.checkin = self.date_start
                if self.date:
                    reservation_form.checkout = self.date
                reservation_form.room_type_id = self.room_type_id
                reservation_form.annual_reservation = True
            reservation = reservation_form.save()
            reservation.reservation_line_ids.write({'price': 0})
        except BaseException as error:
            raise UserError(_('An error occurred during the creation of the reservation\n\n%s') % error)
        return reservation

    def create_folio(self):
        self.ensure_one()
        folio = self.env['pms.folio']
        try:
            with Form(folio) as folio_form:
                folio_form.partner_id = self.partner_id
                folio_form.subscription_id = self
            folio = folio_form.save()
        except BaseException as error:
            raise UserError(_('An error occurred during the creation of the folio\n\n%s') % error)
        return folio

    def set_pin(self):
        self.ensure_one()
        pin = ''
        duplicated = True
        while duplicated:
            pin = ''.join((random.choice(string.digits) for x in range(8)))
            domain = [('pin', '=', pin)]
            duplicated = self.search(domain, limit=1) or self.env['pms.reservation'].search(domain, limit=1)
        self.pin = pin

    def _get_default_l10n_cr_edi_economic_activity(self):
        company = self.company_id or self.env.company
        return company._get_default_l10n_cr_edi_economic_activity()

    def domain_economic_activity(self):
        return [('id', 'in', self.env.company.l10n_cr_edi_economic_activity_ids.ids)]

    l10n_cr_edi_economic_activity_id = fields.Many2one(
        'l10n.cr.account.invoice.economic.activity',
        help='Economic activity whicih corresponds to electronic document. Required', string='Economic Activity',
        default=_get_default_l10n_cr_edi_economic_activity, domain=lambda self: self.domain_economic_activity())

    def _prepare_invoice_data(self):
        vals = super()._prepare_invoice_data()
        if 'l10n_cr_edi_economic_activity_id' not in vals:
            vals.update({
                'l10n_cr_edi_economic_activity_id': self.l10n_cr_edi_economic_activity_id.id
            })
        return vals

    @api.onchange('template_id')
    def _onchange_subscription_template_id(self):
        for subscription in self:
            if not subscription.template_id:
                continue
            subscription.room_type_id = subscription.template_id.room_type_id
