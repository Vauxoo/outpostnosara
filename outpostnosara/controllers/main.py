# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import http, _
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
            'reservation_types': room_types[:1].type_lines_ids.reservation_type_id,
            'room_ids': room_types[:1].room_ids,
        })

        return request.render("outpostnosara.reservation", render_values)

    @http.route('/outpost/reserved_date', type='json', auth="public", website=True)
    def reserved_date(self, room_id=0, **post):
        """Get reserved dates of a room."""
        reserved_dates = request.env['pms.reservation.line'].search([
            ('room_id', '=', int(room_id)),
            ('state', 'in', ['confirm', 'onboard', 'arrival_delayed']),
        ])
        return reserved_dates.mapped('date')

    @http.route('/outpost/rooms_availables', type='json', auth="public", website=True)
    def rooms_availables(self, room_type_id=0, **post):
        """Get rooms_availables of a room kind."""
        room_type = request.env['pms.room.type'].browse([int(room_type_id)])
        return {
            'reservation_types': room_type.type_lines_ids.reservation_type_id.read(['id', 'name', 'code']),
            'room_ids': room_type.room_ids.read(['id', 'name']),
        }

    @http.route('/outpost/validate_reservation/<model("pms.room"):room_id>', type='json', auth="public", website=True)
    def validate_reservation(self, room_id, reservation_type_id, start_date, end_date, **post):
        """Get rooms_availables of a room kind."""
        reservation = request.env['pms.reservation.line']
        if reservation.get_reservation_availability(room_id.id, reservation_type_id, start_date, end_date=end_date):
            raise ValidationError(_("Room Occupied"))

        reservation = request.website.get_reservation()
        reservation.write({
            'preferred_room_id': room_id.id,
            'pms_property_id': room_id.pms_property_id,
            'checkin': start_date,
            'checkout': end_date,
            'adults': 1,
        })
