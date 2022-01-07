# © 2022 Vauxoo, S.A. de C.V.
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).


from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortalPOS(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        pos_order = request.env['pos.order']
        pos_order_count = pos_order.search_count([
            '|',
            ('partner_id', '=', partner.id),
            ('employee_id.user_partner_id', 'child_of', [partner.commercial_partner_id.id])
        ]) if pos_order.check_access_rights('read', raise_exception=False) else 0
        values['pos_order_count'] = pos_order_count
        return values

    @http.route(['/my/pos_orders', '/my/pos_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_pos_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        pos_order = request.env['pos.order']

        domain = ['|', ('partner_id', '=', partner.id),
                  ('employee_id.user_partner_id', 'child_of', [partner.commercial_partner_id.id])]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        pos_order_count = pos_order.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/pos_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=pos_order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager
        orders = pos_order.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'pager': pager,
            'default_url': '/my/pos_orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'page_name': 'POS Orders',
        })
        return request.render("website_point_of_sale.portal_my_pos_orders", values)

    @http.route(['/my/pos_orders/<int:pos_order_id>'], type='http', auth="public", website=True)
    def portal_pos_order_page(self, pos_order_id, **kw):
        try:
            order = self._document_check_access('pos.order', pos_order_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = {
            'pos_order': order,
            'bootstrap_formatting': True,
            'page_name': 'POS Orders',
            'partner_id': order.partner_id.id,
        }
        return request.render("website_point_of_sale.portal_pos_orders_page", values)
