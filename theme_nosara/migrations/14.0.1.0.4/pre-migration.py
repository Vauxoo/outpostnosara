from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    enable_login(env)


def enable_login(env):
    """Remove the deactivated view from the login since it should never have been deactivated"""
    website = env.ref('website.default_website')
    env['ir.ui.view'].with_context(active_test=False).search([
        ('key', '=', 'portal.user_sign_in'),
        ('website_id', '=', website.id),
    ]).unlink()
