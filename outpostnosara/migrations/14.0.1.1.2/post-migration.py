from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_pms_property(env)


def update_pms_property(env):
    main_pms_property = env.ref('pms.main_pms_property', False)
    if main_pms_property:
        main_pms_property.write({'email': "reservations@outpostnosara.com"})
