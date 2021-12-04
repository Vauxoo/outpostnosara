# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


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
        render_values = {}
        render_values['room_types'] = request.env['pms.room.type'].search([])
        render_values['reservation_types'] = render_values['room_types'][:1].type_lines_ids.reservation_type_id
        render_values['room_ids'] = render_values['room_types'][:1].room_ids
        return request.render("outpostnosara.reservation", render_values)

    @http.route('/outpost/reserved_date', type='json', auth="public", website=True)
    def reserved_date(self, room_id=0, **post):
        """Get reserved dates of a room."""
        reserved_dates = request.env['pms.reservation.line'].search([
            ('room_id', '=', int(room_id))
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
