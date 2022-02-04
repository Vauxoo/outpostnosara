# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import _, fields, http
from odoo.http import request
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.account_payment.controllers.payment import PaymentPortal
from odoo.addons.payment_credomatic.controllers.main import safe_int, FacBacController as Credomatic
from odoo.exceptions import ValidationError


class WebsiteOutpost(WebsiteSale):
    @http.route('/outpost/membership', type='http', auth="public", website=True)
    def membership(self, **post):
        """Show Membership Application Form."""
        pricelist = self._get_pricelist_context()[1]
        order = request.website.sale_get_order(force_create=True)
        render_values = self._get_shop_payment_values(order, **post)
        memberships = request.env['product.template'].with_context(pricelist=pricelist.id).search(
            [
                ('recurring_invoice', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence',
        )
        render_values['memberships'] = memberships
        render_values['pricelist'] = pricelist
        return request.render("outpostnosara.membership", render_values)

    @http.route('/outpost/reservation', type='http', auth="user", website=True)
    def reservation(self, **post):
        """Show Reservation Room Form."""
        partner = request.env.user.partner_id
        render_values = request.env['payment.acquirer']._get_available_payment_input(
            partner=partner, company=partner.company_id)
        # PMS Room Type Property(pms_room_type_property_rule)
        domain = [
            '&', '|',
            ('pms_property_ids', 'in', request.env.user.get_active_property_ids()),
            ('pms_property_ids', '=', False),
            ('website_published', '=', True)
        ]

        podcast_room = request.env.ref('outpost.podcast_studio_room_type', False)
        podcast_reservation_types = []
        exclude_room_type_ids = []

        if podcast_room and podcast_room.website_published:
            podcast_reservation_types = podcast_room.type_lines_ids.mapped('reservation_type_id').ids
            exclude_room_type_ids.append(podcast_room.id)

        if partner.is_harmony:
            domain = expression.AND([domain, [('show_harmony', '=', True)]])
        else:
            harmony_room = request.env.ref('outpost.harmony_office_room_type')
            exclude_room_type_ids.append(harmony_room.id)

        if exclude_room_type_ids:
            domain = expression.AND([domain, [('id', 'not in', exclude_room_type_ids)]])

        room_types = request.env['pms.room.type'].search(domain)
        render_values.update({
            'user': request.env.user,
            'room_types': room_types,
            'reservation_types': room_types[:1].type_lines_ids,
            'podcast_types': podcast_reservation_types,
        })

        return request.render("outpostnosara.reservation", render_values)

    @http.route('/outpost/reserved_date/<int:room_id>', type='json', auth="user", website=True)
    def reserved_date(self, room_id, **post):
        """Get reserved dates of a room."""
        return request.env['pms.reservation.line'].with_context(code='day').get_reservation_availability(
            room_id, start_date=fields.Date.today()
        ).mapped('date')

    @http.route('/outpost/types_availables/<model("pms.room.type"):room_type>', type='json', auth="user", website=True)
    def rooms_availables(self, room_type, **post):
        """Get reservation types_availables of a room kind."""
        return {'data': room_type.type_lines_ids.read(['id', 'name', 'code'])}

    def add_reservation_room(self, room_type, reservation_type_id, start_date, end_date, reservation_key, post):
        reservation = request.website.get_reservation(reservation_key)
        reservation_lines = reservation.reservation_line_ids
        values = {
            'type_id': reservation_type_id,
            'room_type_id': room_type.id,
            'checkin': start_date,
            'checkout': end_date,
            'adults': 1,
            'arrival_hour': reservation.pms_property_id.default_arrival_hour,
            'departure_hour': reservation.pms_property_id.default_departure_hour,
        }
        reservation.write({**values, **post})
        # preferred_room_id is autoselect by the room_type_id
        reservation.flush()
        room_name = 'Podcast Equipment' if reservation_key == 'podcast_reservation_id' else 'Room'

        if reservation_lines.get_reservation_availability(
            reservation.preferred_room_id.id, start_date=start_date, end_date=end_date
        ):
            raise ValidationError(_("%s Occupied") % room_name)
        if request.env.user.partner_id.is_harmony:
            reservation.reservation_line_ids.write({'price': 0})
        return reservation

    @http.route(
        '/outpost/validate_reservation/<model("pms.room.type"):room_type>/<int:reservation_type_id>',
        type='json', auth="user", website=True)
    def validate_reservation(self, room_type, reservation_type_id, start_date, end_date, **post):
        """Get rooms_availables of a room kind."""
        podcast_reservation = post.get('podcast')
        request.session['add_podcast'] = post.get('podcast')
        if podcast_reservation:
            del post['podcast']
            podcast_room_id = request.env.ref('outpost.podcast_studio_room_type')
            room_type_lines = request.env['pms.room.type.lines']
            type_lines = room_type_lines.browse(reservation_type_id)
            podcast_type_id = room_type_lines.search([('code', '=', type_lines.code),
                                                      ('room_type_id', '=', podcast_room_id.id)], limit=1)
            podcast_reservation = self.add_reservation_room(
                podcast_room_id, podcast_type_id, start_date, end_date, 'podcast_reservation_id', post)

        reservation = self.add_reservation_room(
            room_type, reservation_type_id, start_date, end_date, 'reservation_id', post)

        self.update_invoice(reservation, podcast_reservation)
        if podcast_reservation:
            reservation |= podcast_reservation
        return reservation.read(['id', 'price_room_services_set'])

    def update_invoice(self, reservation, podcast_reservation=None):
        """  Use this method to create an invoice or update the invoice lines
        for reservations in order to process the payment.

        The last_website_invoice_id values get the last invoice in the draft
        state related to the partner to avoid the creation of multiple draft
        invoices each time the user logs in to his account.
        """
        folio = reservation.folio_id
        lines_to_invoice = folio.sale_line_ids.filtered(lambda l: l.reservation_id.id == reservation.id)
        dict_lines = {}
        for line in lines_to_invoice:
            line.qty_to_invoice = 0 if line.display_type else reservation.nights
            dict_lines[line.id] = 0 if line.display_type else reservation.nights
        partner = request.env.user.partner_id
        invoice = partner.last_website_invoice_id
        if not invoice or invoice.state == 'post':
            invoice = folio._create_invoices(lines_to_invoice=dict_lines)
        else:
            lines = [(5, 0)]
            for line in lines_to_invoice:
                invoice_line_values = line._prepare_invoice_line(qty=line.qty_to_invoice)
                new_line = (0, False, invoice_line_values)
                lines.append(new_line)
            invoice.write({'invoice_line_ids': lines})
        if podcast_reservation:
            podcast_lines = podcast_reservation.folio_id.sale_line_ids.filtered(
                lambda l: l.reservation_id.id == podcast_reservation.id)
            lines = [(3, 0)]
            for line in podcast_lines:
                line.qty_to_invoice = 0 if line.display_type else podcast_reservation.nights
                invoice_line_values = line._prepare_invoice_line(qty=line.qty_to_invoice)
                new_line = (0, False, invoice_line_values)
                lines.append(new_line)
            invoice.write({'invoice_line_ids': lines})
        request.session['last_invoice_id'] = invoice.id
        invoice.write({'website_id': request.website.id})


class OutpostNosaraController(http.Controller):

    @http.route('/membership/apply', type='http', auth="public", website=True)
    def membership_contact(self, **post):
        ext_ids = [
            'outpostnosara.membership_type_office',
            'outpostnosara.membership_type_suite',
            'outpostnosara.membership_type_annual',
            'outpostnosara.membership_type_desk',
        ]
        crm_tags = request.env['crm.tag'].sudo()
        for ext_id in ext_ids:
            tag = crm_tags.env.ref(ext_id, raise_if_not_found=False)
            if tag:
                crm_tags |= tag
        subject_name = _("Membership Application")
        values = {
            'membership_tags': crm_tags,
            'membership_subject': subject_name,
        }
        return request.render("outpostnosara.membership_contact", values)

    @http.route('/outpost/pay/invoice', type='http', auth="user", website=True)
    def redirect_pay_invoice(self, **post):
        if request.session.get('last_invoice_id'):
            invoice_id = request.session.get('last_invoice_id')
            portal_payment = PaymentPortal()
            acquirer_id = post.get('acquirer_id')
            acquirer = request.env['payment.acquirer'].browse(int(acquirer_id))
            if acquirer.payment_flow == 's2s':
                return portal_payment.invoice_pay_token(invoice_id, **post)
            return portal_payment.invoice_pay_form(acquirer_id, invoice_id, **post)
        return request.redirect('/outpost/reservation')

    def confirm_website_reservation(self, reservation, values=None):
        reservation_values = {'preconfirm': True, 'overbooking': False}
        message = values.get('message_post') if values else False
        if request.session.get('add_podcast'):
            reservation_obj = request.env['pms.reservation'].with_company(request.website.company_id.id).sudo()
            reservation |= reservation_obj.browse(request.session.get('podcast_reservation_id'))
        reservation.write(reservation_values)
        reservation.with_context(values=values, message_post=message).confirm()

    @http.route('/outpost/reservation/confirmation', type='http', auth="user", website=True)
    def reservation_confirmation(self, **post):
        if not request.session.get('last_invoice_id'):
            return request.redirect('/outpost/reservation')
        invoice_id = request.session.get('last_invoice_id')
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        reservation_obj = request.env['pms.reservation'].with_company(request.website.company_id.id).sudo()
        reservation = reservation_obj.browse(request.session.get('reservation_id'))
        values = {}
        error = transaction = False
        if not reservation.preconfirm and not request.env.user.partner_id.is_harmony:
            transaction = invoice.get_portal_last_transaction()
            if transaction.state == 'done':
                self.confirm_website_reservation(reservation)
            if transaction.state == 'error':
                error = transaction.state_message
        values.update({
            'reservation': reservation,
            'invoice': invoice,
            'transaction': transaction,
            'error': error,
        })
        return request.render("outpostnosara.reservation_confirmation", values)

    @http.route('/outpost/create_harmony_reservation', type='json', methods=['POST'], auth="user", website=True)
    def create_harmony_reservation(self, **post):
        """ This method allows the confirmation of the reservation for harmony users
            that do not need to use a payment method for their reservations cause the
            cost for reserving a room is 0.

            We retrieve the last invoice created and we posted it once the reservation
            is confirmed. """

        reservation_obj = request.env['pms.reservation'].with_company(request.website.company_id.id).sudo()
        reservation = reservation_obj.browse(request.session.get('reservation_id'))
        post['message_post'] = True
        self.confirm_website_reservation(reservation, values=post)
        invoice = request.env['account.move'].sudo().browse(request.session.get('last_invoice_id'))
        if invoice.state == 'draft':
            invoice.action_post()
        return True


class CredomaticOutpost(Credomatic):

    def credomatic_get_related_document(self, data):
        if data.get('order_id'):
            return request.env['sale.order'].browse(safe_int(data.get('order_id')))
        if data.get('invoice_id'):
            return request.env['account.move'].browse(safe_int(data.get('invoice_id')))
        if request.session.get('last_invoice_id'):
            invoice_id = request.session.get('last_invoice_id')
            return request.env['account.move'].browse(safe_int(invoice_id))
        return request.website.sale_get_order()
