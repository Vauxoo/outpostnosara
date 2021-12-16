from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_room_type(env)
    portal_template(env)


def update_room_type(env):
    """Update type name by client request"""
    reservation_type_by_hour = env.ref('outpostnosara.reservation_type_by_hour', False)
    if not reservation_type_by_hour:
        return True
    reservation_type_by_hour.name = 'Hourly'


def portal_template(env):
    """Update portal_user to avoid error when new portal user is created"""
    portal_user = env.ref('base.template_portal_user_id', False)
    main_pms_property = env.ref('pms.main_pms_property', False)
    if not portal_user or not main_pms_property:
        return True
    portal_user.write({
        'pms_property_id': main_pms_property,
        'pms_property_ids': main_pms_property,
    })
