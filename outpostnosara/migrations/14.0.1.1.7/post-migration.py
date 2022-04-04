from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_logo_url(env)


def update_logo_url(env):
    website = env.ref('website.default_website', False)
    if website:
        website.write({'logo_url': "https://outpostnosara.com"})