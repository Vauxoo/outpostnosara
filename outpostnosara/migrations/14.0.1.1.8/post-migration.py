from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    set_public_user_property(env)


def set_public_user_property(env):
    """Update the public user to avoid error when the reservation of the subscription is created"""
    public_user = env.ref('base.public_user', False)
    main_pms_property = env.ref('pms.main_pms_property', False)
    if not public_user or not main_pms_property:
        return True
    public_user.write({
        'pms_property_id': main_pms_property,
        'pms_property_ids': main_pms_property,
    })
