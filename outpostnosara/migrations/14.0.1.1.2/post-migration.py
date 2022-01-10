from odoo import SUPERUSER_ID, api


def update_reservation_view(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    reservation_views = env['ir.ui.view'].search(
        [('name', '=', 'Reservation Page'), ('key', '=', 'outpostnosara.reservation')])

    if reservation_views:
        for view in reservation_views:
            env['ir.model.data']._update_xmlids([{
                'xml_id': 'outpostnosara.reservation',
                'record': view,
                'noupdate': False}], update=True)


def migrate(cr, version):
    if not version:
        return
    update_reservation_view(cr)
