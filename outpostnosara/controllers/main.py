# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
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
        order = request.website.sale_get_order(force_create=True)
        room_types = request.env['pms.room.type'].search([])
        render_values = self._get_shop_payment_values(order, **post)
        render_values.update({
            'room_types': room_types,
            'reservation_types': room_types[:1].type_lines_ids.filtered('reservation_type_id'),
            'room_ids': room_types[:1].room_ids,
        })

        return request.render("outpostnosara.reservation", render_values)

    @http.route('/outpost/reserved_date/<int:room_id>', type='json', auth="user", website=True)
    def reserved_date(self, room_id, **post):
        """Get reserved dates of a room."""
        return request.env['pms.reservation.line'].get_reservation_availability(
            room_id, start_date=fields.Date.today()
        ).mapped('date')

    @http.route('/outpost/rooms_availables/<model("pms.room.type"):room_type>', type='json', auth="user", website=True)
    def rooms_availables(self, room_type, **post):
        """Get rooms_availables of a room kind."""
        return {
            'reservation_types': room_type.type_lines_ids.read(['id', 'name', 'code']),
            'room_ids': room_type.room_ids.read(['id', 'name']),
        }

    @http.route('/outpost/validate_reservation/<model("pms.room"):room>', type='json', auth="user", website=True)
    def validate_reservation(self, room, reservation_type_id, start_date, end_date, **post):
        """Get rooms_availables of a room kind."""
        reservation = request.env['pms.reservation.line']
        reservation_type_id = int(reservation_type_id)
        if reservation.get_reservation_availability(room.id, start_date=start_date, end_date=end_date):
            raise ValidationError(_("Room Occupied"))

        values = {
            'preferred_room_id': room.id,
            'pms_property_id': room.pms_property_id,
            'type_id': reservation_type_id,
            'checkin': start_date,
            'checkout': end_date,
            'adults': 1,
            'arrival_hour': room.pms_property_id.default_arrival_hour,
            'departure_hour': room.pms_property_id.default_departure_hour,
        }
        values.update(post)
        reservation = request.website.get_reservation()
        reservation.write(values)
        return reservation.read(['id', 'price_room_services_set'])


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
        values = {
            'membership_tags': crm_tags
        }
        return request.render("outpostnosara.membership_contact", values)
