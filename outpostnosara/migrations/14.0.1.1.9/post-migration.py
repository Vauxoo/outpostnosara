from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    set_reservation_pin(env)


def set_reservation_pin(env):
    reservations = env['pms.reservation'].search([])
    reservations.set_pin()
