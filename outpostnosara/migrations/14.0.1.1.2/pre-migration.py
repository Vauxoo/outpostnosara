from odoo import SUPERUSER_ID, api


def set_external_id_room_type(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    room_types = env['pms.room.type'].search([])

    if room_types:
        for room in room_types:
            external_name = "outpost.%s_room_type" % room.name.replace(' ', '_').lower()
            env['ir.model.data']._update_xmlids([{
                'xml_id': external_name,
                'record': room,
                'noupdate': True}], update=True)


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
    set_external_id_room_type(cr)
    update_reservation_view(cr)
