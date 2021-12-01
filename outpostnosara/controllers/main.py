# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteOutpost(WebsiteSale):
    @http.route('/outpost/membership', type='http', auth="user", website=True)
    def membership(self, **post):
        """Show Membership Application Form."""
        pricelist = self._get_pricelist_context()[1]
        order = request.website.sale_get_order(force_create=True)
        render_values = self._get_shop_payment_values(order, **post)
        memberships = request.env['product.template'].with_context(pricelist=pricelist.id).search(
            [
                # ('recurring_invoice', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence',
            limit=5,
        )
        render_values['memberships'] = memberships
        render_values['pricelist'] = pricelist
        return request.render("outpostnosara.membership", render_values)
